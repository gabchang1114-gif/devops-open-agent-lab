"""Evidence-based confidence scoring and validation."""

from app.models.diagnosis import DiagnosisResult


class ConfidenceEngine:
    """Validate and adjust AI confidence scores based on evidence."""

    VALID_SOURCES = {
        "logs",
        "events",
        "pods",
        "deployments",
        "network",
        "topology",
        "observability",
    }

    def apply(self, diagnosis: DiagnosisResult, evidence_context: dict) -> DiagnosisResult:
        score = max(0, min(100, diagnosis.confidence_score))
        evidence_sources = {
            item.source for item in diagnosis.evidence if item.source in self.VALID_SOURCES
        }

        investigation = evidence_context.get("investigation", {})
        available_signals = self._count_available_signals(investigation)

        if score >= 90 and len(evidence_sources) < 2 and available_signals >= 2:
            score = 79
            reason = (
                f"{diagnosis.confidence_reason} Adjusted down because fewer than two "
                "evidence sources were cited despite multiple investigation signals."
            )
            diagnosis.confidence_reason = reason
        elif score >= 70 and len(evidence_sources) == 0:
            score = 35
            diagnosis.confidence_reason = (
                "Insufficient cited evidence despite investigation data being available."
            )
            diagnosis.needs_more_data = True
        elif score <= 39 and available_signals >= 2 and len(evidence_sources) >= 2:
            score = 55
            diagnosis.confidence_reason = (
                f"{diagnosis.confidence_reason} Adjusted up slightly because multiple "
                "investigation signals and cited evidence are present."
            )

        diagnosis.confidence_score = score
        return diagnosis

    def _count_available_signals(self, investigation: dict) -> int:
        signals = 0
        pods = investigation.get("pods", {})
        logs = investigation.get("logs", {})
        events = investigation.get("events", {})
        deployments = investigation.get("deployments", {})
        network = investigation.get("network", {})

        if pods.get("problematic_pods"):
            signals += 1
        if logs.get("logs"):
            signals += 1
        if events.get("findings"):
            signals += 1
        if deployments.get("issues"):
            signals += 1
        if network.get("issues"):
            signals += 1
        return signals
