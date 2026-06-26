"""Kubernetes proactive investigation schedule API."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.auth import UserResponse
from app.models.schedule import (
    InvestigationScheduleCreate,
    InvestigationScheduleListResponse,
    InvestigationScheduleResponse,
    InvestigationScheduleUpdate,
)
from app.services.schedule_runner import schedule_runner
from app.services.schedule_service import ScheduleService

router = APIRouter(tags=["kubernetes-schedules"])
schedule_service = ScheduleService()


@router.get("/kubernetes/schedules", response_model=InvestigationScheduleListResponse)
async def list_schedules(
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> InvestigationScheduleListResponse:
    schedules = await schedule_service.list_for_user(session, current_user.id)
    return InvestigationScheduleListResponse(schedules=schedules)


@router.post("/kubernetes/schedules", response_model=InvestigationScheduleResponse)
async def create_schedule(
    payload: InvestigationScheduleCreate,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> InvestigationScheduleResponse:
    try:
        created = await schedule_service.create(session, current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if created.enabled:
        await schedule_runner.refresh_schedule(created.id)
    return created


@router.put(
    "/kubernetes/schedules/{schedule_id}",
    response_model=InvestigationScheduleResponse,
)
async def update_schedule(
    schedule_id: UUID,
    payload: InvestigationScheduleUpdate,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> InvestigationScheduleResponse:
    try:
        updated = await schedule_service.update(session, current_user.id, schedule_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await schedule_runner.refresh_schedule(schedule_id)
    return updated


@router.delete("/kubernetes/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    deleted = await schedule_service.delete(session, current_user.id, schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Schedule not found")
    schedule_runner.unregister_schedule(schedule_id)
    return {"status": "deleted"}
