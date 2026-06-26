"""CRUD for proactive investigation schedules."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import InvestigationSchedule
from app.models.schedule import (
    InvestigationScheduleCreate,
    InvestigationScheduleResponse,
    InvestigationScheduleUpdate,
    ScheduleKind,
)
from app.services.schedule_cron import build_cron_expression, compute_next_run, validate_cron_expression


def _to_response(row: InvestigationSchedule) -> InvestigationScheduleResponse:
    return InvestigationScheduleResponse(
        id=row.id,
        agent_type=row.agent_type,
        name=row.name,
        cluster_id=row.cluster_id,
        namespace=row.namespace,
        query=row.query,
        include_ai=row.include_ai,
        schedule_kind=row.schedule_kind,  # type: ignore[arg-type]
        hour=row.hour,
        minute=row.minute,
        day_of_week=row.day_of_week,
        cron_expression=row.cron_expression,
        timezone=row.timezone,
        enabled=row.enabled,
        last_run_at=row.last_run_at,
        last_investigation_id=row.last_investigation_id,
        last_status=row.last_status,
        next_run_at=row.next_run_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class ScheduleService:
    async def list_for_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        agent_type: str = "kubernetes",
    ) -> list[InvestigationScheduleResponse]:
        result = await session.execute(
            select(InvestigationSchedule)
            .where(
                InvestigationSchedule.user_id == user_id,
                InvestigationSchedule.agent_type == agent_type,
            )
            .order_by(InvestigationSchedule.created_at.desc())
        )
        return [_to_response(row) for row in result.scalars().all()]

    async def get_for_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        schedule_id: UUID,
    ) -> InvestigationSchedule | None:
        result = await session.execute(
            select(InvestigationSchedule).where(
                InvestigationSchedule.id == schedule_id,
                InvestigationSchedule.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_enabled(
        self,
        session: AsyncSession,
        agent_type: str = "kubernetes",
    ) -> list[InvestigationSchedule]:
        result = await session.execute(
            select(InvestigationSchedule).where(
                InvestigationSchedule.enabled.is_(True),
                InvestigationSchedule.agent_type == agent_type,
            )
        )
        return list(result.scalars().all())

    async def create(
        self,
        session: AsyncSession,
        user_id: UUID,
        payload: InvestigationScheduleCreate,
        agent_type: str = "kubernetes",
    ) -> InvestigationScheduleResponse:
        cron = build_cron_expression(
            payload.schedule_kind,
            hour=payload.hour,
            minute=payload.minute,
            day_of_week=payload.day_of_week,
            cron_expression=payload.cron_expression,
        )
        validate_cron_expression(cron, payload.timezone)
        next_run = compute_next_run(cron, payload.timezone)

        row = InvestigationSchedule(
            user_id=user_id,
            agent_type=agent_type,
            name=payload.name.strip(),
            cluster_id=payload.cluster_id.strip(),
            namespace=payload.namespace.strip() if payload.namespace else None,
            query=payload.query.strip() if payload.query else None,
            include_ai=payload.include_ai,
            schedule_kind=payload.schedule_kind,
            hour=payload.hour,
            minute=payload.minute,
            day_of_week=payload.day_of_week,
            cron_expression=cron,
            timezone=payload.timezone,
            enabled=payload.enabled,
            next_run_at=next_run,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return _to_response(row)

    async def update(
        self,
        session: AsyncSession,
        user_id: UUID,
        schedule_id: UUID,
        payload: InvestigationScheduleUpdate,
    ) -> InvestigationScheduleResponse | None:
        row = await self.get_for_user(session, user_id, schedule_id)
        if row is None:
            return None

        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            if key in {"name", "cluster_id"} and isinstance(value, str):
                value = value.strip()
            if key == "namespace" and isinstance(value, str):
                value = value.strip() or None
            if key == "query" and isinstance(value, str):
                value = value.strip() or None
            setattr(row, key, value)

        schedule_kind: ScheduleKind = row.schedule_kind  # type: ignore[assignment]
        cron = build_cron_expression(
            schedule_kind,
            hour=row.hour,
            minute=row.minute,
            day_of_week=row.day_of_week,
            cron_expression=row.cron_expression if schedule_kind == "custom" else None,
        )
        validate_cron_expression(cron, row.timezone)
        row.cron_expression = cron
        row.next_run_at = compute_next_run(cron, row.timezone)

        await session.commit()
        await session.refresh(row)
        return _to_response(row)

    async def delete(
        self,
        session: AsyncSession,
        user_id: UUID,
        schedule_id: UUID,
    ) -> bool:
        row = await self.get_for_user(session, user_id, schedule_id)
        if row is None:
            return False
        await session.delete(row)
        await session.commit()
        return True

    async def mark_run(
        self,
        session: AsyncSession,
        schedule_id: UUID,
        investigation_id: str,
        status: str,
    ) -> None:
        result = await session.execute(
            select(InvestigationSchedule).where(InvestigationSchedule.id == schedule_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return
        now = datetime.now(timezone.utc)
        row.last_run_at = now
        row.last_investigation_id = investigation_id
        row.last_status = status
        row.next_run_at = compute_next_run(row.cron_expression, row.timezone)
        await session.commit()
