"""CSRF validation middleware."""

import logging
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.utils.csrf import validate_csrf

logger = logging.getLogger("loqui.access")


class CsrfMiddleware(BaseHTTPMiddleware):
    """Reject state-changing requests without a valid CSRF token."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate CSRF before processing mutating requests."""
        if not validate_csrf(request):
            logger.warning(
                "CSRF validation failed for %s %s",
                request.method,
                request.url.path,
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Forbidden"},
            )
        return await call_next(request)
