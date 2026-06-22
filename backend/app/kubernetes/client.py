"""Kubernetes client placeholder for future cluster connectivity."""

from loguru import logger


class KubernetesClient:
    """Placeholder Kubernetes API client."""

    def __init__(self, kubeconfig_path: str | None = None) -> None:
        self.kubeconfig_path = kubeconfig_path
        logger.debug("KubernetesClient initialized (placeholder)")

    async def connect(self, cluster_id: str) -> None:
        """Connect to a Kubernetes cluster. Not implemented in Phase 1."""
        raise NotImplementedError("Kubernetes connectivity is not implemented yet.")

    async def get_resource(self, cluster_id: str, kind: str, name: str, namespace: str) -> dict:
        """Fetch a Kubernetes resource. Not implemented in Phase 1."""
        raise NotImplementedError("Kubernetes resource retrieval is not implemented yet.")
