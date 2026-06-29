"""Build DevOps-focused PR review prompts."""

from __future__ import annotations

import json
from typing import Any

from app.modules.pr_reviewer.models.schemas import PrFileInfo, PrWebhookPayload

OUTPUT_SCHEMA = {
    "summary": "string",
    "overall_risk": "low|medium|high",
    "should_block_merge": False,
    "findings": [
        {
            "severity": "low|medium|high",
            "category": "security|reliability|scalability|cost|observability|ci_cd|kubernetes|terraform|docker|cloud",
            "file": "string",
            "line_reference": "string",
            "issue": "string",
            "why_it_matters": "string",
            "recommendation": "string",
            "example_fix": "string",
        }
    ],
    "positive_observations": ["string"],
    "final_recommendation": "approve|comment|request_changes",
}


class PrReviewPromptBuilder:
    def build_messages(
        self,
        pr: PrWebhookPayload,
        files: list[PrFileInfo],
        mcp_context: dict | None = None,
    ) -> list[dict[str, str]]:
        context = self._build_context(pr, files)
        if mcp_context:
            context["mcp_enrichment"] = mcp_context
        system_prompt = (
            "You are a Senior DevOps Engineer, Platform Engineer, and SRE.\n"
            "Review this pull request for DevOps best practices, reliability, security, "
            "scalability, observability, and production readiness.\n"
            "Focus only on DevOps-related concerns.\n"
            "Do not nitpick formatting.\n"
            "Do not invent issues not supported by the diff.\n"
            "If no serious issue is found, say that clearly.\n"
            "Respond with valid JSON only matching the provided schema."
        )
        user_prompt = (
            "Review the following GitHub pull request.\n\n"
            f"PR metadata:\n{json.dumps(context['metadata'], indent=2)}\n\n"
            f"File summaries:\n{json.dumps(context['file_summaries'], indent=2)}\n\n"
            f"Classified file types present:\n{json.dumps(context['categories'], indent=2)}\n\n"
            f"Diff patches:\n{json.dumps(context['patches'], indent=2)}\n\n"
        )
        if context.get("mcp_enrichment"):
            user_prompt += (
                f"MCP server context (external tools available during review):\n"
                f"{json.dumps(context['mcp_enrichment'], indent=2)}\n\n"
            )
        user_prompt += f"Output JSON schema:\n{json.dumps(OUTPUT_SCHEMA, indent=2)}"
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_context(
        self,
        pr: PrWebhookPayload,
        files: list[PrFileInfo],
    ) -> dict[str, Any]:
        categories = sorted({file.category for file in files if not file.skipped})
        file_summaries = [
            {
                "filename": file.filename,
                "status": file.status,
                "category": file.category,
                "additions": file.additions,
                "deletions": file.deletions,
                "skipped": file.skipped,
                "skip_reason": file.skip_reason,
            }
            for file in files
        ]
        patches = [
            {
                "filename": file.filename,
                "category": file.category,
                "patch": file.patch,
            }
            for file in files
            if file.patch and not file.skipped
        ]
        return {
            "metadata": {
                "owner": pr.owner,
                "repository": pr.repository,
                "pull_request_number": pr.pull_request_number,
                "title": pr.pull_request_title,
                "author": pr.pull_request_author,
                "base_branch": pr.base_branch,
                "head_branch": pr.head_branch,
                "commit_sha": pr.commit_sha,
                "action": pr.action,
            },
            "file_summaries": file_summaries,
            "categories": categories,
            "patches": patches,
        }
