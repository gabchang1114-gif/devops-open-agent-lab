"""Format AI recommendations for Slack messages."""

from __future__ import annotations

from typing import Any

from app.models.diagnosis import DiagnosisResult

_AGENT_LABELS = {
    "kubernetes": "Kubernetes Debugging Agent",
    "aws": "AWS DevOps Agent",
    "cloud_cost": "Cloud Cost Detector",
    "pr_reviewer": "PR Reviewer",
}


def _truncate(text: str, limit: int = 2800) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def _bullet_list(items: list[str], limit: int = 5) -> str:
    if not items:
        return ""
    lines = [f"• {item}" for item in items[:limit]]
    if len(items) > limit:
        lines.append(f"• _+{len(items) - limit} more_")
    return "\n".join(lines)


def format_diagnosis_slack_payload(
    *,
    agent_type: str,
    scope_label: str,
    investigation_id: str,
    diagnosis: DiagnosisResult,
    app_url: str = "",
) -> dict[str, Any]:
    """Build Slack Block Kit payload for an investigation diagnosis."""
    agent_label = _AGENT_LABELS.get(agent_type, agent_type.replace("_", " ").title())
    fields = [
        {"type": "mrkdwn", "text": f"*Agent:*\n{agent_label}"},
        {"type": "mrkdwn", "text": f"*Scope:*\n{scope_label}"},
        {
            "type": "mrkdwn",
            "text": f"*Confidence:*\n{diagnosis.confidence_score}%",
        },
    ]

    blocks: list[dict[str, Any]] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "DevOps Open Agent — AI Recommendation"},
        },
        {"type": "section", "fields": fields},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Root cause*\n{_truncate(diagnosis.root_cause)}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Summary*\n{_truncate(diagnosis.summary)}",
            },
        },
    ]

    if diagnosis.suggested_fix:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Suggested fix*\n{_truncate(diagnosis.suggested_fix)}",
                },
            }
        )

    if diagnosis.prevention_recommendation:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Prevention*\n"
                        f"{_truncate(diagnosis.prevention_recommendation)}"
                    ),
                },
            }
        )

    validation = _bullet_list(diagnosis.validation_steps)
    if validation:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Validation steps*\n{validation}",
                },
            }
        )

    footer_parts = [f"Investigation `{investigation_id[:8]}`"]
    if app_url:
        footer_parts.append(f"<{app_url}|View in DevOps Open Agent>")
    blocks.append(
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": " · ".join(footer_parts)}],
        }
    )

    fallback = (
        f"{agent_label} recommendation for {scope_label}: "
        f"{diagnosis.root_cause} — {diagnosis.suggested_fix or diagnosis.summary}"
    )
    return {"text": _truncate(fallback, 500), "blocks": blocks}


def format_pr_review_slack_payload(
    *,
    owner: str,
    repository: str,
    pull_request_number: int,
    pull_request_title: str,
    overall_risk: str,
    final_recommendation: str,
    findings_count: int,
    review_id: str,
    app_url: str = "",
) -> dict[str, Any]:
    """Build Slack Block Kit payload for a PR review recommendation."""
    repo_label = f"{owner}/{repository}"
    fields = [
        {"type": "mrkdwn", "text": f"*Repository:*\n{repo_label}"},
        {
            "type": "mrkdwn",
            "text": f"*Pull request:*\n#{pull_request_number}",
        },
        {"type": "mrkdwn", "text": f"*Risk:*\n{overall_risk or 'unknown'}"},
        {
            "type": "mrkdwn",
            "text": f"*Findings:*\n{findings_count}",
        },
    ]

    blocks: list[dict[str, Any]] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "DevOps Open Agent — PR Review"},
        },
        {"type": "section", "fields": fields},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Title*\n{_truncate(pull_request_title, 500)}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Recommendation*\n{_truncate(final_recommendation)}",
            },
        },
    ]

    footer_parts = [f"Review `{review_id[:8]}`"]
    if app_url:
        footer_parts.append(f"<{app_url}|View in DevOps Open Agent>")
    blocks.append(
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": " · ".join(footer_parts)}],
        }
    )

    fallback = (
        f"PR Review for {repo_label}#{pull_request_number}: "
        f"{final_recommendation or pull_request_title}"
    )
    return {"text": _truncate(fallback, 500), "blocks": blocks}


def format_test_slack_payload() -> dict[str, Any]:
    return {
        "text": "DevOps Open Agent Slack integration test",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        ":white_check_mark: *Slack integration is working.*\n"
                        "AI recommendations from DevOps Open Agent will be posted here."
                    ),
                },
            }
        ],
    }
