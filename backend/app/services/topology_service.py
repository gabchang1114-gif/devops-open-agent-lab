"""Cluster topology discovery service."""

from app.core.errors import sanitize_error_message
from app.graph.topology_builder import TopologyBuilder
from app.kubernetes.cluster_manager import ClusterManager
from app.kubernetes.executor import KubectlExecutor
from app.kubernetes.resource_discovery import ResourceDiscovery
from app.models.investigation import TopologyResult


class TopologyService:
    """Discover and build cluster resource topology on demand."""

    def __init__(self, cluster_manager: ClusterManager | None = None) -> None:
        self.cluster_manager = cluster_manager or ClusterManager()

    async def get_topology(self, cluster_id: str, namespace: str | None = None) -> TopologyResult:
        cluster_config = self.cluster_manager.resolve(cluster_id)
        executor = KubectlExecutor(
            kubeconfig_path=cluster_config.kubeconfig_path,
            context=cluster_config.context,
        )

        resources, cache = ResourceDiscovery(executor).discover(namespace=namespace)
        topology = TopologyBuilder(executor).build(resources, endpoints_raw=cache.endpoints)
        return topology

    @staticmethod
    def cluster_error_message(exc: Exception) -> str:
        return sanitize_error_message(str(exc))
