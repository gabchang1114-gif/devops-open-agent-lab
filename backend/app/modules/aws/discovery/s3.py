"""Amazon S3 bucket discovery."""

from __future__ import annotations

import asyncio
from typing import Any

from app.modules.aws.client import AwsClientFactory
from app.modules.aws.models import AwsS3Bucket, AwsS3BucketNotification
from app.modules.aws.utils import parse_tags


class AwsS3Discovery:
    def __init__(self, client_factory: AwsClientFactory | None = None) -> None:
        self.client_factory = client_factory or AwsClientFactory()

    async def discover(self, region: str) -> list[AwsS3Bucket]:
        return await asyncio.to_thread(self._discover_sync, region)

    def _discover_sync(self, region: str) -> list[AwsS3Bucket]:
        s3 = self.client_factory.client("s3", region)
        buckets: list[AwsS3Bucket] = []

        for item in s3.list_buckets().get("Buckets", []):
            bucket_name = item.get("Name", "")
            if not bucket_name:
                continue

            bucket_region = self._bucket_region(s3, bucket_name)
            if not self._matches_region(bucket_region, region):
                continue

            creation_date = item.get("CreationDate")
            buckets.append(
                AwsS3Bucket(
                    bucket_name=bucket_name,
                    region=bucket_region,
                    creation_date=creation_date.isoformat() if creation_date is not None else None,
                    public_access_block=self._public_access_block(s3, bucket_name),
                    encryption_enabled=self._encryption_enabled(s3, bucket_name),
                    encryption_type=self._encryption_type(s3, bucket_name),
                    versioning_status=self._versioning_status(s3, bucket_name),
                    policy_is_public=self._policy_is_public(s3, bucket_name),
                    logging_enabled=self._logging_enabled(s3, bucket_name),
                    logging_target_bucket=self._logging_target_bucket(s3, bucket_name),
                    notifications=self._notifications(s3, bucket_name),
                    tags=self._tags(s3, bucket_name),
                )
            )

        return buckets

    def _bucket_region(self, s3: Any, bucket_name: str) -> str:
        try:
            response = s3.get_bucket_location(Bucket=bucket_name)
            location = response.get("LocationConstraint")
            if not location:
                return "us-east-1"
            if location == "EU":
                return "eu-west-1"
            return str(location)
        except Exception:
            return "unknown"

    def _matches_region(self, bucket_region: str, target_region: str) -> bool:
        if bucket_region == "unknown":
            return False
        return bucket_region == target_region

    def _public_access_block(self, s3: Any, bucket_name: str) -> dict[str, bool | None]:
        try:
            response = s3.get_public_access_block(Bucket=bucket_name)
            config = response.get("PublicAccessBlockConfiguration") or {}
            return {
                "block_public_acls": config.get("BlockPublicAcls"),
                "ignore_public_acls": config.get("IgnorePublicAcls"),
                "block_public_policy": config.get("BlockPublicPolicy"),
                "restrict_public_buckets": config.get("RestrictPublicBuckets"),
            }
        except Exception:
            return {}

    def _encryption_enabled(self, s3: Any, bucket_name: str) -> bool | None:
        try:
            response = s3.get_bucket_encryption(Bucket=bucket_name)
            rules = (response.get("ServerSideEncryptionConfiguration") or {}).get("Rules") or []
            return len(rules) > 0
        except Exception:
            return None

    def _encryption_type(self, s3: Any, bucket_name: str) -> str | None:
        try:
            response = s3.get_bucket_encryption(Bucket=bucket_name)
            rules = (response.get("ServerSideEncryptionConfiguration") or {}).get("Rules") or []
            if not rules:
                return None
            rule = rules[0].get("ApplyServerSideEncryptionByDefault") or {}
            return rule.get("SSEAlgorithm")
        except Exception:
            return None

    def _versioning_status(self, s3: Any, bucket_name: str) -> str | None:
        try:
            response = s3.get_bucket_versioning(Bucket=bucket_name)
            return response.get("Status")
        except Exception:
            return None

    def _policy_is_public(self, s3: Any, bucket_name: str) -> bool | None:
        try:
            response = s3.get_bucket_policy_status(Bucket=bucket_name)
            return bool((response.get("PolicyStatus") or {}).get("IsPublic"))
        except Exception:
            return None

    def _logging_enabled(self, s3: Any, bucket_name: str) -> bool | None:
        try:
            response = s3.get_bucket_logging(Bucket=bucket_name)
            logging_enabled = (response.get("LoggingEnabled") or {}).get("TargetBucket")
            return bool(logging_enabled)
        except Exception:
            return None

    def _logging_target_bucket(self, s3: Any, bucket_name: str) -> str | None:
        try:
            response = s3.get_bucket_logging(Bucket=bucket_name)
            return (response.get("LoggingEnabled") or {}).get("TargetBucket")
        except Exception:
            return None

    def _notifications(self, s3: Any, bucket_name: str) -> list[AwsS3BucketNotification]:
        notifications: list[AwsS3BucketNotification] = []
        try:
            response = s3.get_bucket_notification_configuration(Bucket=bucket_name)
        except Exception:
            return notifications

        for item in response.get("LambdaFunctionConfigurations") or []:
            notifications.append(
                AwsS3BucketNotification(
                    target_type="lambda",
                    target_arn=item.get("LambdaFunctionArn"),
                    events=[str(event) for event in item.get("Events") or []],
                )
            )
        for item in response.get("QueueConfigurations") or []:
            notifications.append(
                AwsS3BucketNotification(
                    target_type="sqs",
                    target_arn=item.get("QueueArn"),
                    events=[str(event) for event in item.get("Events") or []],
                )
            )
        for item in response.get("TopicConfigurations") or []:
            notifications.append(
                AwsS3BucketNotification(
                    target_type="sns",
                    target_arn=item.get("TopicArn"),
                    events=[str(event) for event in item.get("Events") or []],
                )
            )
        return notifications

    def _tags(self, s3: Any, bucket_name: str) -> dict[str, str]:
        try:
            response = s3.get_bucket_tagging(Bucket=bucket_name)
            return parse_tags(response.get("TagSet"))
        except Exception:
            return {}
