"""AWS topology builder producing graph-ready relationships."""

from __future__ import annotations

from app.modules.aws.models import (
    AwsResourceDiscoveryResult,
    AwsTopologyGraphNode,
    AwsTopologyRelationship,
    AwsTopologyResult,
)
from app.modules.aws.utils import aws_ref


class AwsTopologyBuilder:
    def build(self, resources: AwsResourceDiscoveryResult, region: str) -> AwsTopologyResult:
        relationships: list[AwsTopologyRelationship] = []
        nodes: set[str] = set()
        graph_nodes: dict[str, AwsTopologyGraphNode] = {}

        def add_node(kind: str, resource_id: str, name: str | None = None) -> str:
            ref = aws_ref(kind, resource_id)
            nodes.add(ref)
            graph_nodes[ref] = AwsTopologyGraphNode(
                id=ref,
                kind=kind,
                name=name or resource_id,
                region=region,
            )
            return ref

        def relate(source: str, target: str, relationship_type: str) -> None:
            relationships.append(
                AwsTopologyRelationship(
                    source=source,
                    target=target,
                    type=relationship_type,
                    region=region,
                )
            )

        for vpc in resources.vpcs:
            vpc_ref = add_node("vpc", vpc.vpc_id, vpc.name)
            for subnet in vpc.subnets:
                subnet_ref = add_node("subnet", subnet.subnet_id, subnet.name)
                relate(vpc_ref, subnet_ref, "contains")
            for route_table in vpc.route_tables:
                table_ref = add_node("route_table", route_table.route_table_id, route_table.name)
                relate(vpc_ref, table_ref, "contains")
                for subnet_id in route_table.associated_subnet_ids:
                    subnet_ref = add_node("subnet", subnet_id)
                    relate(subnet_ref, table_ref, "associated_with")
                for route in route_table.routes:
                    gateway_id = route.get("GatewayId") or route.get("NatGatewayId")
                    if not gateway_id:
                        continue
                    if gateway_id.startswith("igw-"):
                        gateway_ref = add_node("internet_gateway", gateway_id)
                        relate(table_ref, gateway_ref, "routes_to")
                    elif gateway_id.startswith("nat-"):
                        gateway_ref = add_node("nat_gateway", gateway_id)
                        relate(table_ref, gateway_ref, "routes_to")
            for gateway in vpc.internet_gateways:
                gateway_ref = add_node("internet_gateway", gateway.internet_gateway_id, gateway.name)
                relate(vpc_ref, gateway_ref, "attached_to")
            for gateway in vpc.nat_gateways:
                gateway_ref = add_node("nat_gateway", gateway.nat_gateway_id, gateway.name)
                relate(vpc_ref, gateway_ref, "contains")
                if gateway.subnet_id:
                    subnet_ref = add_node("subnet", gateway.subnet_id)
                    relate(subnet_ref, gateway_ref, "hosts")
            for acl in vpc.network_acls:
                acl_ref = add_node("network_acl", acl.network_acl_id, acl.name)
                relate(vpc_ref, acl_ref, "contains")

        for instance in resources.ec2_instances:
            instance_ref = add_node("ec2", instance.instance_id, instance.name)
            if instance.vpc_id:
                relate(add_node("vpc", instance.vpc_id), instance_ref, "contains")
            if instance.subnet_id:
                relate(add_node("subnet", instance.subnet_id), instance_ref, "contains")
            for group_id in instance.security_groups:
                group_ref = add_node("security_group", group_id)
                relate(instance_ref, group_ref, "uses")
            if instance.iam_role:
                role_name = instance.iam_role.rsplit("/", 1)[-1]
                role_ref = add_node("iam_role", role_name, role_name)
                relate(instance_ref, role_ref, "assumes")
            for volume in instance.volumes:
                volume_ref = add_node("ebs", volume.volume_id)
                relate(instance_ref, volume_ref, "attached_to")
            if instance.auto_scaling_group:
                asg_ref = add_node("asg", instance.auto_scaling_group, instance.auto_scaling_group)
                relate(asg_ref, instance_ref, "owns")

        for group in resources.security_groups:
            add_node("security_group", group.security_group_id, group.name)
            for resource_id in group.attached_resource_ids:
                relate(add_node("ec2", resource_id), add_node("security_group", group.security_group_id), "uses")

        for load_balancer in resources.load_balancers:
            lb_ref = add_node("load_balancer", load_balancer.load_balancer_arn, load_balancer.name)
            if load_balancer.vpc_id:
                relate(add_node("vpc", load_balancer.vpc_id), lb_ref, "contains")
            for group_arn in load_balancer.target_group_arns:
                group_ref = add_node("target_group", group_arn)
                relate(lb_ref, group_ref, "routes_to")

        for target_group in resources.target_groups:
            group_ref = add_node("target_group", target_group.target_group_arn, target_group.target_group_name)
            for target in target_group.targets:
                target_ref = add_node("ec2", target.target_id)
                relate(group_ref, target_ref, "routes_to")

        for asg in resources.auto_scaling_groups:
            asg_ref = add_node("asg", asg.auto_scaling_group_name, asg.auto_scaling_group_name)
            for instance_id in asg.instance_ids:
                relate(asg_ref, add_node("ec2", instance_id), "owns")
            for target_group_arn in asg.target_group_arns:
                relate(asg_ref, add_node("target_group", target_group_arn), "registers_with")

        for volume in resources.ebs_volumes:
            volume_ref = add_node("ebs", volume.volume_id)
            if volume.attached_instance_id:
                relate(add_node("ec2", volume.attached_instance_id), volume_ref, "attached_to")

        for address in resources.elastic_ips:
            eip_ref = add_node("elastic_ip", address.allocation_id, address.public_ip)
            if address.instance_id:
                relate(eip_ref, add_node("ec2", address.instance_id), "associated_with")

        for function in resources.lambda_functions:
            function_ref = add_node("lambda", function.function_arn, function.function_name)
            if function.vpc_id:
                relate(add_node("vpc", function.vpc_id), function_ref, "contains")
            for subnet_id in function.subnet_ids:
                relate(add_node("subnet", subnet_id), function_ref, "contains")
            for group_id in function.security_group_ids:
                group_ref = add_node("security_group", group_id)
                relate(function_ref, group_ref, "uses")
            if function.role:
                role_name = function.role.rsplit("/", 1)[-1]
                role_ref = add_node("iam_role", role_name, role_name)
                relate(function_ref, role_ref, "assumes")
            for event_source in function.event_sources:
                if not event_source.event_source_arn:
                    continue
                source_ref = add_node("event_source", event_source.event_source_arn)
                relate(source_ref, function_ref, "invokes")

        for bucket in resources.s3_buckets:
            bucket_ref = add_node("s3", bucket.bucket_name, bucket.bucket_name)
            for notification in bucket.notifications:
                if notification.target_type != "lambda" or not notification.target_arn:
                    continue
                lambda_ref = add_node("lambda", notification.target_arn)
                relate(bucket_ref, lambda_ref, "triggers")

        return AwsTopologyResult(
            relationships=self._deduplicate(relationships),
            nodes=sorted(nodes),
            graph_nodes=sorted(graph_nodes.values(), key=lambda node: (node.kind, node.name)),
        )

    def _deduplicate(
        self, relationships: list[AwsTopologyRelationship]
    ) -> list[AwsTopologyRelationship]:
        seen: set[tuple[str, str, str, str | None]] = set()
        unique: list[AwsTopologyRelationship] = []
        for relationship in relationships:
            key = (
                relationship.source,
                relationship.target,
                relationship.type,
                relationship.region,
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(relationship)
        return unique
