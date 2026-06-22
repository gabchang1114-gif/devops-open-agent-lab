"""Classify changed files into DevOps categories."""

from __future__ import annotations

import re
from pathlib import PurePosixPath


def classify_file(filename: str) -> str:
    name = filename.replace("\\", "/")
    lower = name.lower()
    basename = PurePosixPath(name).name.lower()

    if basename == "dockerfile" or basename.startswith("dockerfile."):
        return "docker"
    if basename == "jenkinsfile":
        return "jenkins"
    if basename.endswith(".tf") or basename.endswith(".tfvars"):
        return "terraform"
    if basename.endswith((".yaml", ".yml")) and (
        "cloudformation" in lower or basename.endswith(".template")
    ):
        return "cloudformation"
    if basename in {"chart.yaml", "values.yaml"} or "/templates/" in lower:
        return "helm"
    if ".github/workflows/" in lower and basename.endswith((".yml", ".yaml")):
        return "github_actions"
    if basename == ".gitlab-ci.yml" or basename.endswith(".gitlab-ci.yml"):
        return "gitlab_ci"
    if basename.endswith((".sh", ".bash")):
        return "shell_script"
    if basename.endswith(".py") and any(
        token in lower for token in ("ansible", "pulumi", "devops", "deploy", "infra")
    ):
        return "python_devops"
    if basename.endswith((".yaml", ".yml")) and any(
        token in lower
        for token in (
            "deployment",
            "service",
            "ingress",
            "configmap",
            "statefulset",
            "daemonset",
            "cronjob",
            "k8s/",
            "kubernetes/",
            "helm/",
        )
    ):
        return "kubernetes"
    if basename.endswith((".yaml", ".yml", ".json")):
        return "yaml_config"
    if re.search(r"(^|/)ansible/", lower):
        return "ansible"
    return "unknown"
