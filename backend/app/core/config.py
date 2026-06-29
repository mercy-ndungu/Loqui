"""Application configuration loaded from environment variables."""

import base64
import json
import os
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256

from dotenv import load_dotenv

load_dotenv()

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "https://yourdomain.com",
)


def get_jwt_role(token: str) -> str | None:
    """Return the Supabase JWT role claim without logging the token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        role = data.get("role")
        return str(role) if role is not None else None
    except Exception:
        return None


def _parse_cors_origins(raw: str | None) -> tuple[str, ...]:
    """Parse a comma-separated CORS origin list from the environment."""
    if not raw:
        return DEFAULT_CORS_ORIGINS
    origins = tuple(origin.strip() for origin in raw.split(",") if origin.strip())
    return origins or DEFAULT_CORS_ORIGINS


def _derive_fernet_key(secret: str) -> str:
    """Derive a Fernet-compatible key from an arbitrary secret string."""
    digest = sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode()


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the Loqui auth service."""

    supabase_url: str
    supabase_service_role_key: str
    jwt_secret: str
    transcription_encryption_key: str
    anthropic_api_key: str | None
    claude_model: str
    unsplash_access_key: str | None
    cors_origins: tuple[str, ...]
    access_token_expire_hours: int = 1
    refresh_token_expire_days: int = 7
    cookie_secure: bool = False
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    jwt_secret = os.getenv("JWT_SECRET")

    missing = [
        name
        for name, value in [
            ("SUPABASE_URL", supabase_url),
            ("SUPABASE_SERVICE_ROLE_KEY", supabase_service_role_key),
            ("JWT_SECRET", jwt_secret),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    transcription_key = os.getenv("TRANSCRIPTION_ENCRYPTION_KEY")
    if not transcription_key:
        transcription_key = _derive_fernet_key(jwt_secret)

    return Settings(
        supabase_url=supabase_url,
        supabase_service_role_key=supabase_service_role_key,
        jwt_secret=jwt_secret,
        transcription_encryption_key=transcription_key,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        claude_model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"),
        unsplash_access_key=os.getenv("UNSPLASH_ACCESS_KEY"),
        cors_origins=_parse_cors_origins(os.getenv("CORS_ORIGINS")),
        cookie_secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        environment=os.getenv("ENVIRONMENT", "development"),
    )
