"""HTTP request logging middleware."""

import logging
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("loqui.access")

SENSITIVE_FIELDS = frozenset({"password", "current_password", "new_password"})


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log HTTP requests and responses without sensitive fields."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Record request metadata and elapsed time."""
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "%s %s -> %s (%.2fms) client=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request.client.host if request.client else "unknown",
        )
        return response
