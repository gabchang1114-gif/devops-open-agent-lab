"""Database seed helpers."""

from loguru import logger
from sqlalchemy import select

from app.auth.passwords import hash_password
from app.core.config import Settings, get_settings
from app.db.models import User
from app.db.session import SessionLocal


async def seed_default_admin(settings: Settings | None = None) -> None:
    """Ensure a default admin account exists for initial login."""
    config = settings or get_settings()
    if not config.seed_default_admin:
        return

    email = config.default_admin_email.lower().strip()
    if not email or not config.default_admin_password:
        logger.warning(
            "Default admin seed skipped | set DEFAULT_ADMIN_EMAIL (username) and DEFAULT_ADMIN_PASSWORD in backend/.env"
        )
        return

    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()
        if existing:
            logger.info("Default admin account already exists | email={}", email)
            return

        session.add(
            User(
                email=email,
                password_hash=hash_password(config.default_admin_password),
            )
        )
        await session.commit()
        logger.info("Default admin account created | email={}", email)
