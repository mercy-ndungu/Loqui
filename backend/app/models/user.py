"""User profile request and response schemas."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserMeResponse(BaseModel):
    """Authenticated user profile returned by GET /users/me."""

    id: str
    email: EmailStr
    full_name: str
    created_at: datetime


class ProfileUpdateRequest(BaseModel):
    """Payload for updating a user's coaching profile."""

    presentation_goal: Annotated[str, Field(min_length=1, max_length=500)]
    target_audience: Annotated[str, Field(min_length=1, max_length=500)]

    @field_validator("presentation_goal", "target_audience")
    @classmethod
    def validate_not_blank(cls, value: str) -> str:
        """Ensure profile fields are not blank."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field must not be empty")
        return stripped


class UserProfileResponse(BaseModel):
    """User coaching profile returned to clients."""

    id: str
    user_id: str
    presentation_goal: str
    target_audience: str
    created_at: datetime
    updated_at: datetime
