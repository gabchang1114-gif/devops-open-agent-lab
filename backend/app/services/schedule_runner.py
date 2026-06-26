"""APScheduler runner for proactive Kubernetes investigations."""

from __future__ import annotations

import asyncio
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from app.db.models import InvestigationSchedule
from app.db.session import SessionLocal
from app.models.diagnosis import InvestigationRequest
from app.services.investigation_job_service import InvestigationJobService
from app.services.schedule_cron import compute_next_run
from app.services.schedule_service import ScheduleService


class InvestigationScheduleRunner:
    """Register cron jobs and trigger scheduled investigations."""

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.schedule_service = ScheduleService()
        self._job_service: InvestigationJobService | None = None

    def bind_job_service(self, job_service: InvestigationJobService) -> None:
        self._job_service = job_service

    async def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()
        await self.reload_all()
        logger.info("Investigation schedule runner started")

    async def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        logger.info("Investigation schedule runner stopped")

    async def reload_all(self) -> None:
        self.scheduler.remove_all_jobs()
        async with SessionLocal() as session:
            schedules = await self.schedule_service.list_enabled(session)
        for schedule in schedules:
            self.register_schedule(schedule)
        logger.info("Loaded {} enabled investigation schedule(s)", len(schedules))

    def register_schedule(self, schedule: InvestigationSchedule) -> None:
        job_id = str(schedule.id)
        trigger = CronTrigger.from_crontab(schedule.cron_expression, timezone=schedule.timezone)
        self.scheduler.add_job(
            self._run_scheduled_job,
            trigger=trigger,
            id=job_id,
            kwargs={"schedule_id": job_id},
            replace_existing=True,
            misfire_grace_time=300,
        )
        logger.info(
            "Registered schedule | id={} name={} cron={}",
            schedule.id,
            schedule.name,
            schedule.cron_expression,
        )

    def unregister_schedule(self, schedule_id: UUID) -> None:
        job_id = str(schedule_id)
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

    async def refresh_schedule(self, schedule_id: UUID) -> None:
        async with SessionLocal() as session:
            result = await session.get(InvestigationSchedule, schedule_id)
            if result is None or not result.enabled:
                self.unregister_schedule(schedule_id)
                return
            result.next_run_at = compute_next_run(result.cron_expression, result.timezone)
            await session.commit()
            self.register_schedule(result)

    async def _run_scheduled_job(self, schedule_id: str) -> None:
        if self._job_service is None:
            logger.error("Schedule runner missing job service | schedule_id={}", schedule_id)
            return

        async with SessionLocal() as session:
            schedule = await session.get(InvestigationSchedule, UUID(schedule_id))
            if schedule is None or not schedule.enabled:
                return

            request = InvestigationRequest(
                cluster_id=schedule.cluster_id,
                namespace=schedule.namespace,
                query=schedule.query,
                include_ai=schedule.include_ai,
                agent_type=schedule.agent_type,
            )

            try:
                investigation_id = await self._job_service.start_investigation(
                    request,
                    user_id=str(schedule.user_id),
                )
                asyncio.create_task(
                    self._job_service.run_investigation(investigation_id, request)
                )
                await self.schedule_service.mark_run(
                    session,
                    schedule.id,
                    investigation_id,
                    "started",
                )
                logger.info(
                    "Scheduled investigation started | schedule_id={} investigation_id={}",
                    schedule_id,
                    investigation_id,
                )
            except Exception as exc:
                logger.exception(
                    "Scheduled investigation failed | schedule_id={} error={}",
                    schedule_id,
                    exc,
                )
                await self.schedule_service.mark_run(
                    session,
                    schedule.id,
                    "",
                    "failed",
                )


schedule_runner = InvestigationScheduleRunner()
