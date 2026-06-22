"""Deployment correlation placeholder for future integrations."""

from app.models.investigation import DeploymentCorrelationResult, IntegrationStatus


class DeploymentCorrelationCollector:
    """Placeholder collector for Helm, ArgoCD, GitHub Actions, and Jenkins."""

    async def collect(self, cluster_id: str) -> DeploymentCorrelationResult:
        return DeploymentCorrelationResult(
            enabled=False,
            helm=IntegrationStatus(enabled=False),
            argocd=IntegrationStatus(enabled=False),
            github_actions=IntegrationStatus(enabled=False),
            jenkins=IntegrationStatus(enabled=False),
        )
