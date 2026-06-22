"""Split multi-pod investigations into separate per-issue diagnoses."""

from __future__ import annotations

import re
from typing import Any

from app.models.diagnosis import DiagnosisEvidence, DiagnosisResult, PodIssueDiagnosis

IMAGE_PULL_REASONS = {"ImagePullBackOff", "ErrImagePull", "InvalidImageName", "Failed"}
CRASH_REASONS = {"CrashLoopBackOff", "Error", "OOMKilled", "CreateContainerConfigError"}


class MultiPodDiagnosisEnricher:
    """Build independent diagnoses when multiple pods are unhealthy."""

    def enrich(
        self,
        diagnosis: DiagnosisResult,
        investigation: dict[str, Any],
    ) -> DiagnosisResult:
        pods = (
            investigation.get("investigation", {})
            .get("pods", {})
            .get("problematic_pods", [])
        )
        if len(pods) <= 1:
            return diagnosis

        issue_diagnoses = [
            self._build_issue_diagnosis(pod, investigation, diagnosis)
            for pod in pods
        ]
        diagnosis.issue_diagnoses = issue_diagnoses
        diagnosis.root_cause = self._build_overview_root_cause(issue_diagnoses)
        diagnosis.summary = self._build_overview_summary(issue_diagnoses)
        diagnosis.evidence = []
        diagnosis.suggested_fix = ""
        diagnosis.kubectl_commands = []
        diagnosis.validation_steps = []
        return diagnosis

    def _build_issue_diagnosis(
        self,
        pod: dict[str, Any],
        investigation: dict[str, Any],
        diagnosis: DiagnosisResult,
    ) -> PodIssueDiagnosis:
        pods = (
            investigation.get("investigation", {})
            .get("pods", {})
            .get("problematic_pods", [])
        )
        other_pod_names = [
            item.get("name")
            for item in pods
            if item.get("name") and item.get("name") != pod.get("name")
        ]
        name = pod.get("name", "unknown")
        namespace = pod.get("namespace") or "default"
        status = pod.get("status") or "Unknown"
        reason = pod.get("reason") or status

        root_cause = self._resolve_root_cause(pod, investigation, diagnosis.root_cause, name, other_pod_names)
        summary = self._resolve_summary(
            pod, root_cause, diagnosis.summary, name, other_pod_names
        )
        evidence = self._collect_pod_evidence(
            name, diagnosis.evidence, pod, investigation, other_pod_names
        )
        suggested_fix = self._resolve_suggested_fix(
            pod, investigation, diagnosis.suggested_fix, name, other_pod_names
        )
        kubectl_commands = self._collect_pod_commands(name, diagnosis.kubectl_commands, pod, investigation)
        validation_steps = self._collect_pod_validation_steps(name, diagnosis.validation_steps)

        return PodIssueDiagnosis(
            pod=name,
            namespace=namespace,
            status=status,
            reason=reason,
            root_cause=root_cause,
            summary=summary,
            evidence=evidence,
            suggested_fix=suggested_fix,
            kubectl_commands=kubectl_commands,
            validation_steps=validation_steps,
            confidence_score=diagnosis.confidence_score,
        )

    def _build_overview_root_cause(self, issues: list[PodIssueDiagnosis]) -> str:
        count = len(issues)
        names = ", ".join(f"'{issue.pod}'" for issue in issues)
        return (
            f"{count} independent pod issues were detected ({names}). "
            "Each issue has its own root cause analysis and fix below."
        )

    def _build_overview_summary(self, issues: list[PodIssueDiagnosis]) -> str:
        lines = ["The investigation found separate failures that should be resolved independently:"]
        for index, issue in enumerate(issues, start=1):
            lines.append(f"{index}. {issue.pod} ({issue.reason})")
        return "\n".join(lines)

    def _resolve_summary(
        self,
        pod: dict[str, Any],
        root_cause: str,
        llm_summary: str,
        pod_name: str,
        other_pod_names: list[str],
    ) -> str:
        extracted = self._extract_pod_summary(llm_summary, pod_name)
        if extracted and not self._text_mentions_other_pods(extracted, pod_name, other_pod_names):
            return extracted
        return self._build_issue_summary(pod, root_cause)

    def _build_issue_summary(self, pod: dict[str, Any], root_cause: str) -> str:
        name = pod.get("name", "unknown")
        reason = pod.get("reason") or pod.get("status") or "Unknown"
        return (
            f"Pod '{name}' is unhealthy with reason '{reason}'. "
            f"{root_cause}"
        )

    def _collect_pod_evidence(
        self,
        pod_name: str,
        llm_evidence: list[DiagnosisEvidence],
        pod: dict[str, Any],
        investigation: dict[str, Any],
        other_pod_names: list[str] | None = None,
    ) -> list[DiagnosisEvidence]:
        matched = [
            item
            for item in llm_evidence
            if self._mentions_pod(item.detail, pod_name)
            and not any(self._mentions_pod(item.detail, other) for other in (other_pod_names or []))
        ]
        if matched:
            return matched
        return self._build_pod_evidence(pod, investigation)

    def _collect_pod_commands(
        self,
        pod_name: str,
        llm_commands: list[str],
        pod: dict[str, Any],
        investigation: dict[str, Any],
    ) -> list[str]:
        matched = [cmd for cmd in llm_commands if pod_name in cmd]
        inferred = self._suggested_commands(pod, investigation)
        combined: list[str] = []
        for command in matched + inferred:
            if command not in combined:
                combined.append(command)
        return combined

    def _collect_pod_validation_steps(
        self,
        pod_name: str,
        llm_steps: list[str],
    ) -> list[str]:
        matched = [step for step in llm_steps if self._mentions_pod(step, pod_name)]
        if matched:
            return matched
        return [
            f"Verify pod '{pod_name}' reaches Running state.",
            f"Confirm warning events stop appearing for pod '{pod_name}'.",
            f"Review logs for pod '{pod_name}' after applying the fix.",
        ]

    def _resolve_root_cause(
        self,
        pod: dict[str, Any],
        investigation: dict[str, Any],
        llm_root_cause: str,
        pod_name: str,
        other_pod_names: list[str],
    ) -> str:
        extracted = self._extract_pod_root_cause(llm_root_cause, pod_name)
        if extracted and not self._text_mentions_other_pods(extracted, pod_name, other_pod_names):
            if not re.search(r"\b(?:two|both|multiple|distinct)\b", extracted, re.IGNORECASE):
                return extracted
        return self._infer_root_cause(pod, investigation)

    def _resolve_suggested_fix(
        self,
        pod: dict[str, Any],
        investigation: dict[str, Any],
        llm_fix: str,
        pod_name: str,
        other_pod_names: list[str],
    ) -> str:
        extracted = self._extract_pod_fix(llm_fix, pod_name, pod_names=other_pod_names)
        if extracted and not self._text_mentions_other_pods(extracted, pod_name, other_pod_names):
            return self._normalize_fix_text(extracted, pod_name)
        return self._infer_suggested_fix(pod, investigation)

    def _normalize_fix_text(self, text: str, pod_name: str) -> str:
        cleaned = self._clean_extracted_text(text)
        cleaned = re.sub(
            rf"^For\s+(?:pod\s+)?['\"]?{re.escape(pod_name)}['\"]?\s*,?\s*:?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        if cleaned.lower().startswith("for "):
            return cleaned[0].upper() + cleaned[1:]
        if not cleaned:
            return f"Review and apply the recommended fix for pod '{pod_name}'."
        return f"For pod '{pod_name}', {cleaned[0].lower() + cleaned[1:]}"

    def _text_mentions_other_pods(
        self,
        text: str,
        pod_name: str,
        other_pod_names: list[str],
    ) -> bool:
        return any(self._mentions_pod(text, other) for other in other_pod_names if other)

    def _extract_pod_root_cause(self, text: str, pod_name: str) -> str | None:
        if not text or not self._mentions_pod(text, pod_name):
            return None

        numbered = re.search(
            rf"(?:\d+\.\s*)?(?:Pod\s+['\"]?{re.escape(pod_name)}['\"]?\s*:|\*\*`{re.escape(pod_name)}`\*\*[^:]*:\*\*)\s*(.+?)(?=\n\d+\.|\n*$)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if numbered:
            return self._clean_extracted_text(numbered.group(1))

        for sentence in re.split(r"(?<=[.!?])\s+|\n", text.strip()):
            if self._mentions_pod(sentence, pod_name):
                cleaned = re.sub(
                    rf"^.*?pod\s+['\"]?{re.escape(pod_name)}['\"]?[^\s:]*\s*(is|:)\s*",
                    "",
                    sentence,
                    flags=re.IGNORECASE,
                )
                return self._clean_extracted_text(cleaned or sentence)
        return None

    def _extract_pod_summary(self, text: str, pod_name: str) -> str | None:
        if not text or not self._mentions_pod(text, pod_name):
            return None

        for sentence in re.split(r"(?<=[.!?])\s+", text.strip()):
            if self._mentions_pod(sentence, pod_name):
                return sentence.strip()
        return None

    def _extract_pod_fix(
        self,
        text: str,
        pod_name: str,
        pod_names: list[str] | None = None,
    ) -> str | None:
        if not text:
            return None

        other_pods = [name for name in (pod_names or []) if name and name != pod_name]

        patterns = [
            rf"For\s+[`'\"]?{re.escape(pod_name)}[`'\"]?\s*,?\s*(.+?)(?=\nFor\s+[`'\"]|$)",
            rf"For\s+pod\s+[`'\"]?{re.escape(pod_name)}[`'\"]?\s*,?\s*(.+?)(?=\nFor\s+|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return self._clean_extracted_text(f"For pod '{pod_name}', {match.group(1)}")

        for paragraph in re.split(r"\n\s*\n", text.strip()):
            if not self._mentions_pod(paragraph, pod_name):
                continue
            if any(self._mentions_pod(paragraph, other) for other in other_pods):
                continue
            return paragraph.strip()

        for sentence in re.split(r"(?<=[.!?])\s+", text.strip()):
            if self._mentions_pod(sentence, pod_name) and not any(
                self._mentions_pod(sentence, other) for other in other_pods
            ):
                return sentence.strip()
        return None

    def _clean_extracted_text(self, text: str) -> str:
        cleaned = text.strip()
        cleaned = re.sub(r"`+", "", cleaned)
        cleaned = re.sub(r"\*\*", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip(" .")

    def _build_pod_evidence(
        self,
        pod: dict[str, Any],
        investigation: dict[str, Any],
    ) -> list[DiagnosisEvidence]:
        name = pod.get("name", "unknown")
        evidence = [
            DiagnosisEvidence(
                source="pods",
                detail=(
                    f"Pod '{name}' in namespace '{pod.get('namespace', 'default')}' "
                    f"has status '{pod.get('status', 'Unknown')}' with reason "
                    f"'{pod.get('reason', 'unknown')}'."
                    + (f" Message: {pod['message']}" if pod.get("message") else "")
                ),
            )
        ]

        for event in self._pod_events(investigation, name)[:3]:
            evidence.append(
                DiagnosisEvidence(
                    source="events",
                    detail=(
                        f"Event for Pod/{name}: {event.get('reason', 'Warning')} - "
                        f"{event.get('message', '')}"
                    ),
                )
            )

        log_lines = self._pod_logs(investigation, name)
        if log_lines:
            excerpt = self._best_log_line(log_lines)
            evidence.append(
                DiagnosisEvidence(
                    source="logs",
                    detail=f"Logs from Pod/{name}: {excerpt}",
                )
            )

        return evidence

    def _infer_root_cause(self, pod: dict[str, Any], investigation: dict[str, Any]) -> str:
        name = pod.get("name", "unknown")
        reason = pod.get("reason") or pod.get("status") or "Unknown"
        message = pod.get("message") or ""

        reason_parts = {part.strip() for part in reason.split(",") if part.strip()}
        if reason_parts & IMAGE_PULL_REASONS or "pull" in message.lower():
            return (
                f"The container image cannot be pulled ({reason}). "
                f"{message or 'Verify the image name, tag, and registry credentials.'}"
            ).strip()

        log_lines = self._pod_logs(investigation, name)
        log_error = self._best_log_line(log_lines, errors_only=True)
        if log_error:
            return f"The container is crash looping ({reason}). Log evidence: {log_error}"

        exit_codes = [
            state.get("exit_code")
            for state in pod.get("container_states", [])
            if state.get("exit_code") is not None
        ]
        exit_text = f" Container exit code: {exit_codes[0]}." if exit_codes else ""

        if reason_parts & CRASH_REASONS or "crash" in reason.lower():
            event = self._pod_events(investigation, name)[:1]
            event_text = event[0].get("message", "") if event else ""
            return (
                f"The container is crash looping ({reason}).{exit_text} "
                f"{event_text or 'Inspect container logs with kubectl logs --previous.'}"
            ).strip()

        return (
            f"The pod is in an unhealthy state ({reason}). "
            f"{message or 'Review pod events and container status.'}"
        ).strip()

    def _infer_suggested_fix(
        self,
        pod: dict[str, Any],
        investigation: dict[str, Any],
    ) -> str:
        name = pod.get("name", "unknown")
        reason = pod.get("reason") or ""
        if any(token in reason for token in IMAGE_PULL_REASONS) or "ImagePull" in reason:
            return (
                f"Fix the container image reference for pod '{name}' in its Deployment or Pod "
                "manifest and verify registry access."
            )

        log_lines = self._pod_logs(investigation, name)
        joined = " ".join(log_lines).lower()
        if "environment variable" in joined or "missing" in joined:
            return (
                f"Add the missing environment variable(s) referenced in the logs for pod '{name}' "
                "to the Deployment or Pod spec."
            )

        return (
            f"Inspect logs for pod '{name}' with `kubectl logs {name} --previous` and fix the "
            "application or container command causing repeated restarts."
        )

    def _suggested_commands(
        self,
        pod: dict[str, Any],
        investigation: dict[str, Any],
    ) -> list[str]:
        name = pod.get("name")
        namespace = pod.get("namespace") or "default"
        if not name:
            return []

        commands = [
            f"kubectl describe pod {name} -n {namespace}",
            f"kubectl get events -n {namespace} --field-selector involvedObject.name={name}",
        ]

        reason = pod.get("reason") or ""
        if any(token in reason for token in IMAGE_PULL_REASONS):
            return commands

        commands.append(f"kubectl logs {name} -n {namespace} --previous --tail=100")
        if self._pod_logs(investigation, name):
            commands.append(f"kubectl logs {name} -n {namespace} --tail=100")
        return commands

    def _pod_events(self, investigation: dict[str, Any], pod_name: str) -> list[dict[str, Any]]:
        findings = (
            investigation.get("investigation", {})
            .get("events", {})
            .get("findings", [])
        )
        return [
            finding
            for finding in findings
            if pod_name in str(finding.get("involved_object", ""))
        ]

    def _pod_logs(self, investigation: dict[str, Any], pod_name: str) -> list[str]:
        for entry in (
            investigation.get("investigation", {})
            .get("logs", {})
            .get("logs", [])
        ):
            if entry.get("pod") == pod_name:
                return entry.get("lines") or []
        return []

    def _best_log_line(self, lines: list[str], errors_only: bool = False) -> str:
        if not lines:
            return ""

        candidates = lines
        if errors_only:
            candidates = [
                line
                for line in lines
                if re.search(r"error|exception|panic|fatal|missing", line, re.IGNORECASE)
            ] or lines

        line = candidates[-1].strip()
        if "Z " in line:
            line = line.split("Z ", 1)[-1]
        return line[:240]

    def _mentions_pod(self, text: str, pod_name: str) -> bool:
        return pod_name.lower() in text.lower()
