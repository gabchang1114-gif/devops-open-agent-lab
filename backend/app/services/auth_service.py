"""User registration and authentication service."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.auth.passwords import hash_password, verify_password
from app.db.models import User
from app.models.auth import AuthTokenResponse, LoginRequest, SignUpRequest, UserResponse


class AuthService:
    async def sign_up(self, session: AsyncSession, request: SignUpRequest) -> AuthTokenResponse:
        user = User(
            email=request.email.lower().strip(),
            password_hash=hash_password(request.password),
        )
        session.add(user)
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this username already exists.",
            ) from exc

        await session.refresh(user)
        return self._build_auth_response(user)

    async def login(self, session: AsyncSession, request: LoginRequest) -> AuthTokenResponse:
        result = await session.execute(
            select(User).where(User.email == request.email.lower().strip())
        )
        user = result.scalar_one_or_none()
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )
        return self._build_auth_response(user)

    async def get_user_by_id(self, session: AsyncSession, user_id: UUID) -> User | None:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    def _build_auth_response(self, user: User) -> AuthTokenResponse:
        token = create_access_token(str(user.id))
        return AuthTokenResponse(
            access_token=token,
            user=UserResponse(
                id=user.id,
                email=user.email,
                created_at=user.created_at,
            ),
        )
