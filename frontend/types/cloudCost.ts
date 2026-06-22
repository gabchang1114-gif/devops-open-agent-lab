export interface CloudCostAccount {
  account_id: string;
  account_name?: string | null;
}

export interface CloudCostRegionsResponse {
  regions: string[];
}

export interface CloudCostAnalyzeRequest {
  account_id: string;
  region: string;
  include_ai?: boolean;
}

export interface CloudCostAnalyzeInventoryRequest {
  account: CloudCostAccount;
  region: string;
  resources: CloudCostResourceInventory;
  include_ai?: boolean;
  collected_at?: string;
  notes?: string[];
}

export interface CloudCostSavingsEstimate {
  amount: number;
  currency: string;
  confidence: string;
  note?: string;
}

export interface CloudCostAnalysisFinding {
  title: string;
  severity: string;
  status: string;
  resource_type: string;
  resource_id: string;
  reason: string;
  estimated_savings: CloudCostSavingsEstimate;
  recommendation: string;
  validation_steps: string[];
  aws_cli_commands: string[];
  safe_to_delete: boolean;
}

export interface CloudCostAnalysis {
  summary: string;
  overall_risk: string;
  estimated_monthly_savings: CloudCostSavingsEstimate;
  findings: CloudCostAnalysisFinding[];
  data_gaps: string[];
  next_steps: string[];
  llm_provider?: string | null;
  llm_error?: string | null;
}

export interface CloudCostAnalyzeInventoryResponse {
  status: string;
  analysis?: CloudCostAnalysis | null;
}

export interface CloudCostSecurityGroupRule {
  protocol?: string | null;
  from_port?: number | null;
  to_port?: number | null;
  cidr_blocks: string[];
  source_security_group_id?: string | null;
  description?: string | null;
}

export interface CloudCostEc2Instance {
  instance_id: string;
  name?: string | null;
  instance_type?: string | null;
  state?: string | null;
  private_ip?: string | null;
  public_ip?: string | null;
  launch_time?: string | null;
  tags: Record<string, string>;
}

export interface CloudCostEbsVolume {
  volume_id: string;
  size_gb?: number | null;
  volume_type?: string | null;
  state?: string | null;
  attached_instance_id?: string | null;
}

export interface CloudCostElasticIp {
  allocation_id: string;
  public_ip?: string | null;
  associated_instance_id?: string | null;
}

export interface CloudCostVpc {
  vpc_id: string;
  cidr_block?: string | null;
  tags: Record<string, string>;
}

export interface CloudCostSubnet {
  subnet_id: string;
  cidr_block?: string | null;
  availability_zone?: string | null;
  vpc_id?: string | null;
}

export interface CloudCostSecurityGroup {
  security_group_id: string;
  name?: string | null;
  ingress_rules: CloudCostSecurityGroupRule[];
  egress_rules: CloudCostSecurityGroupRule[];
}

export interface CloudCostLoadBalancer {
  name?: string | null;
  type?: string | null;
  scheme?: string | null;
  state?: string | null;
  load_balancer_arn?: string | null;
}

export interface CloudCostAutoScalingGroup {
  auto_scaling_group_name: string;
  desired_capacity?: number | null;
  current_capacity?: number | null;
  instance_ids: string[];
}

export interface CloudCostResourceInventory {
  ec2: CloudCostEc2Instance[];
  ebs: CloudCostEbsVolume[];
  elastic_ips: CloudCostElasticIp[];
  vpcs: CloudCostVpc[];
  subnets: CloudCostSubnet[];
  security_groups: CloudCostSecurityGroup[];
  load_balancers: CloudCostLoadBalancer[];
  auto_scaling_groups: CloudCostAutoScalingGroup[];
}

export interface CloudCostResourceSummary {
  ec2_count: number;
  ebs_count: number;
  elastic_ip_count: number;
  vpc_count: number;
  subnet_count: number;
  security_group_count: number;
  load_balancer_count: number;
  auto_scaling_group_count: number;
}

export interface CloudCostFinding {
  finding_id: string;
  category: string;
  resource_type: string;
  resource_id: string;
  resource_name?: string | null;
  severity: string;
  reason: string;
  estimated_impact?: string | null;
  monthly_savings_usd?: number | null;
}

export interface CloudCostResourceSavingsEstimate {
  resource_id: string;
  resource_type: string;
  monthly_savings_usd: number;
  confidence: string;
  calculation_method: string;
  note: string;
}

export interface CloudCostRegionalSpend {
  period_start: string;
  period_end: string;
  total_usd: number;
  by_service: Record<string, number>;
  available: boolean;
  note?: string | null;
}

export interface CloudCostSavingsSummary {
  total_monthly_savings_usd: number;
  currency: string;
  confidence: string;
  resource_estimates: CloudCostResourceSavingsEstimate[];
  regional_spend?: CloudCostRegionalSpend | null;
  note: string;
}

export interface CloudCostFindingsSummary {
  total_findings: number;
  unused_count: number;
  underutilized_count: number;
  findings: CloudCostFinding[];
  by_resource_type: Record<string, number>;
}

export interface CloudCostInvestigationResponse {
  status: string;
  account_id: string;
  account_name?: string | null;
  region: string;
  collected_at: string;
  resources: CloudCostResourceInventory;
  summary: CloudCostResourceSummary;
  findings: CloudCostFindingsSummary;
  analysis?: CloudCostAnalysis | null;
  cost_savings?: CloudCostSavingsSummary | null;
  diagnosis?: import("@/types/investigation").DiagnosisResult | null;
  notes: string[];
  error?: string | null;
}

export interface CloudCostAnalyzeResponse {
  status: string;
  account: CloudCostAccount;
  region: string;
  collected_at: string;
  resources: CloudCostResourceInventory;
  summary: CloudCostResourceSummary;
  notes: string[];
  analysis?: CloudCostAnalysis | null;
  cost_savings?: CloudCostSavingsSummary | null;
}
