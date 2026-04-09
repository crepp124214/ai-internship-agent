"""
Request ID middleware for distributed tracing.

Generates a unique request_id for each request and stores it in:
- request.state.request_id (for access by other components)
- X-Request-ID response header (for client correlation)
- contextvars (for log correlation)
"""

import uuid
from contextvars import ContextVar
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable for request_id - thread/async safe
_request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id_var() -> Optional[str]:
    """Get current request_id from context variable."""
    return _request_id_var.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates a unique request_id for each request.

    The request_id is:
    - Generated as a UUID4 string
    - Stored in request.state.request_id for access by other components
    - Added to X-Request-ID response header for client correlation
    - Stored in contextvars for log correlation
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate or extract request_id
        request_id = self._get_or_create_request_id(request)

        # Store in request.state for access by other components
        request.state.request_id = request_id

        # Set context variable for log correlation
        token = _request_id_var.set(request_id)

        # Execute the request with context
        response = None
        try:
            response = await call_next(request)
        finally:
            # Always add X-Request-ID header to response
            # This ensures the header is present even when an exception occurs
            if response is not None:
                response.headers["X-Request-ID"] = request_id
            # Reset context variable
            _request_id_var.reset(token)

        return response

    def _get_or_create_request_id(self, request: Request) -> str:
        """
        Get request_id from header or generate a new one.

        Allows clients to pass X-Request-ID header for upstream request correlation.
        """
        # Check if client provided X-Request-ID header
        client_request_id = request.headers.get("X-Request-ID")
        if client_request_id:
            # Validate format - allow non-empty strings under 128 chars
            if client_request_id and len(client_request_id) <= 128:
                return client_request_id

        # Generate new UUID4-based request_id
        return str(uuid.uuid4())


def get_request_id(request: Optional[Request] = None) -> Optional[str]:
    """
    Get request_id from request state or context variable.

    Args:
        request: FastAPI Request object (optional)

    Returns:
        request_id string or None if not available
    """
    # Try to get from request.state first
    if request is not None:
        if hasattr(request.state, "request_id"):
            return request.state.request_id

    # Fallback to context variable
    return get_request_id_var()
