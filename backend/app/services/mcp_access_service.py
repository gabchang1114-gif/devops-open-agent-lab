"""User MCP whitelist/blacklist management and URL policy enforcement."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.models import UserMcpBlacklistEntry, UserMcpWhitelistEntry
from app.integrations.mcp.url_policy import (
    McpUrlPolicyError,
    normalize_mcp_url,
    parse_allowed_url_list,
    url_matches_pattern,
    validate_mcp_url,
)
from app.models.mcp_integration import (
    McpBlacklistEntry,
    McpWhitelistCreate,
    McpWhitelistEntry,
)


class McpAccessService:
    """Manage per-user MCP URL whitelist/blacklist and enforce policy."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def instance_allowed_urls(self) -> list[str]:
        return parse_allowed_url_list(self.settings.mcp_allowed_server_urls)

    @property
    def instance_url_restrictions_enabled(self) -> bool:
        return bool(self.instance_allowed_urls)

    async def list_whitelist(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> list[McpWhitelistEntry]:
        rows = await self._list_whitelist_rows(session, user_id)
        return [
            McpWhitelistEntry(
                id=str(row.id),
                name=row.name,
                server_url=row.server_url,
            )
            for row in rows
        ]

    async def list_blacklist(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> list[McpBlacklistEntry]:
        rows = await self._list_blacklist_rows(session, user_id)
        return [
            McpBlacklistEntry(
                id=str(row.id),
                server_url=row.server_url,
            )
            for row in rows
        ]

    async def add_whitelist_entry(
        self,
        session: AsyncSession,
        user_id: UUID,
        payload: McpWhitelistCreate,
    ) -> McpWhitelistEntry:
        name = payload.name.strip()
        if not name:
            raise McpUrlPolicyError("Whitelist entry name is required.")

        blacklist_urls = await self._blacklist_urls(session, user_id)
        normalized = validate_mcp_url(
            payload.server_url,
            instance_allowed=self.instance_allowed_urls,
            user_whitelist=[],
            user_blacklist=blacklist_urls,
            require_user_whitelist=False,
        )

        existing = await self._list_whitelist_rows(session, user_id)
        for row in existing:
            if url_matches_pattern(normalized, row.server_url):
                raise McpUrlPolicyError(
                    "This MCP server URL is already in your whitelist."
                )

        entry = UserMcpWhitelistEntry(
            user_id=user_id,
            name=name,
            server_url=normalized,
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        return McpWhitelistEntry(
            id=str(entry.id),
            name=entry.name,
            server_url=entry.server_url,
        )

    async def remove_whitelist_entry(
        self,
        session: AsyncSession,
        user_id: UUID,
        entry_id: UUID,
    ) -> None:
        row = await self._get_whitelist_row(session, user_id, entry_id)
        if row is None:
            raise McpUrlPolicyError("Whitelist entry not found.")
        await session.delete(row)
        await session.commit()

    async def add_blacklist_entry(
        self,
        session: AsyncSession,
        user_id: UUID,
        server_url: str,
    ) -> McpBlacklistEntry:
        normalized = normalize_mcp_url(server_url)
        existing = await self._list_blacklist_rows(session, user_id)
        for row in existing:
            if url_matches_pattern(normalized, row.server_url):
                raise McpUrlPolicyError(
                    "This MCP server URL is already in your blacklist."
                )

        entry = UserMcpBlacklistEntry(
            user_id=user_id,
            server_url=normalized,
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        return McpBlacklistEntry(
            id=str(entry.id),
            server_url=entry.server_url,
        )

    async def remove_blacklist_entry(
        self,
        session: AsyncSession,
        user_id: UUID,
        entry_id: UUID,
    ) -> None:
        row = await self._get_blacklist_row(session, user_id, entry_id)
        if row is None:
            raise McpUrlPolicyError("Blacklist entry not found.")
        await session.delete(row)
        await session.commit()

    async def validate_active_url(
        self,
        session: AsyncSession,
        user_id: UUID,
        server_url: str,
    ) -> str:
        if not server_url.strip():
            return ""

        whitelist_urls = await self._whitelist_urls(session, user_id)
        blacklist_urls = await self._blacklist_urls(session, user_id)
        require_user_whitelist = bool(whitelist_urls)

        return validate_mcp_url(
            server_url,
            instance_allowed=self.instance_allowed_urls,
            user_whitelist=whitelist_urls,
            user_blacklist=blacklist_urls,
            require_user_whitelist=require_user_whitelist,
        )

    async def validate_resolved_url(
        self,
        session: AsyncSession,
        user_id: UUID | None,
        server_url: str,
    ) -> str:
        if not server_url.strip():
            raise McpUrlPolicyError("MCP server URL is required.")

        blacklist_urls: list[str] = []
        whitelist_urls: list[str] = []
        require_user_whitelist = False

        if user_id is not None:
            blacklist_urls = await self._blacklist_urls(session, user_id)
            whitelist_urls = await self._whitelist_urls(session, user_id)
            require_user_whitelist = bool(whitelist_urls)

        return validate_mcp_url(
            server_url,
            instance_allowed=self.instance_allowed_urls,
            user_whitelist=whitelist_urls,
            user_blacklist=blacklist_urls,
            require_user_whitelist=require_user_whitelist,
        )

    async def _whitelist_urls(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> list[str]:
        rows = await self._list_whitelist_rows(session, user_id)
        return [row.server_url for row in rows]

    async def _blacklist_urls(
        self,
        session: AsyncSession,
        user_id: UUID,
    ) -> list[str]:
        rows = await self._list_blacklist_rows(session, user_id)
        return [row.server_url for row in rows]

    @staticmethod
    async def _list_whitelist_rows(
        session: AsyncSession,
        user_id: UUID,
    ) -> list[UserMcpWhitelistEntry]:
        result = await session.execute(
            select(UserMcpWhitelistEntry)
            .where(UserMcpWhitelistEntry.user_id == user_id)
            .order_by(UserMcpWhitelistEntry.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def _list_blacklist_rows(
        session: AsyncSession,
        user_id: UUID,
    ) -> list[UserMcpBlacklistEntry]:
        result = await session.execute(
            select(UserMcpBlacklistEntry)
            .where(UserMcpBlacklistEntry.user_id == user_id)
            .order_by(UserMcpBlacklistEntry.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def _get_whitelist_row(
        session: AsyncSession,
        user_id: UUID,
        entry_id: UUID,
    ) -> UserMcpWhitelistEntry | None:
        result = await session.execute(
            select(UserMcpWhitelistEntry).where(
                UserMcpWhitelistEntry.user_id == user_id,
                UserMcpWhitelistEntry.id == entry_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_blacklist_row(
        session: AsyncSession,
        user_id: UUID,
        entry_id: UUID,
    ) -> UserMcpBlacklistEntry | None:
        result = await session.execute(
            select(UserMcpBlacklistEntry).where(
                UserMcpBlacklistEntry.user_id == user_id,
                UserMcpBlacklistEntry.id == entry_id,
            )
        )
        return result.scalar_one_or_none()
