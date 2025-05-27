"""
Error handling middleware with structured logging and correlation IDs.
"""

import logging
import traceback
import uuid
from typing import Any, Dict

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError

from app.exceptions import APIError, DatabaseError, ValidationError

# Configure structured logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    """Middleware for centralized error handling with structured logging."""

    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, scope, receive, send):
        """Process request and handle any errors."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Generate correlation ID for request tracking
        headers = dict(scope.get("headers", []))
        correlation_id = headers.get(
            b"x-correlation-id", str(uuid.uuid4()).encode()
        ).decode()

        try:
            # Process the request
            await self.app(scope, receive, send)

        except Exception as exc:
            # Handle exceptions by sending an error response
            await self._send_error_response(send, exc, correlation_id)

    async def _send_error_response(
        self, send, exc: Exception, correlation_id: str
    ) -> None:
        """Send an error response."""

        # Log the error with correlation ID
        error_data = {
            "correlation_id": correlation_id,
            "error_type": exc.__class__.__name__,
            "error_message": str(exc),
        }

        if isinstance(exc, APIError):
            # Handle custom API errors
            logger.error(
                "API Error occurred",
                extra={
                    **error_data,
                    "status_code": exc.status_code,
                    "error_code": exc.error_code,
                    "details": exc.details,
                },
            )

            # Update correlation ID if not set
            if not exc.correlation_id:
                exc.correlation_id = correlation_id

            response_data = exc.to_dict()
            status_code = exc.status_code

        elif isinstance(exc, IntegrityError):
            # Handle database integrity errors
            logger.error("Database integrity error", extra=error_data)

            error = DatabaseError(
                message="Data integrity constraint violation",
                correlation_id=correlation_id,
                details={
                    "database_error": (
                        str(exc.orig) if hasattr(exc, "orig") else str(exc)
                    )
                },
            )

            response_data = error.to_dict()
            status_code = error.status_code

        elif isinstance(exc, OperationalError):
            # Handle database operational errors
            logger.error("Database operational error", extra=error_data)

            error = DatabaseError(
                message="Database operation failed",
                correlation_id=correlation_id,
                details={
                    "database_error": (
                        str(exc.orig) if hasattr(exc, "orig") else str(exc)
                    )
                },
            )

            response_data = error.to_dict()
            status_code = error.status_code

        else:
            # Handle unexpected errors
            logger.error(
                "Unexpected error occurred",
                extra={**error_data, "traceback": traceback.format_exc()},
            )

            error = APIError(
                message="An unexpected error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                correlation_id=correlation_id,
                details={"error_type": exc.__class__.__name__},
            )

            response_data = error.to_dict()
            status_code = error.status_code

        # Send the error response
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"x-correlation-id", correlation_id.encode()],
                ],
            }
        )

        import json

        await send(
            {
                "type": "http.response.body",
                "body": json.dumps(response_data).encode(),
            }
        )


def setup_error_handlers(app: FastAPI) -> None:
    """Setup global error handlers for the FastAPI application."""

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        """Handle APIError exceptions."""
        correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

        if not exc.correlation_id:
            exc.correlation_id = correlation_id

        logger.error(
            f"API Error: {exc.message}",
            extra={
                "correlation_id": correlation_id,
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "details": exc.details,
                "method": request.method,
                "url": str(request.url),
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
            headers={"X-Correlation-ID": correlation_id},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle ValueError exceptions."""
        correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

        error = ValidationError(message=str(exc), correlation_id=correlation_id)

        logger.warning(
            f"Validation Error: {str(exc)}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
            },
        )

        return JSONResponse(
            status_code=error.status_code,
            content=error.to_dict(),
            headers={"X-Correlation-ID": correlation_id},
        )

    @app.exception_handler(500)
    async def internal_server_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle 500 internal server errors."""
        correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

        error = APIError(
            message="Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            correlation_id=correlation_id,
        )

        logger.error(
            f"Internal Server Error: {str(exc)}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
                "traceback": traceback.format_exc(),
            },
        )

        return JSONResponse(
            status_code=error.status_code,
            content=error.to_dict(),
            headers={"X-Correlation-ID": correlation_id},
        )


def add_error_recovery_context(func):
    """Decorator to add error recovery context to functions."""

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Add recovery suggestions based on error type
            if isinstance(e, DatabaseError):
                e.details = e.details or {}
                e.details["recovery_suggestion"] = "Check database connection and retry"
            elif isinstance(e, ValidationError):
                e.details = e.details or {}
                e.details["recovery_suggestion"] = (
                    "Check input parameters and try again"
                )
            raise e

    return wrapper
