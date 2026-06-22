"""LLM-powered DevOps PR review analyzer."""

from __future__ import annotations

import json
import re
from typing import Any

from loguru import logger
from pydantic import ValidationError

from app.ai.llm_factory import LLMProviderFactory
from app.ai.providers.exceptions import LLMProviderError
from app.core.config import Settings, get_settings
from app.modules.pr_reviewer.ai.prompt_builder import PrReviewPromptBuilder
from app.modules.pr_reviewer.models.schemas import PrFileInfo, PrReviewAnalysis, PrWebhookPayload


class PrReviewAnalyzer:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.prompt_builder = PrReviewPromptBuilder()

    async def analyze(
        self,
        pr: PrWebhookPayload,
        files: list[PrFileInfo],
    ) -> PrReviewAnalysis:
        messages = self.prompt_builder.build_messages(pr, files)
        try:
            provider = LLMProviderFactory.create(settings=self.settings)
            raw_response = await provider.generate(messages, temperature=0.1)
            analysis = self._parse_response(raw_response)
            logger.info(
                "PR review AI analysis generated | provider={} risk={} findings={}",
                self.settings.llm_provider,
                analysis.overall_risk,
                len(analysis.findings),
            )
            return analysis
        except LLMProviderError as exc:
            logger.error(
                "PR review LLM analysis failed | provider={} error={}",
                self.settings.llm_provider,
                exc,
            )
            raise
        except Exception:
            logger.exception("Unexpected PR review analysis failure")
            raise

    def _parse_response(self, raw_response: str) -> PrReviewAnalysis:
        payload = self._extract_json(raw_response)
        try:
            return PrReviewAnalysis.model_validate(payload)
        except ValidationError as exc:
            logger.warning("PR review LLM JSON did not match schema | error={}", exc)
            recovered = self._recover_partial_payload(payload)
            return PrReviewAnalysis.model_validate(recovered)

    def _extract_json(self, raw_response: str) -> dict[str, Any]:
        text = raw_response.strip()
        if text.startswith("```"):
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                text = match.group(1).strip()
        return json.loads(text)

    def _recover_partial_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        findings = payload.get("findings") or []
        cleaned_findings = []
        for item in findings:
            if not isinstance(item, dict):
                continue
            cleaned_findings.append(
                {
                    "severity": item.get("severity", "medium"),
                    "category": item.get("category", "cloud"),
                    "file": item.get("file", "unknown"),
                    "line_reference": item.get("line_reference", ""),
                    "issue": item.get("issue", "Review finding"),
                    "why_it_matters": item.get("why_it_matters", ""),
                    "recommendation": item.get("recommendation", ""),
                    "example_fix": item.get("example_fix", ""),
                }
            )
        return {
            "summary": payload.get("summary", "DevOps review completed with partial parsing."),
            "overall_risk": payload.get("overall_risk", "medium"),
            "should_block_merge": bool(payload.get("should_block_merge", False)),
            "findings": cleaned_findings,
            "positive_observations": payload.get("positive_observations") or [],
            "final_recommendation": payload.get("final_recommendation", "comment"),
        }
