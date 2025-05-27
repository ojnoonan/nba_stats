"""
Centralized error handling utilities and middleware.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.settings import settings
from app.schemas.validation import ErrorResponse

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)


class ValidationAPIError(APIError):
    """Exception for validation errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_type="VALIDATION_ERROR",
            details=details,
        )


class NotFoundAPIError(APIError):
    """Exception for not found errors."""

    def __init__(self, message: str, resource: str = "Resource"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_type="NOT_FOUND",
            details={"resource": resource},
        )


class DatabaseAPIError(APIError):
    """Exception for database errors."""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="DATABASE_ERROR",
        )


class RateLimitAPIError(APIError):
    """Exception for rate limiting errors."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_type="RATE_LIMIT_ERROR",
        )


class AuthenticationAPIError(APIError):
    """Exception for authentication errors."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_type="AUTHENTICATION_ERROR",
        )


class AuthorizationAPIError(APIError):
    """Exception for authorization errors."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="AUTHORIZATION_ERROR",
        )


def create_error_response(
    error_type: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Create a standardized error response."""

    error_response = ErrorResponse(
        error=error_type, message=message, details=details, timestamp=datetime.utcnow()
    )

    return JSONResponse(status_code=status_code, content=error_response.model_dump())


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handler for API exceptions."""

    logger.error(
        f"API Error: {exc.error_type} - {exc.message}",
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return create_error_response(
        error_type=exc.error_type,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )


async def validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handler for Pydantic validation errors."""

    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({"field": field, "message": error["msg"], "type": error["type"]})

    logger.warning(
        f"Validation Error: {len(errors)} validation issues",
        extra={"errors": errors, "path": request.url.path, "method": request.method},
    )

    return create_error_response(
        error_type="VALIDATION_ERROR",
        message="Input validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": errors},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler for FastAPI HTTP exceptions."""

    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return create_error_response(
        error_type="HTTP_ERROR", message=str(exc.detail), status_code=exc.status_code
    )


async def sqlalchemy_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handler for SQLAlchemy database errors."""

    logger.error(
        f"Database Error: {type(exc).__name__} - {str(exc)}",
        extra={"path": request.url.path, "method": request.method},
    )

    # Don't expose internal database errors in production
    if settings.is_production:
        message = "A database error occurred"
    else:
        message = str(exc)

    return create_error_response(
        error_type="DATABASE_ERROR",
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for all other exceptions."""

    logger.exception(
        f"Unhandled Exception: {type(exc).__name__} - {str(exc)}",
        extra={"path": request.url.path, "method": request.method},
    )

    # Don't expose internal errors in production
    if settings.is_production:
        message = "An internal error occurred"
    else:
        message = str(exc)

    return create_error_response(
        error_type="INTERNAL_ERROR",
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def validate_admin_access(api_key: Optional[str] = None) -> None:
    """Validate admin access."""

    if not settings.security.admin_enabled:
        raise AuthorizationAPIError("Admin endpoints are disabled")

    if settings.security.admin_api_key:
        if not api_key:
            raise AuthenticationAPIError("Admin API key required")

        if api_key != settings.security.admin_api_key:
            raise AuthenticationAPIError("Invalid admin API key")


def validate_entity_id(entity_id: int, entity_name: str = "Entity") -> None:
    """Validate entity ID format."""

    if entity_id <= 0:
        raise ValidationAPIError(
            f"{entity_name} ID must be a positive integer",
            details={"entity_id": entity_id, "entity_name": entity_name},
        )


def validate_pagination(skip: int, limit: int) -> None:
    """Validate pagination parameters."""

    if skip < 0:
        raise ValidationAPIError("Skip parameter cannot be negative")

    if limit <= 0:
        raise ValidationAPIError("Limit parameter must be positive")

    if limit > 1000:
        raise ValidationAPIError("Limit parameter cannot exceed 1000")


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize string input."""

    if not value:
        return ""

    # Remove potential XSS characters
    sanitized = value.strip()

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized
