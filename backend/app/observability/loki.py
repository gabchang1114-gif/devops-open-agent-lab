"""Loki integration placeholder."""


class LokiClient:
    """Placeholder Loki client."""

    async def query_logs(self, logql: str, limit: int = 100) -> dict:
        raise NotImplementedError("Loki integration is not implemented yet.")

    async def query_range(self, logql: str, start: str, end: str, limit: int = 100) -> dict:
        raise NotImplementedError("Loki integration is not implemented yet.")
