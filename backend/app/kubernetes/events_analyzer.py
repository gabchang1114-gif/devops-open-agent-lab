"""Kubernetes events analysis for troubleshooting evidence."""

from app.kubernetes.executor import KubectlExecutor
from app.kubernetes.utils import extract_items
from app.models.investigation import EventFinding, EventsAnalysisResult

WATCH_REASONS = {
    "FailedScheduling",
    "FailedMount",
    "FailedPull",
    "ErrImagePull",
    "BackOff",
    "Unhealthy",
}


class EventsAnalyzer:
    """Summarize relevant Kubernetes events."""

    def __init__(self, executor: KubectlExecutor) -> None:
        self.executor = executor

    def analyze(self, namespace: str | None = None) -> EventsAnalysisResult:
        args = ["get", "events", "-o", "json", "--sort-by=.lastTimestamp"]
        if namespace:
            args.extend(["-n", namespace])
        else:
            args.append("-A")

        result, payload = self.executor.run_json(args)
        if not result.success:
            return EventsAnalysisResult(total_events=0, findings=[], summary=[])

        return self.analyze_events(extract_items(payload))

    def analyze_events(self, events: list[dict]) -> EventsAnalysisResult:
        findings: list[EventFinding] = []

        for event in events:
            reason = event.get("reason", "")
            if reason not in WATCH_REASONS and event.get("type") != "Warning":
                continue

            involved = event.get("involvedObject", {})
            involved_name = involved.get("name", "unknown")
            involved_kind = involved.get("kind", "Resource")

            findings.append(
                EventFinding(
                    type=event.get("type", "Unknown"),
                    reason=reason,
                    message=event.get("message", ""),
                    namespace=event.get("metadata", {}).get("namespace", ""),
                    involved_object=f"{involved_kind}/{involved_name}",
                    count=event.get("count", 1) or 1,
                    last_timestamp=event.get("lastTimestamp") or event.get("eventTime"),
                )
            )

        summary = self._build_summary(findings)
        return EventsAnalysisResult(
            total_events=len(events),
            findings=findings[-100:],
            summary=summary,
        )

    def _build_summary(self, findings: list[EventFinding]) -> list[str]:
        if not findings:
            return ["No critical Kubernetes events detected."]

        grouped: dict[str, int] = {}
        for finding in findings:
            key = finding.reason or finding.type
            grouped[key] = grouped.get(key, 0) + finding.count

        summary = [
            f"{reason}: {count} occurrence(s)"
            for reason, count in sorted(grouped.items(), key=lambda item: item[1], reverse=True)
        ]
        return summary[:10]
