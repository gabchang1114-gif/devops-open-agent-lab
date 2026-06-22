"""Prometheus integration placeholder."""


class PrometheusClient:
    """Placeholder Prometheus client."""

    async def query(self, promql: str) -> dict:
        raise NotImplementedError("Prometheus integration is not implemented yet.")

    async def query_range(self, promql: str, start: str, end: str, step: str) -> dict:
        raise NotImplementedError("Prometheus integration is not implemented yet.")
