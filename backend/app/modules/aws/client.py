"""Boto3 session and client factory."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from loguru import logger

from app.core.config import Settings, get_settings
from app.modules.aws.errors import AwsApiError, AwsCredentialsError


class AwsClientFactory:
    """Create boto3 clients for a given account and region."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def session(self, region: str) -> boto3.Session:
        session_kwargs: dict[str, Any] = {"region_name": region}
        profile = (self.settings.aws_profile or "").strip()
        if profile:
            session_kwargs["profile_name"] = profile
            return boto3.Session(**session_kwargs)

        # Docker env_file often sets AWS_PROFILE= with no value. Boto3 treats that
        # as a named profile and fails with "config profile () could not be found".
        saved_profile = os.environ.pop("AWS_PROFILE", None)
        if saved_profile is not None and not str(saved_profile).strip():
            saved_profile = None
        try:
            return boto3.Session(**session_kwargs)
        finally:
            if saved_profile is not None:
                os.environ["AWS_PROFILE"] = saved_profile

    def client(self, service_name: str, region: str) -> Any:
        return self.session(region).client(service_name)

    def resource(self, service_name: str, region: str) -> Any:
        return self.session(region).resource(service_name)

    def call(self, service_name: str, region: str, operation: str, **kwargs: Any) -> dict[str, Any]:
        client = self.client(service_name, region)
        try:
            method = getattr(client, operation)
            return method(**kwargs)
        except NoCredentialsError as exc:
            raise AwsCredentialsError(
                "AWS credentials not found. Configure AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY, "
                "AWS_PROFILE, or mount ~/.aws into the backend container."
            ) from exc
        except (ClientError, BotoCoreError) as exc:
            logger.warning(
                "AWS API call failed | service={} region={} operation={} error={}",
                service_name,
                region,
                operation,
                exc,
            )
            raise AwsApiError(str(exc)) from exc


@lru_cache
def get_aws_client_factory() -> AwsClientFactory:
    return AwsClientFactory()
