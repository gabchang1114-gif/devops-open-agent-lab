"""Rule-based monthly savings estimates for unused AWS resources."""

from __future__ import annotations

from app.modules.cloud_cost_detector.analysis.pricing import (
    ALB_BASE_MONTH_USD,
    DEFAULT_EBS_GB_MONTH_USD,
    EBS_GB_MONTH_USD,
    NLB_BASE_MONTH_USD,
    UNASSOCIATED_EIP_MONTH_USD,
)
from app.modules.cloud_cost_detector.collectors.cost_explorer import CloudCostExplorerCollector
from app.modules.cloud_cost_detector.models.schemas import (
    CloudCostFindingsSummary,
    CloudCostLoadBalancer,
    CloudCostResourceInventory,
    CloudCostResourceSavingsEstimate,
    CloudCostSavingsSummary,
)


class CloudCostEstimator:
    """Estimate monthly savings for rule-based findings using list pricing + Cost Explorer."""

    def __init__(self, cost_explorer: CloudCostExplorerCollector | None = None) -> None:
        self.cost_explorer = cost_explorer or CloudCostExplorerCollector()

    async def estimate(
        self,
        inventory: CloudCostResourceInventory,
        findings: CloudCostFindingsSummary,
        region: str,
    ) -> CloudCostSavingsSummary:
        regional_spend = await self.cost_explorer.get_regional_spend(region)
        resource_estimates = self._estimate_from_findings(inventory, findings)
        total = round(sum(item.monthly_savings_usd for item in resource_estimates), 2)
        confidence = self._overall_confidence(resource_estimates, regional_spend.available)

        note_parts: list[str] = []
        if total > 0:
            note_parts.append(
                f"Estimated ${total:,.2f}/month recoverable from {len(resource_estimates)} "
                "unused or wasteful resource(s) using AWS list pricing."
            )
        else:
            note_parts.append("No quantified savings could be estimated for current findings.")

        if regional_spend.available:
            note_parts.append(
                f"Regional spend (last 30 days): ${regional_spend.total_usd:,.2f} via Cost Explorer."
            )
        elif regional_spend.note:
            note_parts.append(regional_spend.note)

        return CloudCostSavingsSummary(
            total_monthly_savings_usd=total,
            confidence=confidence,
            resource_estimates=resource_estimates,
            regional_spend=regional_spend,
            note=" ".join(note_parts),
        )

    def _estimate_from_findings(
        self,
        inventory: CloudCostResourceInventory,
        findings: CloudCostFindingsSummary,
    ) -> list[CloudCostResourceSavingsEstimate]:
        volumes_by_id = {volume.volume_id: volume for volume in inventory.ebs}
        load_balancers_by_key = self._index_load_balancers(inventory.load_balancers)
        estimates: list[CloudCostResourceSavingsEstimate] = []

        for finding in findings.findings:
            if finding.resource_type == "ebs":
                volume = volumes_by_id.get(finding.resource_id)
                if not volume or not volume.size_gb:
                    continue
                rate = EBS_GB_MONTH_USD.get((volume.volume_type or "").lower(), DEFAULT_EBS_GB_MONTH_USD)
                amount = round(volume.size_gb * rate, 2)
                estimates.append(
                    CloudCostResourceSavingsEstimate(
                        resource_id=finding.resource_id,
                        resource_type="ebs",
                        monthly_savings_usd=amount,
                        confidence="high",
                        calculation_method="aws_list_price",
                        note=f"{volume.size_gb} GB {volume.volume_type or 'volume'} at ${rate:.3f}/GB-month.",
                    )
                )
            elif finding.resource_type == "elastic_ip":
                estimates.append(
                    CloudCostResourceSavingsEstimate(
                        resource_id=finding.resource_id,
                        resource_type="elastic_ip",
                        monthly_savings_usd=UNASSOCIATED_EIP_MONTH_USD,
                        confidence="high",
                        calculation_method="aws_list_price",
                        note="Unassociated Elastic IP hourly charge (~$3.65/month).",
                    )
                )
            elif finding.resource_type == "ec2" and (finding.category == "unused"):
                attached_cost = self._attached_ebs_monthly_cost(inventory, finding.resource_id)
                if attached_cost > 0:
                    estimates.append(
                        CloudCostResourceSavingsEstimate(
                            resource_id=finding.resource_id,
                            resource_type="ec2",
                            monthly_savings_usd=attached_cost,
                            confidence="medium",
                            calculation_method="aws_list_price",
                            note=(
                                "Stopped instance compute is $0; estimate reflects attached "
                                "EBS storage that could be eliminated if the instance is terminated."
                            ),
                        )
                    )
            elif finding.resource_type == "load_balancer":
                lb = load_balancers_by_key.get(finding.resource_id) or load_balancers_by_key.get(
                    finding.resource_name or ""
                )
                lb_type = (lb.type if lb else "application") or "application"
                amount = NLB_BASE_MONTH_USD if lb_type == "network" else ALB_BASE_MONTH_USD
                estimates.append(
                    CloudCostResourceSavingsEstimate(
                        resource_id=finding.resource_id,
                        resource_type="load_balancer",
                        monthly_savings_usd=amount,
                        confidence="medium",
                        calculation_method="aws_list_price",
                        note=f"Base monthly load balancer charge estimate for {lb_type.upper()}.",
                    )
                )

        return estimates

    def _attached_ebs_monthly_cost(self, inventory: CloudCostResourceInventory, instance_id: str) -> float:
        total = 0.0
        for volume in inventory.ebs:
            if volume.attached_instance_id != instance_id or not volume.size_gb:
                continue
            rate = EBS_GB_MONTH_USD.get((volume.volume_type or "").lower(), DEFAULT_EBS_GB_MONTH_USD)
            total += volume.size_gb * rate
        return round(total, 2)

    @staticmethod
    def _index_load_balancers(load_balancers: list[CloudCostLoadBalancer]) -> dict[str, CloudCostLoadBalancer]:
        indexed: dict[str, CloudCostLoadBalancer] = {}
        for lb in load_balancers:
            if lb.load_balancer_arn:
                indexed[lb.load_balancer_arn] = lb
            if lb.name:
                indexed[lb.name] = lb
        return indexed

    @staticmethod
    def _overall_confidence(
        estimates: list[CloudCostResourceSavingsEstimate],
        has_cost_explorer: bool,
    ) -> str:
        if not estimates:
            return "low"
        high_count = sum(1 for item in estimates if item.confidence == "high")
        if high_count >= 2 or (high_count >= 1 and has_cost_explorer):
            return "high"
        if high_count >= 1 or has_cost_explorer:
            return "medium"
        return "low"
