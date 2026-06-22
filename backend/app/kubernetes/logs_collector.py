"""Log collection for unhealthy Kubernetes workloads."""

import re

from app.kubernetes.executor import KubectlExecutor
from app.kubernetes.utils import resource_ref
from app.models.investigation import LogsCollectionResult, PodLogEntry, ProblematicPod

LOG_PATTERNS = [
    ("exception", re.compile(r"\bException\b", re.IGNORECASE)),
    ("error", re.compile(r"\bError\b|\bERROR\b")),
    ("connection_refused", re.compile(r"Connection Refused|connection refused", re.IGNORECASE)),
    ("timeout", re.compile(r"Timeout|timed out", re.IGNORECASE)),
    ("crash", re.compile(r"\bCrash\b|\bCRASH\b")),
    ("panic", re.compile(r"\bpanic:\b|\bPanic\b")),
    ("missing_env", re.compile(r"Missing Environment Variable|required environment variable", re.IGNORECASE)),
]

NOISE_PATTERNS = [
    re.compile(r"^\s*$"),
    re.compile(r"^I\d{4}"),
    re.compile(r"^DEBUG", re.IGNORECASE),
]


class LogsCollector:
    """Collect recent logs for unhealthy pods only."""

    MAX_LINES = 200

    def __init__(self, executor: KubectlExecutor) -> None:
        self.executor = executor

    def collect(self, problematic_pods: list[ProblematicPod]) -> LogsCollectionResult:
        if not problematic_pods:
            return LogsCollectionResult(collected=False, pod_count=0, logs=[])

        collected_logs: list[PodLogEntry] = []

        for pod in problematic_pods:
            log_text = self._fetch_logs(pod, previous=False)
            if not log_text.strip():
                log_text = self._fetch_logs(pod, previous=True)
            if not log_text.strip():
                continue

            filtered_lines, matched_patterns = self._filter_lines(log_text.splitlines())
            if not filtered_lines:
                filtered_lines = log_text.splitlines()[-20:]

            collected_logs.append(
                PodLogEntry(
                    pod=pod.name,
                    namespace=pod.namespace,
                    lines=filtered_lines[: self.MAX_LINES],
                    matched_patterns=sorted(matched_patterns),
                    resource_ref=resource_ref("pod", pod.name),
                )
            )

        return LogsCollectionResult(
            collected=bool(collected_logs),
            pod_count=len(collected_logs),
            logs=collected_logs,
        )

    def _fetch_logs(self, pod: ProblematicPod, previous: bool = False) -> str:
        args = [
            "logs",
            pod.name,
            "--all-containers=true",
            f"--tail={self.MAX_LINES}",
            "--timestamps=true",
        ]
        if previous:
            args.append("--previous")

        result = self.executor.run(
            args,
            namespace=pod.namespace,
            timeout=45,
        )
        if result.success and result.stdout.strip():
            return result.stdout
        return ""

    def _filter_lines(self, lines: list[str]) -> tuple[list[str], set[str]]:
        matched_patterns: set[str] = set()
        filtered: list[str] = []

        for line in lines:
            if any(pattern.search(line) for pattern in NOISE_PATTERNS):
                continue

            line_matches = [
                label for label, pattern in LOG_PATTERNS if pattern.search(line)
            ]
            if line_matches:
                matched_patterns.update(line_matches)
                filtered.append(line)

        if not filtered:
            for line in lines[-50:]:
                if line.strip():
                    filtered.append(line)

        return filtered[: self.MAX_LINES], matched_patterns
