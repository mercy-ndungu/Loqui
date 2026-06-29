"""User profile routes."""

import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import CurrentUser
from app.core.limiter import limiter
from app.models import ProfileUpdateRequest, UserMeResponse, UserProfileResponse
from app.services.profile_service import upsert_profile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMeResponse)
@limiter.limit("100/minute")
async def get_me(request: Request, current_user: CurrentUser) -> UserMeResponse:
    """
    Return the authenticated user's profile.

    Requires a valid JWT access token in an httpOnly cookie.
    """
    return current_user


@router.post("/profile", response_model=UserProfileResponse)
@limiter.limit("30/minute")
async def update_profile(
    request: Request,
    payload: ProfileUpdateRequest,
    current_user: CurrentUser,
) -> UserProfileResponse:
    """
    Create or update the authenticated user's coaching profile.

    Stores presentation goal and target audience in Supabase user_profiles.
    """
    profile = upsert_profile(
        user_id=current_user.id,
        presentation_goal=payload.presentation_goal,
        target_audience=payload.target_audience,
    )
    if not profile:
        logger.error("Profile update failed for user id=%s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile update failed",
        )

    logger.info("Profile updated for user id=%s", current_user.id)

    return UserProfileResponse(
        id=str(profile["id"]),
        user_id=str(profile["user_id"]),
        presentation_goal=profile["presentation_goal"],
        target_audience=profile["target_audience"],
        created_at=profile["created_at"],
        updated_at=profile.get("updated_at") or profile["created_at"],
    )
