"""Grafana integration placeholder."""


class GrafanaClient:
    """Placeholder Grafana client."""

    async def get_dashboard(self, dashboard_uid: str) -> dict:
        raise NotImplementedError("Grafana integration is not implemented yet.")

    async def search_dashboards(self, query: str) -> list[dict]:
        raise NotImplementedError("Grafana integration is not implemented yet.")
