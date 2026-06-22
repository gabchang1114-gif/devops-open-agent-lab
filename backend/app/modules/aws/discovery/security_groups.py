"""Security group discovery."""

from __future__ import annotations

import asyncio
from typing import Any

from app.modules.aws.client import AwsClientFactory
from app.modules.aws.models import AwsSecurityGroup, AwsSecurityGroupRule


class AwsSecurityGroupDiscovery:
    def __init__(self, client_factory: AwsClientFactory | None = None) -> None:
        self.client_factory = client_factory or AwsClientFactory()

    async def discover(
        self,
        region: str,
        instance_security_map: dict[str, list[str]] | None = None,
    ) -> list[AwsSecurityGroup]:
        return await asyncio.to_thread(self._discover_sync, region, instance_security_map or {})

    def _discover_sync(
        self,
        region: str,
        instance_security_map: dict[str, list[str]],
    ) -> list[AwsSecurityGroup]:
        ec2 = self.client_factory.client("ec2", region)
        attached_resources: dict[str, list[str]] = {}
        for instance_id, group_ids in instance_security_map.items():
            for group_id in group_ids:
                attached_resources.setdefault(group_id, []).append(instance_id)

        groups: list[AwsSecurityGroup] = []
        for group in ec2.describe_security_groups().get("SecurityGroups", []):
            group_id = group.get("GroupId", "")
            if not group_id:
                continue
            groups.append(
                AwsSecurityGroup(
                    security_group_id=group_id,
                    name=group.get("GroupName"),
                    description=group.get("Description"),
                    vpc_id=group.get("VpcId"),
                    ingress_rules=self._parse_permissions(group.get("IpPermissions", [])),
                    egress_rules=self._parse_permissions(group.get("IpPermissionsEgress", [])),
                    attached_resource_ids=attached_resources.get(group_id, []),
                )
            )
        return groups

    def _parse_permissions(self, permissions: list[dict[str, Any]]) -> list[AwsSecurityGroupRule]:
        rules: list[AwsSecurityGroupRule] = []
        for permission in permissions:
            protocol = permission.get("IpProtocol")
            from_port = permission.get("FromPort")
            to_port = permission.get("ToPort")
            for ip_range in permission.get("IpRanges", []):
                rules.append(
                    AwsSecurityGroupRule(
                        protocol=protocol,
                        from_port=from_port,
                        to_port=to_port,
                        cidr_blocks=[ip_range.get("CidrIp", "")] if ip_range.get("CidrIp") else [],
                        description=ip_range.get("Description"),
                    )
                )
            for pair in permission.get("UserIdGroupPairs", []):
                rules.append(
                    AwsSecurityGroupRule(
                        protocol=protocol,
                        from_port=from_port,
                        to_port=to_port,
                        source_security_group_id=pair.get("GroupId"),
                        description=pair.get("Description"),
                    )
                )
        return rules
