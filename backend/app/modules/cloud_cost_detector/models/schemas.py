"""Pydantic schemas for Cloud Cost Detector.

Designed for future extension with cost analysis, recommendations, and rightsizing.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models.diagnosis import DiagnosisResult


class CloudCostAccountResponse(BaseModel):
    account_id: str
    account_name: str | None = None


class CloudCostRegionsResponse(BaseModel):
    regions: list[str] = Field(default_factory=list)


class CloudCostAnalyzeRequest(BaseModel):
    account_id: str
    region: str
    include_ai: bool = True


class CloudCostAnalyzeInventoryRequest(BaseModel):
    account: CloudCostAccountResponse
    region: str
    resources: CloudCostResourceInventory
    include_ai: bool = True
    collected_at: str | None = None
    notes: list[str] = Field(default_factory=list)


class CloudCostSavingsEstimate(BaseModel):
    amount: float = 0
    currency: str = "USD"
    confidence: str = "low"
    note: str = ""


class CloudCostResourceSavingsEstimate(BaseModel):
    resource_id: str
    resource_type: str
    monthly_savings_usd: float = 0
    confidence: str = "low"
    calculation_method: str = "aws_list_price"
    note: str = ""


class CloudCostRegionalSpend(BaseModel):
    period_start: str
    period_end: str
    total_usd: float = 0
    by_service: dict[str, float] = Field(default_factory=dict)
    available: bool = False
    note: str | None = None


class CloudCostSavingsSummary(BaseModel):
    total_monthly_savings_usd: float = 0
    currency: str = "USD"
    confidence: str = "low"
    resource_estimates: list[CloudCostResourceSavingsEstimate] = Field(default_factory=list)
    regional_spend: CloudCostRegionalSpend | None = None
    note: str = ""


class CloudCostAnalysisFinding(BaseModel):
    title: str
    severity: str
    status: str
    resource_type: str
    resource_id: str
    reason: str
    estimated_savings: CloudCostSavingsEstimate = Field(default_factory=CloudCostSavingsEstimate)
    recommendation: str
    validation_steps: list[str] = Field(default_factory=list)
    aws_cli_commands: list[str] = Field(default_factory=list)
    safe_to_delete: bool = False


class CloudCostAnalysis(BaseModel):
    summary: str
    overall_risk: str = "low"
    estimated_monthly_savings: CloudCostSavingsEstimate = Field(default_factory=CloudCostSavingsEstimate)
    findings: list[CloudCostAnalysisFinding] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    llm_provider: str | None = None
    llm_error: str | None = None


class CloudCostSecurityGroupRule(BaseModel):
    protocol: str | None = None
    from_port: int | None = None
    to_port: int | None = None
    cidr_blocks: list[str] = Field(default_factory=list)
    source_security_group_id: str | None = None
    description: str | None = None


class CloudCostEc2Instance(BaseModel):
    instance_id: str
    name: str | None = None
    instance_type: str | None = None
    state: str | None = None
    private_ip: str | None = None
    public_ip: str | None = None
    launch_time: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    # Future: monthly_cost, utilization_score, rightsizing_recommendation


class CloudCostEbsVolume(BaseModel):
    volume_id: str
    size_gb: int | None = None
    volume_type: str | None = None
    state: str | None = None
    attached_instance_id: str | None = None
    # Future: monthly_cost, unused_flag


class CloudCostElasticIp(BaseModel):
    allocation_id: str
    public_ip: str | None = None
    associated_instance_id: str | None = None
    # Future: idle_cost_estimate


class CloudCostVpc(BaseModel):
    vpc_id: str
    cidr_block: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class CloudCostSubnet(BaseModel):
    subnet_id: str
    cidr_block: str | None = None
    availability_zone: str | None = None
    vpc_id: str | None = None


class CloudCostSecurityGroup(BaseModel):
    security_group_id: str
    name: str | None = None
    ingress_rules: list[CloudCostSecurityGroupRule] = Field(default_factory=list)
    egress_rules: list[CloudCostSecurityGroupRule] = Field(default_factory=list)


class CloudCostLoadBalancer(BaseModel):
    name: str | None = None
    type: str | None = None
    scheme: str | None = None
    state: str | None = None
    load_balancer_arn: str | None = None
    # Future: monthly_cost, unused_targets


class CloudCostAutoScalingGroup(BaseModel):
    auto_scaling_group_name: str
    desired_capacity: int | None = None
    current_capacity: int | None = None
    instance_ids: list[str] = Field(default_factory=list)


class CloudCostResourceInventory(BaseModel):
    """Resource inventory for a single region. Extensible for cost metadata."""

    ec2: list[CloudCostEc2Instance] = Field(default_factory=list)
    ebs: list[CloudCostEbsVolume] = Field(default_factory=list)
    elastic_ips: list[CloudCostElasticIp] = Field(default_factory=list)
    vpcs: list[CloudCostVpc] = Field(default_factory=list)
    subnets: list[CloudCostSubnet] = Field(default_factory=list)
    security_groups: list[CloudCostSecurityGroup] = Field(default_factory=list)
    load_balancers: list[CloudCostLoadBalancer] = Field(default_factory=list)
    auto_scaling_groups: list[CloudCostAutoScalingGroup] = Field(default_factory=list)
  # Future slots: rds, nat_gateways, snapshots, cost_explorer_summary


class CloudCostResourceSummary(BaseModel):
    ec2_count: int = 0
    ebs_count: int = 0
    elastic_ip_count: int = 0
    vpc_count: int = 0
    subnet_count: int = 0
    security_group_count: int = 0
    load_balancer_count: int = 0
    auto_scaling_group_count: int = 0

    @classmethod
    def from_inventory(cls, inventory: CloudCostResourceInventory) -> CloudCostResourceSummary:
        return cls(
            ec2_count=len(inventory.ec2),
            ebs_count=len(inventory.ebs),
            elastic_ip_count=len(inventory.elastic_ips),
            vpc_count=len(inventory.vpcs),
            subnet_count=len(inventory.subnets),
            security_group_count=len(inventory.security_groups),
            load_balancer_count=len(inventory.load_balancers),
            auto_scaling_group_count=len(inventory.auto_scaling_groups),
        )


class CloudCostAnalyzeResponse(BaseModel):
    status: str = "success"
    account: CloudCostAccountResponse
    region: str
    collected_at: str
    resources: CloudCostResourceInventory
    summary: CloudCostResourceSummary
    notes: list[str] = Field(default_factory=list)
    analysis: CloudCostAnalysis | None = None
    cost_savings: CloudCostSavingsSummary | None = None


class CloudCostAnalyzeInventoryResponse(BaseModel):
    status: str = "success"
    analysis: CloudCostAnalysis | None = None


class CloudCostFinding(BaseModel):
    finding_id: str
    category: str
    resource_type: str
    resource_id: str
    resource_name: str | None = None
    severity: str
    reason: str
    estimated_impact: str | None = None
    monthly_savings_usd: float | None = None


class CloudCostFindingsSummary(BaseModel):
    total_findings: int = 0
    unused_count: int = 0
    underutilized_count: int = 0
    findings: list[CloudCostFinding] = Field(default_factory=list)
    by_resource_type: dict[str, int] = Field(default_factory=dict)


class CloudCostInvestigationResponse(BaseModel):
    status: str = "success"
    account_id: str
    account_name: str | None = None
    region: str
    collected_at: str
    resources: CloudCostResourceInventory
    summary: CloudCostResourceSummary
    findings: CloudCostFindingsSummary = Field(default_factory=CloudCostFindingsSummary)
    analysis: CloudCostAnalysis | None = None
    diagnosis: DiagnosisResult | None = None
    cost_savings: CloudCostSavingsSummary | None = None
    notes: list[str] = Field(default_factory=list)
    error: str | None = None


class CloudCostAnalyzeError(BaseModel):
    status: str = "error"
    detail: str
    metadata: dict[str, Any] = Field(default_factory=dict)
