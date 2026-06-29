"""HTTPS redirect middleware for production."""

from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.core.config import get_settings


class HttpsRedirectMiddleware(BaseHTTPMiddleware):
    """Redirect HTTP to HTTPS in production environments."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Force HTTPS when running in production behind plain HTTP."""
        settings = get_settings()
        if (
            settings.environment == "production"
            and request.url.scheme == "http"
            and request.client
            and request.client.host not in ("127.0.0.1", "localhost", "testclient")
        ):
            url = str(request.url).replace("http://", "https://", 1)
            return RedirectResponse(url=url, status_code=308)
        return await call_next(request)
