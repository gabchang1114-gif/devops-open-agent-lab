"""AWS account and region discovery."""

from __future__ import annotations

import asyncio

from app.modules.aws.client import AwsClientFactory
from app.modules.aws.models import AwsAccountInfo, AwsAccountSummary, AwsRegionInfo


class AwsAccountDiscovery:
    def __init__(self, client_factory: AwsClientFactory | None = None) -> None:
        self.client_factory = client_factory or AwsClientFactory()

    async def discover_account(self, region: str) -> AwsAccountInfo:
        return await asyncio.to_thread(self._discover_account_sync, region)

    def _discover_account_sync(self, region: str) -> AwsAccountInfo:
        sts = self.client_factory.client("sts", region)
        identity = sts.get_caller_identity()
        account_id = identity["Account"]

        account_name = None
        try:
            iam = self.client_factory.client("iam", region)
            aliases = iam.list_account_aliases().get("AccountAliases") or []
            if aliases:
                account_name = aliases[0]
        except Exception:
            account_name = None

        ec2 = self.client_factory.client("ec2", region)
        regions_response = ec2.describe_regions(AllRegions=False)
        enabled_regions = sorted(
            item["RegionName"]
            for item in regions_response.get("Regions", [])
            if item.get("RegionName")
        )

        credential_source = "profile" if self.client_factory.settings.aws_profile else "default"

        return AwsAccountInfo(
            account_id=account_id,
            account_name=account_name,
            enabled_regions=enabled_regions,
            credential_source=credential_source,
            caller_arn=identity.get("Arn"),
            user_id=identity.get("UserId"),
        )

    async def list_accounts(self, region: str) -> list[AwsAccountSummary]:
        account = await self.discover_account(region)
        return [
            AwsAccountSummary(
                account_id=account.account_id,
                account_name=account.account_name,
            )
        ]

    async def list_regions(self, account_id: str, region: str) -> list[AwsRegionInfo]:
        account = await self.discover_account(region)
        if account.account_id != account_id:
            return []

        return [AwsRegionInfo(region=name) for name in account.enabled_regions]
