"""Recording storage and database operations."""

import logging
import time
from typing import Any

from app.db.database import get_supabase_client
from app.services.presentation_service import get_presentation_by_id
from app.utils.supabase_errors import format_supabase_error
from app.utils.video_validation import build_recording_storage_path

logger = logging.getLogger(__name__)

BUCKET_NAME = "recordings"
SIGNED_URL_EXPIRY_SECONDS = 3600


def _storage():
    """Return the Supabase Storage bucket client for recordings."""
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
    """Generate a time-limited signed URL for a stored recording."""
    try:
        result = _storage().create_signed_url(storage_path, SIGNED_URL_EXPIRY_SECONDS)
        return result.get("signedURL") or result.get("signedUrl")
    except Exception as exc:
        logger.error(
            "Failed to create signed URL for recording: %s",
            format_supabase_error(exc),
        )
    return None


def upload_video(
    *,
    user_id: str,
    presentation_id: str,
    filename: str,
    content: bytes,
    mime_type: str,
) -> str | None:
    """Upload a recording video and return its storage path."""
    storage_path = build_recording_storage_path(
        user_id,
        presentation_id,
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
        logger.error(
            "Recording storage upload failed for user_id=%s: %s",
            user_id,
            format_supabase_error(exc),
        )
    return None


def delete_storage_file(storage_path: str) -> bool:
    """Remove a recording video from Supabase Storage."""
    try:
        _storage().remove([storage_path])
        return True
    except Exception as exc:
        logger.error(
            "Recording storage delete failed: %s",
            format_supabase_error(exc),
        )
    return False


def create_recording_record(
    *,
    presentation_id: str,
    storage_path: str,
    duration_seconds: int,
    transcription_encrypted: str,
) -> dict[str, Any] | None:
    """Insert a recording row and return the created record."""
    try:
        client = get_supabase_client()
        payload = {
            "presentation_id": presentation_id,
            "storage_path": storage_path,
            "video_url": storage_path,
            "duration_seconds": duration_seconds,
            "transcription_encrypted": transcription_encrypted,
        }
        response = client.table("recordings").insert(payload).execute()
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error(
            "Failed to create recording for presentation_id=%s: %s",
            presentation_id,
            format_supabase_error(exc),
        )
    return None


def get_recording_by_id(recording_id: str) -> dict[str, Any] | None:
    """Fetch a recording by primary key."""
    try:
        client = get_supabase_client()
        response = (
            client.table("recordings")
            .select("*")
            .eq("id", recording_id)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error(
            "Failed to fetch recording id=%s: %s",
            recording_id,
            format_supabase_error(exc),
        )
    return None


def delete_recording_record(recording_id: str) -> bool:
    """Delete a recording row (feedback cascades via FK)."""
    try:
        client = get_supabase_client()
        response = (
            client.table("recordings")
            .delete()
            .eq("id", recording_id)
            .execute()
        )
        return bool(response.data)
    except Exception as exc:
        logger.error(
            "Failed to delete recording id=%s: %s",
            recording_id,
            format_supabase_error(exc),
        )
    return False


def user_owns_recording(recording: dict[str, Any], user_id: str) -> bool:
    """Return True when the user owns the presentation linked to the recording."""
    presentation = get_presentation_by_id(str(recording["presentation_id"]))
    if not presentation:
        return False
    return str(presentation["user_id"]) == user_id


def user_owns_presentation(presentation_id: str, user_id: str) -> bool:
    """Return True when the presentation belongs to the user."""
    presentation = get_presentation_by_id(presentation_id)
    if not presentation:
        return False
    return str(presentation["user_id"]) == user_id
