"""Phase 1 topology builder producing graph-ready relationships."""

from app.kubernetes.executor import KubectlExecutor
from app.kubernetes.utils import resource_ref
from app.models.investigation import (
    ResourceDiscoveryResult,
    TopologyGraphNode,
    TopologyRelationship,
    TopologyResult,
)


class TopologyBuilder:
    """Build graph-ready relationships from discovered Kubernetes resources."""

    def __init__(self, executor: KubectlExecutor) -> None:
        self.executor = executor

    def build(
        self,
        resources: ResourceDiscoveryResult,
        endpoints_raw: list[dict] | None = None,
    ) -> TopologyResult:
        relationships: list[TopologyRelationship] = []
        nodes: set[str] = set()

        for namespace_item in resources.namespaces:
            nodes.add(resource_ref("namespace", namespace_item.name))

        for deployment in resources.deployments:
            nodes.add(resource_ref("deployment", deployment.name))
            nodes.add(resource_ref("namespace", deployment.namespace))
            relationships.append(
                TopologyRelationship(
                    source=resource_ref("namespace", deployment.namespace),
                    target=resource_ref("deployment", deployment.name),
                    type="contains",
                    namespace=deployment.namespace,
                )
            )

        for replica_set in resources.replica_sets:
            nodes.add(resource_ref("replicaset", replica_set.name))
            owner_refs = replica_set.metadata.get("owner_references") or []
            for owner in owner_refs:
                if owner.get("kind") == "Deployment":
                    relationships.append(
                        TopologyRelationship(
                            source=resource_ref("deployment", owner.get("name", "")),
                            target=resource_ref("replicaset", replica_set.name),
                            type="owns",
                            namespace=replica_set.namespace,
                        )
                    )

        for pod in resources.pods:
            nodes.add(resource_ref("pod", pod.name))
            owner_refs = pod.metadata.get("owner_references") or []
            for owner in owner_refs:
                owner_kind = owner.get("kind", "").lower()
                owner_name = owner.get("name", "")
                if owner_kind and owner_name:
                    relationships.append(
                        TopologyRelationship(
                            source=resource_ref(owner_kind, owner_name),
                            target=resource_ref("pod", pod.name),
                            type="owns",
                            namespace=pod.namespace,
                        )
                    )

        for service in resources.services:
            nodes.add(resource_ref("service", service.name))
            selector = (service.metadata.get("spec") or {}).get("selector") or {}
            for deployment in resources.deployments:
                if deployment.namespace != service.namespace:
                    continue
                template_labels = (
                    (deployment.metadata.get("spec") or {}).get("selector", {}).get("matchLabels")
                )
                if not template_labels and deployment.metadata.get("spec"):
                    template_labels = deployment.metadata["spec"].get("selector")
                if template_labels is None:
                    template_labels = {}
                if selector and selector == template_labels:
                    relationships.append(
                        TopologyRelationship(
                            source=resource_ref("service", service.name),
                            target=resource_ref("deployment", deployment.name),
                            type="targets",
                            namespace=service.namespace,
                        )
                    )

            for pod in resources.pods:
                if pod.namespace != service.namespace:
                    continue
                labels = pod.labels or {}
                if selector and all(labels.get(k) == v for k, v in selector.items()):
                    relationships.append(
                        TopologyRelationship(
                            source=resource_ref("service", service.name),
                            target=resource_ref("pod", pod.name),
                            type="routes_to",
                            namespace=service.namespace,
                        )
                    )

        for ingress in resources.ingresses:
            nodes.add(resource_ref("ingress", ingress.name))
            rules = (ingress.metadata.get("spec") or {}).get("rules") or []
            for rule in rules:
                http = rule.get("http") or {}
                for path in http.get("paths") or []:
                    backend = path.get("backend") or {}
                    service_name = (backend.get("service") or {}).get("name")
                    if service_name:
                        relationships.append(
                            TopologyRelationship(
                                source=resource_ref("ingress", ingress.name),
                                target=resource_ref("service", service_name),
                                type="routes_to",
                                namespace=ingress.namespace,
                            )
                        )

        endpoint_relationships = self._build_endpoint_relationships(endpoints_raw or [])
        relationships.extend(endpoint_relationships)
        nodes.update(relationship.source for relationship in endpoint_relationships)
        nodes.update(relationship.target for relationship in endpoint_relationships)

        graph_nodes = self._build_graph_nodes(resources, nodes)

        return TopologyResult(
            relationships=self._deduplicate(relationships),
            nodes=sorted(nodes),
            graph_nodes=graph_nodes,
        )

    def _build_graph_nodes(
        self, resources: ResourceDiscoveryResult, node_refs: set[str]
    ) -> list[TopologyGraphNode]:
        """Return enriched node metadata for graph rendering."""
        by_ref: dict[str, TopologyGraphNode] = {}

        def add(kind: str, name: str, namespace: str) -> None:
            ref = resource_ref(kind, name)
            if ref not in node_refs:
                return
            by_ref[ref] = TopologyGraphNode(
                id=ref,
                kind=kind.lower(),
                name=name,
                namespace=namespace or "default",
            )

        for namespace_item in resources.namespaces:
            add("namespace", namespace_item.name, namespace_item.name)

        for deployment in resources.deployments:
            add("deployment", deployment.name, deployment.namespace)
        for replica_set in resources.replica_sets:
            add("replicaset", replica_set.name, replica_set.namespace)
        for pod in resources.pods:
            add("pod", pod.name, pod.namespace)
        for service in resources.services:
            add("service", service.name, service.namespace)
        for ingress in resources.ingresses:
            add("ingress", ingress.name, ingress.namespace)

        for ref in sorted(node_refs):
            if ref in by_ref:
                continue
            kind_raw, _, name = ref.partition("/")
            if not name:
                continue
            by_ref[ref] = TopologyGraphNode(
                id=ref,
                kind=kind_raw.lower(),
                name=name,
                namespace="default",
            )

        return sorted(by_ref.values(), key=lambda node: (node.namespace, node.kind, node.name))

    def _build_endpoint_relationships(
        self, endpoints_raw: list[dict]
    ) -> list[TopologyRelationship]:
        if not endpoints_raw:
            return []

        relationships: list[TopologyRelationship] = []
        for endpoint in endpoints_raw:
            metadata = endpoint.get("metadata", {})
            service_name = metadata.get("name", "")
            namespace = metadata.get("namespace", "")
            for subset in endpoint.get("subsets") or []:
                for address in subset.get("addresses") or []:
                    target_ref = address.get("targetRef") or {}
                    if target_ref.get("kind") == "Pod":
                        relationships.append(
                            TopologyRelationship(
                                source=resource_ref("service", service_name),
                                target=resource_ref("pod", target_ref.get("name", "")),
                                type="routes_to",
                                namespace=namespace,
                            )
                        )
        return relationships

    def _deduplicate(
        self, relationships: list[TopologyRelationship]
    ) -> list[TopologyRelationship]:
        seen: set[tuple[str, str, str, str | None]] = set()
        unique: list[TopologyRelationship] = []
        for relationship in relationships:
            key = (
                relationship.source,
                relationship.target,
                relationship.type,
                relationship.namespace,
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(relationship)
        return unique
