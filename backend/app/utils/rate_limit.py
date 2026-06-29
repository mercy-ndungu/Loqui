"""Rate-limit key helpers."""

import jwt
from fastapi import Request
from slowapi.util import get_remote_address

from app.core.security import ACCESS_TOKEN_COOKIE, decode_token


def get_user_or_ip_key(request: Request) -> str:
    """Rate-limit by authenticated user id, falling back to client IP."""
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        return get_remote_address(request)

    try:
        payload = decode_token(token)
        if payload.get("type") == "access" and payload.get("sub"):
            return f"user:{payload['sub']}"
    except jwt.PyJWTError:
        pass

    return get_remote_address(request)
