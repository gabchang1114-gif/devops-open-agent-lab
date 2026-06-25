"""Assess whether collected evidence matches the investigation scope."""

from __future__ import annotations

import re
from typing import Any

INSTANCE_ID_PATTERN = re.compile(r"\bi-[0-9a-f]{8,17}\b", re.IGNORECASE)
SECURITY_GROUP_ID_PATTERN = re.compile(r"\bsg-[0-9a-f]{8,17}\b", re.IGNORECASE)
TAG_KEY_PATTERN = re.compile(
    r'\btag(?:s)?\s+(?:named?\s+|key\s+)?["\']?([A-Za-z0-9_.:/=+\-@]+)["\']?'
    r'|["\']?([A-Za-z0-9_.:/=+\-@]+)["\']?\s+tag\b',
    re.IGNORECASE,
)


def extract_referenced_tag_keys(
    text: str | None,
    known_tag_keys: list[str] | None = None,
) -> list[str]:
    if not text:
        return []
    keys: set[str] = set()
    for match in TAG_KEY_PATTERN.finditer(text):
        keys.update(group for group in match.groups() if group)
    for key in known_tag_keys or []:
        if re.search(rf"\b{re.escape(key)}\b", text, re.IGNORECASE):
            keys.add(key)
    return sorted(keys)


def extract_referenced_resource_ids(text: str | None) -> dict[str, list[str]]:
    if not text:
        return {"instance_ids": [], "security_group_ids": []}
    return {
        "instance_ids": sorted(set(INSTANCE_ID_PATTERN.findall(text))),
        "security_group_ids": sorted(set(SECURITY_GROUP_ID_PATTERN.findall(text))),
    }


def build_discovery_assessment(
    investigation_ctx: dict[str, Any],
    ec2_instances: list[dict[str, Any]],
    security_groups: list[dict[str, Any]],
    troubleshooting_focus: dict[str, Any],
    cloudtrail_findings: dict[str, Any],
) -> dict[str, Any]:
    region = investigation_ctx.get("region")
    resource_counts = investigation_ctx.get("resource_counts") or {}
    lookback_hours = cloudtrail_findings.get("lookback_hours")

    discovered_instance_ids = {
        str(instance.get("instance_id"))
        for instance in ec2_instances
        if instance.get("instance_id")
    }
    discovered_security_group_ids = {
        str(group.get("security_group_id"))
        for group in security_groups
        if group.get("security_group_id")
    }

    referenced = extract_referenced_resource_ids(troubleshooting_focus.get("query"))
    missing_instances = [
        instance_id
        for instance_id in referenced["instance_ids"]
        if instance_id not in discovered_instance_ids
    ]
    missing_security_groups = [
        group_id
        for group_id in referenced["security_group_ids"]
        if group_id not in discovered_security_group_ids
    ]

    referenced_tag_keys = extract_referenced_tag_keys(
        troubleshooting_focus.get("query"),
        sorted({str(key) for instance in ec2_instances for key in (instance.get("tags") or {})}),
    )
    instances_by_tag_key: dict[str, list[dict[str, str]]] = {}
    for instance in ec2_instances:
        instance_id = str(instance.get("instance_id") or "")
        tags = instance.get("tags") or {}
        for key, value in tags.items():
            instances_by_tag_key.setdefault(str(key), []).append(
                {"instance_id": instance_id, "value": str(value)}
            )

    missing_tag_keys = [
        key
        for key in referenced_tag_keys
        if key not in instances_by_tag_key
    ]

    warnings: list[str] = []
    if len(ec2_instances) == 0:
        warnings.append(
            f"No EC2 instances were discovered in region {region}. "
            "Do not diagnose a specific instance state unless it appears in ec2_findings.instances."
        )
    if missing_instances:
        warnings.append(
            "User query references instance(s) "
            f"{', '.join(missing_instances)} that were not discovered in region {region}. "
            "Confirm the correct region or whether the resource exists in this account."
        )
    if missing_security_groups:
        warnings.append(
            "User query references security group(s) "
            f"{', '.join(missing_security_groups)} that were not discovered in region {region}."
        )
    if referenced_tag_keys:
        found = [
            f"{key} on {', '.join(item['instance_id'] for item in instances_by_tag_key.get(key, []))}"
            for key in referenced_tag_keys
            if key in instances_by_tag_key
        ]
        if found:
            warnings.append(f"Discovered tag(s) from query: {'; '.join(found)}.")
        if missing_tag_keys:
            warnings.append(
                "User query references tag key(s) "
                f"{', '.join(missing_tag_keys)} not found on any discovered EC2 instance in {region}."
            )
    if lookback_hours:
        warnings.append(
            f"CloudTrail and CloudWatch evidence are limited to the last {lookback_hours} hour(s). "
            "Older changes will not appear."
        )

    has_actionable_findings = bool(
        resource_counts.get("ec2_instances")
        or resource_counts.get("lambda_functions")
        or resource_counts.get("s3_buckets")
        or resource_counts.get("security_groups")
        or resource_counts.get("load_balancers")
        or resource_counts.get("topology_relationships")
    )

    return {
        "region": region,
        "resource_counts": resource_counts,
        "discovered_instance_ids": sorted(discovered_instance_ids),
        "discovered_security_group_ids": sorted(discovered_security_group_ids),
        "discovered_tags_by_key": {
            key: values for key, values in sorted(instances_by_tag_key.items())
        },
        "referenced_tag_keys": referenced_tag_keys,
        "referenced_but_not_discovered": {
            "instance_ids": missing_instances,
            "security_group_ids": missing_security_groups,
        },
        "warnings": warnings,
        "has_discovered_resources": has_actionable_findings,
        "analysis_constraint": (
            "Only analyze resources listed in discovery evidence for the selected region. "
            "If discovery is empty or a referenced resource is missing, say so explicitly and "
            "recommend selecting the correct region or widening the evidence window."
        ),
    }
