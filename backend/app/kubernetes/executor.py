"""Reusable kubectl subprocess executor."""

import json
import subprocess
from dataclasses import dataclass, field

from loguru import logger


@dataclass
class KubectlResult:
    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    command: list[str] = field(default_factory=list)
    error: str | None = None


class KubectlExecutor:
    """Execute kubectl commands with timeout, logging, and structured errors."""

    def __init__(
        self,
        kubeconfig_path: str | None = None,
        context: str | None = None,
        default_timeout: int = 30,
    ) -> None:
        self.kubeconfig_path = kubeconfig_path or None
        self.context = context or None
        self.default_timeout = default_timeout

    def _build_command(self, args: list[str], namespace: str | None = None) -> list[str]:
        command = ["kubectl"]
        if self.kubeconfig_path:
            command.extend(["--kubeconfig", self.kubeconfig_path])
        if self.context:
            command.extend(["--context", self.context])
        if namespace:
            command.extend(["-n", namespace])
        command.extend(args)
        return command

    def run(
        self,
        args: list[str],
        namespace: str | None = None,
        timeout: int | None = None,
    ) -> KubectlResult:
        command = self._build_command(args, namespace=namespace)
        effective_timeout = timeout or self.default_timeout

        logger.debug("Running kubectl command: {}", " ".join(command))

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                check=False,
            )
            success = completed.returncode == 0
            result = KubectlResult(
                success=success,
                stdout=completed.stdout,
                stderr=completed.stderr,
                returncode=completed.returncode,
                command=command,
                error=None if success else completed.stderr.strip() or "kubectl command failed",
            )

            if not success:
                logger.warning(
                    "kubectl command failed | command={} returncode={} stderr={}",
                    " ".join(command),
                    completed.returncode,
                    completed.stderr.strip(),
                )
            return result

        except subprocess.TimeoutExpired as exc:
            error = f"kubectl command timed out after {effective_timeout}s"
            logger.error("{} | command={}", error, " ".join(command))
            return KubectlResult(
                success=False,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                returncode=-1,
                command=command,
                error=error,
            )
        except FileNotFoundError:
            error = "kubectl binary not found in PATH"
            logger.error(error)
            return KubectlResult(
                success=False,
                command=command,
                returncode=-1,
                error=error,
            )
        except Exception as exc:
            error = f"unexpected kubectl execution error: {exc}"
            logger.exception(error)
            return KubectlResult(
                success=False,
                command=command,
                returncode=-1,
                error=error,
            )

    def run_json(
        self,
        args: list[str],
        namespace: str | None = None,
        timeout: int | None = None,
    ) -> tuple[KubectlResult, dict | list | None]:
        result = self.run(args, namespace=namespace, timeout=timeout)
        if not result.success:
            return result, None

        try:
            return result, json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            result.success = False
            result.error = f"failed to parse kubectl JSON output: {exc}"
            logger.error(result.error)
            return result, None
