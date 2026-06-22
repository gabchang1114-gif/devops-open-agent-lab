"""Investigator agent placeholder.

Future responsibility: Collect Evidence
"""

from app.models.diagnosis import InvestigationRequest


class InvestigatorAgent:
    """Placeholder investigator agent."""

    async def collect_evidence(self, request: InvestigationRequest) -> dict:
        raise NotImplementedError("Investigator agent is not implemented yet.")

    async def run(self, request: InvestigationRequest) -> dict:
        raise NotImplementedError("Investigator agent is not implemented yet.")
