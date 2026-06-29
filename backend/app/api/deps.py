"""Shared FastAPI dependencies."""

import logging
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status

from app.core.security import ACCESS_TOKEN_COOKIE, decode_token
from app.models import UserMeResponse
from app.services.user_service import get_user_by_id

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> UserMeResponse:
    """
    Extract and validate the JWT access token from cookies.

    Returns the authenticated user's profile or raises 401.
    """
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    try:
        payload = decode_token(token)
    except jwt.PyJWTError as exc:
        logger.warning("Invalid access token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        ) from exc

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    user = get_user_by_id(str(user_id))
    if not user:
        logger.warning("Access token references missing user id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    return UserMeResponse(
        id=str(user["id"]),
        email=user["email"],
        full_name=user["full_name"],
        created_at=user["created_at"],
    )


async def get_optional_user(request: Request) -> UserMeResponse | None:
    """Return the authenticated user when a valid session cookie is present."""
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        return None
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


CurrentUser = Annotated[UserMeResponse, Depends(get_current_user)]
OptionalUser = Annotated[UserMeResponse | None, Depends(get_optional_user)]
