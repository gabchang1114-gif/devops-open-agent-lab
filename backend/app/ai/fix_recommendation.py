"""Validate and sanitize fix recommendations."""

import re

from app.models.diagnosis import DiagnosisResult

DANGEROUS_PATTERNS = [
    re.compile(r"kubectl\s+delete\s+(namespace|ns)\b", re.IGNORECASE),
    re.compile(r"kubectl\s+delete\s+--all\b", re.IGNORECASE),
    re.compile(r"--force\b", re.IGNORECASE),
    re.compile(r"--grace-period=0\b", re.IGNORECASE),
]


class FixRecommendationEngine:
    """Ensure fix recommendations remain safe and human-reviewed."""

    SAFETY_NOTE = (
        " Review all commands manually before execution. Destructive operations require "
        "explicit human approval."
    )

    def apply(self, diagnosis: DiagnosisResult) -> DiagnosisResult:
        sanitized_commands: list[str] = []
        risky = False

        for command in diagnosis.kubectl_commands:
            command = command.strip()
            if not command:
                continue
            if any(pattern.search(command) for pattern in DANGEROUS_PATTERNS):
                risky = True
                sanitized_commands.append(f"# REVIEW CAREFULLY: {command}")
            else:
                sanitized_commands.append(command)

        diagnosis.kubectl_commands = sanitized_commands

        if risky and self.SAFETY_NOTE not in diagnosis.suggested_fix:
            diagnosis.suggested_fix = f"{diagnosis.suggested_fix}{self.SAFETY_NOTE}"

        if not diagnosis.validation_steps:
            diagnosis.validation_steps = [
                "Verify pod or deployment health after applying the recommended change.",
                "Confirm error events stop appearing.",
                "Review application logs after the fix.",
            ]

        return diagnosis
