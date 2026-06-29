"""Authentication request and response schemas."""

import re
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    """Payload for user registration."""

    email: EmailStr
    password: Annotated[str, Field(min_length=8)]
    full_name: Annotated[str, Field(min_length=1)]

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        """Ensure full_name is not blank."""
        if not value.strip():
            raise ValueError("full_name must not be empty")
        return value.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Enforce password complexity rules."""
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must include at least one uppercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must include at least one number")
        return value


class LoginRequest(BaseModel):
    """Payload for user login."""

    email: EmailStr
    password: str


class UserPublic(BaseModel):
    """Public user fields returned to clients."""

    id: str
    email: EmailStr
    full_name: str | None = None


class LoginUserPublic(BaseModel):
    """User fields returned after login."""

    id: str
    email: EmailStr


class SignupResponse(BaseModel):
    """Successful signup response."""

    message: str
    user: UserPublic


class LoginResponse(BaseModel):
    """Successful login response."""

    message: str
    user: LoginUserPublic


class LogoutResponse(BaseModel):
    """Successful logout response."""

    message: str


class CsrfResponse(BaseModel):
    """CSRF token for double-submit cookie protection."""

    csrf_token: str


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
