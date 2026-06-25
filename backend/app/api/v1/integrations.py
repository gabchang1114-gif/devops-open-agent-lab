"""Integration API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db_session
from app.integrations.slack.client import SlackDeliveryError
from app.models.auth import UserResponse
from app.models.slack_integration import (
    SlackIntegrationResponse,
    SlackIntegrationSettings,
    SlackTestResponse,
)
from app.notifications.slack_notification_service import slack_notification_service
from app.services.slack_settings_service import SlackSettingsService

router = APIRouter(tags=["integrations"])
slack_settings_service = SlackSettingsService()


@router.get("/integrations/slack", response_model=SlackIntegrationResponse)
async def get_slack_integration(
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SlackIntegrationResponse:
    return await slack_settings_service.get_settings(session, current_user.id)


@router.put("/integrations/slack", response_model=SlackIntegrationResponse)
async def update_slack_integration(
    payload: SlackIntegrationSettings,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SlackIntegrationResponse:
    if payload.enabled:
        if payload.delivery_method == "webhook":
            existing = await slack_settings_service.get_settings(session, current_user.id)
            has_webhook = bool(payload.webhook_url and payload.webhook_url.strip())
            if not has_webhook and not existing.webhook_url_configured:
                if not existing.instance_webhook_configured:
                    raise HTTPException(
                        status_code=400,
                        detail="Webhook URL is required when using webhook delivery.",
                    )
        elif payload.delivery_method == "channel":
            if not payload.channel.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Slack channel is required when using channel delivery.",
                )
            existing = await slack_settings_service.get_settings(session, current_user.id)
            if not existing.instance_bot_configured:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "SLACK_BOT_TOKEN must be configured on the server "
                        "for channel delivery."
                    ),
                )

    return await slack_settings_service.upsert_settings(session, current_user.id, payload)


@router.post("/integrations/slack/test", response_model=SlackTestResponse)
async def test_slack_integration(
    current_user: UserResponse = Depends(get_current_user),
) -> SlackTestResponse:
    try:
        await slack_notification_service.send_test_message(current_user.id)
    except SlackDeliveryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SlackTestResponse(
        status="sent",
        message="Test message delivered to your configured Slack destination.",
    )
