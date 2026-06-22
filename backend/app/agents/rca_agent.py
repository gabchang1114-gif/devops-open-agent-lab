"""RCA agent placeholder.

Future responsibility: Generate Diagnosis
"""

from app.models.diagnosis import DiagnosisResult


class RCAAgent:
    """Placeholder root cause analysis agent."""

    async def generate_diagnosis(self, evidence: dict) -> DiagnosisResult:
        raise NotImplementedError("RCA agent is not implemented yet.")

    async def generate_report(self, evidence: dict) -> str:
        raise NotImplementedError("RCA report generation is not implemented yet.")
