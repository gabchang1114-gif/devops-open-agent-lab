"""GitHub webhook event handling."""

from __future__ import annotations

from typing import Any

from app.core.config import Settings, get_settings
from app.modules.pr_reviewer.github.github_client import GitHubClient
from app.modules.pr_reviewer.github.signature import (
    should_skip_signature_validation,
    verify_github_signature,
)
from app.modules.pr_reviewer.models.schemas import PrWebhookPayload


class WebhookValidationError(Exception):
    """Raised when webhook signature validation fails."""


class WebhookHandler:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.github_client = GitHubClient(self.settings)

    def validate_signature(self, body: bytes, signature_header: str | None) -> None:
        secret = self.settings.github_webhook_secret.strip()
        if should_skip_signature_validation(secret, self.settings.app_env):
            return
        if not verify_github_signature(body, signature_header, secret):
            raise WebhookValidationError("Invalid GitHub webhook signature")

    def parse_event(self, payload: dict[str, Any]) -> PrWebhookPayload | None:
        return GitHubClient.parse_webhook_payload(payload)
