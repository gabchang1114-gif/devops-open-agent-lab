"""Authentication request/response models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SignUpRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255, description="Username")
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255, description="Username")
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: UUID
    email: str
    created_at: datetime


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
