"""
Enhanced admin security module with proper access controls.
"""

from functools import wraps
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import (
    get_admin_api_key,
    require_admin_access,
    validate_admin_key,
)
from app.core.settings import settings

security = HTTPBearer(auto_error=False)


def admin_required(f):
    """Decorator to require admin access for endpoints."""

    @wraps(f)
    async def wrapper(*args, **kwargs):
        # Extract credentials from dependencies
        credentials = kwargs.get("credentials")
        if credentials:
            api_key = get_admin_api_key(credentials)
            require_admin_access(api_key)
        else:
            require_admin_access()

        return await f(*args, **kwargs)

    return wrapper


def get_admin_credentials(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """Dependency to extract and validate admin credentials."""

    # Check if admin endpoints are enabled
    if not settings.security.admin_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin endpoints are disabled"
        )

    # If no admin key is configured, allow access
    if not settings.security.admin_api_key:
        return None

    # Extract API key from credentials
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    api_key = get_admin_api_key(credentials)

    # Validate the key
    if not validate_admin_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return api_key


def log_admin_action(request: Request, action: str, details: Optional[str] = None):
    """Log admin actions for audit trail."""
    import logging

    logger = logging.getLogger("admin_audit")

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    log_entry = {
        "action": action,
        "ip": client_ip,
        "user_agent": user_agent,
        "path": request.url.path,
        "method": request.method,
        "details": details,
        "timestamp": (
            request.state.timestamp if hasattr(request.state, "timestamp") else None
        ),
    }

    logger.info(f"Admin action: {log_entry}")


class AdminRateLimiter:
    """Special rate limiter for admin endpoints."""

    def __init__(self):
        self.admin_requests = {}
        self.max_requests = 10  # Lower limit for admin endpoints
        self.window_seconds = 60

    def check_rate_limit(self, client_ip: str) -> bool:
        """Check if admin request is within rate limit."""
        import time

        # Skip rate limiting in testing mode
        if settings.is_testing:
            return True

        current_time = time.time()

        # Clean old entries
        if client_ip in self.admin_requests:
            self.admin_requests[client_ip] = [
                req_time
                for req_time in self.admin_requests[client_ip]
                if req_time > current_time - self.window_seconds
            ]
        else:
            self.admin_requests[client_ip] = []

        # Check limit
        if len(self.admin_requests[client_ip]) >= self.max_requests:
            return False

        # Add current request
        self.admin_requests[client_ip].append(current_time)
        return True

    def clear(self):
        """Clear admin rate limit store. Useful for testing."""
        self.admin_requests.clear()

    def reload_config(self):
        """Reload configuration. Useful for testing."""
        # Update limits based on current settings
        if settings.is_testing:
            self.max_requests = 10000  # Very high limit for testing
        else:
            self.max_requests = 10  # Normal admin limit


# Global instance
admin_rate_limiter = AdminRateLimiter()


def check_admin_rate_limit(request: Request):
    """Dependency to check admin rate limits."""
    # Skip admin rate limiting in testing mode
    if settings.is_testing:
        return

    client_ip = request.client.host if request.client else "unknown"

    if not admin_rate_limiter.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Admin rate limit exceeded",
        )
