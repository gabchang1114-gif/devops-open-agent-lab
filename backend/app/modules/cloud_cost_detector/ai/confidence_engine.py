"""Evidence-based confidence scoring for Cloud Cost analysis."""

from __future__ import annotations

import re

from app.models.diagnosis import DiagnosisResult
from app.modules.cloud_cost_detector.ai.analysis_adapter import analysis_to_diagnosis
from app.modules.cloud_cost_detector.models.schemas import CloudCostAnalysis

RESOURCE_ID_PATTERN = re.compile(
    r"\b("
    r"i-[0-9a-f]{8,17}|"
    r"vol-[0-9a-f]{8,17}|"
    r"eipalloc-[0-9a-f]{8,17}|"
    r"arn:aws:elasticloadbalancing:[^ \n\"']+"
    r")\b",
    re.IGNORECASE,
)

SEVERITY_WEIGHTS = {
    "high": 28,
    "medium": 18,
    "low": 10,
}

SCORE_TO_CONFIDENCE = (
    (85, "high"),
    (65, "medium"),
    (0, "low"),
)


class CloudCostConfidenceEngine:
    """Compute trustworthy confidence from rule-based findings and cited evidence."""

    def apply(self, diagnosis: DiagnosisResult, evidence_context: dict) -> DiagnosisResult:
        """Backward-compatible path for shared DiagnosisResult consumers."""
        score, reason, data_gaps = self._compute_score(evidence_context, diagnosis_text=self._diagnosis_text(diagnosis))
        diagnosis.confidence_score = score
        diagnosis.confidence_reason = reason
        if data_gaps:
            diagnosis.needs_more_data = True
            diagnosis.additional_data_needed = list(dict.fromkeys([*diagnosis.additional_data_needed, *data_gaps]))
        return diagnosis

    def apply_to_analysis(self, analysis: CloudCostAnalysis, evidence_context: dict) -> CloudCostAnalysis:
        """Apply evidence-based confidence to the CloudCostAnalysis schema."""
        score, reason, data_gaps = self._compute_score(
            evidence_context,
            diagnosis_text=self._analysis_text(analysis),
        )
        analysis.estimated_monthly_savings.confidence = self._score_to_confidence_label(score)
        analysis.estimated_monthly_savings.note = reason
        if data_gaps:
            analysis.data_gaps = list(dict.fromkeys([*analysis.data_gaps, *data_gaps]))
        return analysis

    def apply_via_diagnosis(self, analysis: CloudCostAnalysis, evidence_context: dict) -> DiagnosisResult:
        """Bridge for investigation history that stores DiagnosisResult."""
        adjusted = self.apply_to_analysis(analysis, evidence_context)
        diagnosis = analysis_to_diagnosis(adjusted)
        diagnosis.confidence_score = self._confidence_label_to_score(adjusted.estimated_monthly_savings.confidence)
        diagnosis.confidence_reason = adjusted.estimated_monthly_savings.note
        return diagnosis

    def _compute_score(self, evidence_context: dict, diagnosis_text: str) -> tuple[int, str, list[str]]:
        findings = evidence_context.get("unused_findings") or []
        summary = evidence_context.get("findings_summary") or {}
        total_findings = int(summary.get("total_findings") or 0)
        known_ids = self._collect_known_resource_ids(evidence_context)
        cited_ids = self._cited_resource_ids(diagnosis_text, known_ids)
        unknown_ids = self._unknown_resource_ids(diagnosis_text, known_ids)

        score = self._score_from_findings(findings, total_findings)
        reason = self._build_reason(findings, summary, cited_ids)
        data_gaps: list[str] = []

        if total_findings == 0:
            score = 58
            reason = (
                "No unused or underutilized resources were detected by current heuristics. "
                "Confidence is moderate because this scan does not include Cost Explorer, "
                "CloudWatch utilization, or Trusted Advisor data."
            )
            data_gaps = [
                "Cost Explorer spend breakdown",
                "CloudWatch CPU/network utilization",
                "Trusted Advisor cost optimization checks",
            ]
        elif cited_ids:
            score = min(95, score + 5)
            reason = (
                f"{reason} Confidence increased because the analysis cites "
                f"{len(cited_ids)} discovered resource(s)."
            )

        if unknown_ids:
            score = min(score, 45)
            reason = (
                "Adjusted down because the analysis references resource IDs that were not "
                f"discovered in this scan: {', '.join(sorted(unknown_ids))}."
            )
            data_gaps.append("Verify region and account selection for referenced resources")

        savings_note = self._savings_note(evidence_context)
        return max(0, min(100, score)), reason + savings_note, data_gaps

    def _savings_note(self, evidence_context: dict) -> str:
        cost_savings = evidence_context.get("cost_savings") or {}
        total = float(cost_savings.get("total_monthly_savings_usd") or 0)
        if total > 0:
            confidence = cost_savings.get("confidence", "medium")
            return (
                f" Estimated monthly savings: ${total:,.2f} ({confidence} confidence) "
                "from AWS list pricing and Cost Explorer context."
            )
        return " Exact dollar savings were not available in this scan."

    def _score_from_findings(self, findings: list[dict], total_findings: int) -> int:
        if total_findings == 0:
            return 58

        score = 48
        for finding in findings:
            severity = str(finding.get("severity") or "low").lower()
            score += SEVERITY_WEIGHTS.get(severity, 10)

        high_count = sum(1 for item in findings if str(item.get("severity")).lower() == "high")
        if high_count >= 1 and total_findings >= 2:
            score += 6

        return min(92, score)

    def _build_reason(self, findings: list[dict], summary: dict, cited_ids: set[str]) -> str:
        total = int(summary.get("total_findings") or 0)
        unused = int(summary.get("unused_count") or 0)
        underutilized = int(summary.get("underutilized_count") or 0)
        high_count = sum(1 for item in findings if str(item.get("severity")).lower() == "high")

        parts = [
            f"Based on {total} rule-based finding(s) "
            f"({unused} unused, {underutilized} underutilized)"
        ]
        if high_count:
            parts.append(f"including {high_count} high-severity item(s)")
        parts.append("from live AWS discovery in the selected region.")
        if cited_ids:
            parts.append(f"The analysis references {len(cited_ids)} discovered resource ID(s).")
        return " ".join(parts)

    def _score_to_confidence_label(self, score: int) -> str:
        for threshold, label in SCORE_TO_CONFIDENCE:
            if score >= threshold:
                return label
        return "low"

    def _confidence_label_to_score(self, label: str) -> int:
        mapping = {"high": 88, "medium": 70, "low": 45}
        return mapping.get((label or "low").lower(), 58)

    def _collect_known_resource_ids(self, context: dict) -> set[str]:
        known: set[str] = set()

        for finding in context.get("unused_findings") or []:
            resource_id = finding.get("resource_id")
            if resource_id:
                known.add(str(resource_id))

        for instance in context.get("ec2_sample") or []:
            if instance.get("instance_id"):
                known.add(str(instance["instance_id"]))

        for volume in context.get("ebs_sample") or []:
            if volume.get("volume_id"):
                known.add(str(volume["volume_id"]))

        for eip in context.get("elastic_ips") or []:
            if eip.get("allocation_id"):
                known.add(str(eip["allocation_id"]))

        for load_balancer in context.get("load_balancers") or []:
            for key in ("load_balancer_arn", "name"):
                value = load_balancer.get(key)
                if value:
                    known.add(str(value))

        for group in context.get("auto_scaling_groups") or []:
            name = group.get("auto_scaling_group_name")
            if name:
                known.add(str(name))

        return known

    def _analysis_text(self, analysis: CloudCostAnalysis) -> str:
        parts = [analysis.summary, analysis.estimated_monthly_savings.note]
        for finding in analysis.findings:
            parts.extend(
                [
                    finding.title,
                    finding.reason,
                    finding.recommendation,
                    " ".join(finding.aws_cli_commands),
                ]
            )
        return " ".join(part for part in parts if part)

    def _diagnosis_text(self, diagnosis: DiagnosisResult) -> str:
        parts = [
            diagnosis.root_cause,
            diagnosis.summary,
            diagnosis.suggested_fix,
            diagnosis.confidence_reason,
            " ".join(diagnosis.kubectl_commands),
        ]
        parts.extend(item.detail for item in diagnosis.evidence)
        return " ".join(parts)

    def _cited_resource_ids(self, text: str, known_ids: set[str]) -> set[str]:
        if not known_ids:
            return set()
        mentioned = set(RESOURCE_ID_PATTERN.findall(text))
        return {item for item in mentioned if item in known_ids or any(item in known for known in known_ids)}

    def _unknown_resource_ids(self, text: str, known_ids: set[str]) -> set[str]:
        mentioned = set(RESOURCE_ID_PATTERN.findall(text))
        if not mentioned:
            return set()

        unknown: set[str] = set()
        for item in mentioned:
            if item in known_ids:
                continue
            if any(item in known for known in known_ids):
                continue
            unknown.add(item)
        return unknown
