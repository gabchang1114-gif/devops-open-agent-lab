"""AWS Cost Explorer collector for regional spend context."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from botocore.exceptions import ClientError

from app.modules.aws.errors import AwsApiError
from app.modules.cloud_cost_detector.discovery.aws_clients import AwsClientFactory
from app.modules.cloud_cost_detector.models.schemas import CloudCostRegionalSpend


class CloudCostExplorerCollector:
    """Fetch recent regional spend from AWS Cost Explorer."""

    def __init__(self, client_factory: AwsClientFactory | None = None) -> None:
        self.client_factory = client_factory or AwsClientFactory()

    async def get_regional_spend(self, region: str) -> CloudCostRegionalSpend:
        return await asyncio.to_thread(self._get_regional_spend_sync, region)

    def _get_regional_spend_sync(self, region: str) -> CloudCostRegionalSpend:
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=30)
        try:
            ce = self.client_factory.client("ce", "us-east-1")
            response = ce.get_cost_and_usage(
                TimePeriod={
                    "Start": start.isoformat(),
                    "End": end.isoformat(),
                },
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                Filter={
                    "Dimensions": {
                        "Key": "REGION",
                        "Values": [region],
                    }
                },
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"AccessDeniedException", "UnauthorizedOperation"}:
                return CloudCostRegionalSpend(
                    period_start=start.isoformat(),
                    period_end=end.isoformat(),
                    total_usd=0,
                    available=False,
                    note=(
                        "Cost Explorer access denied. Grant ce:GetCostAndUsage to show "
                        "actual regional spend."
                    ),
                )
            raise AwsApiError(str(exc)) from exc

        by_service: dict[str, float] = {}
        total = 0.0
        for result in response.get("ResultsByTime", []):
            for group in result.get("Groups", []):
                service = (group.get("Keys") or ["Unknown"])[0]
                amount = float(group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", 0) or 0)
                by_service[service] = by_service.get(service, 0) + amount
                total += amount

        return CloudCostRegionalSpend(
            period_start=start.isoformat(),
            period_end=end.isoformat(),
            total_usd=round(total, 2),
            by_service={key: round(value, 2) for key, value in sorted(by_service.items(), key=lambda item: -item[1])},
            available=True,
            note="Last 30 days unblended spend for the selected region (Cost Explorer).",
        )
