"""Pod inspection for unhealthy workload detection."""

from app.kubernetes.executor import KubectlExecutor
from app.kubernetes.utils import age_in_seconds, extract_items, resource_ref
from app.models.investigation import PodInspectionResult, ProblematicPod

PROBLEMATIC_REASONS = {
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "CreateContainerConfigError",
    "CreateContainerError",
    "InvalidImageName",
    "Error",
    "OOMKilled",
}


class PodInspector:
    """Detect problematic pod states across the cluster."""

    STUCK_CREATING_SECONDS = 300
    STUCK_TERMINATING_SECONDS = 300

    def __init__(self, executor: KubectlExecutor) -> None:
        self.executor = executor

    def inspect(self, namespace: str | None = None) -> PodInspectionResult:
        args = ["get", "pods", "-o", "json"]
        if namespace:
            args.extend(["-n", namespace])
        else:
            args.append("-A")

        result, payload = self.executor.run_json(args)
        if not result.success:
            return PodInspectionResult(healthy=True, total_pods=0, problematic_pods=[])

        return self.inspect_pods(extract_items(payload))

    def inspect_pods(self, pods: list[dict]) -> PodInspectionResult:
        problematic: list[ProblematicPod] = []

        for pod in pods:
            metadata = pod.get("metadata", {})
            status = pod.get("status", {})
            name = metadata.get("name", "")
            ns = metadata.get("namespace", "")
            phase = status.get("phase", "Unknown")
            deletion_timestamp = metadata.get("deletionTimestamp")
            pod_age = age_in_seconds(metadata.get("creationTimestamp"))

            container_states = []
            reasons: set[str] = set()
            messages: list[str] = []

            for container_status in status.get("containerStatuses") or []:
                state_info = self._inspect_container_status(container_status, pod_age)
                if state_info:
                    container_states.append(state_info)
                    if state_info.get("reason"):
                        reasons.add(state_info["reason"])
                    if state_info.get("message"):
                        messages.append(state_info["message"])

            for init_status in status.get("initContainerStatuses") or []:
                state_info = self._inspect_container_status(init_status, pod_age)
                if state_info:
                    container_states.append(state_info)
                    if state_info.get("reason"):
                        reasons.add(state_info["reason"])

            if phase == "Pending":
                reasons.add("Pending")
                for condition in status.get("conditions") or []:
                    if condition.get("reason"):
                        reasons.add(condition["reason"])
                    if condition.get("message"):
                        messages.append(condition["message"])

            if deletion_timestamp:
                age = age_in_seconds(deletion_timestamp)
                if age is not None and age > self.STUCK_TERMINATING_SECONDS:
                    reasons.add("TerminatingStuck")

            if not reasons:
                for condition in status.get("conditions") or []:
                    if condition.get("type") == "Ready" and condition.get("status") != "True":
                        if condition.get("reason"):
                            reasons.add(condition["reason"])

            filtered_reasons = reasons & PROBLEMATIC_REASONS | {
                reason
                for reason in reasons
                if reason in {"Pending", "TerminatingStuck", "ContainerCreatingStuck"}
            }

            if filtered_reasons or phase in {"Failed", "Unknown"}:
                problematic.append(
                    ProblematicPod(
                        name=name,
                        namespace=ns,
                        status=phase,
                        reason=", ".join(sorted(filtered_reasons)) or phase,
                        message="; ".join(messages[:3]) or None,
                        container_states=container_states,
                        resource_ref=resource_ref("pod", name),
                    )
                )

        return PodInspectionResult(
            healthy=len(problematic) == 0,
            total_pods=len(pods),
            problematic_pods=problematic,
        )

    def _inspect_container_status(
        self, container_status: dict, pod_age: float | None
    ) -> dict | None:
        name = container_status.get("name", "")
        state = container_status.get("state") or {}
        waiting = state.get("waiting") or {}
        terminated = state.get("terminated") or {}
        running = state.get("running")

        if waiting:
            reason = waiting.get("reason", "")
            message = waiting.get("message")
            if reason == "ContainerCreating" and pod_age is not None and pod_age > self.STUCK_CREATING_SECONDS:
                return {
                    "container": name,
                    "state": "waiting",
                    "reason": "ContainerCreatingStuck",
                    "message": message,
                }
            return {
                "container": name,
                "state": "waiting",
                "reason": reason,
                "message": message,
            }

        if terminated and terminated.get("reason") in PROBLEMATIC_REASONS | {"Error"}:
            return {
                "container": name,
                "state": "terminated",
                "reason": terminated.get("reason"),
                "message": terminated.get("message"),
                "exit_code": terminated.get("exitCode"),
            }

        if running is None and not waiting and not terminated:
            return {"container": name, "state": "unknown", "reason": "Error"}

        return None
