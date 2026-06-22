"""Cloud Cost Detector analysis orchestration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import NamedTuple

from loguru import logger

from app.core.errors import sanitize_error_message
from app.modules.aws.errors import AwsCredentialsError, AwsError
from app.modules.cloud_cost_detector.ai.analysis_adapter import analysis_to_diagnosis, create_failed_analysis
from app.modules.cloud_cost_detector.ai.cost_analyzer import CloudCostAnalyzer
from app.modules.cloud_cost_detector.ai.confidence_engine import CloudCostConfidenceEngine
from app.modules.cloud_cost_detector.ai.context_builder import CloudCostContextBuilder
from app.modules.cloud_cost_detector.ai.savings_enricher import enrich_analysis_with_savings
from app.modules.cloud_cost_detector.analysis.cost_estimator import CloudCostEstimator
from app.modules.cloud_cost_detector.analysis.unused_resource_analyzer import UnusedResourceAnalyzer
from app.modules.cloud_cost_detector.discovery.aws_discovery import AwsCostDiscoveryEngine
from app.modules.cloud_cost_detector.models.schemas import (
    CloudCostAnalyzeInventoryRequest,
    CloudCostAnalyzeInventoryResponse,
    CloudCostAnalyzeResponse,
    CloudCostFindingsSummary,
    CloudCostInvestigationResponse,
    CloudCostResourceInventory,
    CloudCostResourceSummary,
    CloudCostSavingsSummary,
)

ProgressCallback = Callable[[str, int], Awaitable[None] | None]

CLOUD_COST_STEP_PROGRESS = {
    "Account Discovery": 10,
    "Resource Discovery": 45,
    "Unused Resource Analysis": 75,
    "Cost Estimation": 82,
    "AI Cost Analysis": 95,
}


class DiscoveryAssessment(NamedTuple):
    inventory_response: CloudCostAnalyzeResponse
    heuristic_findings: CloudCostFindingsSummary
    investigation_payload: CloudCostInvestigationResponse


class CloudCostAnalysisService:
    """Single orchestration path for discovery, heuristics, and AI cost analysis."""

    def __init__(self) -> None:
        self.discovery_engine = AwsCostDiscoveryEngine()
        self.unused_analyzer = UnusedResourceAnalyzer()
        self.cost_estimator = CloudCostEstimator()
        self.cost_analyzer = CloudCostAnalyzer()
        self.confidence_engine = CloudCostConfidenceEngine()
        self.context_builder = CloudCostContextBuilder()

    async def _report_progress(
        self,
        callback: ProgressCallback | None,
        step: str,
    ) -> None:
        if callback is None:
            return
        progress = CLOUD_COST_STEP_PROGRESS.get(step, 0)
        result = callback(step, progress)
        if result is not None:
            await result

    async def _discover_and_assess(
        self,
        account_id: str,
        region: str,
        on_progress: ProgressCallback | None = None,
    ) -> DiscoveryAssessment:
        await self._report_progress(on_progress, "Account Discovery")
        await self.discovery_engine.get_account(region)

        await self._report_progress(on_progress, "Resource Discovery")
        inventory = await self.discovery_engine.analyze(account_id, region)

        await self._report_progress(on_progress, "Unused Resource Analysis")
        heuristic_findings = self.unused_analyzer.analyze(inventory.resources)

        inventory_response = CloudCostAnalyzeResponse(
            status="success",
            account=inventory.account,
            region=inventory.region,
            collected_at=inventory.collected_at,
            resources=inventory.resources,
            summary=inventory.summary,
            notes=inventory.notes,
        )
        investigation_payload = CloudCostInvestigationResponse(
            status="success",
            account_id=inventory.account.account_id,
            account_name=inventory.account.account_name,
            region=inventory.region,
            collected_at=inventory.collected_at,
            resources=inventory.resources,
            summary=inventory.summary,
            findings=heuristic_findings,
            notes=inventory.notes,
        )
        return DiscoveryAssessment(inventory_response, heuristic_findings, investigation_payload)

    async def _apply_cost_estimation(
        self,
        assessment: DiscoveryAssessment,
        on_progress: ProgressCallback | None = None,
    ) -> CloudCostSavingsSummary:
        await self._report_progress(on_progress, "Cost Estimation")
        savings = await self.cost_estimator.estimate(
            assessment.inventory_response.resources,
            assessment.heuristic_findings,
            assessment.inventory_response.region,
        )
        estimates_by_id = {item.resource_id: item for item in savings.resource_estimates}
        for finding in assessment.heuristic_findings.findings:
            estimate = estimates_by_id.get(finding.resource_id)
            if estimate:
                finding.monthly_savings_usd = estimate.monthly_savings_usd

        assessment.investigation_payload.cost_savings = savings
        assessment.inventory_response.cost_savings = savings
        return savings

    async def analyze_region(
        self,
        account_id: str,
        region: str,
        include_ai: bool = True,
        on_progress: ProgressCallback | None = None,
    ) -> CloudCostAnalyzeResponse:
        assessment = await self._discover_and_assess(account_id, region, on_progress)
        savings = await self._apply_cost_estimation(assessment, on_progress)
        response = assessment.inventory_response
        if not include_ai:
            return response

        await self._report_progress(on_progress, "AI Cost Analysis")
        analysis = await self.cost_analyzer.analyze(assessment.investigation_payload)
        analysis = enrich_analysis_with_savings(analysis, savings)
        response.analysis = analysis
        if analysis.llm_error:
            response.status = "partial_success"
        return response

    async def analyze_inventory(
        self,
        request: CloudCostAnalyzeInventoryRequest,
    ) -> CloudCostAnalyzeInventoryResponse:
        collected_at = request.collected_at or datetime.now(timezone.utc).isoformat()
        summary = CloudCostResourceSummary.from_inventory(request.resources)
        heuristic_findings = self.unused_analyzer.analyze(request.resources)
        savings = await self.cost_estimator.estimate(request.resources, heuristic_findings, request.region)
        estimates_by_id = {item.resource_id: item for item in savings.resource_estimates}
        for finding in heuristic_findings.findings:
            estimate = estimates_by_id.get(finding.resource_id)
            if estimate:
                finding.monthly_savings_usd = estimate.monthly_savings_usd

        if not request.include_ai:
            return CloudCostAnalyzeInventoryResponse(status="success", analysis=None)

        investigation_payload = CloudCostInvestigationResponse(
            status="success",
            account_id=request.account.account_id,
            account_name=request.account.account_name,
            region=request.region,
            collected_at=collected_at,
            resources=request.resources,
            summary=summary,
            findings=heuristic_findings,
            cost_savings=savings,
            notes=request.notes,
        )
        analysis = await self.cost_analyzer.analyze(investigation_payload)
        analysis = enrich_analysis_with_savings(analysis, savings)
        status = "partial_success" if analysis.llm_error else "success"
        return CloudCostAnalyzeInventoryResponse(status=status, analysis=analysis)

    async def investigate(
        self,
        account_id: str,
        region: str,
        include_ai: bool = True,
        on_progress: ProgressCallback | None = None,
    ) -> CloudCostInvestigationResponse:
        try:
            assessment = await self._discover_and_assess(account_id, region, on_progress)
            savings = await self._apply_cost_estimation(assessment, on_progress)
            analysis = None
            status = assessment.inventory_response.status

            if include_ai:
                await self._report_progress(on_progress, "AI Cost Analysis")
                analysis = await self.cost_analyzer.analyze(assessment.investigation_payload)
                analysis = enrich_analysis_with_savings(analysis, savings)
                if analysis.llm_error:
                    status = "partial_success"

            diagnosis = None
            if analysis is not None:
                context = self.context_builder.build(assessment.investigation_payload)
                diagnosis = self.confidence_engine.apply_via_diagnosis(analysis, context)

            return CloudCostInvestigationResponse(
                status=status,
                account_id=assessment.inventory_response.account.account_id,
                account_name=assessment.inventory_response.account.account_name,
                region=assessment.inventory_response.region,
                collected_at=assessment.inventory_response.collected_at,
                resources=assessment.inventory_response.resources,
                summary=assessment.inventory_response.summary,
                findings=assessment.heuristic_findings,
                analysis=analysis,
                cost_savings=savings,
                diagnosis=diagnosis or (analysis_to_diagnosis(analysis) if analysis else None),
                notes=assessment.inventory_response.notes,
            )
        except AwsCredentialsError as exc:
            logger.warning("Cloud cost investigation credentials error | error={}", exc)
            return self._error_response(account_id, region, str(exc))
        except AwsError as exc:
            logger.warning("Cloud cost investigation AWS error | error={}", exc)
            return self._error_response(account_id, region, str(exc))
        except Exception as exc:
            logger.exception("Cloud cost investigation failed")
            return self._error_response(account_id, region, str(exc))

    def _error_response(
        self,
        account_id: str,
        region: str,
        error: str,
        resources: CloudCostResourceInventory | None = None,
        summary: CloudCostResourceSummary | None = None,
    ) -> CloudCostInvestigationResponse:
        failed_analysis = create_failed_analysis(sanitize_error_message(error))
        return CloudCostInvestigationResponse(
            status="error",
            account_id=account_id,
            region=region,
            collected_at=datetime.now(timezone.utc).isoformat(),
            resources=resources or CloudCostResourceInventory(),
            summary=summary or CloudCostResourceSummary(),
            analysis=failed_analysis,
            diagnosis=analysis_to_diagnosis(failed_analysis),
            error=sanitize_error_message(error),
        )
