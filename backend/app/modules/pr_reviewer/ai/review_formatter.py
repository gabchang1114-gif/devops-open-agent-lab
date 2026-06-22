"""Format structured PR review JSON as GitHub Markdown."""

from __future__ import annotations

from app.modules.pr_reviewer.models.schemas import PrReviewAnalysis


def format_review_markdown(analysis: PrReviewAnalysis) -> str:
    risk = analysis.overall_risk.capitalize()
    lines = [
        "## DevOps PR Review",
        "",
        "### Summary",
        "",
        analysis.summary.strip(),
        "",
        "### Overall Risk",
        "",
        risk,
        "",
    ]

    if analysis.findings:
        lines.extend(["### Findings", ""])
        for index, finding in enumerate(analysis.findings, start=1):
            severity = finding.severity.capitalize()
            category = finding.category.replace("_", " ").title()
            lines.extend(
                [
                    f"#### {index}. [{severity}] {category}",
                    "",
                    f"File: `{finding.file}`",
                    "",
                    "Issue:",
                    finding.issue.strip(),
                    "",
                    "Why it matters:",
                    finding.why_it_matters.strip(),
                    "",
                    "Recommendation:",
                    finding.recommendation.strip(),
                    "",
                ]
            )
            if finding.example_fix.strip():
                lines.extend(
                    [
                        "Example fix:",
                        finding.example_fix.strip(),
                        "",
                    ]
                )
    else:
        lines.extend(["### Findings", "", "No DevOps issues identified in the changed files.", ""])

    if analysis.positive_observations:
        lines.extend(["### Positive Observations", ""])
        for item in analysis.positive_observations:
            lines.append(f"- {item.strip()}")
        lines.append("")

    recommendation = analysis.final_recommendation.replace("_", " ").title()
    lines.extend(
        [
            "### Final Recommendation",
            "",
            recommendation,
        ]
    )
    return "\n".join(lines)
