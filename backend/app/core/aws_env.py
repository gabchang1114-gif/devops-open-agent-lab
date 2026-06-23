"""Normalize AWS environment variables for boto3 inside Docker."""

from __future__ import annotations

import os

from loguru import logger


def sanitize_aws_environment() -> None:
    """Remove blank AWS_PROFILE values injected by empty .env entries."""
    profile = os.environ.get("AWS_PROFILE")
    if profile is not None and not profile.strip():
        os.environ.pop("AWS_PROFILE", None)
        logger.info("Removed empty AWS_PROFILE from environment")
