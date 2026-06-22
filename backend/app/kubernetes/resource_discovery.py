"""Resource discovery for Kubernetes investigations."""

from app.kubernetes.executor import KubectlExecutor
from app.kubernetes.investigation_cache import InvestigationCache
from app.kubernetes.utils import extract_items, secret_metadata_only, to_resource_item
from app.models.investigation import ResourceDiscoveryResult, ResourceItem


class ResourceDiscovery:
    """Collect Kubernetes resource inventory across the cluster."""

    NAMESPACED_RESOURCES = [
        ("deployments", "deployments"),
        ("replica_sets", "replicasets"),
        ("pods", "pods"),
        ("services", "services"),
        ("ingresses", "ingress"),
        ("config_maps", "configmaps"),
        ("secrets", "secrets"),
        ("persistent_volume_claims", "pvc"),
    ]

    def __init__(self, executor: KubectlExecutor) -> None:
        self.executor = executor

    def discover(self, namespace: str | None = None) -> tuple[ResourceDiscoveryResult, InvestigationCache]:
        result = ResourceDiscoveryResult()
        cache = InvestigationCache()
        namespace_args = ["-n", namespace] if namespace else ["-A"]

        namespaces_result, namespaces_payload = self.executor.run_json(
            ["get", "namespaces", "-o", "json"]
            if not namespace
            else ["get", "namespace", namespace, "-o", "json"]
        )
        if namespaces_result.success:
            namespace_items = extract_items(namespaces_payload)
            if namespace and not namespace_items:
                namespace_items = [namespaces_payload] if isinstance(namespaces_payload, dict) else []
            cache.namespaces = namespace_items
            result.namespaces = [
                ResourceItem(**to_resource_item(item)) for item in namespace_items
            ]

        for field_name, resource_type in self.NAMESPACED_RESOURCES:
            kubectl_result, payload = self.executor.run_json(
                ["get", resource_type, *namespace_args, "-o", "json"]
            )
            if not kubectl_result.success:
                continue

            raw_items = extract_items(payload)
            if field_name == "pods":
                cache.pods = raw_items
            elif field_name == "deployments":
                cache.deployments = raw_items
            elif field_name == "replica_sets":
                cache.replica_sets = raw_items
            elif field_name == "services":
                cache.services = raw_items
            elif field_name == "ingresses":
                cache.ingresses = raw_items

            items: list[ResourceItem] = []
            for item in raw_items:
                if field_name == "secrets":
                    data = secret_metadata_only(item)
                else:
                    data = to_resource_item(
                        item,
                        include_spec=field_name in {"services", "ingresses", "deployments"},
                    )
                items.append(ResourceItem(**data))
            setattr(result, field_name, items)

        endpoints_result, endpoints_payload = self.executor.run_json(
            ["get", "endpoints", *namespace_args, "-o", "json"]
        )
        if endpoints_result.success:
            cache.endpoints = extract_items(endpoints_payload)

        events_result, events_payload = self.executor.run_json(
            ["get", "events", *namespace_args, "-o", "json", "--sort-by=.lastTimestamp"]
        )
        if events_result.success:
            cache.events = extract_items(events_payload)

        pv_result, pv_payload = self.executor.run_json(["get", "pv", "-o", "json"])
        if pv_result.success:
            result.persistent_volumes = [
                ResourceItem(**to_resource_item(item)) for item in extract_items(pv_payload)
            ]

        return result, cache
