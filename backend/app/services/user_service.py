"""User persistence operations via Supabase."""

import logging
from typing import Any

from app.db.database import get_supabase_client
from app.utils.supabase_errors import format_supabase_error

logger = logging.getLogger(__name__)


def get_user_by_email(email: str) -> dict[str, Any] | None:
    """Fetch a user record by email address."""
    try:
        client = get_supabase_client()
        response = client.table("users").select("*").eq("email", email).limit(1).execute()
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error("Failed to fetch user by email: %s", format_supabase_error(exc))
    return None


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    """Fetch a user record by primary key."""
    try:
        client = get_supabase_client()
        response = client.table("users").select("*").eq("id", user_id).limit(1).execute()
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error("Failed to fetch user by id=%s: %s", user_id, format_supabase_error(exc))
    return None


def create_user(email: str, password_hash: str, full_name: str) -> dict[str, Any] | None:
    """Insert a new user and return the created record."""
    try:
        client = get_supabase_client()
        payload = {
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name,
        }
        response = client.table("users").insert(payload).execute()
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error(
            "Failed to create user for email=%s: %s",
            email,
            format_supabase_error(exc),
        )
    return None
