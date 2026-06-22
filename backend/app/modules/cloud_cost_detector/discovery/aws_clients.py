"""AWS client access for Cloud Cost Detector — reuses platform boto3 factory."""

from app.modules.aws.client import AwsClientFactory, get_aws_client_factory

__all__ = ["AwsClientFactory", "get_aws_client_factory"]
