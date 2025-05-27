"""
Security middleware and utilities.
"""

import time
from collections import defaultdict, deque
from typing import Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.errors import AuthenticationAPIError, RateLimitAPIError
from app.core.settings import settings

# In-memory store for rate limiting (use Redis in production)
rate_limit_store: Dict[str, deque] = defaultdict(deque)

security = HTTPBearer(auto_error=False)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(
        self,
        app,
        requests_per_minute: Optional[int] = None,
        window_seconds: Optional[int] = None,
    ):
        super().__init__(app)
        # Use different rate limits for testing
        if settings.is_testing:
            self.requests_per_minute = (
                requests_per_minute or settings.api.test_rate_limit_requests
            )
            self.window_seconds = window_seconds or settings.api.test_rate_limit_window
        else:
            self.requests_per_minute = (
                requests_per_minute or settings.api.rate_limit_requests
            )
            self.window_seconds = window_seconds or settings.api.rate_limit_window

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting completely in testing mode
        if settings.is_testing:
            response = await call_next(request)
            # Still add headers for testing purposes
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(
                self.requests_per_minute - 1
            )
            response.headers["X-RateLimit-Reset"] = str(
                int(time.time() + self.window_seconds)
            )
            return response

        # Skip rate limiting for health checks and docs
        if request.url.path in ["/docs", "/redoc", "/openapi.json", "/status"]:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Clean old entries
        self._clean_old_entries(client_ip, current_time)

        # Check rate limit
        if len(rate_limit_store[client_ip]) >= self.requests_per_minute:
            return Response(
                content='{"error": "RATE_LIMIT_ERROR", "message": "Rate limit exceeded"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
            )

        # Add current request
        rate_limit_store[client_ip].append(current_time)

        response = await call_next(request)

        # Add rate limit headers
        remaining = max(0, self.requests_per_minute - len(rate_limit_store[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            int(current_time + self.window_seconds)
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _clean_old_entries(self, client_ip: str, current_time: float):
        """Remove entries older than the time window."""
        window_start = current_time - self.window_seconds
        while (
            rate_limit_store[client_ip]
            and rate_limit_store[client_ip][0] < window_start
        ):
            rate_limit_store[client_ip].popleft()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # CSP for docs pages
        if request.url.path in ["/docs", "/redoc"]:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self'"
            )

        return response


def get_admin_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = None,
) -> Optional[str]:
    """Extract admin API key from Authorization header."""

    if not credentials:
        return None

    if credentials.scheme.lower() != "bearer":
        raise AuthenticationAPIError("Invalid authentication scheme")

    return credentials.credentials


def validate_admin_key(api_key: Optional[str]) -> bool:
    """Validate admin API key."""

    if not settings.security.admin_enabled:
        return False

    if not settings.security.admin_api_key:
        return True  # No key required if not set

    return api_key == settings.security.admin_api_key


def require_admin_access(api_key: Optional[str] = None) -> None:
    """Require admin access or raise exception."""

    if not settings.security.admin_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin endpoints are disabled"
        )

    if settings.security.admin_api_key and not validate_admin_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


def sanitize_query_param(value: str, max_length: int = 100) -> str:
    """Sanitize query parameter input."""

    if not value:
        return ""

    # Basic sanitization
    sanitized = value.strip()[:max_length]

    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", "&", '"', "'", "%", ";"]
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")

    return sanitized


def validate_date_string(date_str: str) -> bool:
    """Validate date string format (YYYY-MM-DD)."""

    import re
    from datetime import datetime

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_request_info(request: Request) -> dict:
    """Extract request information for logging."""

    return {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", ""),
        "referer": request.headers.get("referer", ""),
    }
