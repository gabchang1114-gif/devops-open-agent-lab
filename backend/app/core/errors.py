"""User-friendly error messages for API responses."""

from __future__ import annotations

import re


def sanitize_error_message(raw_error: str | None) -> str:
    """Convert internal errors into safe, user-friendly messages."""
    if not raw_error:
        return "An unexpected error occurred. Please try again."

    normalized = raw_error.strip()
    lowered = normalized.lower()

    if "kubectl binary not found" in lowered:
        return (
            "kubectl is not available in the backend environment.\n\n"
            "Please verify:\n"
            "• kubectl is installed\n"
            "• the backend container or process can access kubectl"
        )

    if "kubeconfig" in lowered and ("no such file" in lowered or "not found" in lowered):
        return (
            "Unable to locate a kubeconfig file.\n\n"
            "Please verify:\n"
            "• kubeconfig path\n"
            "• KUBECONFIG environment variable\n"
            "• ~/.kube/config exists"
        )

    if "connection refused" in lowered or "unable to connect" in lowered or "dial tcp" in lowered:
        return (
            "Unable to connect to the Kubernetes cluster.\n\n"
            "Please verify:\n"
            "• kubeconfig path\n"
            "• current context\n"
            "• cluster availability\n"
            "• kubectl access"
        )

    if "failed to verify certificate" in lowered or "x509:" in lowered:
        return (
            "Unable to connect to the Kubernetes cluster due to a TLS certificate mismatch.\n\n"
            "If you are using Kind or minikube with Docker, restart the backend so it can "
            "regenerate a Docker-compatible kubeconfig."
        )

    if "timed out" in lowered or "timeout" in lowered:
        return (
            "The investigation timed out while communicating with the cluster.\n\n"
            "Please verify cluster responsiveness and try again."
        )

    if "forbidden" in lowered or "access denied" in lowered or "unauthorized" in lowered:
        return (
            "Access to the Kubernetes cluster was denied.\n\n"
            "Please verify:\n"
            "• your kubeconfig credentials\n"
            "• namespace permissions\n"
            "• RBAC access for the current context"
        )

    if "invalid configuration" in lowered or "invalid kubeconfig" in lowered:
        return (
            "The kubeconfig file appears to be invalid.\n\n"
            "Please verify the kubeconfig format and current context."
        )

    if "openai_api_key" in lowered or "anthropic_api_key" in lowered or "openrouter_api_key" in lowered:
        return (
            "The configured LLM provider is unavailable.\n\n"
            "Please verify:\n"
            "• LLM_PROVIDER setting\n"
            "• API key configuration\n"
            "• model name"
        )

    if "ollama" in lowered and ("connect" in lowered or "unavailable" in lowered):
        return (
            "Ollama is unavailable.\n\n"
            "Please verify:\n"
            "• Ollama is running\n"
            "• OLLAMA_BASE_URL is correct\n"
            "• OLLAMA_MODEL is installed"
        )

    if "rate limit" in lowered:
        return "The LLM provider rate limit was exceeded. Please wait and try again."

    if "github authentication failed" in lowered or "github token" in lowered:
        return normalized

    if "authentication failed" in lowered or "401" in lowered:
        return (
            "LLM authentication failed.\n\n"
            "Please verify your provider API key and model configuration."
        )

    if "malformed response" in lowered or "failed to parse" in lowered:
        return (
            "AI reasoning returned an invalid response.\n\n"
            "Investigation evidence was collected, but diagnosis parsing failed."
        )

    if len(normalized) > 500:
        return summarize_technical_error(normalized)

    return normalized


def summarize_technical_error(raw_error: str) -> str:
    """Reduce noisy kubectl stderr into a concise user-facing message."""
    lines = [line.strip() for line in raw_error.splitlines() if line.strip()]
    if not lines:
        return "Investigation failed. Please verify cluster connectivity and try again."

    last_line = lines[-1]
    if "connection refused" in last_line.lower():
        return sanitize_error_message(last_line)

    match = re.search(r'error: (.+)$', last_line, re.IGNORECASE)
    if match:
        return sanitize_error_message(match.group(1))

    return (
        "Investigation failed while communicating with the cluster.\n\n"
        "Please verify cluster connectivity, context selection, and kubectl access."
    )


def healthy_cluster_message() -> str:
    return (
        "No unhealthy resources detected.\n\n"
        "The selected cluster appears healthy based on the collected investigation evidence."
    )
