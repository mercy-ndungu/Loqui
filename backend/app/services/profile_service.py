"""User profile persistence operations via Supabase."""

import logging
from typing import Any

from app.db.database import get_supabase_client
from app.utils.supabase_errors import format_supabase_error

logger = logging.getLogger(__name__)


def get_profile_by_user_id(user_id: str) -> dict[str, Any] | None:
    """Fetch a coaching profile for the given user."""
    try:
        client = get_supabase_client()
        response = (
            client.table("user_profiles")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error(
            "Failed to fetch profile for user_id=%s: %s",
            user_id,
            format_supabase_error(exc),
        )
    return None


def upsert_profile(
    user_id: str,
    presentation_goal: str,
    target_audience: str,
) -> dict[str, Any] | None:
    """Create or update a user's coaching profile."""
    try:
        client = get_supabase_client()
        payload = {
            "user_id": user_id,
            "presentation_goal": presentation_goal,
            "target_audience": target_audience,
        }
        response = (
            client.table("user_profiles")
            .upsert(payload, on_conflict="user_id")
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error(
            "Failed to upsert profile for user_id=%s: %s",
            user_id,
            format_supabase_error(exc),
        )
    return None
