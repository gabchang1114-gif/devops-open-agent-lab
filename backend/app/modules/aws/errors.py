"""AWS module errors."""


class AwsError(Exception):
    """Base AWS module error."""


class AwsCredentialsError(AwsError):
    """AWS credentials are missing or invalid."""


class AwsApiError(AwsError):
    """AWS API call failed."""
