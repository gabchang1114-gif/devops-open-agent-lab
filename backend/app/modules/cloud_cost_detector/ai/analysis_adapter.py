"""Adapters between CloudCostAnalysis and shared platform diagnosis models."""

from __future__ import annotations

from app.models.diagnosis import DiagnosisEvidence, DiagnosisResult
from app.modules.cloud_cost_detector.models.schemas import CloudCostAnalysis

CONFIDENCE_TO_SCORE = {
    "low": 45,
    "medium": 70,
    "high": 88,
}


def analysis_to_diagnosis(analysis: CloudCostAnalysis) -> DiagnosisResult:
    """Map Cloud Cost analysis to the shared DiagnosisResult used by Investigations UI."""
    evidence = [
        DiagnosisEvidence(
            source=finding.resource_type,
            detail=f"{finding.resource_id} ({finding.status}): {finding.reason}",
        )
        for finding in analysis.findings
    ]
    commands: list[str] = []
    validation_steps: list[str] = []
    for finding in analysis.findings:
        commands.extend(finding.aws_cli_commands)
        validation_steps.extend(finding.validation_steps)

    recommendations = [finding.recommendation for finding in analysis.findings if finding.recommendation]
    root_cause = analysis.findings[0].title if analysis.findings else analysis.summary
    savings_confidence = (analysis.estimated_monthly_savings.confidence or "low").lower()

    return DiagnosisResult(
        root_cause=root_cause,
        summary=analysis.summary,
        evidence=evidence,
        suggested_fix="\n".join(f"{index + 1}. {item}" for index, item in enumerate(recommendations))
        or analysis.summary,
        kubectl_commands=commands,
        validation_steps=validation_steps or list(analysis.next_steps),
        prevention_recommendation="; ".join(analysis.next_steps),
        confidence_score=CONFIDENCE_TO_SCORE.get(savings_confidence, 58),
        confidence_reason=analysis.estimated_monthly_savings.note or "Derived from AI cost analysis confidence.",
        needs_more_data=bool(analysis.data_gaps),
        additional_data_needed=list(analysis.data_gaps),
        llm_provider=analysis.llm_provider,
        llm_error=analysis.llm_error,
    )


def create_failed_analysis(error: str | None = None, provider: str | None = None) -> CloudCostAnalysis:
    return CloudCostAnalysis(
        summary="AWS resources were discovered, but AI cost analysis failed.",
        overall_risk="unknown",
        data_gaps=[
            "Check LLM provider configuration",
            "Verify API key",
            "Verify model name",
        ],
        next_steps=["Run analysis again after fixing LLM configuration"],
        llm_provider=provider,
        llm_error=error,
    )
