"""OpenTelemetry integration placeholder."""


class OpenTelemetryClient:
    """Placeholder OpenTelemetry client."""

    async def get_traces(self, service_name: str, trace_id: str | None = None) -> dict:
        raise NotImplementedError("OpenTelemetry integration is not implemented yet.")

    async def get_metrics(self, service_name: str) -> dict:
        raise NotImplementedError("OpenTelemetry integration is not implemented yet.")
