"""Application and Network Load Balancer discovery."""

from __future__ import annotations

import asyncio
from typing import Any

from app.modules.aws.client import AwsClientFactory
from app.modules.aws.models import AwsLoadBalancer, AwsLoadBalancerListener, AwsTargetGroup, AwsTargetHealth


class AwsLoadBalancerDiscovery:
    def __init__(self, client_factory: AwsClientFactory | None = None) -> None:
        self.client_factory = client_factory or AwsClientFactory()

    async def discover(self, region: str) -> tuple[list[AwsLoadBalancer], list[AwsTargetGroup]]:
        return await asyncio.to_thread(self._discover_sync, region)

    def _discover_sync(self, region: str) -> tuple[list[AwsLoadBalancer], list[AwsTargetGroup]]:
        elbv2 = self.client_factory.client("elbv2", region)

        load_balancers: list[AwsLoadBalancer] = []
        target_groups: list[AwsTargetGroup] = []

        for item in elbv2.describe_load_balancers().get("LoadBalancers", []):
            lb_type = item.get("Type")
            if lb_type not in {"application", "network"}:
                continue

            lb_arn = item.get("LoadBalancerArn", "")
            listeners = self._discover_listeners(elbv2, lb_arn)
            target_group_arns = self._discover_target_group_arns(elbv2, lb_arn)

            load_balancers.append(
                AwsLoadBalancer(
                    load_balancer_arn=lb_arn,
                    name=item.get("LoadBalancerName"),
                    type=lb_type,
                    scheme=item.get("Scheme"),
                    dns_name=item.get("DNSName"),
                    vpc_id=item.get("VpcId"),
                    security_groups=item.get("SecurityGroups", []),
                    availability_zones=[
                        zone.get("ZoneName", "")
                        for zone in item.get("AvailabilityZones", [])
                        if zone.get("ZoneName")
                    ],
                    state=(item.get("State") or {}).get("Code"),
                    listeners=listeners,
                    target_group_arns=target_group_arns,
                )
            )

        for group in elbv2.describe_target_groups().get("TargetGroups", []):
            group_arn = group.get("TargetGroupArn", "")
            targets = self._discover_target_health(elbv2, group_arn)
            target_groups.append(
                AwsTargetGroup(
                    target_group_arn=group_arn,
                    target_group_name=group.get("TargetGroupName", ""),
                    protocol=group.get("Protocol"),
                    port=group.get("Port"),
                    vpc_id=group.get("VpcId"),
                    load_balancer_arns=group.get("LoadBalancerArns", []),
                    targets=targets,
                )
            )

        return load_balancers, target_groups

    def _discover_listeners(self, elbv2: Any, load_balancer_arn: str) -> list[AwsLoadBalancerListener]:
        listeners = []
        response = elbv2.describe_listeners(LoadBalancerArn=load_balancer_arn)
        for listener in response.get("Listeners", []):
            listener_arn = listener.get("ListenerArn", "")
            rules = elbv2.describe_rules(ListenerArn=listener_arn).get("Rules", [])
            listeners.append(
                AwsLoadBalancerListener(
                    listener_arn=listener_arn,
                    protocol=listener.get("Protocol"),
                    port=listener.get("Port"),
                    rules=[
                        {
                            "rule_arn": rule.get("RuleArn"),
                            "priority": rule.get("Priority"),
                            "conditions": rule.get("Conditions", []),
                            "actions": rule.get("Actions", []),
                        }
                        for rule in rules
                    ],
                )
            )
        return listeners

    def _discover_target_group_arns(self, elbv2: Any, load_balancer_arn: str) -> list[str]:
        response = elbv2.describe_target_groups(LoadBalancerArn=load_balancer_arn)
        return [
            group.get("TargetGroupArn", "")
            for group in response.get("TargetGroups", [])
            if group.get("TargetGroupArn")
        ]

    def _discover_target_health(self, elbv2: Any, target_group_arn: str) -> list[AwsTargetHealth]:
        try:
            response = elbv2.describe_target_health(TargetGroupArn=target_group_arn)
        except Exception:
            return []

        targets = []
        for description in response.get("TargetHealthDescriptions", []):
            target = description.get("Target", {})
            health = description.get("TargetHealth", {})
            target_id = target.get("Id", "")
            if not target_id:
                continue
            targets.append(
                AwsTargetHealth(
                    target_id=target_id,
                    port=target.get("Port"),
                    health_state=health.get("State"),
                    reason=health.get("Reason"),
                    description=health.get("Description"),
                )
            )
        return targets
