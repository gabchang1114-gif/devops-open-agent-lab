"""Build AI-ready context from investigation evidence."""

from typing import Any

from app.models.investigation import InvestigationResponse


class ContextBuilder:
    """Transform investigation payloads into compact LLM context."""

    def build(self, investigation: InvestigationResponse | dict[str, Any]) -> dict[str, Any]:
        if isinstance(investigation, InvestigationResponse):
            payload = investigation.model_dump(exclude={"diagnosis", "error"})
        else:
            payload = investigation

        investigation_details = payload.get("investigation", {})
        pods = investigation_details.get("pods", {})
        logs = investigation_details.get("logs", {})
        events = investigation_details.get("events", {})
        deployments = investigation_details.get("deployments", {})
        network = investigation_details.get("network", {})

        return {
            "cluster_info": payload.get("cluster", {}),
            "pod_findings": {
                "healthy": pods.get("healthy", True),
                "total_pods": pods.get("total_pods", 0),
                "problematic_pods": pods.get("problematic_pods", []),
            },
            "per_pod_issues": self._build_per_pod_issues(
                pods.get("problematic_pods", []),
                logs,
                events,
            ),
            "log_findings": {
                "collected": logs.get("collected", False),
                "pod_count": logs.get("pod_count", 0),
                "logs": logs.get("logs", []),
            },
            "event_findings": {
                "total_events": events.get("total_events", 0),
                "summary": events.get("summary", []),
                "findings": events.get("findings", []),
            },
            "deployment_findings": {
                "healthy": deployments.get("healthy", True),
                "deployments_checked": deployments.get("deployments_checked", 0),
                "issues": deployments.get("issues", []),
            },
            "network_findings": {
                "healthy": network.get("healthy", True),
                "services_checked": network.get("services_checked", 0),
                "issues": network.get("issues", []),
            },
            "topology_relationships": payload.get("topology", {}).get("relationships", []),
            "observability_data": payload.get("observability", {}),
            "deployment_correlation_data": payload.get("deployments", {}),
            "resource_summary": self._summarize_resources(payload.get("resources", {})),
        }

    def _summarize_resources(self, resources: dict[str, Any]) -> dict[str, int]:
        if not resources:
            return {}
        return {
            key: len(value) if isinstance(value, list) else 0
            for key, value in resources.items()
        }

    def _build_per_pod_issues(
        self,
        problematic_pods: list[dict[str, Any]],
        logs: dict[str, Any],
        events: dict[str, Any],
    ) -> dict[str, Any]:
        if not problematic_pods:
            return {"count": 0, "issues": []}

        log_map = {entry.get("pod"): entry for entry in logs.get("logs", [])}
        event_findings = events.get("findings", [])

        issues = []
        for pod in problematic_pods:
            pod_name = pod.get("name", "")
            related_events = [
                {
                    "reason": event.get("reason"),
                    "message": event.get("message"),
                    "type": event.get("type"),
                }
                for event in event_findings
                if pod_name and pod_name in str(event.get("involved_object", ""))
            ][:5]
            log_entry = log_map.get(pod_name, {})
            log_lines = log_entry.get("lines") or []

            issues.append(
                {
                    "pod": pod_name,
                    "namespace": pod.get("namespace"),
                    "status": pod.get("status"),
                    "reason": pod.get("reason"),
                    "message": pod.get("message"),
                    "container_states": pod.get("container_states", []),
                    "related_events": related_events,
                    "logs_collected": bool(log_lines),
                    "log_excerpt": log_lines[-5:],
                }
            )

        return {
            "count": len(issues),
            "requires_independent_analysis": len(issues) > 1,
            "issues": issues,
        }
