"""CloudWatch metrics and alarm collection."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from app.modules.aws.client import AwsClientFactory
from app.modules.aws.models import AwsCloudWatchAlarm, AwsCloudWatchResult, AwsEc2Instance, AwsMetricSample

METRIC_DEFINITIONS = [
    ("AWS/EC2", "CPUUtilization"),
    ("AWS/EC2", "NetworkIn"),
    ("AWS/EC2", "NetworkOut"),
    ("AWS/EC2", "DiskReadOps"),
    ("AWS/EC2", "DiskWriteOps"),
    ("AWS/EC2", "StatusCheckFailed"),
]

WINDOW_TO_HOURS = {"1h": 1, "24h": 24, "7d": 24 * 7}


class AwsCloudWatchCollector:
    def __init__(self, client_factory: AwsClientFactory | None = None) -> None:
        self.client_factory = client_factory or AwsClientFactory()

    async def collect(
        self,
        region: str,
        instances: list[AwsEc2Instance],
        window: str = "24h",
    ) -> AwsCloudWatchResult:
        return await asyncio.to_thread(self._collect_sync, region, instances, window)

    def _collect_sync(
        self,
        region: str,
        instances: list[AwsEc2Instance],
        window: str,
    ) -> AwsCloudWatchResult:
        if not instances:
            return AwsCloudWatchResult(collected=True, window=window, metrics=[], alarms=[])

        cloudwatch = self.client_factory.client("cloudwatch", region)
        hours = WINDOW_TO_HOURS.get(window, 24)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        period = 300 if hours <= 1 else 3600

        metrics: list[AwsMetricSample] = []
        for instance in instances[:25]:
            for namespace, metric_name in METRIC_DEFINITIONS:
                try:
                    response = cloudwatch.get_metric_statistics(
                        Namespace=namespace,
                        MetricName=metric_name,
                        Dimensions=[{"Name": "InstanceId", "Value": instance.instance_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=period,
                        Statistics=["Average", "Maximum"],
                    )
                    datapoints = sorted(
                        response.get("Datapoints", []),
                        key=lambda point: point.get("Timestamp") or datetime.min.replace(tzinfo=timezone.utc),
                    )
                    metrics.append(
                        AwsMetricSample(
                            metric_name=metric_name,
                            namespace=namespace,
                            dimensions={"InstanceId": instance.instance_id},
                            window=window,
                            datapoints=[
                                {
                                    "timestamp": (
                                        point.get("Timestamp").isoformat()
                                        if point.get("Timestamp") is not None
                                        else None
                                    ),
                                    "average": point.get("Average"),
                                    "maximum": point.get("Maximum"),
                                    "unit": point.get("Unit"),
                                }
                                for point in datapoints
                            ],
                            unit=datapoints[-1].get("Unit") if datapoints else None,
                        )
                    )
                except Exception:
                    continue

        alarms = self._collect_alarms(cloudwatch)
        return AwsCloudWatchResult(collected=True, window=window, metrics=metrics, alarms=alarms)

    def _collect_alarms(self, cloudwatch: Any) -> list[AwsCloudWatchAlarm]:
        alarms = []
        paginator = cloudwatch.get_paginator("describe_alarms")
        for page in paginator.paginate():
            for alarm in page.get("MetricAlarms", []):
                alarms.append(
                    AwsCloudWatchAlarm(
                        alarm_name=alarm.get("AlarmName", ""),
                        alarm_arn=alarm.get("AlarmArn"),
                        state_value=alarm.get("StateValue"),
                        state_reason=alarm.get("StateReason"),
                        metric_name=alarm.get("MetricName"),
                        namespace=alarm.get("Namespace"),
                        threshold=alarm.get("Threshold"),
                        comparison_operator=alarm.get("ComparisonOperator"),
                    )
                )
        return alarms
