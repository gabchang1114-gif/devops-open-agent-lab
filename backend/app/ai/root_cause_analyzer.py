"""Root cause analyzer using LLM providers."""

import json
import re
from typing import Any

from loguru import logger
from pydantic import ValidationError

from app.ai.multi_pod_enricher import MultiPodDiagnosisEnricher
from app.ai.confidence_engine import ConfidenceEngine
from app.ai.context_builder import ContextBuilder
from app.ai.fix_recommendation import FixRecommendationEngine
from app.ai.llm_factory import LLMProviderFactory
from app.ai.prompt_builder import PromptBuilder
from app.ai.providers.exceptions import LLMProviderError
from app.core.config import Settings, get_settings
from app.models.diagnosis import DiagnosisEvidence, DiagnosisResult
from app.models.investigation import InvestigationResponse


class RootCauseAnalyzer:
    """Analyze investigation evidence and produce structured diagnosis."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.context_builder = ContextBuilder()
        self.prompt_builder = PromptBuilder()
        self.confidence_engine = ConfidenceEngine()
        self.fix_recommendation_engine = FixRecommendationEngine()
        self.multi_pod_enricher = MultiPodDiagnosisEnricher()

    async def analyze(
        self,
        investigation: InvestigationResponse | dict[str, Any],
    ) -> DiagnosisResult:
        context = self.context_builder.build(investigation)
        messages = self.prompt_builder.build_messages(context)

        try:
            provider = LLMProviderFactory.create(settings=self.settings)
            raw_response = await provider.generate(messages, temperature=0.1)
            diagnosis = self._parse_response(raw_response)
            diagnosis.llm_provider = self.settings.llm_provider
            investigation_dict = self._as_dict(investigation)
            diagnosis = self.multi_pod_enricher.enrich(diagnosis, investigation_dict)
            diagnosis = self.confidence_engine.apply(diagnosis, investigation_dict)
            diagnosis = self.fix_recommendation_engine.apply(diagnosis)
            logger.info(
                "AI diagnosis generated | provider={} confidence={}",
                self.settings.llm_provider,
                diagnosis.confidence_score,
            )
            return diagnosis
        except LLMProviderError as exc:
            logger.error("LLM diagnosis failed | provider={} error={}", self.settings.llm_provider, exc)
            return self.create_fallback_diagnosis(str(exc))
        except Exception as exc:
            logger.exception("Unexpected diagnosis failure")
            return self.create_fallback_diagnosis(str(exc))

    def create_fallback_diagnosis(self, error: str | None = None) -> DiagnosisResult:
        return DiagnosisResult(
            root_cause="Unable to generate AI diagnosis",
            summary="Kubernetes evidence was collected, but LLM reasoning failed.",
            evidence=[],
            suggested_fix="Review LLM provider configuration and retry diagnosis.",
            kubectl_commands=[],
            validation_steps=[],
            prevention_recommendation="",
            confidence_score=0,
            confidence_reason="LLM call failed.",
            needs_more_data=True,
            additional_data_needed=[
                "Check LLM provider configuration",
                "Verify API key",
                "Verify model name",
            ],
            llm_provider=self.settings.llm_provider,
            llm_error=error,
        )

    def _parse_response(self, raw_response: str) -> DiagnosisResult:
        payload = self._extract_json(raw_response)
        try:
            return DiagnosisResult.model_validate(payload)
        except ValidationError as exc:
            logger.warning("LLM JSON did not match schema, attempting recovery | error={}", exc)
            recovered = self._recover_partial_payload(payload)
            return DiagnosisResult.model_validate(recovered)

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
        evidence = payload.get("evidence", [])
        normalized_evidence = []
        for item in evidence if isinstance(evidence, list) else []:
            if isinstance(item, dict):
                normalized_evidence.append(
                    DiagnosisEvidence(
                        source=str(item.get("source", "pods")),
                        detail=str(item.get("detail", "")),
                    ).model_dump()
                )

        return {
            "root_cause": str(payload.get("root_cause", "Unknown root cause")),
            "summary": str(payload.get("summary", "Summary unavailable.")),
            "evidence": normalized_evidence,
            "suggested_fix": str(payload.get("suggested_fix", "Review investigation evidence manually.")),
            "kubectl_commands": payload.get("kubectl_commands") or [],
            "validation_steps": payload.get("validation_steps") or [],
            "prevention_recommendation": str(payload.get("prevention_recommendation", "")),
            "confidence_score": int(payload.get("confidence_score", 0) or 0),
            "confidence_reason": str(payload.get("confidence_reason", "Recovered from partial LLM output.")),
            "needs_more_data": bool(payload.get("needs_more_data", False)),
            "additional_data_needed": payload.get("additional_data_needed") or [],
        }

    def _as_dict(self, investigation: InvestigationResponse | dict[str, Any]) -> dict[str, Any]:
        if isinstance(investigation, InvestigationResponse):
            return investigation.model_dump()
        return investigation
