"""
Unified exception handling for NBA Stats application.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class APIError(Exception):
    """Base API error with structured response format."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON response."""
        return {
            "error": {
                "message": self.message,
                "code": self.error_code,
                "status_code": self.status_code,
                "details": self.details,
                "correlation_id": self.correlation_id,
                "timestamp": self.timestamp,
            }
        }


class ValidationError(APIError):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        field_errors: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ):
        details = {"field_errors": field_errors or []}
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            **kwargs,
        )


class NotFoundError(APIError):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: Union[str, int], **kwargs):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(
            message=message, status_code=status.HTTP_404_NOT_FOUND, **kwargs
        )


class ConflictError(APIError):
    """Raised when there's a conflict with the current state."""

    def __init__(self, message: str = "Conflict with current state", **kwargs):
        super().__init__(
            message=message, status_code=status.HTTP_409_CONFLICT, **kwargs
        )


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs,
    ):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
            **kwargs,
        )


class AuthenticationError(APIError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication required", **kwargs):
        super().__init__(
            message=message, status_code=status.HTTP_401_UNAUTHORIZED, **kwargs
        )


class AuthorizationError(APIError):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(
            message=message, status_code=status.HTTP_403_FORBIDDEN, **kwargs
        )


class ExternalServiceError(APIError):
    """Raised when external service fails."""

    def __init__(
        self, service_name: str, message: str = "External service unavailable", **kwargs
    ):
        details = {"service": service_name}
        super().__init__(
            message=f"{service_name}: {message}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
            **kwargs,
        )


# Legacy exceptions maintained for backward compatibility
class TaskCancelledError(APIError):
    """Raised when a background task is cancelled"""

    def __init__(self, message: str = "Task was cancelled", **kwargs):
        super().__init__(
            message=message, status_code=status.HTTP_409_CONFLICT, **kwargs
        )


class DataUpdateError(APIError):
    """Raised when there's an error updating data"""

    def __init__(self, message: str = "Data update failed", **kwargs):
        super().__init__(
            message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, **kwargs
        )


class DatabaseError(APIError):
    """Raised when there's an error with the database"""

    def __init__(self, message: str = "Database operation failed", **kwargs):
        super().__init__(
            message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, **kwargs
        )


class ConfigurationError(APIError):
    """Raised when there's an error with configuration"""

    def __init__(self, message: str = "Configuration error", **kwargs):
        super().__init__(
            message=message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, **kwargs
        )
