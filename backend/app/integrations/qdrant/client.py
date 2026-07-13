"""Minimal async Qdrant REST client.

Uses the HTTP API directly (via httpx) so we avoid adding a heavy client
dependency. Covers only what the RAG feature needs: collection management,
point upsert, and vector search.
"""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger


class QdrantError(Exception):
    """Raised when a Qdrant request fails."""


class QdrantClient:
    """Small wrapper over the Qdrant HTTP API."""

    def __init__(
        self,
        url: str,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (url or "").rstrip("/")
        self.api_key = (api_key or "").strip() or None
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.base_url:
            raise QdrantError("Qdrant URL is not configured")
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=json,
                )
        except httpx.HTTPError as exc:
            raise QdrantError(f"Qdrant request failed: {exc}") from exc

        if response.status_code == 401 or response.status_code == 403:
            raise QdrantError("Qdrant authentication failed — check the API key")
        if response.status_code >= 400:
            raise QdrantError(
                f"Qdrant API error ({response.status_code}): {response.text[:300]}"
            )
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError as exc:
            raise QdrantError("Qdrant returned a non-JSON response") from exc

    async def health(self) -> dict[str, Any]:
        """Return root info (Qdrant version). Confirms connectivity."""
        return await self._request("GET", "/")

    async def collection_exists(self, collection: str) -> bool:
        try:
            await self._request("GET", f"/collections/{collection}")
            return True
        except QdrantError as exc:
            if "404" in str(exc):
                return False
            raise

    async def collection_info(self, collection: str) -> dict[str, Any] | None:
        try:
            result = await self._request("GET", f"/collections/{collection}")
            return result.get("result")
        except QdrantError as exc:
            if "404" in str(exc):
                return None
            raise

    async def ensure_collection(self, collection: str, vector_size: int) -> None:
        """Create the collection with cosine distance if it does not exist."""
        if await self.collection_exists(collection):
            return
        logger.info(
            "Creating Qdrant collection | name={} size={}", collection, vector_size
        )
        await self._request(
            "PUT",
            f"/collections/{collection}",
            json={"vectors": {"size": vector_size, "distance": "Cosine"}},
        )

    async def upsert_point(
        self,
        collection: str,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        await self._request(
            "PUT",
            f"/collections/{collection}/points?wait=true",
            json={
                "points": [
                    {"id": point_id, "vector": vector, "payload": payload}
                ]
            },
        )

    async def search(
        self,
        collection: str,
        vector: list[float],
        limit: int = 4,
        query_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        body: dict[str, Any] = {
            "vector": vector,
            "limit": limit,
            "with_payload": True,
        }
        if query_filter:
            body["filter"] = query_filter
        result = await self._request(
            "POST",
            f"/collections/{collection}/points/search",
            json=body,
        )
        return result.get("result", []) or []

    async def count(self, collection: str) -> int | None:
        try:
            result = await self._request(
                "POST",
                f"/collections/{collection}/points/count",
                json={"exact": True},
            )
            return result.get("result", {}).get("count")
        except QdrantError:
            return None
