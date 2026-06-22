"""ArgoCD deployment correlation placeholder."""


class ArgoCDClient:
    """Placeholder ArgoCD integration."""

    async def get_application(self, app_name: str) -> dict:
        raise NotImplementedError("ArgoCD integration is not implemented yet.")

    async def list_applications(self, cluster_id: str | None = None) -> list[dict]:
        raise NotImplementedError("ArgoCD integration is not implemented yet.")
