"""PR Reviewer request/response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PrReviewFinding(BaseModel):
    severity: Literal["low", "medium", "high"]
    category: Literal[
        "security",
        "reliability",
        "scalability",
        "cost",
        "observability",
        "ci_cd",
        "kubernetes",
        "terraform",
        "docker",
        "cloud",
    ]
    file: str
    line_reference: str = ""
    issue: str
    why_it_matters: str
    recommendation: str
    example_fix: str = ""


class PrReviewAnalysis(BaseModel):
    summary: str
    overall_risk: Literal["low", "medium", "high"] = "low"
    should_block_merge: bool = False
    findings: list[PrReviewFinding] = Field(default_factory=list)
    positive_observations: list[str] = Field(default_factory=list)
    final_recommendation: Literal["approve", "comment", "request_changes"] = "comment"


class PrFileInfo(BaseModel):
    filename: str
    status: str
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    patch: str | None = None
    raw_url: str | None = None
    blob_url: str | None = None
    category: str = "unknown"
    skipped: bool = False
    skip_reason: str | None = None


class PrWebhookPayload(BaseModel):
    owner: str
    repository: str
    pull_request_number: int
    pull_request_title: str
    pull_request_body: str = ""
    pull_request_author: str
    base_branch: str
    head_branch: str
    commit_sha: str
    action: str
    changed_files_url: str | None = None


class ManualReviewRequest(BaseModel):
    owner: str
    repo: str
    pull_request_number: int


class ReviewStartResponse(BaseModel):
    review_id: str
    status: str
    message: str


class PrReviewHistoryItem(BaseModel):
    id: str
    owner: str
    repository: str
    pull_request_number: int
    pull_request_title: str | None = None
    overall_risk: str | None = None
    findings_count: int = 0
    final_recommendation: str | None = None
    status: str
    created_at: str
    commit_sha: str | None = None


class PrReviewHistoryResponse(BaseModel):
    reviews: list[PrReviewHistoryItem]


class PrReviewStatusResponse(BaseModel):
    review_id: str
    status: str
    current_step: str | None = None
    progress_percentage: int = 0
    error: str | None = None


class PrReviewDetailResponse(BaseModel):
    id: str
    owner: str
    repository: str
    pull_request_number: int
    pull_request_title: str | None = None
    pull_request_author: str | None = None
    base_branch: str | None = None
    head_branch: str | None = None
    commit_sha: str | None = None
    overall_risk: str | None = None
    findings_count: int = 0
    final_recommendation: str | None = None
    status: str
    current_step: str | None = None
    progress_percentage: int = 0
    review_markdown: str | None = None
    review: PrReviewAnalysis | None = None
    mcp_enrichment: dict | None = None
    github_comment_url: str | None = None
    error: str | None = None
    created_at: str
    updated_at: str | None = None
