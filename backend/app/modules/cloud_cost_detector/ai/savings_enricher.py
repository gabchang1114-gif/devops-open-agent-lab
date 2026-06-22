"""Merge calculated savings into AI analysis output."""

from __future__ import annotations

from app.modules.cloud_cost_detector.models.schemas import CloudCostAnalysis, CloudCostSavingsSummary


def enrich_analysis_with_savings(
    analysis: CloudCostAnalysis,
    savings: CloudCostSavingsSummary | None,
) -> CloudCostAnalysis:
    """Apply rule-based dollar estimates to LLM findings without duplicating analysis logic."""
    if savings is None or savings.total_monthly_savings_usd <= 0:
        return analysis

    savings_by_id = {item.resource_id: item for item in savings.resource_estimates}
    matched_total = 0.0

    for finding in analysis.findings:
        estimate = savings_by_id.get(finding.resource_id)
        if estimate is None:
            for key, value in savings_by_id.items():
                if key in finding.resource_id or finding.resource_id in key:
                    estimate = value
                    break
        if estimate is None:
            continue
        finding.estimated_savings.amount = estimate.monthly_savings_usd
        finding.estimated_savings.confidence = estimate.confidence
        finding.estimated_savings.note = estimate.note
        matched_total += estimate.monthly_savings_usd

    analysis.estimated_monthly_savings.amount = round(
        matched_total or savings.total_monthly_savings_usd,
        2,
    )
    analysis.estimated_monthly_savings.confidence = savings.confidence
    analysis.estimated_monthly_savings.note = savings.note
    return analysis
