"""Cluster discovery for Kubernetes investigations."""

from app.kubernetes.executor import KubectlExecutor
from app.kubernetes.utils import extract_items
from app.models.investigation import ClusterInfo


class ClusterDiscovery:
    """Collect cluster metadata and inventory basics."""

    def __init__(self, executor: KubectlExecutor, cluster_id: str) -> None:
        self.executor = executor
        self.cluster_id = cluster_id

    def discover(self) -> tuple[ClusterInfo, str | None]:
        context_result = self.executor.run(["config", "current-context"])
        if not context_result.success:
            return ClusterInfo(cluster_id=self.cluster_id), context_result.error

        context = context_result.stdout.strip()

        version_result, version_payload = self.executor.run_json(["version", "--output=json"])
        version = None
        if version_result.success and isinstance(version_payload, dict):
            version = (
                version_payload.get("serverVersion", {}).get("gitVersion")
                or version_payload.get("clientVersion", {}).get("gitVersion")
            )

        nodes_result, nodes_payload = self.executor.run_json(["get", "nodes", "-o", "json"])
        if not nodes_result.success:
            return (
                ClusterInfo(
                    cluster_id=self.cluster_id,
                    name=self.cluster_id,
                    context=context,
                    version=version,
                ),
                nodes_result.error,
            )

        namespaces_result, namespaces_payload = self.executor.run_json(
            ["get", "namespaces", "-o", "json"]
        )
        namespaces = []
        if namespaces_result.success:
            namespaces = [
                item.get("metadata", {}).get("name", "")
                for item in extract_items(namespaces_payload)
                if item.get("metadata", {}).get("name")
            ]

        return (
            ClusterInfo(
                cluster_id=self.cluster_id,
                name=self.cluster_id,
                context=context,
                version=version,
                node_count=len(extract_items(nodes_payload)),
                namespaces=namespaces,
            ),
            None,
        )
