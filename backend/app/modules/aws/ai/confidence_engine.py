"""Evidence-based confidence scoring for AWS diagnoses."""

from __future__ import annotations

import re

from app.models.diagnosis import DiagnosisResult
from app.modules.aws.ai.discovery_assessment import INSTANCE_ID_PATTERN

VALID_SOURCES = {
    "ec2",
    "vpc",
    "security_groups",
    "load_balancers",
    "cloudwatch",
    "cloudtrail",
    "config",
    "topology",
    "auto_scaling",
}


class AwsConfidenceEngine:
    """Validate and adjust AI confidence scores based on AWS evidence."""

    def apply(self, diagnosis: DiagnosisResult, evidence_context: dict) -> DiagnosisResult:
        score = max(0, min(100, diagnosis.confidence_score))
        evidence_sources = {
            item.source for item in diagnosis.evidence if item.source in VALID_SOURCES
        }
        available_signals = self._count_available_signals(evidence_context)
        discovery = evidence_context.get("discovery_assessment", {})
        ec2_findings = evidence_context.get("ec2_findings", {})
        discovered_instance_ids = set(discovery.get("discovered_instance_ids") or [])

        if score >= 90 and len(evidence_sources) < 2 and available_signals >= 2:
            score = 79
            diagnosis.confidence_reason = (
                f"{diagnosis.confidence_reason} Adjusted down because fewer than two "
                "evidence sources were cited despite multiple investigation signals."
            )
        elif score >= 70 and len(evidence_sources) == 0:
            score = 35
            diagnosis.confidence_reason = (
                "Insufficient cited evidence despite investigation data being available."
            )
            diagnosis.needs_more_data = True
        elif score <= 39 and available_signals >= 2 and len(evidence_sources) >= 2:
            score = 55
            diagnosis.confidence_reason = (
                f"{diagnosis.confidence_reason} Adjusted up slightly because multiple "
                "investigation signals and cited evidence are present."
            )

        if ec2_findings.get("status") == "no_instances_discovered" and score > 45:
            score = min(score, 45)
            diagnosis.confidence_reason = (
                "Adjusted down because no EC2 instances were discovered in the selected region."
            )
            diagnosis.needs_more_data = True

        referenced_missing = discovery.get("referenced_but_not_discovered", {}).get("instance_ids") or []
        if referenced_missing and self._diagnosis_mentions_any(diagnosis, referenced_missing):
            score = min(score, 40)
            diagnosis.confidence_reason = (
                "Adjusted down because the diagnosis references instance IDs not discovered "
                f"in region {discovery.get('region')}: {', '.join(referenced_missing)}."
            )
            diagnosis.needs_more_data = True

        if self._mentions_undiscovered_instances(diagnosis, discovered_instance_ids):
            score = min(score, 35)
            diagnosis.confidence_reason = (
                "Adjusted down because the diagnosis mentions EC2 instances that were not "
                "discovered in the collected evidence."
            )
            diagnosis.needs_more_data = True

        finding_count = evidence_context.get("finding_summary", {}).get("total_findings", 0)
        if finding_count == 0 and score > 50:
            score = min(score, 50)
            diagnosis.confidence_reason = (
                "Adjusted down because no actionable findings were detected in the investigation scope."
            )

        diagnosis.confidence_score = score
        return diagnosis

    def _mentions_undiscovered_instances(
        self,
        diagnosis: DiagnosisResult,
        discovered_instance_ids: set[str],
    ) -> bool:
        if discovered_instance_ids:
            return False
        text = self._diagnosis_text(diagnosis)
        mentioned = set(INSTANCE_ID_PATTERN.findall(text))
        return bool(mentioned)

    def _diagnosis_mentions_any(self, diagnosis: DiagnosisResult, resource_ids: list[str]) -> bool:
        text = self._diagnosis_text(diagnosis)
        return any(resource_id in text for resource_id in resource_ids)

    def _diagnosis_text(self, diagnosis: DiagnosisResult) -> str:
        parts = [
            diagnosis.root_cause,
            diagnosis.summary,
            diagnosis.suggested_fix,
            " ".join(diagnosis.kubectl_commands),
        ]
        parts.extend(item.detail for item in diagnosis.evidence)
        return " ".join(parts)

    def _count_available_signals(self, context: dict) -> int:
        signals = 0
        ec2 = context.get("ec2_findings", {})
        network = context.get("network_findings", {})
        load_balancers = context.get("load_balancer_findings", {})
        asg = context.get("auto_scaling_findings", {})
        cloudwatch = context.get("cloudwatch_findings", {})
        cloudtrail = context.get("cloudtrail_findings", {})
        security_findings = context.get("security_findings", {})

        if ec2.get("problematic_instances"):
            signals += 1
        if security_findings.get("internet_exposed_ingress_rules") or network.get(
            "internet_exposed_ingress_rules"
        ):
            signals += 1
        if load_balancers.get("unhealthy_targets") or load_balancers.get("inactive_load_balancers"):
            signals += 1
        if asg.get("issues"):
            signals += 1
        if cloudwatch.get("alarms_in_alarm_state"):
            signals += 1
        if cloudtrail.get("error_events"):
            signals += 1
        if cloudtrail.get("security_group_change_events"):
            signals += 1
        if cloudtrail.get("instance_state_change_events") or cloudtrail.get("state_change_events"):
            signals += 1
        return signals
