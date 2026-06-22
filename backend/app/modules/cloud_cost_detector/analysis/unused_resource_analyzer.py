"""Rule-based detection of unused and underutilized AWS resources."""

from __future__ import annotations

import uuid

from app.modules.cloud_cost_detector.models.schemas import (
    CloudCostFinding,
    CloudCostFindingsSummary,
    CloudCostResourceInventory,
)


class UnusedResourceAnalyzer:
    """Identify cost optimization candidates from discovered inventory."""

    def analyze(self, inventory: CloudCostResourceInventory) -> CloudCostFindingsSummary:
        findings: list[CloudCostFinding] = []

        asg_instances = {
            instance_id
            for group in inventory.auto_scaling_groups
            for instance_id in group.instance_ids
        }
        associated_eips = {
            eip.associated_instance_id
            for eip in inventory.elastic_ips
            if eip.associated_instance_id
        }

        for instance in inventory.ec2:
            state = (instance.state or "").lower()
            if state == "stopped":
                findings.append(
                    CloudCostFinding(
                        finding_id=self._finding_id(),
                        category="unused",
                        resource_type="ec2",
                        resource_id=instance.instance_id,
                        resource_name=instance.name,
                        severity="medium",
                        reason="EC2 instance is stopped but still incurring EBS and Elastic IP charges.",
                        estimated_impact="Stopped instances avoid compute charges but attached storage and IPs may still bill.",
                    )
                )
            elif state == "running" and instance.instance_id not in asg_instances:
                if not instance.public_ip and instance.instance_id not in associated_eips:
                    findings.append(
                        CloudCostFinding(
                            finding_id=self._finding_id(),
                            category="underutilized",
                            resource_type="ec2",
                            resource_id=instance.instance_id,
                            resource_name=instance.name,
                            severity="low",
                            reason="Running standalone EC2 instance is not part of an Auto Scaling group.",
                            estimated_impact="Review utilization metrics and consider rightsizing or scheduling.",
                        )
                    )

        for volume in inventory.ebs:
            state = (volume.state or "").lower()
            if state == "available" or not volume.attached_instance_id:
                findings.append(
                    CloudCostFinding(
                        finding_id=self._finding_id(),
                        category="unused",
                        resource_type="ebs",
                        resource_id=volume.volume_id,
                        severity="high",
                        reason="EBS volume is unattached and still billing for provisioned storage.",
                        estimated_impact=f"{volume.size_gb or 0} GB of unattached storage.",
                    )
                )

        for eip in inventory.elastic_ips:
            if not eip.associated_instance_id:
                findings.append(
                    CloudCostFinding(
                        finding_id=self._finding_id(),
                        category="unused",
                        resource_type="elastic_ip",
                        resource_id=eip.allocation_id,
                        resource_name=eip.public_ip,
                        severity="medium",
                        reason="Elastic IP is allocated but not associated with a running instance.",
                        estimated_impact="Unassociated Elastic IPs incur hourly charges.",
                    )
                )

        for load_balancer in inventory.load_balancers:
            state = (load_balancer.state or "").lower()
            if state in {"inactive", "failed"}:
                findings.append(
                    CloudCostFinding(
                        finding_id=self._finding_id(),
                        category="unused",
                        resource_type="load_balancer",
                        resource_id=load_balancer.load_balancer_arn or load_balancer.name or "unknown",
                        resource_name=load_balancer.name,
                        severity="medium",
                        reason=f"Load balancer is in {state} state.",
                        estimated_impact="Inactive load balancers may still incur charges.",
                    )
                )

        for group in inventory.auto_scaling_groups:
            desired = group.desired_capacity or 0
            current = group.current_capacity or 0
            if desired == 0 and current == 0:
                findings.append(
                    CloudCostFinding(
                        finding_id=self._finding_id(),
                        category="underutilized",
                        resource_type="auto_scaling_group",
                        resource_id=group.auto_scaling_group_name,
                        resource_name=group.auto_scaling_group_name,
                        severity="low",
                        reason="Auto Scaling group has zero desired and zero running instances.",
                        estimated_impact="Group configuration remains active; review whether it is still needed.",
                    )
                )

        unused_count = sum(1 for item in findings if item.category == "unused")
        underutilized_count = sum(1 for item in findings if item.category == "underutilized")
        by_resource_type: dict[str, int] = {}
        for item in findings:
            by_resource_type[item.resource_type] = by_resource_type.get(item.resource_type, 0) + 1

        return CloudCostFindingsSummary(
            total_findings=len(findings),
            unused_count=unused_count,
            underutilized_count=underutilized_count,
            findings=findings,
            by_resource_type=by_resource_type,
        )

    @staticmethod
    def _finding_id() -> str:
        return str(uuid.uuid4())
