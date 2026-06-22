"""Helm deployment correlation placeholder."""


class HelmClient:
    """Placeholder Helm integration."""

    async def get_release(self, cluster_id: str, namespace: str, release_name: str) -> dict:
        raise NotImplementedError("Helm integration is not implemented yet.")

    async def list_releases(self, cluster_id: str, namespace: str | None = None) -> list[dict]:
        raise NotImplementedError("Helm integration is not implemented yet.")
