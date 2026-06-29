"""Cloud Cost Detector investigation orchestration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.modules.cloud_cost_detector.models.schemas import CloudCostInvestigationResponse
from app.modules.cloud_cost_detector.services.cost_analysis_service import CloudCostAnalysisService

ProgressCallback = Callable[[str, int], Awaitable[None] | None]


class CloudCostInvestigationService:
    """Async investigation wrapper used by the shared investigation job pipeline."""

    def __init__(self, analysis_service: CloudCostAnalysisService | None = None) -> None:
        self.analysis_service = analysis_service or CloudCostAnalysisService()

    async def investigate(
        self,
        account_id: str,
        region: str,
        include_ai: bool = True,
        on_progress: ProgressCallback | None = None,
        user_id: str | None = None,
    ) -> CloudCostInvestigationResponse:
        return await self.analysis_service.investigate(
            account_id=account_id,
            region=region,
            include_ai=include_ai,
            on_progress=on_progress,
            user_id=user_id,
        )
