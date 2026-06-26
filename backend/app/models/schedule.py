"""Investigation schedule request/response models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

ScheduleKind = Literal["hourly", "daily", "weekly", "custom"]


class InvestigationScheduleBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    cluster_id: str = Field(min_length=1, max_length=255)
    namespace: str | None = Field(default=None, max_length=255)
    query: str | None = Field(default=None, max_length=2000)
    include_ai: bool = True
    schedule_kind: ScheduleKind = "daily"
    hour: int = Field(default=8, ge=0, le=23)
    minute: int = Field(default=0, ge=0, le=59)
    day_of_week: int = Field(default=1, ge=0, le=6, description="0=Sunday … 6=Saturday")
    cron_expression: str | None = Field(
        default=None,
        description="Required when schedule_kind is custom (5-field cron).",
    )
    timezone: str = "UTC"
    enabled: bool = True

    @field_validator("name", "cluster_id")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Value cannot be empty")
        return cleaned


class InvestigationScheduleCreate(InvestigationScheduleBase):
    pass


class InvestigationScheduleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    cluster_id: str | None = Field(default=None, min_length=1, max_length=255)
    namespace: str | None = None
    query: str | None = None
    include_ai: bool | None = None
    schedule_kind: ScheduleKind | None = None
    hour: int | None = Field(default=None, ge=0, le=23)
    minute: int | None = Field(default=None, ge=0, le=59)
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    cron_expression: str | None = None
    timezone: str | None = None
    enabled: bool | None = None


class InvestigationScheduleResponse(BaseModel):
    id: UUID
    agent_type: str
    name: str
    cluster_id: str
    namespace: str | None
    query: str | None
    include_ai: bool
    schedule_kind: ScheduleKind
    hour: int
    minute: int
    day_of_week: int
    cron_expression: str
    timezone: str
    enabled: bool
    last_run_at: datetime | None
    last_investigation_id: str | None
    last_status: str | None
    next_run_at: datetime | None
    created_at: datetime
    updated_at: datetime


class InvestigationScheduleListResponse(BaseModel):
    schedules: list[InvestigationScheduleResponse]
