"""AWS resource discovery for Cloud Cost Detector."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from botocore.exceptions import ClientError, NoCredentialsError

from app.modules.aws.errors import AwsApiError, AwsCredentialsError
from app.modules.aws.utils import parse_tags, tag_name
from app.modules.cloud_cost_detector.discovery.aws_clients import AwsClientFactory
from app.modules.cloud_cost_detector.models.schemas import (
    CloudCostAccountResponse,
    CloudCostAnalyzeResponse,
    CloudCostAutoScalingGroup,
    CloudCostEbsVolume,
    CloudCostEc2Instance,
    CloudCostElasticIp,
    CloudCostLoadBalancer,
    CloudCostResourceInventory,
    CloudCostResourceSummary,
    CloudCostSecurityGroup,
    CloudCostSecurityGroupRule,
    CloudCostSubnet,
    CloudCostVpc,
)


class AwsCostDiscoveryEngine:
    """Discover AWS resource inventory for cost optimization analysis."""

    def __init__(self, client_factory: AwsClientFactory | None = None) -> None:
        self.client_factory = client_factory or AwsClientFactory()

    async def get_account(self, region: str) -> CloudCostAccountResponse:
        return await asyncio.to_thread(self._get_account_sync, region)

    async def list_regions(self, region: str) -> list[str]:
        return await asyncio.to_thread(self._list_regions_sync, region)

    async def analyze(self, account_id: str, region: str) -> CloudCostAnalyzeResponse:
        return await asyncio.to_thread(self._analyze_sync, account_id, region)

    def _get_account_sync(self, region: str) -> CloudCostAccountResponse:
        sts = self._client("sts", region)
        try:
            identity = sts.get_caller_identity()
        except NoCredentialsError as exc:
            raise AwsCredentialsError(
                "AWS credentials not found. Configure credentials or mount ~/.aws."
            ) from exc
        except ClientError as exc:
            raise AwsApiError(str(exc)) from exc

        account_name = None
        try:
            iam = self._client("iam", region)
            aliases = iam.list_account_aliases().get("AccountAliases") or []
            if aliases:
                account_name = aliases[0]
        except Exception:
            account_name = None

        return CloudCostAccountResponse(
            account_id=identity["Account"],
            account_name=account_name,
        )

    def _list_regions_sync(self, region: str) -> list[str]:
        ec2 = self._client("ec2", region)
        try:
            response = ec2.describe_regions(AllRegions=False)
        except NoCredentialsError as exc:
            raise AwsCredentialsError(
                "AWS credentials not found. Configure credentials or mount ~/.aws."
            ) from exc
        except ClientError as exc:
            raise AwsApiError(str(exc)) from exc

        return sorted(
            item["RegionName"]
            for item in response.get("Regions", [])
            if item.get("RegionName")
        )

    def _analyze_sync(self, account_id: str, region: str) -> CloudCostAnalyzeResponse:
        notes: list[str] = []
        account = self._get_account_sync(region)
        if account.account_id != account_id:
            notes.append(
                "Requested account_id does not match active credentials. "
                "Using the credential account for discovery."
            )

        ec2 = self._client("ec2", region)
        self._validate_region(ec2, region)

        instances = self._discover_ec2(ec2)
        ebs_volumes = self._discover_ebs(ec2)
        elastic_ips = self._discover_elastic_ips(ec2)
        vpcs = self._discover_vpcs(ec2)
        subnets = self._discover_subnets(ec2)
        instance_security_map = {
            instance.instance_id: self._security_group_ids_for_instance(ec2, instance.instance_id)
            for instance in instances
        }
        security_groups = self._discover_security_groups(ec2, instance_security_map)
        load_balancers = self._discover_load_balancers(region)
        auto_scaling_groups = self._discover_auto_scaling_groups(region)

        inventory = CloudCostResourceInventory(
            ec2=instances,
            ebs=ebs_volumes,
            elastic_ips=elastic_ips,
            vpcs=vpcs,
            subnets=subnets,
            security_groups=security_groups,
            load_balancers=load_balancers,
            auto_scaling_groups=auto_scaling_groups,
        )

        return CloudCostAnalyzeResponse(
            account=account,
            region=region,
            collected_at=datetime.now(timezone.utc).isoformat(),
            resources=inventory,
            summary=CloudCostResourceSummary.from_inventory(inventory),
            notes=notes,
        )

    def _client(self, service_name: str, region: str) -> Any:
        try:
            return self.client_factory.client(service_name, region)
        except AwsCredentialsError:
            raise
        except Exception as exc:
            raise AwsApiError(str(exc)) from exc

    def _validate_region(self, ec2: Any, region: str) -> None:
        try:
            ec2.describe_availability_zones()
        except ClientError as exc:
            error = exc.response.get("Error", {})
            code = error.get("Code", "")
            if code in {"InvalidParameterValue", "AuthFailure"}:
                raise AwsApiError(f"Invalid or inaccessible region: {region}") from exc
            raise AwsApiError(str(exc)) from exc

    def _discover_ec2(self, ec2: Any) -> list[CloudCostEc2Instance]:
        instances: list[CloudCostEc2Instance] = []
        for reservation in ec2.describe_instances().get("Reservations", []):
            for item in reservation.get("Instances", []):
                instance_id = item.get("InstanceId")
                if not instance_id:
                    continue
                state = item.get("State") or {}
                launch_time = item.get("LaunchTime")
                instances.append(
                    CloudCostEc2Instance(
                        instance_id=instance_id,
                        name=tag_name(item.get("Tags")),
                        instance_type=item.get("InstanceType"),
                        state=state.get("Name"),
                        private_ip=item.get("PrivateIpAddress"),
                        public_ip=item.get("PublicIpAddress"),
                        launch_time=launch_time.isoformat() if launch_time is not None else None,
                        tags=parse_tags(item.get("Tags")),
                    )
                )
        return instances

    def _discover_ebs(self, ec2: Any) -> list[CloudCostEbsVolume]:
        volumes: list[CloudCostEbsVolume] = []
        for volume in ec2.describe_volumes().get("Volumes", []):
            attachment = (volume.get("Attachments") or [{}])[0]
            volumes.append(
                CloudCostEbsVolume(
                    volume_id=volume.get("VolumeId", ""),
                    size_gb=volume.get("Size"),
                    volume_type=volume.get("VolumeType"),
                    state=volume.get("State"),
                    attached_instance_id=attachment.get("InstanceId"),
                )
            )
        return volumes

    def _discover_elastic_ips(self, ec2: Any) -> list[CloudCostElasticIp]:
        addresses: list[CloudCostElasticIp] = []
        for address in ec2.describe_addresses().get("Addresses", []):
            allocation_id = address.get("AllocationId")
            if not allocation_id:
                continue
            addresses.append(
                CloudCostElasticIp(
                    allocation_id=allocation_id,
                    public_ip=address.get("PublicIp"),
                    associated_instance_id=address.get("InstanceId"),
                )
            )
        return addresses

    def _discover_vpcs(self, ec2: Any) -> list[CloudCostVpc]:
        vpcs: list[CloudCostVpc] = []
        for vpc in ec2.describe_vpcs().get("Vpcs", []):
            vpc_id = vpc.get("VpcId")
            if not vpc_id:
                continue
            vpcs.append(
                CloudCostVpc(
                    vpc_id=vpc_id,
                    cidr_block=vpc.get("CidrBlock"),
                    tags=parse_tags(vpc.get("Tags")),
                )
            )
        return vpcs

    def _discover_subnets(self, ec2: Any) -> list[CloudCostSubnet]:
        subnets: list[CloudCostSubnet] = []
        for subnet in ec2.describe_subnets().get("Subnets", []):
            subnet_id = subnet.get("SubnetId")
            if not subnet_id:
                continue
            subnets.append(
                CloudCostSubnet(
                    subnet_id=subnet_id,
                    cidr_block=subnet.get("CidrBlock"),
                    availability_zone=subnet.get("AvailabilityZone"),
                    vpc_id=subnet.get("VpcId"),
                )
            )
        return subnets

    def _security_group_ids_for_instance(self, ec2: Any, instance_id: str) -> list[str]:
        try:
            response = ec2.describe_instances(InstanceIds=[instance_id])
            for reservation in response.get("Reservations", []):
                for item in reservation.get("Instances", []):
                    return [
                        group.get("GroupId", "")
                        for group in item.get("SecurityGroups", [])
                        if group.get("GroupId")
                    ]
        except ClientError:
            return []
        return []

    def _discover_security_groups(
        self,
        ec2: Any,
        instance_security_map: dict[str, list[str]],
    ) -> list[CloudCostSecurityGroup]:
        groups: list[CloudCostSecurityGroup] = []
        for group in ec2.describe_security_groups().get("SecurityGroups", []):
            group_id = group.get("GroupId")
            if not group_id:
                continue
            groups.append(
                CloudCostSecurityGroup(
                    security_group_id=group_id,
                    name=group.get("GroupName"),
                    ingress_rules=self._parse_permissions(group.get("IpPermissions", [])),
                    egress_rules=self._parse_permissions(group.get("IpPermissionsEgress", [])),
                )
            )
        return groups

    def _parse_permissions(self, permissions: list[dict[str, Any]]) -> list[CloudCostSecurityGroupRule]:
        rules: list[CloudCostSecurityGroupRule] = []
        for permission in permissions:
            protocol = permission.get("IpProtocol")
            from_port = permission.get("FromPort")
            to_port = permission.get("ToPort")
            for ip_range in permission.get("IpRanges", []):
                rules.append(
                    CloudCostSecurityGroupRule(
                        protocol=protocol,
                        from_port=from_port,
                        to_port=to_port,
                        cidr_blocks=[ip_range.get("CidrIp", "")] if ip_range.get("CidrIp") else [],
                        description=ip_range.get("Description"),
                    )
                )
            for pair in permission.get("UserIdGroupPairs", []):
                source_sg = pair.get("GroupId")
                if source_sg:
                    rules.append(
                        CloudCostSecurityGroupRule(
                            protocol=protocol,
                            from_port=from_port,
                            to_port=to_port,
                            source_security_group_id=source_sg,
                            description=pair.get("Description"),
                        )
                    )
        return rules

    def _discover_load_balancers(self, region: str) -> list[CloudCostLoadBalancer]:
        elbv2 = self._client("elbv2", region)
        load_balancers: list[CloudCostLoadBalancer] = []
        for item in elbv2.describe_load_balancers().get("LoadBalancers", []):
            lb_type = item.get("Type")
            if lb_type not in {"application", "network"}:
                continue
            load_balancers.append(
                CloudCostLoadBalancer(
                    name=item.get("LoadBalancerName"),
                    type=lb_type,
                    scheme=item.get("Scheme"),
                    state=(item.get("State") or {}).get("Code"),
                    load_balancer_arn=item.get("LoadBalancerArn"),
                )
            )
        return load_balancers

    def _discover_auto_scaling_groups(self, region: str) -> list[CloudCostAutoScalingGroup]:
        autoscaling = self._client("autoscaling", region)
        groups: list[CloudCostAutoScalingGroup] = []
        paginator = autoscaling.get_paginator("describe_auto_scaling_groups")
        for page in paginator.paginate():
            for group in page.get("AutoScalingGroups", []):
                name = group.get("AutoScalingGroupName")
                if not name:
                    continue
                instances = [
                    instance.get("InstanceId", "")
                    for instance in group.get("Instances", [])
                    if instance.get("InstanceId")
                ]
                groups.append(
                    CloudCostAutoScalingGroup(
                        auto_scaling_group_name=name,
                        desired_capacity=group.get("DesiredCapacity"),
                        current_capacity=len(instances),
                        instance_ids=instances,
                    )
                )
        return groups
