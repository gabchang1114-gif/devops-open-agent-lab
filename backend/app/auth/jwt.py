"""JWT token helpers."""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import Settings, get_settings


def create_access_token(
    subject: str,
    settings: Settings | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    config = settings or get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=config.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)


def decode_access_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    config = settings or get_settings()
    return jwt.decode(token, config.jwt_secret, algorithms=[config.jwt_algorithm])


def get_subject_from_token(token: str, settings: Settings | None = None) -> str | None:
    try:
        payload = decode_access_token(token, settings=settings)
        subject = payload.get("sub")
        return str(subject) if subject else None
    except JWTError:
        return None
