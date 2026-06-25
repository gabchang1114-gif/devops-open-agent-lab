"""CloudWatch metrics and alarm collection."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from app.modules.aws.client import AwsClientFactory
from app.modules.aws.models import (
    AwsCloudWatchAlarm,
    AwsCloudWatchResult,
    AwsEc2Instance,
    AwsLambdaFunction,
    AwsLambdaInvocationMetrics,
    AwsMetricSample,
)

EC2_METRIC_DEFINITIONS = [
    ("AWS/EC2", "CPUUtilization"),
    ("AWS/EC2", "NetworkIn"),
    ("AWS/EC2", "NetworkOut"),
    ("AWS/EC2", "DiskReadOps"),
    ("AWS/EC2", "DiskWriteOps"),
    ("AWS/EC2", "StatusCheckFailed"),
]

LAMBDA_METRIC_DEFINITIONS = [
    ("Errors", "Sum"),
    ("Throttles", "Sum"),
    ("Duration", "Maximum"),
    ("Duration", "Average"),
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
        lambda_functions: list[AwsLambdaFunction] | None = None,
    ) -> AwsCloudWatchResult:
        return await asyncio.to_thread(
            self._collect_sync,
            region,
            instances,
            window,
            lambda_functions or [],
        )

    def _collect_sync(
        self,
        region: str,
        instances: list[AwsEc2Instance],
        window: str,
        lambda_functions: list[AwsLambdaFunction],
    ) -> AwsCloudWatchResult:
        cloudwatch = self.client_factory.client("cloudwatch", region)
        hours = WINDOW_TO_HOURS.get(window, 24)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        period = 300 if hours <= 1 else 3600

        metrics: list[AwsMetricSample] = []
        if instances:
            metrics = self._collect_ec2_metrics(
                cloudwatch,
                instances,
                start_time,
                end_time,
                period,
                window,
            )

        lambda_metrics: list[AwsLambdaInvocationMetrics] = []
        if lambda_functions:
            logs = self.client_factory.client("logs", region)
            lambda_metrics = self._collect_lambda_metrics(
                cloudwatch,
                logs,
                lambda_functions,
                start_time,
                end_time,
                period,
            )

        alarms = self._collect_alarms(cloudwatch)
        collected = bool(instances or lambda_functions)
        return AwsCloudWatchResult(
            collected=collected,
            window=window,
            metrics=metrics,
            lambda_metrics=lambda_metrics,
            alarms=alarms,
        )

    def _collect_ec2_metrics(
        self,
        cloudwatch: Any,
        instances: list[AwsEc2Instance],
        start_time: datetime,
        end_time: datetime,
        period: int,
        window: str,
    ) -> list[AwsMetricSample]:
        metrics: list[AwsMetricSample] = []
        for instance in instances[:25]:
            for namespace, metric_name in EC2_METRIC_DEFINITIONS:
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
                        key=lambda point: point.get("Timestamp")
                        or datetime.min.replace(tzinfo=timezone.utc),
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
        return metrics

    def _collect_lambda_metrics(
        self,
        cloudwatch: Any,
        logs: Any,
        functions: list[AwsLambdaFunction],
        start_time: datetime,
        end_time: datetime,
        period: int,
    ) -> list[AwsLambdaInvocationMetrics]:
        results: list[AwsLambdaInvocationMetrics] = []
        for function in functions[:25]:
            dimensions = [{"Name": "FunctionName", "Value": function.function_name}]
            errors = self._metric_sum(
                cloudwatch,
                "Errors",
                dimensions,
                start_time,
                end_time,
                period,
            )
            throttles = self._metric_sum(
                cloudwatch,
                "Throttles",
                dimensions,
                start_time,
                end_time,
                period,
            )
            max_duration = self._metric_stat(
                cloudwatch,
                "Duration",
                dimensions,
                start_time,
                end_time,
                period,
                "Maximum",
            )
            avg_duration = self._metric_stat(
                cloudwatch,
                "Duration",
                dimensions,
                start_time,
                end_time,
                period,
                "Average",
            )
            timeout_log_events = self._count_timeout_log_events(
                logs,
                function.function_name,
                start_time,
                end_time,
            )
            timeout_ms = (function.timeout or 0) * 1000
            duration_at_timeout = bool(
                function.timeout
                and max_duration is not None
                and max_duration >= max(timeout_ms - 25, 0)
            )
            results.append(
                AwsLambdaInvocationMetrics(
                    function_name=function.function_name,
                    configured_timeout_sec=function.timeout,
                    errors=errors,
                    throttles=throttles,
                    max_duration_ms=max_duration,
                    avg_duration_ms=avg_duration,
                    timeout_log_events=timeout_log_events,
                    duration_at_timeout=duration_at_timeout,
                )
            )
        return results

    def _metric_sum(
        self,
        cloudwatch: Any,
        metric_name: str,
        dimensions: list[dict[str, str]],
        start_time: datetime,
        end_time: datetime,
        period: int,
    ) -> int:
        value = self._metric_stat(
            cloudwatch,
            metric_name,
            dimensions,
            start_time,
            end_time,
            period,
            "Sum",
        )
        return int(value or 0)

    def _metric_stat(
        self,
        cloudwatch: Any,
        metric_name: str,
        dimensions: list[dict[str, str]],
        start_time: datetime,
        end_time: datetime,
        period: int,
        statistic: str,
    ) -> float | None:
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/Lambda",
                MetricName=metric_name,
                Dimensions=dimensions,
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=[statistic],
            )
            datapoints = response.get("Datapoints") or []
            if not datapoints:
                return None
            values = [point.get(statistic) for point in datapoints if point.get(statistic) is not None]
            if not values:
                return None
            if statistic == "Maximum":
                return float(max(values))
            if statistic == "Sum":
                return float(sum(values))
            return float(sum(values) / len(values))
        except Exception:
            return None

    def _count_timeout_log_events(
        self,
        logs: Any,
        function_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        log_group = f"/aws/lambda/{function_name}"
        total = 0
        for pattern in ('"Status: timeout"', '"Task timed out"'):
            try:
                response = logs.filter_log_events(
                    logGroupName=log_group,
                    startTime=int(start_time.timestamp() * 1000),
                    endTime=int(end_time.timestamp() * 1000),
                    filterPattern=pattern,
                    limit=100,
                )
                total += len(response.get("events") or [])
            except Exception:
                continue
        return total

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
