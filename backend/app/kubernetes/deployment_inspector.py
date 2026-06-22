"""Deployment inspection for rollout and replica issues."""

from app.kubernetes.executor import KubectlExecutor
from app.kubernetes.utils import extract_items, resource_ref
from app.models.investigation import DeploymentInspectionResult, DeploymentIssue


class DeploymentInspector:
    """Inspect deployment and replicaset health."""

    def __init__(self, executor: KubectlExecutor) -> None:
        self.executor = executor

    def inspect(self, namespace: str | None = None) -> DeploymentInspectionResult:
        args = ["get", "deployments", "-o", "json"]
        if namespace:
            args.extend(["-n", namespace])
        else:
            args.append("-A")

        result, payload = self.executor.run_json(args)
        if not result.success:
            return DeploymentInspectionResult(healthy=True, deployments_checked=0, issues=[])

        return self.inspect_deployments(extract_items(payload))

    def inspect_deployments(self, deployments: list[dict]) -> DeploymentInspectionResult:
        issues: list[DeploymentIssue] = []

        for deployment in deployments:
            metadata = deployment.get("metadata", {})
            spec = deployment.get("spec", {})
            status = deployment.get("status", {})
            name = metadata.get("name", "")
            ns = metadata.get("namespace", "")

            desired = spec.get("replicas", 1) or 0
            available = status.get("availableReplicas", 0) or 0
            unavailable = status.get("unavailableReplicas", 0) or 0
            updated = status.get("updatedReplicas", 0) or 0
            ready = status.get("readyReplicas", 0) or 0

            conditions = {
                condition.get("type"): condition
                for condition in status.get("conditions") or []
            }
            progressing = conditions.get("Progressing", {})
            available_condition = conditions.get("Available", {})

            if unavailable > 0 or available < desired:
                issues.append(
                    DeploymentIssue(
                        name=name,
                        namespace=ns,
                        issue_type="replica_mismatch",
                        message=(
                            f"Deployment has {available}/{desired} available replicas "
                            f"({unavailable} unavailable)."
                        ),
                        desired_replicas=desired,
                        available_replicas=available,
                        unavailable_replicas=unavailable,
                        resource_ref=resource_ref("deployment", name),
                    )
                )

            if progressing.get("status") == "False":
                issues.append(
                    DeploymentIssue(
                        name=name,
                        namespace=ns,
                        issue_type="rollout_failed",
                        message=progressing.get("message", "Deployment rollout is not progressing."),
                        desired_replicas=desired,
                        available_replicas=available,
                        unavailable_replicas=unavailable,
                        resource_ref=resource_ref("deployment", name),
                    )
                )

            if available_condition.get("status") == "False":
                issues.append(
                    DeploymentIssue(
                        name=name,
                        namespace=ns,
                        issue_type="not_available",
                        message=available_condition.get("message", "Deployment is not available."),
                        desired_replicas=desired,
                        available_replicas=available,
                        unavailable_replicas=unavailable,
                        resource_ref=resource_ref("deployment", name),
                    )
                )

            if updated < desired and unavailable > 0:
                issues.append(
                    DeploymentIssue(
                        name=name,
                        namespace=ns,
                        issue_type="rollout_in_progress",
                        message=(
                            f"Rollout stalled: {updated} updated, {ready} ready, "
                            f"{desired} desired, {unavailable} unavailable."
                        ),
                        desired_replicas=desired,
                        available_replicas=available,
                        unavailable_replicas=unavailable,
                        resource_ref=resource_ref("deployment", name),
                    )
                )

        unique_issues = self._deduplicate_issues(issues)
        return DeploymentInspectionResult(
            healthy=len(unique_issues) == 0,
            deployments_checked=len(deployments),
            issues=unique_issues,
        )

    def _deduplicate_issues(self, issues: list[DeploymentIssue]) -> list[DeploymentIssue]:
        seen: set[tuple[str, str, str]] = set()
        unique: list[DeploymentIssue] = []
        for issue in issues:
            key = (issue.namespace, issue.name, issue.issue_type)
            if key in seen:
                continue
            seen.add(key)
            unique.append(issue)
        return unique
