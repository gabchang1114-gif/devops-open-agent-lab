"""EC2 and EBS discovery."""

from __future__ import annotations

import asyncio
from typing import Any

from app.modules.aws.client import AwsClientFactory
from app.modules.aws.models import AwsEbsVolume, AwsEc2Instance, AwsElasticIp
from app.modules.aws.utils import parse_tags, tag_name


class AwsEc2Discovery:
    def __init__(self, client_factory: AwsClientFactory | None = None) -> None:
        self.client_factory = client_factory or AwsClientFactory()

    async def discover(self, region: str) -> tuple[list[AwsEc2Instance], list[AwsEbsVolume], list[AwsElasticIp]]:
        return await asyncio.to_thread(self._discover_sync, region)

    def _discover_sync(self, region: str) -> tuple[list[AwsEc2Instance], list[AwsEbsVolume], list[AwsElasticIp]]:
        ec2 = self.client_factory.client("ec2", region)

        reservations = ec2.describe_instances().get("Reservations", [])
        volumes_by_instance = self._map_volumes(ec2)
        instance_to_asg: dict[str, str] = {}

        instances: list[AwsEc2Instance] = []
        for reservation in reservations:
            for item in reservation.get("Instances", []):
                instance_id = item.get("InstanceId", "")
                if not instance_id:
                    continue

                for tag in item.get("Tags", []):
                    if tag.get("Key") == "aws:autoscaling:groupName":
                        instance_to_asg[instance_id] = tag.get("Value", "")

                security_groups = [
                    group.get("GroupId", "")
                    for group in item.get("SecurityGroups", [])
                    if group.get("GroupId")
                ]
                iam_profile = item.get("IamInstanceProfile") or {}
                state = item.get("State", {})
                launch_time = item.get("LaunchTime")
                instances.append(
                    AwsEc2Instance(
                        instance_id=instance_id,
                        name=tag_name(item.get("Tags")),
                        tags=parse_tags(item.get("Tags")),
                        instance_type=item.get("InstanceType"),
                        private_ip=item.get("PrivateIpAddress"),
                        public_ip=item.get("PublicIpAddress"),
                        ami_id=item.get("ImageId"),
                        subnet_id=item.get("SubnetId"),
                        vpc_id=item.get("VpcId"),
                        security_groups=security_groups,
                        iam_role=iam_profile.get("Arn"),
                        auto_scaling_group=instance_to_asg.get(instance_id),
                        volumes=volumes_by_instance.get(instance_id, []),
                        state=state.get("Name"),
                        state_transition_reason=item.get("StateTransitionReason"),
                        launch_time=launch_time.isoformat() if launch_time is not None else None,
                        status_checks=self._status_checks(ec2, instance_id),
                    )
                )

        standalone_volumes = self._discover_volumes(ec2)
        elastic_ips = self._discover_elastic_ips(ec2)
        return instances, standalone_volumes, elastic_ips

    def _map_volumes(self, ec2: Any) -> dict[str, list[AwsEbsVolume]]:
        volumes_by_instance: dict[str, list[AwsEbsVolume]] = {}
        for volume in ec2.describe_volumes().get("Volumes", []):
            attachment = (volume.get("Attachments") or [{}])[0]
            instance_id = attachment.get("InstanceId")
            if not instance_id:
                continue
            volumes_by_instance.setdefault(instance_id, []).append(self._volume_model(volume, attachment))
        return volumes_by_instance

    def _discover_volumes(self, ec2: Any) -> list[AwsEbsVolume]:
        return [self._volume_model(volume) for volume in ec2.describe_volumes().get("Volumes", [])]

    def _volume_model(self, volume: dict[str, Any], attachment: dict[str, Any] | None = None) -> AwsEbsVolume:
        attachment = attachment or ((volume.get("Attachments") or [{}])[0])
        return AwsEbsVolume(
            volume_id=volume.get("VolumeId", ""),
            size_gb=volume.get("Size"),
            volume_type=volume.get("VolumeType"),
            iops=volume.get("Iops"),
            throughput=volume.get("Throughput"),
            state=volume.get("State"),
            attached_instance_id=attachment.get("InstanceId"),
            device=attachment.get("Device"),
            encrypted=volume.get("Encrypted"),
        )

    def _discover_elastic_ips(self, ec2: Any) -> list[AwsElasticIp]:
        addresses = []
        for address in ec2.describe_addresses().get("Addresses", []):
            addresses.append(
                AwsElasticIp(
                    allocation_id=address.get("AllocationId", ""),
                    public_ip=address.get("PublicIp"),
                    instance_id=address.get("InstanceId"),
                    network_interface_id=address.get("NetworkInterfaceId"),
                    domain=address.get("Domain"),
                )
            )
        return addresses

    def _status_checks(self, ec2: Any, instance_id: str) -> dict[str, Any]:
        try:
            response = ec2.describe_instance_status(InstanceIds=[instance_id], IncludeAllInstances=True)
            statuses = response.get("InstanceStatuses") or []
            if not statuses:
                return {}
            status = statuses[0]
            return {
                "instance_status": (status.get("InstanceStatus") or {}).get("Status"),
                "system_status": (status.get("SystemStatus") or {}).get("Status"),
            }
        except Exception:
            return {}
