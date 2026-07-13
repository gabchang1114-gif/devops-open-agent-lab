"""Retrieval Augmented Generation over past investigations, backed by Qdrant.

Two responsibilities:
1. index_investigation — store a completed investigation's diagnosis as a vector.
2. enrich — retrieve similar past investigations and attach them to the payload
   under ``rag_context`` so the prompt builders can feed them to the LLM.

All failures are logged and swallowed: RAG must never break an investigation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from loguru import logger

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal
from app.integrations.qdrant.client import QdrantClient, QdrantError
from app.integrations.qdrant.embeddings import (
    EmbeddingClient,
    EmbeddingError,
    resolve_embedding_provider,
)
from app.services.qdrant_settings_service import QdrantConnection, QdrantSettingsService

_MAX_TEXT_CHARS = 6000


class RagService:
    """Index and retrieve investigation knowledge from Qdrant."""

    def __init__(
        self,
        settings: Settings | None = None,
        settings_service: QdrantSettingsService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.settings_service = settings_service or QdrantSettingsService(self.settings)

    # ------------------------------------------------------------------ index

    async def index_investigation(
        self,
        *,
        user_id: str | UUID | None,
        agent_type: str,
        investigation_id: str,
        scope_label: str,
        status: str,
        diagnosis: Any,
    ) -> None:
        parsed_user_id = self._parse_user_id(user_id)
        try:
            async with SessionLocal() as session:
                connection = await self.settings_service.resolve_connection(
                    session,
                    parsed_user_id,
                    agent_type=agent_type,
                )
            if connection is None:
                return

            text, payload = self._build_index_record(
                agent_type=agent_type,
                investigation_id=investigation_id,
                scope_label=scope_label,
                status=status,
                diagnosis=diagnosis,
                user_id=parsed_user_id,
            )
            if not text:
                return

            vector = await EmbeddingClient(self.settings).embed(text)
            client = QdrantClient(connection.url, connection.api_key)
            await client.ensure_collection(connection.collection, len(vector))
            await client.upsert_point(
                connection.collection,
                investigation_id,
                vector,
                payload,
            )
            logger.info(
                "Indexed investigation into RAG | agent={} id={} collection={}",
                agent_type,
                investigation_id,
                connection.collection,
            )
        except (QdrantError, EmbeddingError) as exc:
            logger.warning(
                "RAG indexing skipped | agent={} id={} error={}",
                agent_type,
                investigation_id,
                exc,
            )
        except Exception as exc:  # never break the investigation pipeline
            logger.exception("RAG indexing failed | id={} error={}", investigation_id, exc)

    # --------------------------------------------------------------- retrieve

    async def enrich(
        self,
        payload: dict[str, Any],
        user_id: str | UUID | None,
        agent_type: str,
    ) -> dict[str, Any]:
        """Attach similar past investigations to ``payload['rag_context']``."""
        parsed_user_id = self._parse_user_id(user_id)
        try:
            async with SessionLocal() as session:
                connection = await self.settings_service.resolve_connection(
                    session,
                    parsed_user_id,
                    agent_type=agent_type,
                )
            if connection is None:
                enriched = dict(payload)
                enriched["rag_context"] = {
                    "enabled": True,
                    "connected": False,
                    "reason": "Qdrant is not configured for this agent.",
                    "matches": [],
                }
                return enriched

            query_text = self._build_query_text(payload, agent_type)
            if not query_text:
                return payload

            matches = await self._search(connection, query_text, parsed_user_id, agent_type)
            enriched = dict(payload)
            enriched["rag_context"] = {
                "enabled": True,
                "connected": True,
                "collection": connection.collection,
                "match_count": len(matches),
                "matches": matches,
            }
            logger.info(
                "RAG context attached | agent={} matches={}", agent_type, len(matches)
            )
            return enriched
        except (QdrantError, EmbeddingError) as exc:
            logger.warning("RAG retrieval skipped | agent={} error={}", agent_type, exc)
            enriched = dict(payload)
            enriched["rag_context"] = {
                "enabled": True,
                "connected": False,
                "reason": str(exc),
                "matches": [],
            }
            return enriched
        except Exception as exc:
            logger.exception("RAG retrieval failed | agent={} error={}", agent_type, exc)
            return payload

    async def _search(
        self,
        connection: QdrantConnection,
        query_text: str,
        user_id: UUID | None,
        agent_type: str,
    ) -> list[dict[str, Any]]:
        client = QdrantClient(connection.url, connection.api_key)
        if not await client.collection_exists(connection.collection):
            return []

        vector = await EmbeddingClient(self.settings).embed(query_text)
        must: list[dict[str, Any]] = [
            {"key": "agent_type", "match": {"value": agent_type}}
        ]
        if user_id is not None:
            must.append({"key": "user_id", "match": {"value": str(user_id)}})

        results = await client.search(
            connection.collection,
            vector,
            limit=max(1, self.settings.rag_max_results),
            query_filter={"must": must},
        )

        matches: list[dict[str, Any]] = []
        for item in results:
            item_payload = item.get("payload") or {}
            matches.append(
                {
                    "scope": item_payload.get("scope"),
                    "root_cause": item_payload.get("root_cause"),
                    "summary": item_payload.get("summary"),
                    "suggested_fix": item_payload.get("suggested_fix"),
                    "confidence_score": item_payload.get("confidence_score"),
                    "created_at": item_payload.get("created_at"),
                    "similarity": round(float(item.get("score", 0.0)), 3),
                }
            )
        return matches

    # ------------------------------------------------------------ text helpers

    def _build_index_record(
        self,
        *,
        agent_type: str,
        investigation_id: str,
        scope_label: str,
        status: str,
        diagnosis: Any,
        user_id: UUID | None,
    ) -> tuple[str, dict[str, Any]]:
        root_cause = getattr(diagnosis, "root_cause", "") or ""
        summary = getattr(diagnosis, "summary", "") or ""
        suggested_fix = getattr(diagnosis, "suggested_fix", "") or ""
        confidence = getattr(diagnosis, "confidence_score", None)

        text_parts = [scope_label, root_cause, summary, suggested_fix]
        text = "\n".join(part for part in text_parts if part).strip()[:_MAX_TEXT_CHARS]

        payload = {
            "user_id": str(user_id) if user_id else None,
            "agent_type": agent_type,
            "investigation_id": investigation_id,
            "scope": scope_label,
            "status": status,
            "root_cause": root_cause[:2000],
            "summary": summary[:2000],
            "suggested_fix": suggested_fix[:2000],
            "confidence_score": confidence,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return text, payload

    def _build_query_text(self, payload: dict[str, Any], agent_type: str) -> str:
        normalized = agent_type.replace("-", "_")
        if normalized == "aws":
            return self._build_aws_query_text(payload)
        if normalized == "cloud_cost":
            return self._build_cloud_cost_query_text(payload)
        return self._build_kubernetes_query_text(payload)

    def _build_kubernetes_query_text(self, payload: dict[str, Any]) -> str:
        parts: list[str] = []
        cluster = payload.get("cluster", {}) or {}
        cluster_name = cluster.get("name") or cluster.get("cluster_id") or ""
        if cluster_name:
            parts.append(f"Kubernetes cluster {cluster_name}")

        investigation = payload.get("investigation", {}) or {}
        pods = investigation.get("pods", {}) or {}
        for pod in (pods.get("problematic_pods") or [])[:10]:
            parts.append(
                " ".join(
                    str(value)
                    for value in (
                        pod.get("name"),
                        pod.get("namespace"),
                        pod.get("status"),
                        pod.get("reason"),
                        pod.get("message"),
                    )
                    if value
                )
            )
        events = investigation.get("events", {}) or {}
        for finding in (events.get("findings") or [])[:10]:
            parts.append(
                " ".join(
                    str(value)
                    for value in (finding.get("reason"), finding.get("message"))
                    if value
                )
            )
        return self._join(parts)

    def _build_aws_query_text(self, payload: dict[str, Any]) -> str:
        parts: list[str] = []
        investigation = payload.get("investigation", {}) or {}
        account = payload.get("account", {}) or {}
        parts.append(
            f"AWS {investigation.get('issue_type', 'full_scan')} "
            f"account {account.get('account_id', '')} region {account.get('region', '')}"
        )
        if investigation.get("query"):
            parts.append(str(investigation["query"]))

        resources = payload.get("resources", {}) or {}
        for instance in (resources.get("ec2_instances") or [])[:8]:
            state = instance.get("state")
            if state and str(state).lower() not in {"running"}:
                parts.append(f"EC2 {instance.get('instance_id')} state {state}")
        return self._join(parts)

    def _build_cloud_cost_query_text(self, payload: dict[str, Any]) -> str:
        parts: list[str] = []
        investigation = payload.get("investigation", {}) or {}
        parts.append(
            f"AWS cloud cost account {investigation.get('account_id', '')} "
            f"region {investigation.get('region', '')}"
        )
        if investigation.get("query"):
            parts.append(str(investigation["query"]))
        return self._join(parts)

    @staticmethod
    def _join(parts: list[str]) -> str:
        text = "\n".join(part.strip() for part in parts if part and part.strip())
        return text.strip()[:_MAX_TEXT_CHARS]

    # ---------------------------------------------------------------- testing

    async def test_connection(self, connection: QdrantConnection) -> dict[str, Any]:
        """Validate connectivity + embeddings for the integration test button."""
        client = QdrantClient(connection.url, connection.api_key)
        await client.health()
        vector_count = None
        if await client.collection_exists(connection.collection):
            vector_count = await client.count(connection.collection)

        provider = resolve_embedding_provider(self.settings)
        dimension: int | None = None
        try:
            probe = await EmbeddingClient(self.settings).embed("connection test")
            dimension = len(probe)
        except EmbeddingError as exc:
            raise QdrantError(
                f"Qdrant reachable, but embeddings failed: {exc}"
            ) from exc

        return {
            "collection": connection.collection,
            "vector_count": vector_count,
            "embedding_provider": provider,
            "embedding_dimension": dimension,
        }

    @staticmethod
    def _parse_user_id(user_id: str | UUID | None) -> UUID | None:
        if user_id is None:
            return None
        if isinstance(user_id, UUID):
            return user_id
        try:
            return UUID(user_id)
        except ValueError:
            return None


rag_service = RagService()
