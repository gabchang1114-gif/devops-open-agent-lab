"""Authentication dependencies for protected routes."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import get_subject_from_token
from app.db.session import get_db_session
from app.models.auth import UserResponse
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)
auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    subject = get_subject_from_token(credentials.credentials)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(subject)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc

    user = await auth_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
    )
