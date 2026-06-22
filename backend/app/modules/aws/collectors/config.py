"""AWS Config collection."""

from __future__ import annotations

import asyncio
import json

from app.modules.aws.client import AwsClientFactory
from app.modules.aws.models import AwsConfigChange, AwsConfigResult, AwsEc2Instance


class AwsConfigCollector:
    def __init__(self, client_factory: AwsClientFactory | None = None) -> None:
        self.client_factory = client_factory or AwsClientFactory()

    async def collect(self, region: str, instances: list[AwsEc2Instance]) -> AwsConfigResult:
        return await asyncio.to_thread(self._collect_sync, region, instances)

    def _collect_sync(self, region: str, instances: list[AwsEc2Instance]) -> AwsConfigResult:
        config = self.client_factory.client("config", region)
        try:
            recorders = config.describe_configuration_recorders().get("ConfigurationRecorders", [])
            if not recorders:
                return AwsConfigResult(enabled=False)

            recorder_name = recorders[0].get("name")
            status_response = config.describe_configuration_recorder_status(
                ConfigurationRecorderNames=[recorder_name]
            )
            statuses = status_response.get("ConfigurationRecorderStatuses") or []
            if not statuses or not statuses[0].get("recording"):
                return AwsConfigResult(enabled=False, recorder_name=recorder_name)

            recent_changes: list[AwsConfigChange] = []
            for instance in instances[:10]:
                try:
                    history = config.get_resource_config_history(
                        resourceType="AWS::EC2::Instance",
                        resourceId=instance.instance_id,
                        limit=5,
                    )
                    for item in history.get("configurationItems", []):
                        configuration = item.get("configuration")
                        if isinstance(configuration, str):
                            try:
                                configuration = json.loads(configuration)
                            except json.JSONDecodeError:
                                configuration = {"raw": configuration}
                        recent_changes.append(
                            AwsConfigChange(
                                resource_type=item.get("resourceType"),
                                resource_id=item.get("resourceId"),
                                capture_time=(
                                    item.get("configurationItemCaptureTime").isoformat()
                                    if item.get("configurationItemCaptureTime") is not None
                                    else None
                                ),
                                configuration_state=configuration or {},
                            )
                        )
                except Exception:
                    continue

            return AwsConfigResult(
                enabled=True,
                recorder_name=recorder_name,
                recent_changes=recent_changes,
            )
        except Exception as exc:
            return AwsConfigResult(enabled=False, error=str(exc))
