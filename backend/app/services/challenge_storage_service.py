"""Challenge storage and database operations."""

import logging
import time
from datetime import datetime, timezone
from typing import Any

from app.db.database import get_supabase_client
from app.utils.supabase_errors import format_supabase_error
from app.utils.video_validation import build_challenge_storage_path

logger = logging.getLogger(__name__)

BUCKET_NAME = "recordings"
SIGNED_URL_EXPIRY_SECONDS = 3600


def _storage():
    return get_supabase_client().storage.from_(BUCKET_NAME)


def bucket_accessible() -> bool:
    """Return True when the recordings storage bucket can be reached."""
    try:
        _storage().list("", {"limit": 1})
        return True
    except Exception as exc:
        logger.error("Recordings bucket check failed: %s", format_supabase_error(exc))
        return False


def create_signed_url(storage_path: str) -> str | None:
    try:
        result = _storage().create_signed_url(storage_path, SIGNED_URL_EXPIRY_SECONDS)
        return result.get("signedURL") or result.get("signedUrl")
    except Exception as exc:
        logger.error(
            "Failed to create signed URL for challenge video: %s",
            format_supabase_error(exc),
        )
    return None


def upload_video(
    *,
    user_id: str,
    challenge_id: str,
    filename: str,
    content: bytes,
    mime_type: str,
) -> str | None:
    """Upload a challenge recording video and return its storage path."""
    storage_path = build_challenge_storage_path(
        user_id,
        challenge_id,
        filename,
        int(time.time() * 1000),
    )
    try:
        _storage().upload(
            storage_path,
            content,
            file_options={"content-type": mime_type, "upsert": "false"},
        )
        return storage_path
    except Exception as exc:
        error = format_supabase_error(exc)
        logger.error(
            "Challenge video upload failed user_id=%s challenge_id=%s: %s",
            user_id,
            challenge_id,
            error,
        )
        if "bucket" in error.lower() or "not found" in error.lower():
            logger.error(
                "Ensure the private Supabase Storage bucket '%s' exists.",
                BUCKET_NAME,
            )
    return None


def delete_storage_file(storage_path: str) -> bool:
    try:
        _storage().remove([storage_path])
        return True
    except Exception as exc:
        logger.error("Challenge storage delete failed: %s", format_supabase_error(exc))
    return False


def create_challenge_record(
    *,
    user_id: str | None,
    challenge_type: str,
    title: str,
    topic_or_images: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Insert a pending challenge row before the user records."""
    try:
        client = get_supabase_client()
        payload: dict[str, Any] = {
            "challenge_type": challenge_type,
            "title": title,
            "topic_or_images": topic_or_images,
            "metadata": metadata or {},
        }
        if user_id is not None:
            payload["user_id"] = user_id
        response = client.table("challenges").insert(payload).execute()
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error(
            "Failed to create challenge user_id=%s: %s",
            user_id,
            format_supabase_error(exc),
        )
    return None


def assign_challenge_user(challenge_id: str, user_id: str) -> bool:
    """Claim an anonymous pending challenge for an authenticated user."""
    try:
        client = get_supabase_client()
        response = (
            client.table("challenges")
            .update({"user_id": user_id})
            .eq("id", challenge_id)
            .is_("user_id", "null")
            .execute()
        )
        return bool(response.data)
    except Exception as exc:
        logger.error(
            "Failed to assign challenge id=%s to user_id=%s: %s",
            challenge_id,
            user_id,
            format_supabase_error(exc),
        )
    return False


def get_challenge_by_id(challenge_id: str) -> dict[str, Any] | None:
    try:
        client = get_supabase_client()
        response = (
            client.table("challenges")
            .select("*")
            .eq("id", challenge_id)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error(
            "Failed to fetch challenge id=%s: %s",
            challenge_id,
            format_supabase_error(exc),
        )
    return None


def update_challenge_after_upload(
    *,
    challenge_id: str,
    storage_path: str,
    duration_seconds: int,
    transcription_encrypted: str,
) -> dict[str, Any] | None:
    """Mark a challenge complete with video and transcription."""
    try:
        client = get_supabase_client()
        payload = {
            "storage_path": storage_path,
            "video_url": storage_path,
            "duration_seconds": duration_seconds,
            "transcription_encrypted": transcription_encrypted,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        response = (
            client.table("challenges")
            .update(payload)
            .eq("id", challenge_id)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error(
            "Failed to update challenge id=%s: %s",
            challenge_id,
            format_supabase_error(exc),
        )
    return None


def list_completed_challenges(user_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """Return recent completed challenges for a user."""
    try:
        client = get_supabase_client()
        response = (
            client.table("challenges")
            .select("*")
            .eq("user_id", user_id)
            .not_.is_("completed_at", "null")
            .order("completed_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as exc:
        logger.error(
            "Failed to list challenges for user_id=%s: %s",
            user_id,
            format_supabase_error(exc),
        )
    return []


def user_can_submit_challenge(challenge: dict[str, Any], user_id: str) -> bool:
    """Allow upload when the user owns the challenge or it is an unclaimed session."""
    owner = challenge.get("user_id")
    if owner is None:
        return True
    return str(owner) == user_id


def user_owns_challenge(challenge: dict[str, Any], user_id: str) -> bool:
    return str(challenge.get("user_id")) == user_id
