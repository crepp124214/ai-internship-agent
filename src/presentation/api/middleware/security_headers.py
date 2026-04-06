"""
Security headers middleware for production.
Adds HSTS, CSP, frame and referrer protections.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.utils.config_loader import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        settings = get_settings()

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        app_env = str(settings.APP_ENV).strip().lower()
        request_proto = request.headers.get("x-forwarded-proto", request.url.scheme)
        if app_env in {"production", "prod", "staging"} and str(request_proto).lower() == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        response.headers["Content-Security-Policy"] = settings.CSP_POLICY
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response
