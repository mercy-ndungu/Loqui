"""Feedback persistence operations."""

import logging
from typing import Any

from app.db.database import get_supabase_client
from app.utils.supabase_errors import format_supabase_error

logger = logging.getLogger(__name__)


def create_feedback_record(
    *,
    recording_id: str | None = None,
    challenge_id: str | None = None,
    feedback_json: dict[str, Any],
) -> dict[str, Any] | None:
    """Insert a feedback row linked to a recording or challenge."""
    if not recording_id and not challenge_id:
        logger.error("Feedback requires recording_id or challenge_id")
        return None
    try:
        client = get_supabase_client()
        payload: dict[str, Any] = {"feedback_json": feedback_json}
        if recording_id:
            payload["recording_id"] = recording_id
        if challenge_id:
            payload["challenge_id"] = challenge_id
        response = client.table("feedback").insert(payload).execute()
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error(
            "Failed to store feedback recording_id=%s challenge_id=%s: %s",
            recording_id,
            challenge_id,
            format_supabase_error(exc),
        )
    return None


def get_feedback_by_recording_id(recording_id: str) -> dict[str, Any] | None:
    """Fetch the most recent feedback row for a recording."""
    try:
        client = get_supabase_client()
        response = (
            client.table("feedback")
            .select("*")
            .eq("recording_id", recording_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error(
            "Failed to fetch feedback for recording_id=%s: %s",
            recording_id,
            format_supabase_error(exc),
        )
    return None


def get_feedback_by_challenge_id(challenge_id: str) -> dict[str, Any] | None:
    """Fetch the most recent feedback row for a challenge."""
    try:
        client = get_supabase_client()
        response = (
            client.table("feedback")
            .select("*")
            .eq("challenge_id", challenge_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error(
            "Failed to fetch feedback for challenge_id=%s: %s",
            challenge_id,
            format_supabase_error(exc),
        )
    return None
