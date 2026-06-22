"""GitHub Actions deployment correlation placeholder."""


class GitHubActionsClient:
    """Placeholder GitHub Actions integration."""

    async def get_workflow_runs(self, repo: str, workflow_id: str) -> list[dict]:
        raise NotImplementedError("GitHub Actions integration is not implemented yet.")

    async def get_deployment_events(self, repo: str, environment: str) -> list[dict]:
        raise NotImplementedError("GitHub Actions integration is not implemented yet.")
