"""Network inspection for services, endpoints, and ingress routing."""

from app.kubernetes.executor import KubectlExecutor
from app.kubernetes.utils import extract_items, resource_ref
from app.models.investigation import NetworkInspectionResult, NetworkIssue


class NetworkInspector:
    """Detect service routing and endpoint issues."""

    def __init__(self, executor: KubectlExecutor) -> None:
        self.executor = executor

    def inspect(self, namespace: str | None = None) -> NetworkInspectionResult:
        namespace_args = ["-n", namespace] if namespace else ["-A"]

        services_result, services_payload = self.executor.run_json(
            ["get", "services", *namespace_args, "-o", "json"]
        )
        endpoints_result, endpoints_payload = self.executor.run_json(
            ["get", "endpoints", *namespace_args, "-o", "json"]
        )
        ingress_result, ingress_payload = self.executor.run_json(
            ["get", "ingress", *namespace_args, "-o", "json"]
        )
        pods_result, pods_payload = self.executor.run_json(
            ["get", "pods", *namespace_args, "-o", "json"]
        )

        if not services_result.success:
            return NetworkInspectionResult(healthy=True, services_checked=0, issues=[])

        return self.inspect_from_cache(
            extract_items(services_payload),
            extract_items(endpoints_payload),
            extract_items(pods_payload),
            extract_items(ingress_payload),
        )

    def inspect_from_cache(
        self,
        services: list[dict],
        endpoints_payload: list[dict],
        pods: list[dict],
        ingresses: list[dict],
    ) -> NetworkInspectionResult:
        endpoints = {
            (item.get("metadata", {}).get("namespace", ""), item.get("metadata", {}).get("name", "")): item
            for item in endpoints_payload
        }

        issues: list[NetworkIssue] = []

        for service in services:
            metadata = service.get("metadata", {})
            spec = service.get("spec", {})
            name = metadata.get("name", "")
            ns = metadata.get("namespace", "")
            selector = spec.get("selector") or {}

            if name == "kubernetes" and ns == "default":
                continue

            if spec.get("type") == "ExternalName":
                continue

            endpoint = endpoints.get((ns, name))
            if endpoint is None:
                issues.append(
                    NetworkIssue(
                        name=name,
                        namespace=ns,
                        issue_type="missing_endpoints",
                        message=f"Service '{name}' has no Endpoints resource.",
                        resource_ref=resource_ref("service", name),
                    )
                )
                continue

            subsets = endpoint.get("subsets") or []
            addresses = [
                address
                for subset in subsets
                for address in subset.get("addresses") or []
            ]
            if selector and not addresses:
                issues.append(
                    NetworkIssue(
                        name=name,
                        namespace=ns,
                        issue_type="missing_endpoints",
                        message=f"Service '{name}' has no ready endpoint addresses.",
                        resource_ref=resource_ref("service", name),
                    )
                )

            if selector:
                matching_pods = self._pods_matching_selector(pods, ns, selector)
                if not matching_pods:
                    issues.append(
                        NetworkIssue(
                            name=name,
                            namespace=ns,
                            issue_type="selector_mismatch",
                            message=f"Service '{name}' selector does not match any pods.",
                            resource_ref=resource_ref("service", name),
                        )
                    )

        for ingress in ingresses:
            metadata = ingress.get("metadata", {})
            spec = ingress.get("spec", {})
            name = metadata.get("name", "")
            ns = metadata.get("namespace", "")

            backend_services = self._ingress_backend_services(spec)
            for backend_service in backend_services:
                if (ns, backend_service) not in endpoints:
                    issues.append(
                        NetworkIssue(
                            name=name,
                            namespace=ns,
                            issue_type="broken_ingress_routing",
                            message=(
                                f"Ingress '{name}' routes to missing service '{backend_service}'."
                            ),
                            resource_ref=resource_ref("ingress", name),
                        )
                    )

        return NetworkInspectionResult(
            healthy=len(issues) == 0,
            services_checked=len(services),
            issues=issues,
        )

    def _pods_matching_selector(
        self, pods: list[dict], namespace: str, selector: dict[str, str]
    ) -> list[dict]:
        matched = []
        for pod in pods:
            metadata = pod.get("metadata", {})
            if metadata.get("namespace") != namespace:
                continue
            labels = metadata.get("labels") or {}
            if all(labels.get(key) == value for key, value in selector.items()):
                matched.append(pod)
        return matched

    def _ingress_backend_services(self, spec: dict) -> list[str]:
        services: list[str] = []
        for rule in spec.get("rules") or []:
            http = rule.get("http") or {}
            for path in http.get("paths") or []:
                backend = path.get("backend") or {}
                service = backend.get("service") or {}
                service_name = service.get("name")
                if service_name:
                    services.append(service_name)
                resource = backend.get("resource")
                if resource and resource.get("name"):
                    services.append(resource["name"])
        default_backend = spec.get("defaultBackend") or {}
        default_service = default_backend.get("service") or {}
        if default_service.get("name"):
            services.append(default_service["name"])
        return services
