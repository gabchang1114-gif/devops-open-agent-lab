"""Kubeconfig context discovery."""

from dataclasses import dataclass

from app.core.config import Settings, get_settings
from app.kubernetes.executor import KubectlExecutor
from app.kubernetes.kubeconfig_resolver import KubeconfigResolver


@dataclass
class ClusterContext:
    cluster_id: str
    context: str
    name: str
    active: bool = False


def _display_name_for_context(context: str) -> str:
    if context.startswith("kind-"):
        return context.removeprefix("kind-")
    return context


class KubeconfigService:
    """Discover clusters and contexts from the user's kubeconfig."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._resolver = KubeconfigResolver(
            configured_path=self.settings.kubeconfig_path,
            api_host_rewrite=self.settings.kube_api_host_rewrite,
            output_dir="data",
        )

    def resolved_kubeconfig_path(self) -> str | None:
        return self._resolver.resolve()

    def _executor(self, context: str | None = None) -> KubectlExecutor:
        return KubectlExecutor(
            kubeconfig_path=self.resolved_kubeconfig_path(),
            context=context,
        )

    def list_clusters(self) -> tuple[list[ClusterContext], str | None]:
        executor = self._executor()

        current_result = executor.run(["config", "current-context"])
        if not current_result.success:
            return [], current_result.error

        current_context = current_result.stdout.strip()
        contexts_result = executor.run(["config", "get-contexts", "-o", "name"])
        if not contexts_result.success:
            return [], contexts_result.error

        contexts = [
            line.strip()
            for line in contexts_result.stdout.splitlines()
            if line.strip()
        ]

        if not contexts and current_context:
            contexts = [current_context]

        clusters = [
            ClusterContext(
                cluster_id=context,
                context=context,
                name=_display_name_for_context(context),
                active=context == current_context,
            )
            for context in contexts
        ]
        return clusters, None

    def has_kubeconfig(self) -> bool:
        executor = self._executor()
        result = executor.run(["config", "view", "--minify", "--output", "json"])
        return result.success

    def kubectl_available(self) -> bool:
        executor = self._executor()
        result = executor.run(["version", "--client=true", "--output=json"], timeout=10)
        return result.success

    def cluster_reachable(self, context: str | None = None) -> bool:
        executor = self._executor(context=context)
        result, _ = executor.run_json(["get", "nodes", "-o", "json"], timeout=15)
        return result.success
