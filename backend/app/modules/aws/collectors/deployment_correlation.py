"""Deployment correlation placeholder for AWS agent."""

from app.modules.aws.models import (
    AwsDeploymentCorrelationResult,
    AwsDeploymentIntegrationStatus,
)


class AwsDeploymentCorrelationCollector:
    async def collect(self) -> AwsDeploymentCorrelationResult:
        disabled = AwsDeploymentIntegrationStatus(enabled=False)
        return AwsDeploymentCorrelationResult(
            enabled=False,
            github_actions=disabled,
            gitlab_ci=disabled,
            jenkins=disabled,
            aws_codepipeline=disabled,
        )
