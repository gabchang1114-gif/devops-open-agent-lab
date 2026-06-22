"""Cached Kubernetes resource payloads for investigation reuse."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class InvestigationCache:
    """Raw Kubernetes payloads collected once and reused across inspectors."""

    namespaces: list[dict[str, Any]] = field(default_factory=list)
    deployments: list[dict[str, Any]] = field(default_factory=list)
    replica_sets: list[dict[str, Any]] = field(default_factory=list)
    pods: list[dict[str, Any]] = field(default_factory=list)
    services: list[dict[str, Any]] = field(default_factory=list)
    ingresses: list[dict[str, Any]] = field(default_factory=list)
    endpoints: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
