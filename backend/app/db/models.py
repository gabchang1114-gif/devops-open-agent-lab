"""SQLAlchemy models for authentication and integrations."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class UserSlackIntegration(Base):
    __tablename__ = "user_slack_integrations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    delivery_method: Mapped[str] = mapped_column(String(32), nullable=False, default="webhook")
    webhook_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    channel: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notify_kubernetes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_aws: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_cloud_cost: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notify_pr_reviewer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
