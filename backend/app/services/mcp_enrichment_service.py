"""Enrich investigation payloads with MCP server context before AI analysis."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from loguru import logger

from app.db.session import SessionLocal
from app.integrations.mcp.client import McpClient, McpClientError
from app.services.mcp_settings_service import McpSettingsService


class McpEnrichmentService:
    """Fetch MCP tools/resources and attach them to investigation evidence."""

    def __init__(
        self,
        settings_service: McpSettingsService | None = None,
        client: McpClient | None = None,
    ) -> None:
        self.settings_service = settings_service or McpSettingsService()
        self.client = client or McpClient()

    async def enrich(
        self,
        payload: dict[str, Any],
        user_id: str | UUID | None,
        agent_type: str,
    ) -> dict[str, Any]:
        parsed_user_id = self._parse_user_id(user_id)

        async with SessionLocal() as session:
            server_url, api_key = await self.settings_service.resolve_connection(
                session,
                parsed_user_id,
                agent_type=agent_type,
            )

        if not server_url:
            return payload

        try:
            probe = await self.client.probe_server(server_url, api_key)
        except McpClientError as exc:
            logger.warning(
                "MCP enrichment skipped | agent={} user={} error={}",
                agent_type,
                parsed_user_id,
                exc,
            )
            enriched = dict(payload)
            enriched["mcp_enrichment"] = {
                "connected": False,
                "server_url": server_url,
                "error": str(exc),
            }
            return enriched

        enriched = dict(payload)
        enriched["mcp_enrichment"] = {
            "connected": True,
            "server_url": server_url,
            "tool_count": probe["tool_count"],
            "resource_count": probe["resource_count"],
            "tools": probe["tools"][:25],
            "resources": probe["resources"][:25],
        }
        logger.info(
            "MCP enrichment attached | agent={} tools={} resources={}",
            agent_type,
            probe["tool_count"],
            probe["resource_count"],
        )
        return enriched

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


mcp_enrichment_service = McpEnrichmentService()
