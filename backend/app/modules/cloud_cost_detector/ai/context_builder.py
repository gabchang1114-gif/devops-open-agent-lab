"""Build AI-ready context from Cloud Cost investigation evidence."""

from __future__ import annotations

from typing import Any

from app.modules.cloud_cost_detector.models.schemas import CloudCostInvestigationResponse


class CloudCostContextBuilder:
    """Transform cloud cost investigation payloads into compact LLM context."""

    MAX_FINDINGS = 40
    MAX_EC2 = 30
    MAX_EBS = 30

    def build(self, investigation: CloudCostInvestigationResponse | dict[str, Any]) -> dict[str, Any]:
        if isinstance(investigation, CloudCostInvestigationResponse):
            payload = investigation.model_dump(exclude={"diagnosis", "error"})
        else:
            payload = dict(investigation)
            payload.pop("diagnosis", None)
            payload.pop("error", None)

        resources = payload.get("resources", {})
        findings = payload.get("findings", {})
        summary = payload.get("summary", {})

        return {
            "account_id": payload.get("account_id"),
            "account_name": payload.get("account_name"),
            "region": payload.get("region"),
            "collected_at": payload.get("collected_at"),
            "resource_summary": summary,
            "unused_findings": (findings.get("findings") or [])[: self.MAX_FINDINGS],
            "findings_summary": {
                "total_findings": findings.get("total_findings", 0),
                "unused_count": findings.get("unused_count", 0),
                "underutilized_count": findings.get("underutilized_count", 0),
                "by_resource_type": findings.get("by_resource_type", {}),
            },
            "ec2_sample": (resources.get("ec2") or [])[: self.MAX_EC2],
            "ebs_sample": (resources.get("ebs") or [])[: self.MAX_EBS],
            "elastic_ips": resources.get("elastic_ips") or [],
            "load_balancers": resources.get("load_balancers") or [],
            "auto_scaling_groups": resources.get("auto_scaling_groups") or [],
            "cost_savings": payload.get("cost_savings") or {},
            "notes": payload.get("notes") or [],
        }
