import type { AwsIssueType } from "@/types/aws";

export interface AwsIssueTypeOption {
  value: AwsIssueType;
  label: string;
  description: string;
}

export const AWS_ISSUE_TYPES: AwsIssueTypeOption[] = [
  {
    value: "full_scan",
    label: "Full Scan",
    description: "Detect all issues — security, EC2, network, load balancers, alarms, and changes",
  },
  {
    value: "security",
    label: "Security & Exposure",
    description: "Open security groups, internet exposure, and who changed rules (CloudTrail)",
  },
  {
    value: "ec2_availability",
    label: "EC2 Availability",
    description: "Stopped instances, health checks, and who stopped them",
  },
  {
    value: "network",
    label: "Network & Connectivity",
    description: "VPC, subnets, routing, and connectivity-blocking rules",
  },
  {
    value: "load_balancer",
    label: "Load Balancers",
    description: "Unhealthy targets, inactive load balancers, routing issues",
  },
  {
    value: "performance",
    label: "Performance & Alarms",
    description: "CloudWatch alarms, metric anomalies, and capacity signals",
  },
  {
    value: "change_audit",
    label: "Change Audit",
    description: "Who changed what and when — CloudTrail and Config timeline",
  },
];

export function getAwsIssueTypeLabel(value: AwsIssueType): string {
  return AWS_ISSUE_TYPES.find((item) => item.value === value)?.label ?? value;
}
