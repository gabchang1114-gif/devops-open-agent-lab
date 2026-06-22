"""VPC networking discovery."""

from __future__ import annotations

import asyncio
from typing import Any

from app.modules.aws.client import AwsClientFactory
from app.modules.aws.models import (
    AwsInternetGateway,
    AwsNatGateway,
    AwsNetworkAcl,
    AwsRouteTable,
    AwsSubnet,
    AwsVpc,
)
from app.modules.aws.utils import tag_name


class AwsVpcDiscovery:
    def __init__(self, client_factory: AwsClientFactory | None = None) -> None:
        self.client_factory = client_factory or AwsClientFactory()

    async def discover(self, region: str) -> list[AwsVpc]:
        return await asyncio.to_thread(self._discover_sync, region)

    def _discover_sync(self, region: str) -> list[AwsVpc]:
        ec2 = self.client_factory.client("ec2", region)

        subnets = self._discover_subnets(ec2)
        route_tables = self._discover_route_tables(ec2)
        internet_gateways = self._discover_internet_gateways(ec2)
        nat_gateways = self._discover_nat_gateways(ec2)
        network_acls = self._discover_network_acls(ec2)

        vpcs: list[AwsVpc] = []
        for vpc in ec2.describe_vpcs().get("Vpcs", []):
            vpc_id = vpc.get("VpcId", "")
            if not vpc_id:
                continue
            vpcs.append(
                AwsVpc(
                    vpc_id=vpc_id,
                    name=tag_name(vpc.get("Tags")),
                    cidr_block=vpc.get("CidrBlock"),
                    is_default=vpc.get("IsDefault"),
                    state=vpc.get("State"),
                    subnets=[subnet for subnet in subnets if subnet.vpc_id == vpc_id],
                    route_tables=[table for table in route_tables if table.vpc_id == vpc_id],
                    internet_gateways=[
                        gateway for gateway in internet_gateways if vpc_id in gateway.vpc_ids
                    ],
                    nat_gateways=[gateway for gateway in nat_gateways if gateway.vpc_id == vpc_id],
                    network_acls=[acl for acl in network_acls if acl.vpc_id == vpc_id],
                )
            )
        return vpcs

    def _discover_subnets(self, ec2: Any) -> list[AwsSubnet]:
        subnets = []
        for subnet in ec2.describe_subnets().get("Subnets", []):
            subnets.append(
                AwsSubnet(
                    subnet_id=subnet.get("SubnetId", ""),
                    name=tag_name(subnet.get("Tags")),
                    vpc_id=subnet.get("VpcId", ""),
                    cidr_block=subnet.get("CidrBlock"),
                    availability_zone=subnet.get("AvailabilityZone"),
                    map_public_ip_on_launch=subnet.get("MapPublicIpOnLaunch"),
                )
            )
        return subnets

    def _discover_route_tables(self, ec2: Any) -> list[AwsRouteTable]:
        tables = []
        for table in ec2.describe_route_tables().get("RouteTables", []):
            associated_subnet_ids = [
                association.get("SubnetId", "")
                for association in table.get("Associations", [])
                if association.get("SubnetId")
            ]
            tables.append(
                AwsRouteTable(
                    route_table_id=table.get("RouteTableId", ""),
                    name=tag_name(table.get("Tags")),
                    vpc_id=table.get("VpcId", ""),
                    associated_subnet_ids=associated_subnet_ids,
                    routes=table.get("Routes", []),
                )
            )
        return tables

    def _discover_internet_gateways(self, ec2: Any) -> list[AwsInternetGateway]:
        gateways = []
        for gateway in ec2.describe_internet_gateways().get("InternetGateways", []):
            vpc_ids = [
                attachment.get("VpcId", "")
                for attachment in gateway.get("Attachments", [])
                if attachment.get("VpcId")
            ]
            gateways.append(
                AwsInternetGateway(
                    internet_gateway_id=gateway.get("InternetGatewayId", ""),
                    name=tag_name(gateway.get("Tags")),
                    vpc_ids=vpc_ids,
                    state=(gateway.get("Attachments") or [{}])[0].get("State"),
                )
            )
        return gateways

    def _discover_nat_gateways(self, ec2: Any) -> list[AwsNatGateway]:
        gateways = []
        for gateway in ec2.describe_nat_gateways().get("NatGateways", []):
            public_ip = None
            addresses = gateway.get("NatGatewayAddresses") or []
            if addresses:
                public_ip = addresses[0].get("PublicIp")
            gateways.append(
                AwsNatGateway(
                    nat_gateway_id=gateway.get("NatGatewayId", ""),
                    name=tag_name(gateway.get("Tags")),
                    subnet_id=gateway.get("SubnetId"),
                    vpc_id=gateway.get("VpcId"),
                    state=gateway.get("State"),
                    public_ip=public_ip,
                )
            )
        return gateways

    def _discover_network_acls(self, ec2: Any) -> list[AwsNetworkAcl]:
        acls = []
        for acl in ec2.describe_network_acls().get("NetworkAcls", []):
            associated_subnet_ids = [
                association.get("SubnetId", "")
                for association in acl.get("Associations", [])
                if association.get("SubnetId")
            ]
            acls.append(
                AwsNetworkAcl(
                    network_acl_id=acl.get("NetworkAclId", ""),
                    name=tag_name(acl.get("Tags")),
                    vpc_id=acl.get("VpcId", ""),
                    associated_subnet_ids=associated_subnet_ids,
                    is_default=acl.get("IsDefault"),
                )
            )
        return acls
