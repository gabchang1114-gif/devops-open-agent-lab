"""Diagnosis service for AI reasoning over investigation evidence."""

from typing import Any

from loguru import logger

from app.ai.root_cause_analyzer import RootCauseAnalyzer
from app.models.diagnosis import DiagnoseResponse, DiagnosisResult
from app.models.investigation import InvestigationResponse


class DiagnosisService:
    """Generate AI diagnosis from investigation payloads."""

    def __init__(self, analyzer: RootCauseAnalyzer | None = None) -> None:
        self.analyzer = analyzer or RootCauseAnalyzer()

    async def diagnose(
        self,
        investigation: InvestigationResponse | dict[str, Any],
    ) -> DiagnosisResult:
        return await self.analyzer.analyze(investigation)

    async def diagnose_payload(self, investigation_payload: dict[str, Any]) -> DiagnoseResponse:
        logger.info("Running AI diagnosis from provided investigation payload")
        diagnosis = await self.analyze_payload(investigation_payload)
        status = "success"
        if diagnosis.llm_error:
            status = "partial_success"
        return DiagnoseResponse(status=status, diagnosis=diagnosis)

    async def analyze_payload(self, investigation_payload: dict[str, Any]) -> DiagnosisResult:
        return await self.analyzer.analyze(investigation_payload)
