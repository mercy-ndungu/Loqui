"""Presentation storage and database operations."""

import logging
import time
from typing import Any

from app.db.database import get_supabase_client
from app.utils.file_validation import build_storage_path, title_from_filename
from app.utils.supabase_errors import format_supabase_error

logger = logging.getLogger(__name__)

BUCKET_NAME = "presentations"
SIGNED_URL_EXPIRY_SECONDS = 3600
DECK_TYPES = frozenset({"pitch", "interview", "networking", "general"})
CHALLENGE_TYPES = frozenset({"improv", "random_topic"})


def _storage():
    """Return the Supabase Storage bucket client."""
    return get_supabase_client().storage.from_(BUCKET_NAME)


def create_signed_url(storage_path: str) -> str | None:
    """Generate a time-limited signed URL for a stored presentation file."""
    try:
        result = _storage().create_signed_url(storage_path, SIGNED_URL_EXPIRY_SECONDS)
        return result.get("signedURL") or result.get("signedUrl")
    except Exception as exc:
        logger.error(
            "Failed to create signed URL for path=%s: %s",
            storage_path,
            format_supabase_error(exc),
        )
    return None


def upload_file(
    *,
    user_id: str,
    filename: str,
    content: bytes,
    mime_type: str,
) -> str | None:
    """Upload a presentation file and return its storage path."""
    storage_path = build_storage_path(user_id, filename, int(time.time() * 1000))
    try:
        _storage().upload(
            storage_path,
            content,
            file_options={"content-type": mime_type, "upsert": "false"},
        )
        return storage_path
    except Exception as exc:
        logger.error(
            "Storage upload failed for user_id=%s path=%s: %s",
            user_id,
            storage_path,
            format_supabase_error(exc),
        )
    return None


def delete_storage_file(storage_path: str) -> bool:
    """Remove a file from Supabase Storage."""
    try:
        _storage().remove([storage_path])
        return True
    except Exception as exc:
        logger.error(
            "Storage delete failed for path=%s: %s",
            storage_path,
            format_supabase_error(exc),
        )
    return False


def create_challenge_presentation(
    *,
    user_id: str,
    title: str,
    presentation_type: str,
    challenge_metadata: dict,
) -> dict[str, Any] | None:
    """Insert a challenge session presentation (no uploaded file)."""
    try:
        client = get_supabase_client()
        payload = {
            "user_id": user_id,
            "title": title,
            "presentation_type": presentation_type,
            "storage_path": None,
            "pdf_url": None,
            "challenge_metadata": challenge_metadata,
        }
        response = client.table("presentations").insert(payload).execute()
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error(
            "Failed to create challenge presentation for user_id=%s: %s",
            user_id,
            format_supabase_error(exc),
        )
    return None


def create_presentation_record(
    *,
    user_id: str,
    title: str,
    presentation_type: str,
    storage_path: str,
) -> dict[str, Any] | None:
    """Insert a presentation row and return the created record."""
    try:
        client = get_supabase_client()
        payload = {
            "user_id": user_id,
            "title": title,
            "presentation_type": presentation_type,
            "storage_path": storage_path,
            "pdf_url": storage_path,
        }
        response = client.table("presentations").insert(payload).execute()
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error(
            "Failed to create presentation for user_id=%s: %s",
            user_id,
            format_supabase_error(exc),
        )
    return None


def list_presentations_by_user(user_id: str) -> list[dict[str, Any]]:
    """Return deck presentations belonging to a user (excludes challenge sessions)."""
    try:
        client = get_supabase_client()
        response = (
            client.table("presentations")
            .select("*")
            .eq("user_id", user_id)
            .in_("presentation_type", list(DECK_TYPES))
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as exc:
        logger.error(
            "Failed to list presentations for user_id=%s: %s",
            user_id,
            format_supabase_error(exc),
        )
    return []


def get_presentation_by_id(presentation_id: str) -> dict[str, Any] | None:
    """Fetch a single presentation by primary key."""
    try:
        client = get_supabase_client()
        response = (
            client.table("presentations")
            .select("*")
            .eq("id", presentation_id)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as exc:
        logger.error(
            "Failed to fetch presentation id=%s: %s",
            presentation_id,
            format_supabase_error(exc),
        )
    return None


def delete_presentation_record(presentation_id: str) -> bool:
    """
    Delete a presentation and cascade to recordings and feedback via FK constraints.

    Returns True when the presentation row was removed.
    """
    try:
        client = get_supabase_client()
        response = (
            client.table("presentations")
            .delete()
            .eq("id", presentation_id)
            .execute()
        )
        return bool(response.data)
    except Exception as exc:
        logger.error(
            "Failed to delete presentation id=%s: %s",
            presentation_id,
            format_supabase_error(exc),
        )
    return False


def build_title(filename: str) -> str:
    """Public helper to derive title from an uploaded filename."""
    return title_from_filename(filename)
