"""Auto Scaling group discovery."""

from __future__ import annotations

import asyncio

from app.modules.aws.client import AwsClientFactory
from app.modules.aws.models import AwsAutoScalingGroup, AwsScalingActivity


class AwsAutoScalingDiscovery:
    def __init__(self, client_factory: AwsClientFactory | None = None) -> None:
        self.client_factory = client_factory or AwsClientFactory()

    async def discover(self, region: str) -> list[AwsAutoScalingGroup]:
        return await asyncio.to_thread(self._discover_sync, region)

    def _discover_sync(self, region: str) -> list[AwsAutoScalingGroup]:
        autoscaling = self.client_factory.client("autoscaling", region)
        groups: list[AwsAutoScalingGroup] = []

        for group in autoscaling.describe_auto_scaling_groups().get("AutoScalingGroups", []):
            name = group.get("AutoScalingGroupName", "")
            launch_template = None
            launch_template_spec = group.get("LaunchTemplate") or group.get("MixedInstancesPolicy", {}).get(
                "LaunchTemplate", {}
            ).get("LaunchTemplateSpecification")
            if launch_template_spec:
                launch_template = launch_template_spec.get("LaunchTemplateName") or launch_template_spec.get(
                    "LaunchTemplateId"
                )

            instance_ids = [
                instance.get("InstanceId", "")
                for instance in group.get("Instances", [])
                if instance.get("InstanceId")
            ]

            activities_response = autoscaling.describe_scaling_activities(
                AutoScalingGroupName=name,
                MaxRecords=10,
            )
            activities = [
                AwsScalingActivity(
                    activity_id=activity.get("ActivityId", ""),
                    status_code=activity.get("StatusCode"),
                    description=activity.get("Description"),
                    cause=activity.get("Cause"),
                    start_time=(
                        activity.get("StartTime").isoformat()
                        if activity.get("StartTime") is not None
                        else None
                    ),
                    end_time=(
                        activity.get("EndTime").isoformat()
                        if activity.get("EndTime") is not None
                        else None
                    ),
                )
                for activity in activities_response.get("Activities", [])
            ]

            groups.append(
                AwsAutoScalingGroup(
                    auto_scaling_group_name=name,
                    launch_template=launch_template,
                    desired_capacity=group.get("DesiredCapacity"),
                    min_size=group.get("MinSize"),
                    max_size=group.get("MaxSize"),
                    current_capacity=len(instance_ids),
                    instance_ids=instance_ids,
                    target_group_arns=group.get("TargetGroupARNs", []),
                    scaling_activities=activities,
                )
            )

        return groups
