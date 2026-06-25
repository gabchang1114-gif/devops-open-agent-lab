"""AWS resource discovery package."""

from app.modules.aws.discovery.account import AwsAccountDiscovery
from app.modules.aws.discovery.autoscaling import AwsAutoScalingDiscovery
from app.modules.aws.discovery.ec2 import AwsEc2Discovery
from app.modules.aws.discovery.lambda_functions import AwsLambdaDiscovery
from app.modules.aws.discovery.load_balancers import AwsLoadBalancerDiscovery
from app.modules.aws.discovery.s3 import AwsS3Discovery
from app.modules.aws.discovery.security_groups import AwsSecurityGroupDiscovery
from app.modules.aws.discovery.vpc import AwsVpcDiscovery

__all__ = [
    "AwsAccountDiscovery",
    "AwsAutoScalingDiscovery",
    "AwsEc2Discovery",
    "AwsLambdaDiscovery",
    "AwsLoadBalancerDiscovery",
    "AwsS3Discovery",
    "AwsSecurityGroupDiscovery",
    "AwsVpcDiscovery",
]
