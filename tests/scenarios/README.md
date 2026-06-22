# Kubernetes Failure Test Scenarios

These manifests create controlled failure scenarios for end-to-end validation of the Kubernetes Debugging Agent.

## Prerequisites

- A running Kubernetes cluster (`kind`, `minikube`, or cloud cluster)
- `kubectl` configured and context selected
- Kubernetes Debugging Agent backend running with cluster access

## Deploy a Scenario

```bash
kubectl apply -f tests/scenarios/01-crashloop-missing-env.yaml
```

Run an investigation from the dashboard or API:

```bash
curl -X POST http://localhost:8000/api/v1/investigate \
  -H "Content-Type: application/json" \
  -d '{"cluster_id":"<your-context>","include_ai":true}'
```

## Scenarios

| Scenario | File | Expected Root Cause Theme |
|----------|------|---------------------------|
| CrashLoopBackOff | `01-crashloop-missing-env.yaml` | Missing environment variable |
| ImagePullBackOff | `02-imagepull-invalid-tag.yaml` | Invalid image tag |
| OOMKilled | `03-oomkilled-low-limit.yaml` | Memory limit too low |
| FailedScheduling | `04-failed-scheduling.yaml` | Insufficient cluster resources |
| Service Selector Mismatch | `05-service-selector-mismatch.yaml` | Service cannot route traffic |

## Cleanup

```bash
kubectl delete -f tests/scenarios/ --ignore-not-found
```

## Validation Checklist

- [ ] Cluster appears in `GET /api/v1/clusters`
- [ ] Investigation progress updates every 2 seconds
- [ ] Evidence includes pods, logs, events, deployments, network, topology
- [ ] AI diagnosis correlates multiple evidence sources
- [ ] Investigation appears in history with root cause and confidence
- [ ] `GET /api/v1/system/readiness` reports component status
