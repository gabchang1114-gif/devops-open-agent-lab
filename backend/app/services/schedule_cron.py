"""Build and validate cron expressions for investigation schedules."""

from __future__ import annotations

from datetime import datetime, timezone

from apscheduler.triggers.cron import CronTrigger

from app.models.schedule import ScheduleKind


def build_cron_expression(
    schedule_kind: ScheduleKind,
    *,
    hour: int = 8,
    minute: int = 0,
    day_of_week: int = 1,
    cron_expression: str | None = None,
) -> str:
    if schedule_kind == "hourly":
        return f"{minute} * * * *"
    if schedule_kind == "daily":
        return f"{minute} {hour} * * *"
    if schedule_kind == "weekly":
        return f"{minute} {hour} * * {day_of_week}"
    if schedule_kind == "custom":
        if not cron_expression or not cron_expression.strip():
            raise ValueError("cron_expression is required for custom schedules")
        return cron_expression.strip()
    raise ValueError(f"Unsupported schedule kind: {schedule_kind}")


def validate_cron_expression(cron_expression: str, timezone: str = "UTC") -> None:
    try:
        CronTrigger.from_crontab(cron_expression, timezone=timezone)
    except Exception as exc:
        raise ValueError(f"Invalid cron expression: {exc}") from exc


def compute_next_run(cron_expression: str, tz: str = "UTC"):
    trigger = CronTrigger.from_crontab(cron_expression, timezone=tz)
    return trigger.get_next_fire_time(None, datetime.now(timezone.utc))
