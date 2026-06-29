"""CSRF token generation and validation."""

import secrets

from starlette.requests import Request

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# Auth endpoints that must work before a CSRF cookie exists.
CSRF_EXEMPT_PATHS = frozenset({
    "/auth/csrf",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/challenges/topics/random",
    "/challenges/improv/generate",
})


def generate_csrf_token() -> str:
    """Return a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(32)


def validate_csrf(request: Request) -> bool:
    """Validate double-submit CSRF token for state-changing requests."""
    if request.method in SAFE_METHODS:
        return True

    path = request.url.path.rstrip("/") or "/"
    if path in CSRF_EXEMPT_PATHS or path.startswith("/docs"):
        return True

    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get(CSRF_HEADER_NAME)

    if not cookie_token or not header_token:
        return False

    return secrets.compare_digest(cookie_token, header_token)
