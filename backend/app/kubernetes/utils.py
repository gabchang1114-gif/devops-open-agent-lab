"""Shared helpers for Kubernetes investigation modules."""

from datetime import datetime, timezone
from typing import Any


def resource_ref(kind: str, name: str) -> str:
    return f"{kind.lower()}/{name}"


def parse_k8s_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def age_in_seconds(value: str | None) -> float | None:
    parsed = parse_k8s_timestamp(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - parsed).total_seconds()


def extract_items(payload: dict | list | None) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return payload
    return payload.get("items", [])


def to_resource_item(item: dict[str, Any], include_spec: bool = False) -> dict[str, Any]:
    metadata = item.get("metadata", {})
    result = {
        "name": metadata.get("name", ""),
        "namespace": metadata.get("namespace", ""),
        "uid": metadata.get("uid"),
        "labels": metadata.get("labels") or {},
        "created_at": metadata.get("creationTimestamp"),
        "metadata": {
            "annotations": metadata.get("annotations") or {},
            "owner_references": metadata.get("ownerReferences") or [],
        },
    }

    if include_spec:
        spec = item.get("spec") or {}
        result["metadata"]["spec"] = {
            key: spec.get(key)
            for key in ("selector", "type", "clusterIP", "ports", "rules", "tls", "accessModes")
            if key in spec
        }

    return result


def secret_metadata_only(item: dict[str, Any]) -> dict[str, Any]:
    metadata = item.get("metadata", {})
    return {
        "name": metadata.get("name", ""),
        "namespace": metadata.get("namespace", ""),
        "uid": metadata.get("uid"),
        "labels": metadata.get("labels") or {},
        "created_at": metadata.get("creationTimestamp"),
        "metadata": {
            "type": item.get("type"),
            "annotations": metadata.get("annotations") or {},
        },
    }
