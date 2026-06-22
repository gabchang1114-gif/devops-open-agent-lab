"""GitHub webhook signature validation."""

from __future__ import annotations

import hashlib
import hmac

from loguru import logger


def verify_github_signature(
    payload_body: bytes,
    signature_header: str | None,
    secret: str,
) -> bool:
    if not signature_header:
        return False
    if not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        secret.encode("utf-8"),
        payload_body,
        hashlib.sha256,
    ).hexdigest()
    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)


def should_skip_signature_validation(secret: str, app_env: str) -> bool:
    if secret:
        return False
    if app_env.lower() == "production":
        return False
    logger.warning(
        "GITHUB_WEBHOOK_SECRET is not configured; accepting unsigned webhook in development"
    )
    return True
