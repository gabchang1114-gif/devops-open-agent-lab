"""PR Reviewer API routes."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from app.auth.dependencies import get_current_user
from app.core.config import get_settings
from app.core.errors import sanitize_error_message
from app.models.auth import UserResponse
from app.modules.pr_reviewer.github.webhook_handler import WebhookHandler, WebhookValidationError
from app.modules.pr_reviewer.models.schemas import (
    ManualReviewRequest,
    PrReviewDetailResponse,
    PrReviewHistoryItem,
    PrReviewHistoryResponse,
    PrReviewStatusResponse,
    ReviewStartResponse,
)
from app.modules.pr_reviewer.services.pr_review_service import PrReviewService
from app.storage.factory import get_pr_review_store

router = APIRouter(tags=["pr-reviewer"])
review_service = PrReviewService()
webhook_handler = WebhookHandler()


@router.post("/pr-reviewer/webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    try:
        webhook_handler.validate_signature(body, signature)
    except WebhookValidationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    try:
        payload: dict[str, Any] = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    event = request.headers.get("X-GitHub-Event", "")
    if event != "pull_request":
        return {"status": "ignored", "message": f"Unsupported event type: {event}"}

    pr_payload = webhook_handler.parse_event(payload)
    if pr_payload is None:
        return {"status": "ignored", "message": "Pull request action ignored"}

    review_id = await review_service.enqueue_review(
        pr_payload.owner,
        pr_payload.repository,
        pr_payload.pull_request_number,
        metadata=pr_payload,
    )
    background_tasks.add_task(
        review_service.process_review,
        review_id,
        pr_payload.owner,
        pr_payload.repository,
        pr_payload.pull_request_number,
        pr_payload,
    )
    return {"status": "accepted", "review_id": review_id}


@router.post("/pr-reviewer/review", response_model=ReviewStartResponse)
async def manual_review(
    request: ManualReviewRequest,
    background_tasks: BackgroundTasks,
    _current_user: UserResponse = Depends(get_current_user),
) -> ReviewStartResponse:
    settings = get_settings()
    if not settings.github_token.strip():
        raise HTTPException(status_code=400, detail="GitHub token is not configured")

    review_id = await review_service.enqueue_review(
        request.owner,
        request.repo,
        request.pull_request_number,
    )
    background_tasks.add_task(
        review_service.process_review,
        review_id,
        request.owner,
        request.repo,
        request.pull_request_number,
        None,
    )
    return ReviewStartResponse(
        review_id=review_id,
        status="queued",
        message="PR review started",
    )


@router.get("/pr-reviewer/history", response_model=PrReviewHistoryResponse)
async def list_review_history(
    limit: int = 50,
    _current_user: UserResponse = Depends(get_current_user),
) -> PrReviewHistoryResponse:
    store = get_pr_review_store()
    rows = await store.list_history(limit=limit)
    return PrReviewHistoryResponse(
        reviews=[PrReviewHistoryItem.model_validate(row) for row in rows]
    )


@router.get("/pr-reviewer/reviews/{review_id}", response_model=PrReviewDetailResponse)
async def get_review(
    review_id: str,
    _current_user: UserResponse = Depends(get_current_user),
) -> PrReviewDetailResponse:
    store = get_pr_review_store()
    row = await store.get(review_id)
    if not row:
        raise HTTPException(status_code=404, detail="Review not found")
    return PrReviewDetailResponse.model_validate(row)


@router.get("/pr-reviewer/reviews/{review_id}/status", response_model=PrReviewStatusResponse)
async def get_review_status(
    review_id: str,
    _current_user: UserResponse = Depends(get_current_user),
) -> PrReviewStatusResponse:
    store = get_pr_review_store()
    row = await store.get(review_id)
    if not row:
        raise HTTPException(status_code=404, detail="Review not found")
    return PrReviewStatusResponse(
        review_id=review_id,
        status=row.get("status", "unknown"),
        current_step=row.get("current_step"),
        progress_percentage=int(row.get("progress_percentage", 0)),
        error=row.get("error"),
    )
