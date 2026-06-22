"""Incident memory placeholder.

Future memory will store:
    - Previous investigations
    - RCA reports
    - Recurring issues
    - Successful fixes
    - Operational runbooks
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class IncidentRecord:
    incident_id: str
    cluster_id: str
    summary: str
    root_cause: str | None = None
    fix_applied: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class IncidentMemory:
    """Placeholder interface for incident memory."""

    async def store_investigation(self, record: IncidentRecord) -> None:
        raise NotImplementedError("Incident memory is not implemented yet.")

    async def get_similar_incidents(self, cluster_id: str, query: str) -> list[IncidentRecord]:
        raise NotImplementedError("Incident memory is not implemented yet.")

    async def store_runbook(self, cluster_id: str, title: str, content: str) -> None:
        raise NotImplementedError("Runbook storage is not implemented yet.")
