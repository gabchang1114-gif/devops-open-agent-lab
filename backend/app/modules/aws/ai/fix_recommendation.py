"""Validate and enrich AWS fix recommendations using investigation evidence only."""

from __future__ import annotations

import re
from typing import Any

from app.models.diagnosis import DiagnosisResult
from app.modules.aws.ai.discovery_assessment import INSTANCE_ID_PATTERN

DANGEROUS_PATTERNS = [
    re.compile(r"aws\s+ec2\s+terminate-instances\b", re.IGNORECASE),
    re.compile(r"aws\s+cloudformation\s+delete-stack\b", re.IGNORECASE),
    re.compile(r"aws\s+s3\s+rb\b", re.IGNORECASE),
    re.compile(r"--force\b", re.IGNORECASE),
    re.compile(r"delete-bucket\b", re.IGNORECASE),
]


class AwsFixRecommendationEngine:
    """Sanitize commands and supplement the LLM output with evidence-derived actions."""

    SAFETY_NOTE = (
        "\n\nSafety: Review every command manually before execution. "
        "Destructive operations require explicit human approval."
    )

    def apply(self, diagnosis: DiagnosisResult, context: dict[str, Any] | None = None) -> DiagnosisResult:
        context = context or {}
        region = context.get("investigation", {}).get("region")

        evidence_commands = self._build_evidence_commands(context, region)
        evidence_validation = self._build_evidence_validation(context)
        evidence_notes = self._build_evidence_notes(context, diagnosis.suggested_fix or "")

        sanitized_commands: list[str] = []
        risky = False
        seen_commands: set[str] = set()

        for command in [*diagnosis.kubectl_commands, *evidence_commands]:
            command = command.strip()
            if not command or command in seen_commands:
                continue
            if self._references_undiscovered_instance(command, context):
                continue
            seen_commands.add(command)
            if any(pattern.search(command) for pattern in DANGEROUS_PATTERNS):
                risky = True
                sanitized_commands.append(f"# REVIEW CAREFULLY: {command}")
            else:
                sanitized_commands.append(command)

        diagnosis.kubectl_commands = sanitized_commands
        diagnosis.validation_steps = self._merge_validation_steps(
            diagnosis.validation_steps,
            evidence_validation,
        )

        if evidence_notes:
            llm_fix = (diagnosis.suggested_fix or "").strip()
            diagnosis.suggested_fix = f"{llm_fix}\n\n{evidence_notes}".strip() if llm_fix else evidence_notes

        scope_notes = self._build_scope_notes(context)
        if scope_notes and scope_notes not in (diagnosis.suggested_fix or ""):
            diagnosis.suggested_fix = f"{(diagnosis.suggested_fix or '').strip()}\n\n{scope_notes}".strip()

        if not diagnosis.prevention_recommendation.strip():
            diagnosis.prevention_recommendation = self._build_prevention_from_findings(context)

        if risky and self.SAFETY_NOTE.strip() not in diagnosis.suggested_fix:
            diagnosis.suggested_fix = f"{diagnosis.suggested_fix}{self.SAFETY_NOTE}"

        return diagnosis

    def _build_evidence_commands(self, context: dict[str, Any], region: str | None) -> list[str]:
        if not region:
            return []

        commands: list[str] = []
        region_flag = f"--region {region}"

        for incident in context.get("incident_attribution", {}).get("stopped_instance_incidents") or []:
            instance_id = incident.get("instance_id")
            if not instance_id:
                continue
            discovered_ids = set(context.get("discovery_assessment", {}).get("discovered_instance_ids") or [])
            if discovered_ids and instance_id not in discovered_ids:
                continue
            commands.append(f"aws ec2 start-instances --instance-ids {instance_id} {region_flag}")
            commands.append(
                f"aws ec2 describe-instance-status --instance-ids {instance_id} "
                f"--include-all-instances {region_flag}"
            )

        for rule in context.get("security_findings", {}).get("internet_exposed_ingress_rules") or []:
            group_id = rule.get("security_group_id")
            if not group_id:
                continue
            commands.extend(self._revoke_commands_for_rule(rule, group_id, region_flag))
            commands.append(f"aws ec2 describe-security-groups --group-ids {group_id} {region_flag}")

        for target in context.get("load_balancer_findings", {}).get("unhealthy_targets") or []:
            target_id = target.get("target_id")
            if target_id and str(target_id).startswith("i-"):
                commands.append(
                    f"aws ec2 describe-instance-status --instance-ids {target_id} "
                    f"--include-all-instances {region_flag}"
                )

        for alarm in context.get("cloudwatch_findings", {}).get("alarms_in_alarm_state") or []:
            alarm_name = alarm.get("alarm_name")
            if alarm_name:
                commands.append(f"aws cloudwatch describe-alarms --alarm-names {alarm_name} {region_flag}")

        return commands

    def _references_undiscovered_instance(self, command: str, context: dict[str, Any]) -> bool:
        discovery = context.get("discovery_assessment", {})
        missing = set(discovery.get("referenced_but_not_discovered", {}).get("instance_ids") or [])
        if not missing:
            return False
        mentioned = set(INSTANCE_ID_PATTERN.findall(command))
        return bool(mentioned & missing)

    def _build_scope_notes(self, context: dict[str, Any]) -> str:
        discovery = context.get("discovery_assessment", {})
        warnings = discovery.get("warnings") or []
        if not warnings:
            return ""
        lines = ["Scope notes (from discovery assessment):"]
        lines.extend(f"- {warning}" for warning in warnings)
        return "\n".join(lines)

    def _revoke_commands_for_rule(
        self,
        rule: dict[str, Any],
        group_id: str,
        region_flag: str,
    ) -> list[str]:
        protocol = rule.get("protocol")
        from_port = rule.get("from_port")
        to_port = rule.get("to_port")
        cidrs = [cidr for cidr in (rule.get("cidr_blocks") or []) if cidr]
        if not cidrs or not protocol or protocol in {"-1", "all"}:
            return []
        if from_port is None and to_port is None:
            return []

        from_port = from_port if from_port is not None else to_port
        to_port = to_port if to_port is not None else from_port

        commands: list[str] = []
        for cidr in cidrs:
            if cidr == "::/0":
                commands.append(
                    f"aws ec2 revoke-security-group-ingress --group-id {group_id} "
                    f"--ip-permissions IpProtocol={protocol},FromPort={from_port},ToPort={to_port},"
                    f"Ipv6Ranges=[{{CidrIpv6={cidr}}}] {region_flag}"
                )
            else:
                if from_port == to_port:
                    commands.append(
                        f"aws ec2 revoke-security-group-ingress --group-id {group_id} "
                        f"--protocol {protocol} --port {from_port} --cidr {cidr} {region_flag}"
                    )
                else:
                    commands.append(
                        f"aws ec2 revoke-security-group-ingress --group-id {group_id} "
                        f"--ip-permissions IpProtocol={protocol},FromPort={from_port},ToPort={to_port},"
                        f"IpRanges=[{{CidrIp={cidr}}}] {region_flag}"
                    )
        return commands

    def _build_evidence_validation(self, context: dict[str, Any]) -> list[str]:
        steps: list[str] = []

        for incident in context.get("incident_attribution", {}).get("stopped_instance_incidents") or []:
            instance_id = incident.get("instance_id")
            if instance_id:
                steps.append(
                    f"Confirm instance {instance_id} reaches running state with passing status checks."
                )

        for rule in context.get("security_findings", {}).get("internet_exposed_ingress_rules") or []:
            group_id = rule.get("security_group_id")
            port = rule.get("port")
            cidrs = ", ".join(rule.get("cidr_blocks") or [])
            if group_id and cidrs:
                steps.append(
                    f"Confirm security group {group_id} no longer exposes port {port} to {cidrs}."
                )

        for target in context.get("load_balancer_findings", {}).get("unhealthy_targets") or []:
            target_id = target.get("target_id")
            target_group = target.get("target_group")
            if target_id and target_group:
                steps.append(f"Confirm target {target_id} is healthy in target group {target_group}.")

        for alarm in context.get("cloudwatch_findings", {}).get("alarms_in_alarm_state") or []:
            alarm_name = alarm.get("alarm_name")
            if alarm_name:
                steps.append(f"Confirm CloudWatch alarm {alarm_name} returns to OK state.")

        return steps

    def _build_evidence_notes(self, context: dict[str, Any], existing_fix: str) -> str:
        """Add concise evidence-based actions only for findings not already mentioned."""
        lines: list[str] = []
        existing_lower = existing_fix.lower()

        for finding in context.get("finding_summary", {}).get("findings") or []:
            resource_id = str(finding.get("resource_id") or "")
            title = str(finding.get("title") or "")
            detail = str(finding.get("detail") or "")
            if resource_id and resource_id.lower() in existing_lower:
                continue
            if title.lower() in existing_lower:
                continue
            if not detail:
                continue
            lines.append(f"- [{finding.get('severity', 'info').upper()}] {title}: {detail}")

        if not lines:
            return ""

        return "Evidence-based actions (from collected findings):\n" + "\n".join(lines)

    def _build_prevention_from_findings(self, context: dict[str, Any]) -> str:
        notes: list[str] = []
        categories = context.get("finding_summary", {}).get("by_category") or {}

        if categories.get("security"):
            notes.append(
                "Monitor security group changes with AWS Config or Security Hub and alert on internet-wide ingress."
            )
        if categories.get("ec2") or context.get("incident_attribution", {}).get("stopped_instance_incidents"):
            notes.append(
                "Alert on StopInstances and unexpected instance state changes via CloudTrail or EventBridge."
            )
        if categories.get("load_balancer"):
            notes.append("Review target group health check settings and dependency security group paths.")
        if categories.get("performance"):
            notes.append("Tune CloudWatch alarm thresholds based on observed baseline metrics.")

        return " ".join(notes)

    def _merge_validation_steps(
        self,
        existing: list[str],
        generated: list[str],
    ) -> list[str]:
        merged: list[str] = []
        for step in [*existing, *generated]:
            step = step.strip()
            if step and step not in merged:
                merged.append(step)
        return merged[:12]
