"""Multi-cluster management for investigation workflows."""

from dataclasses import dataclass

from app.core.config import Settings, get_settings
from app.kubernetes.kubeconfig_resolver import KubeconfigResolver


@dataclass
class ClusterConfig:
    cluster_id: str
    name: str
    kubeconfig_path: str | None = None
    context: str | None = None
    enabled: bool = True


class ClusterManager:
    """Resolve cluster configuration for multi-cluster investigations."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._clusters: dict[str, ClusterConfig] = {}
        self._resolver = KubeconfigResolver(
            configured_path=self.settings.kubeconfig_path,
            api_host_rewrite=self.settings.kube_api_host_rewrite,
            output_dir="data",
        )

    def register_cluster(self, config: ClusterConfig) -> None:
        self._clusters[config.cluster_id] = config

    def get_cluster(self, cluster_id: str) -> ClusterConfig | None:
        return self._clusters.get(cluster_id)

    def list_clusters(self) -> list[ClusterConfig]:
        return list(self._clusters.values())

    def resolve(self, cluster_id: str) -> ClusterConfig:
        registered = self.get_cluster(cluster_id)
        if registered:
            return registered

        return ClusterConfig(
            cluster_id=cluster_id,
            name=cluster_id,
            kubeconfig_path=self._resolver.resolve(),
            context=cluster_id,
            enabled=True,
        )
