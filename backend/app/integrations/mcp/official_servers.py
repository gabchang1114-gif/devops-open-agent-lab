"""Curated official remote MCP servers supported by DevOps Open Agent."""

from __future__ import annotations

from dataclasses import dataclass

from app.integrations.mcp.url_policy import url_matches_pattern
from app.models.mcp_integration import McpOfficialServer


@dataclass(frozen=True)
class OfficialMcpServerDefinition:
    id: str
    name: str
    server_url: str
    description: str
    docs_url: str
    auth_hint: str
    category: str


OFFICIAL_MCP_SERVER_DEFINITIONS: tuple[OfficialMcpServerDefinition, ...] = (
    OfficialMcpServerDefinition(
        id="github",
        name="GitHub",
        server_url="https://api.githubcopilot.com/mcp/",
        description="Repositories, pull requests, issues, actions, and Copilot tools.",
        docs_url="https://github.com/github/github-mcp-server/blob/main/docs/remote-server.md",
        auth_hint="GitHub personal access token (Bearer)",
        category="devops",
    ),
    OfficialMcpServerDefinition(
        id="linear",
        name="Linear",
        server_url="https://mcp.linear.app/mcp",
        description="Issues, projects, comments, cycles, and team workflows.",
        docs_url="https://linear.app/docs/mcp",
        auth_hint="OAuth 2.1 via browser, or Bearer token if your client supports it",
        category="devops",
    ),
    OfficialMcpServerDefinition(
        id="sentry",
        name="Sentry",
        server_url="https://mcp.sentry.dev/mcp",
        description="Issues, events, releases, and debugging context from Sentry.",
        docs_url="https://github.com/getsentry/sentry-mcp",
        auth_hint="Sentry OAuth or Sentry-Bearer access token",
        category="observability",
    ),
    OfficialMcpServerDefinition(
        id="github-readonly",
        name="GitHub (read-only)",
        server_url="https://api.githubcopilot.com/mcp/readonly",
        description="Read-only GitHub tools for safer PR and repository inspection.",
        docs_url="https://github.com/github/github-mcp-server/blob/main/docs/remote-server.md",
        auth_hint="GitHub personal access token (Bearer)",
        category="devops",
    ),
)


def list_official_mcp_servers(
    instance_allowed_urls: list[str] | None = None,
) -> list[McpOfficialServer]:
    """Return official MCP servers, filtered by instance allowlist when configured."""
    allowed = instance_allowed_urls or []
    servers: list[McpOfficialServer] = []
    for definition in OFFICIAL_MCP_SERVER_DEFINITIONS:
        if allowed and not any(
            url_matches_pattern(definition.server_url, pattern) for pattern in allowed
        ):
            continue
        servers.append(
            McpOfficialServer(
                id=definition.id,
                name=definition.name,
                server_url=definition.server_url,
                description=definition.description,
                docs_url=definition.docs_url,
                auth_hint=definition.auth_hint,
                category=definition.category,
            )
        )
    return servers


def find_official_server_by_url(server_url: str) -> McpOfficialServer | None:
    trimmed = server_url.strip()
    if not trimmed:
        return None
    for definition in OFFICIAL_MCP_SERVER_DEFINITIONS:
        if url_matches_pattern(trimmed, definition.server_url):
            return McpOfficialServer(
                id=definition.id,
                name=definition.name,
                server_url=definition.server_url,
                description=definition.description,
                docs_url=definition.docs_url,
                auth_hint=definition.auth_hint,
                category=definition.category,
            )
    return None
