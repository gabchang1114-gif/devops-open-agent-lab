"""Observability collector placeholder for future integrations."""

from app.models.investigation import IntegrationStatus, ObservabilityResult


class ObservabilityCollector:
    """Placeholder collector for Prometheus, Grafana, Loki, and OpenTelemetry."""

    async def collect(self, cluster_id: str) -> ObservabilityResult:
        return ObservabilityResult(
            enabled=False,
            prometheus=IntegrationStatus(enabled=False),
            grafana=IntegrationStatus(enabled=False),
            loki=IntegrationStatus(enabled=False),
            opentelemetry=IntegrationStatus(enabled=False),
        )
