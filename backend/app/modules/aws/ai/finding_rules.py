"""Shared rules for detecting AWS infrastructure findings."""

from __future__ import annotations

from typing import Any

INTERNET_CIDRS = {"0.0.0.0/0", "::/0"}

CRITICAL_PORTS = {22, 3389, 445, 1433, 5432, 3306, 6379, 9200, 27017, 5985, 5986}
HIGH_PORTS = {80, 443, 8080, 8443, 8000, 8888, 3000, 5000}
MEDIUM_PORTS = {21, 25, 53, 110, 143, 389, 636, 2049, 5601, 9090}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

SECURITY_EVENT_NAMES = {
    "AuthorizeSecurityGroupIngress",
    "RevokeSecurityGroupIngress",
    "AuthorizeSecurityGroupEgress",
    "RevokeSecurityGroupEgress",
    "ModifySecurityGroupRules",
    "CreateSecurityGroup",
    "DeleteSecurityGroup",
}


def is_internet_exposed(cidr_blocks: list[str]) -> bool:
    return any(cidr in INTERNET_CIDRS for cidr in cidr_blocks)


def classify_ingress_rule(rule: dict[str, Any]) -> dict[str, Any] | None:
    cidrs = rule.get("cidr_blocks") or []
    if not is_internet_exposed(cidrs):
        return None

    protocol = str(rule.get("protocol") or "").lower()
    from_port = rule.get("from_port")
    to_port = rule.get("to_port")

    if protocol in {"-1", "all"}:
        return {
            "severity": "critical",
            "risk": "internet-wide all traffic",
            "port_label": "ALL",
            "protocol": protocol,
        }

    if from_port is None and to_port is None:
        return {
            "severity": "critical",
            "risk": "internet-wide all ports",
            "port_label": "ALL",
            "protocol": protocol,
        }

    port_label = (
        str(from_port)
        if from_port == to_port
        else f"{from_port}-{to_port}"
    )

    ports_to_check: set[int] = set()
    if isinstance(from_port, int):
        ports_to_check.add(from_port)
    if isinstance(to_port, int):
        ports_to_check.add(to_port)
    if isinstance(from_port, int) and isinstance(to_port, int) and from_port <= to_port:
        ports_to_check.update({from_port, to_port})

    if ports_to_check.intersection(CRITICAL_PORTS):
        severity = "critical"
        risk = "internet-exposed sensitive/admin port"
    elif ports_to_check.intersection(HIGH_PORTS) or from_port == 80 or to_port == 80:
        severity = "high"
        risk = "internet-exposed web/application port"
    elif ports_to_check.intersection(MEDIUM_PORTS):
        severity = "medium"
        risk = "internet-exposed service port"
    else:
        severity = "medium"
        risk = "internet-wide ingress"

    return {
        "severity": severity,
        "risk": risk,
        "port_label": port_label,
        "protocol": protocol,
    }


def analyze_security_groups(
    security_groups: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    internet_exposed: list[dict[str, Any]] = []
    permissive_egress: list[dict[str, Any]] = []

    for group in security_groups:
        group_id = group.get("security_group_id")
        group_name = group.get("name")
        attached = group.get("attached_resource_ids") or []

        for rule in group.get("ingress_rules", []):
            classification = classify_ingress_rule(rule)
            if not classification:
                continue
            internet_exposed.append(
                {
                    "security_group_id": group_id,
                    "name": group_name,
                    "attached_instance_ids": attached,
                    "severity": classification["severity"],
                    "risk": classification["risk"],
                    "protocol": classification["protocol"],
                    "port": classification["port_label"],
                    "from_port": rule.get("from_port"),
                    "to_port": rule.get("to_port"),
                    "cidr_blocks": rule.get("cidr_blocks") or [],
                    "description": rule.get("description"),
                }
            )

        for rule in group.get("egress_rules", []):
            cidrs = rule.get("cidr_blocks") or []
            if not is_internet_exposed(cidrs):
                continue
            protocol = str(rule.get("protocol") or "").lower()
            if protocol in {"-1", "all"}:
                permissive_egress.append(
                    {
                        "security_group_id": group_id,
                        "name": group_name,
                        "risk": "allows all outbound traffic to the internet",
                        "protocol": protocol,
                        "port": "ALL",
                    }
                )

    internet_exposed.sort(
        key=lambda item: (
            SEVERITY_ORDER.get(str(item.get("severity")), 99),
            str(item.get("security_group_id")),
        )
    )
    return internet_exposed, permissive_egress
