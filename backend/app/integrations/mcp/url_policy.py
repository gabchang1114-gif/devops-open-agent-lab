"""MCP server URL validation and allowlist matching."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse


class McpUrlPolicyError(ValueError):
    """Raised when an MCP server URL fails security policy checks."""


def normalize_mcp_url(url: str) -> str:
    trimmed = url.strip()
    if not trimmed:
        raise McpUrlPolicyError("MCP server URL is required.")

    parsed = urlparse(trimmed)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise McpUrlPolicyError("MCP server URL must use http or https.")
    if not parsed.netloc:
        raise McpUrlPolicyError("MCP server URL must include a host.")

    path = parsed.path.rstrip("/")
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            "",
            parsed.query,
            "",
        )
    )


def parse_allowed_url_list(raw: str) -> list[str]:
    if not raw.strip():
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def url_matches_pattern(url: str, pattern: str) -> bool:
    normalized_url = normalize_mcp_url(url)
    trimmed_pattern = pattern.strip()
    if not trimmed_pattern:
        return False

    if "://" not in trimmed_pattern:
        host = urlparse(normalized_url).netloc
        pattern_host = trimmed_pattern.lower().split("/")[0]
        return host == pattern_host or host.endswith(f".{pattern_host}")

    normalized_pattern = normalize_mcp_url(trimmed_pattern)
    return (
        normalized_url == normalized_pattern
        or normalized_url.startswith(f"{normalized_pattern}/")
    )


def validate_mcp_url(
    url: str,
    *,
    instance_allowed: list[str],
    user_whitelist: list[str],
    user_blacklist: list[str],
    require_user_whitelist: bool = False,
) -> str:
    """Validate and return a normalized MCP URL."""
    normalized = normalize_mcp_url(url)

    for blocked in user_blacklist:
        if url_matches_pattern(normalized, blocked):
            raise McpUrlPolicyError(
                "This MCP server URL is blocked by your blacklist."
            )

    if instance_allowed:
        if not any(url_matches_pattern(normalized, allowed) for allowed in instance_allowed):
            raise McpUrlPolicyError(
                "This MCP server URL is not allowed by the platform administrator."
            )

    if require_user_whitelist and user_whitelist:
        if not any(url_matches_pattern(normalized, allowed) for allowed in user_whitelist):
            raise McpUrlPolicyError(
                "Add this MCP server to your whitelist before using it."
            )

    return normalized
