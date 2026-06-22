"""AWS collector package."""

from app.modules.aws.collectors.cloudtrail import AwsCloudTrailCollector
from app.modules.aws.collectors.cloudwatch import AwsCloudWatchCollector
from app.modules.aws.collectors.config import AwsConfigCollector
from app.modules.aws.collectors.deployment_correlation import AwsDeploymentCorrelationCollector

__all__ = [
    "AwsCloudTrailCollector",
    "AwsCloudWatchCollector",
    "AwsConfigCollector",
    "AwsDeploymentCorrelationCollector",
]
