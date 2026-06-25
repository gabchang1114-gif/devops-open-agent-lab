"""Slack delivery via incoming webhook or bot token."""

from __future__ import annotations

import httpx
from loguru import logger


class SlackDeliveryError(Exception):
    """Raised when Slack message delivery fails."""


class SlackClient:
    """Post messages to Slack using webhook URL or chat.postMessage."""

    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout

    async def post_webhook(self, webhook_url: str, payload: dict) -> None:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(webhook_url, json=payload)
            if response.status_code != 200:
                body = response.text[:200]
                raise SlackDeliveryError(
                    f"Slack webhook failed ({response.status_code}): {body}"
                )
            if response.text.strip() != "ok":
                raise SlackDeliveryError(f"Slack webhook unexpected response: {response.text[:200]}")

    async def post_channel_message(
        self,
        bot_token: str,
        channel: str,
        payload: dict,
    ) -> None:
        body = {
            "channel": channel,
            **payload,
        }
        headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers=headers,
                json=body,
            )
            data = response.json()
            if not data.get("ok"):
                error = data.get("error", "unknown_error")
                logger.warning("Slack chat.postMessage failed | error={}", error)
                raise SlackDeliveryError(f"Slack API error: {error}")
