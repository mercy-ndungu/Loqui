"""Supabase / PostgREST error helpers."""

from typing import Any


def format_supabase_error(exc: Exception) -> str:
    """Extract a readable message from a Supabase/PostgREST exception."""
    parts: list[str] = [str(exc)]

    for attr in ("message", "details", "hint", "code"):
        value = getattr(exc, attr, None)
        if value:
            parts.append(f"{attr}={value}")

    if hasattr(exc, "json"):
        try:
            payload: dict[str, Any] = exc.json()  # type: ignore[union-attr]
            if isinstance(payload, dict):
                for key in ("message", "details", "hint", "code"):
                    if payload.get(key):
                        parts.append(f"{key}={payload[key]}")
        except Exception:
            pass

    return "; ".join(dict.fromkeys(parts))
