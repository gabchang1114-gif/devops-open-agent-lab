"""Cloud Cost Detector discovery orchestration."""

from __future__ import annotations

from app.modules.cloud_cost_detector.models.schemas import (
    CloudCostAccountResponse,
    CloudCostAnalyzeInventoryRequest,
    CloudCostAnalyzeInventoryResponse,
    CloudCostAnalyzeRequest,
    CloudCostAnalyzeResponse,
)
from app.modules.cloud_cost_detector.services.cost_analysis_service import CloudCostAnalysisService


class CloudCostDiscoveryService:
    """Service layer for Cloud Cost Detector AWS inventory and analysis."""

    def __init__(self, analysis_service: CloudCostAnalysisService | None = None) -> None:
        self.analysis_service = analysis_service or CloudCostAnalysisService()

    async def get_account(self, region: str | None = None) -> CloudCostAccountResponse:
        target_region = region or "us-east-1"
        return await self.analysis_service.discovery_engine.get_account(target_region)

    async def list_regions(self, region: str | None = None) -> list[str]:
        target_region = region or "us-east-1"
        return await self.analysis_service.discovery_engine.list_regions(target_region)

    async def analyze(self, request: CloudCostAnalyzeRequest) -> CloudCostAnalyzeResponse:
        return await self.analysis_service.analyze_region(
            account_id=request.account_id,
            region=request.region,
            include_ai=request.include_ai,
        )

    async def analyze_inventory(
        self,
        request: CloudCostAnalyzeInventoryRequest,
    ) -> CloudCostAnalyzeInventoryResponse:
        return await self.analysis_service.analyze_inventory(request)
