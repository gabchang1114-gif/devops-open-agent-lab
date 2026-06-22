"""Shared AWS module helpers."""

from typing import Any


def aws_ref(resource_type: str, resource_id: str) -> str:
    return f"{resource_type.lower()}/{resource_id}"


def tag_name(tags: list[dict[str, str]] | None) -> str | None:
    if not tags:
        return None
    for tag in tags:
        if tag.get("Key") == "Name":
            return tag.get("Value")
    return None


def parse_tags(tags: list[dict[str, str]] | None) -> dict[str, str]:
    if not tags:
        return {}
    parsed: dict[str, str] = {}
    for tag in tags:
        key = tag.get("Key")
        if key:
            parsed[str(key)] = str(tag.get("Value") or "")
    return parsed


def chunk_list(items: list[str], size: int = 100) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def safe_get(payload: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current
