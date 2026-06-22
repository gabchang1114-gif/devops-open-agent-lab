"""Cloud cost optimization analyzer using shared LLM providers."""

from __future__ import annotations

import json
import re
from typing import Any

from loguru import logger
from pydantic import ValidationError

from app.ai.llm_factory import LLMProviderFactory
from app.ai.providers.exceptions import LLMProviderError
from app.core.config import Settings, get_settings
from app.modules.cloud_cost_detector.ai.analysis_adapter import create_failed_analysis
from app.modules.cloud_cost_detector.ai.confidence_engine import CloudCostConfidenceEngine
from app.modules.cloud_cost_detector.ai.context_builder import CloudCostContextBuilder
from app.modules.cloud_cost_detector.ai.cost_prompt_builder import CloudCostPromptBuilder
from app.modules.cloud_cost_detector.models.schemas import (
    CloudCostAnalysis,
    CloudCostAnalysisFinding,
    CloudCostInvestigationResponse,
    CloudCostSavingsEstimate,
)


class CloudCostAnalyzer:
    """Analyze cloud cost investigation evidence and produce structured cost analysis."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.context_builder = CloudCostContextBuilder()
        self.prompt_builder = CloudCostPromptBuilder()
        self.confidence_engine = CloudCostConfidenceEngine()

    async def analyze(
        self,
        investigation: CloudCostInvestigationResponse | dict[str, Any],
    ) -> CloudCostAnalysis:
        context = self.context_builder.build(investigation)
        messages = self.prompt_builder.build_messages(context)

        try:
            provider = LLMProviderFactory.create(settings=self.settings)
            raw_response = await provider.generate(messages, temperature=0.1)
            analysis = self._parse_response(raw_response)
            analysis.llm_provider = self.settings.llm_provider
            analysis = self.confidence_engine.apply_to_analysis(analysis, context)
            logger.info(
                "Cloud cost AI analysis generated | provider={} risk={} findings={}",
                self.settings.llm_provider,
                analysis.overall_risk,
                len(analysis.findings),
            )
            return analysis
        except LLMProviderError as exc:
            logger.error(
                "Cloud cost LLM analysis failed | provider={} error={}",
                self.settings.llm_provider,
                exc,
            )
            return create_failed_analysis(str(exc), provider=self.settings.llm_provider)
        except Exception as exc:
            logger.exception("Unexpected cloud cost analysis failure")
            return create_failed_analysis(str(exc), provider=self.settings.llm_provider)

    def _parse_response(self, raw_response: str) -> CloudCostAnalysis:
        payload = self._extract_json(raw_response)
        try:
            return CloudCostAnalysis.model_validate(payload)
        except ValidationError as exc:
            logger.warning("Cloud cost LLM JSON did not match schema, attempting recovery | error={}", exc)
            recovered = self._recover_partial_payload(payload)
            return CloudCostAnalysis.model_validate(recovered)

    def _extract_json(self, raw_response: str) -> dict[str, Any]:
        text = raw_response.strip()
        if text.startswith("```"):
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1).strip()
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("LLM response JSON must be an object")
        return data

    def _recover_partial_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        findings_raw = payload.get("findings", [])
        normalized_findings: list[dict[str, Any]] = []
        if isinstance(findings_raw, list):
            for item in findings_raw:
                if not isinstance(item, dict):
                    continue
                savings = item.get("estimated_savings") or {}
                normalized_findings.append(
                    CloudCostAnalysisFinding(
                        title=str(item.get("title", "Cost optimization finding")),
                        severity=str(item.get("severity", "medium")),
                        status=str(item.get("status", "potential")),
                        resource_type=str(item.get("resource_type", "unknown")),
                        resource_id=str(item.get("resource_id", "unknown")),
                        reason=str(item.get("reason", "")),
                        estimated_savings=CloudCostSavingsEstimate(
                            amount=float(savings.get("amount", 0) or 0),
                            currency=str(savings.get("currency", "USD")),
                            confidence=str(savings.get("confidence", "low")),
                        ),
                        recommendation=str(item.get("recommendation", "")),
                        validation_steps=item.get("validation_steps") or [],
                        aws_cli_commands=item.get("aws_cli_commands") or [],
                        safe_to_delete=bool(item.get("safe_to_delete", False)),
                    ).model_dump()
                )

        savings = payload.get("estimated_monthly_savings") or {}
        return {
            "summary": str(payload.get("summary", "Cost analysis summary unavailable.")),
            "overall_risk": str(payload.get("overall_risk", "medium")),
            "estimated_monthly_savings": {
                "amount": float(savings.get("amount", 0) or 0),
                "currency": str(savings.get("currency", "USD")),
                "confidence": str(savings.get("confidence", "low")),
                "note": str(savings.get("note", "Recovered from partial LLM response.")),
            },
            "findings": normalized_findings,
            "data_gaps": payload.get("data_gaps") or [],
            "next_steps": payload.get("next_steps") or [],
        }
