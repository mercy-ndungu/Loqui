"""Loqui authentication API."""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_jwt_role, get_settings
from app.db.database import get_supabase_client
from app.utils.supabase_errors import format_supabase_error
from app.core.limiter import limiter
from app.middleware import (
    CsrfMiddleware,
    HttpsRedirectMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from app.api.routers import auth, challenges, feedback, presentations, recordings, users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title="Loqui Auth API",
    description="Secure authentication backend for Loqui AI speech coach",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    allow_methods=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CsrfMiddleware)
app.add_middleware(HttpsRedirectMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(presentations.router)
app.include_router(challenges.router)
app.include_router(recordings.router)
app.include_router(feedback.router)


@app.on_event("startup")
async def verify_supabase_connection() -> None:
    """Validate Supabase credentials and table access at startup."""
    key_role = get_jwt_role(settings.supabase_service_role_key)
    if key_role != "service_role":
        logger.error(
            "SUPABASE_SERVICE_ROLE_KEY has role=%r; expected 'service_role'. "
            "Signup/login will fail until you replace it with the service_role "
            "secret from Supabase Dashboard -> Settings -> API (not the anon key).",
            key_role,
        )

    try:
        client = get_supabase_client()
        client.table("users").select("id").limit(1).execute()
        client.table("user_profiles").select("id").limit(1).execute()
        client.table("presentations").select("id").limit(1).execute()
        client.table("recordings").select("id").limit(1).execute()
        client.table("feedback").select("id").limit(1).execute()
        client.table("challenges").select("id").limit(1).execute()
        logger.info(
            "Supabase users, user_profiles, presentations, recordings, feedback, "
            "and challenges tables are reachable"
        )
    except Exception as exc:
        error = format_supabase_error(exc)
        logger.error("Supabase startup check failed: %s", error)
        if key_role == "anon":
            logger.error(
                "This usually means the anon key is configured instead of the "
                "service_role key while RLS is enabled on public.users."
            )
        if "does not exist" in error.lower() or "schema cache" in error.lower():
            logger.error(
                "Run supabase/schema.sql in the Supabase SQL editor to create "
                "the required tables."
            )

    from app.services.audio_service import ffmpeg_available
    from app.services.challenge_storage_service import bucket_accessible as challenge_bucket_ok
    from app.services.recording_service import bucket_accessible as recording_bucket_ok

    if not ffmpeg_available():
        logger.warning(
            "ffmpeg is not installed. Recording uploads will fail until ffmpeg is available."
        )

    if not recording_bucket_ok():
        logger.warning(
            "Supabase 'recordings' bucket is not accessible. Create a private bucket named "
            "'recordings' in Supabase Dashboard -> Storage."
        )
    elif not challenge_bucket_ok():
        logger.warning("Challenge video storage check failed.")

    if not settings.anthropic_api_key:
        logger.warning(
            "ANTHROPIC_API_KEY is not set. Dynamic topic generation will use static fallback topics."
        )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return validation errors without leaking sensitive input."""
    sanitized_errors: list[dict[str, Any]] = []
    for error in exc.errors():
        loc = list(error.get("loc", ()))
        if "password" in loc or "transcription" in loc:
            sanitized_errors.append(
                {
                    "loc": loc,
                    "msg": "Invalid input" if "transcription" in loc else "Invalid password format",
                    "type": error.get("type"),
                }
            )
        else:
            sanitized_errors.append(
                {
                    "loc": loc,
                    "msg": error.get("msg"),
                    "type": error.get("type"),
                }
            )

    logger.info("Validation error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": sanitized_errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected errors and return a generic response."""
    logger.exception("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}
