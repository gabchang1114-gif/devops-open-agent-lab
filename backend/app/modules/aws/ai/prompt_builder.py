"""AWS troubleshooting prompt builder."""

import json
from typing import Any

BASE_SYSTEM_PROMPT = """You are a Senior AWS Cloud Engineer and SRE performing infrastructure troubleshooting.

Analyze the provided evidence and produce a precise root cause analysis with actionable recommendations.

CORE RULES:
- Use ONLY provided evidence — do not guess or invent values.
- Never use placeholder resource IDs, CIDRs, account IDs, regions, or usernames.
- Every AWS CLI command must use resource IDs, ports, protocols, and regions copied from the evidence JSON.
- Cite resource IDs, ports, principals, timestamps, and source IPs from evidence.
- Never reference EC2 instances or security groups unless they appear in discovery_assessment or ec2_findings.instances.
- If ec2_findings.status is no_instances_discovered, report that no instances exist in the selected region — do not claim an instance is stopped or healthy.
- If referenced_but_not_discovered lists resource IDs, tell the user to verify region/account selection.
- Confidence above 70 requires findings backed by discovered resources, not user query text alone.
- If finding_summary is empty and discovery found no issues, say no issues were found in scope — do not invent incidents.
- Put AWS CLI commands in kubectl_commands field for schema compatibility.
- Safe by default — flag destructive commands for human review.

SUGGESTED_FIX REQUIREMENTS:
- suggested_fix must be detailed, numbered, and grounded entirely in finding_summary and evidence sections.
- Address each finding category present in the evidence (do not assume EC2 or security issues exist unless evidence shows them).
- For each security group rule in evidence: include SG ID, port/protocol, CIDR, attribution if present, and exact remediation approach.
- For each stopped instance in evidence: include attribution if present, restart decision, and verification steps.
- Do not repeat boilerplate unrelated to the collected findings.
- kubectl_commands must mirror commands described in suggested_fix.
- validation_steps and prevention_recommendation must relate to findings actually detected in this investigation.

Evidence source values: ec2, vpc, security_groups, load_balancers, cloudwatch, cloudtrail, config, topology, auto_scaling

Respond with valid JSON only using this exact schema:
{
  "root_cause": "string",
  "summary": "string",
  "evidence": [{"source": "...", "detail": "string"}],
  "suggested_fix": "string",
  "kubectl_commands": ["string"],
  "validation_steps": ["string"],
  "prevention_recommendation": "string",
  "confidence_score": 0,
  "confidence_reason": "string",
  "needs_more_data": false,
  "additional_data_needed": []
}"""

ISSUE_TYPE_INSTRUCTIONS: dict[str, str] = {
    "full_scan": """TROUBLESHOOTING MODE: Full infrastructure scan.
- Review finding_summary and report ALL issues ranked by severity (critical → high → medium).
- Include security exposures, EC2 state issues, load balancer health, CloudWatch alarms, and recent changes.
- Do not ignore security group rules (including HTTP/80 and HTTPS/443 on 0.0.0.0/0).
- If multiple unrelated issues exist, summarize each clearly in root_cause.""",
    "security": """TROUBLESHOOTING MODE: Security & exposure.
- Focus on security_findings.internet_exposed_ingress_rules — every 0.0.0.0/0 and ::/0 rule MUST be reported.
- Include HTTP (80), HTTPS (443), SSH (22), and all-traffic rules.
- Correlate with cloudtrail_findings.attribution_by_security_group and security_group_change_events.
- AWS Console changes often appear as ModifySecurityGroupRules (not only AuthorizeSecurityGroupIngress) — use both.
- For each exposed rule, state WHO added it, WHEN, and source IP when CloudTrail provides attribution.
- Recommend least-privilege fixes with specific revoke/modify commands.""",
    "ec2_availability": """TROUBLESHOOTING MODE: EC2 availability.
- Focus on stopped/unhealthy instances and incident_attribution.
- Answer WHO stopped each instance, WHEN, and FROM WHERE using CloudTrail.
- Correlate CloudWatch instance_activity timeline.
- Still mention critical security issues if present, but EC2 availability is primary.""",
    "network": """TROUBLESHOOTING MODE: Network & connectivity.
- Focus on VPC topology, security group rules affecting connectivity, and internet exposure.
- Analyze whether traffic can reach instances (SG ingress/egress, subnets, route implications from topology).""",
    "load_balancer": """TROUBLESHOOTING MODE: Load balancers.
- Focus on unhealthy targets, inactive load balancers, and target group health reasons.
- Correlate with EC2 instance state if targets are instances.""",
    "performance": """TROUBLESHOOTING MODE: Performance & monitoring.
- Focus on CloudWatch alarms in ALARM state and instance metric activity.
- Identify metric anomalies, idle vs active instances, and threshold breaches.""",
    "change_audit": """TROUBLESHOOTING MODE: Change audit & attribution.
- Focus on CloudTrail events: who changed what, when, from which IP.
- Include tag changes (CreateTags/DeleteTags) with tag key/value from tag_change_events and ec2_findings.instances.tags.
- Include security group changes, instance state changes, and AWS Config recent_changes.
- Build a timeline of relevant API activity.""",
}


class AwsPromptBuilder:
    """Build LLM prompts from AWS investigation context."""

    def build_messages(self, context: dict[str, Any]) -> list[dict[str, str]]:
        issue_type = context.get("troubleshooting_focus", {}).get("issue_type", "full_scan")
        mode_instructions = ISSUE_TYPE_INSTRUCTIONS.get(
            issue_type,
            ISSUE_TYPE_INSTRUCTIONS["full_scan"],
        )
        system_prompt = f"{BASE_SYSTEM_PROMPT}\n\n{mode_instructions}"
        user_prompt = self._build_user_prompt(context)
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_user_prompt(self, context: dict[str, Any]) -> str:
        focus = context.get("troubleshooting_focus", {})
        sections = [
            "Analyze the AWS evidence below according to the troubleshooting mode in the system prompt.",
            "",
            "## Discovery Assessment (READ FIRST — defines what was actually found)",
            json.dumps(context.get("discovery_assessment", {}), indent=2),
            "",
            "## Troubleshooting Focus",
            json.dumps(focus, indent=2),
            "",
            "## Finding Summary (ALL detected issues — prioritize these)",
            json.dumps(context.get("finding_summary", {}), indent=2),
            "",
            "## Security Findings",
            json.dumps(context.get("security_findings", {}), indent=2),
            "",
            "## EC2 Findings",
            json.dumps(context.get("ec2_findings", {}), indent=2),
            "",
            "## Incident Attribution (EC2 stop/start)",
            json.dumps(context.get("incident_attribution", {}), indent=2),
            "",
            "## CloudTrail Findings",
            json.dumps(context.get("cloudtrail_findings", {}), indent=2),
            "",
            "## CloudWatch Findings",
            json.dumps(context.get("cloudwatch_findings", {}), indent=2),
            "",
            "## Network Findings",
            json.dumps(context.get("network_findings", {}), indent=2),
            "",
            "## Load Balancer Findings",
            json.dumps(context.get("load_balancer_findings", {}), indent=2),
            "",
            "## Auto Scaling Findings",
            json.dumps(context.get("auto_scaling_findings", {}), indent=2),
            "",
            "## AWS Config Findings",
            json.dumps(context.get("config_findings", {}), indent=2),
            "",
            "## Account & Resource Counts",
            json.dumps(
                {
                    "account": context.get("account", {}),
                    "resource_counts": context.get("resource_counts", {}),
                },
                indent=2,
            ),
            "",
        ]

        if focus.get("query"):
            sections.extend(
                [
                    "## User-Reported Problem",
                    focus["query"],
                    "",
                    "Address the user-reported problem directly while grounding answers in evidence.",
                    "",
                ]
            )

        sections.append(
            "Return JSON only. Base every recommendation on the evidence above — no placeholders or assumed resources."
        )
        return "\n".join(sections)
