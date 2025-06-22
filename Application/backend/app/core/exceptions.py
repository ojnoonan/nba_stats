"""
Centralized exception handling for the NBA Stats API.
Provides consistent error responses and logging across all endpoints.
"""
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError, OperationalError
from pydantic import ValidationError
import traceback

logger = logging.getLogger(__name__)

class NBAStatsException(Exception):
    """Base exception for NBA Stats application."""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationException(NBAStatsException):
    """Exception raised for validation errors."""
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(message, status_code=400, details=details)

class NotFoundError(NBAStatsException):
    """Exception raised when a resource is not found."""
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, status_code=404)

class DatabaseError(NBAStatsException):
    """Exception raised for database-related errors."""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=500)

class ExternalServiceError(NBAStatsException):
    """Exception raised for external service errors."""
    def __init__(self, service: str, message: str = "External service unavailable"):
        message = f"{service}: {message}"
        super().__init__(message, status_code=503)

def handle_database_error(error: SQLAlchemyError, operation: str = "database operation") -> HTTPException:
    """Handle SQLAlchemy database errors with appropriate logging and response."""
    error_msg = str(error)
    
    if isinstance(error, IntegrityError):
        logger.warning(f"Database integrity error during {operation}: {error_msg}")
        return HTTPException(
            status_code=400,
            detail="Data integrity constraint violation"
        )
    elif isinstance(error, DataError):
        logger.warning(f"Database data error during {operation}: {error_msg}")
        return HTTPException(
            status_code=400,
            detail="Invalid data format or constraint violation"
        )
    elif isinstance(error, OperationalError):
        logger.error(f"Database operational error during {operation}: {error_msg}")
        return HTTPException(
            status_code=503,
            detail="Database service temporarily unavailable"
        )
    else:
        logger.error(f"Unknown database error during {operation}: {error_msg}")
        return HTTPException(
            status_code=500,
            detail="Internal database error"
        )

def handle_validation_error(error: ValidationError) -> HTTPException:
    """Handle Pydantic validation errors with detailed field information."""
    errors = []
    for err in error.errors():
        field = " -> ".join(str(loc) for loc in err["loc"])
        errors.append({
            "field": field,
            "message": err["msg"],
            "type": err["type"]
        })
    
    logger.warning(f"Validation error: {errors}")
    return HTTPException(
        status_code=422,
        detail={
            "message": "Validation failed",
            "errors": errors
        }
    )

def handle_generic_error(error: Exception, operation: str = "operation") -> HTTPException:
    """Handle generic exceptions with proper logging."""
    error_msg = str(error)
    error_type = type(error).__name__
    
    # Log the full traceback for debugging
    logger.error(f"Unexpected error during {operation}: {error_type}: {error_msg}")
    logger.debug(f"Full traceback: {traceback.format_exc()}")
    
    # Don't expose internal errors to the client
    return HTTPException(
        status_code=500,
        detail="An unexpected error occurred"
    )

class ErrorHandler:
    """Centralized error handler class for consistent error processing."""
    
    @staticmethod
    def handle_error(error: Exception, operation: str = "operation") -> HTTPException:
        """Route errors to appropriate handlers based on type."""
        if isinstance(error, HTTPException):
            # Re-raise HTTP exceptions as-is
            return error
        elif isinstance(error, NBAStatsException):
            logger.warning(f"NBA Stats error during {operation}: {error.message}")
            return HTTPException(status_code=error.status_code, detail=error.message)
        elif isinstance(error, ValidationError):
            return handle_validation_error(error)
        elif isinstance(error, SQLAlchemyError):
            return handle_database_error(error, operation)
        elif isinstance(error, ValueError):
            logger.warning(f"Value error during {operation}: {str(error)}")
            return HTTPException(status_code=400, detail=str(error))
        else:
            return handle_generic_error(error, operation)

def create_error_response(
    status_code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create standardized error response format."""
    response = {
        "error": True,
        "status_code": status_code,
        "message": message,
        "timestamp": logging.Formatter().formatTime(logging.LogRecord(
            name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None
        ))
    }
    
    if details:
        response["details"] = details
    
    if request_id:
        response["request_id"] = request_id
    
    return response

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for FastAPI application."""
    operation = f"{request.method} {request.url.path}"
    http_exc = ErrorHandler.handle_error(exc, operation)
    
    return JSONResponse(
        status_code=http_exc.status_code,
        content=create_error_response(
            status_code=http_exc.status_code,
            message=http_exc.detail,
            request_id=getattr(request.state, 'request_id', None)
        )
    )

# Decorator for consistent error handling in route functions
def handle_errors(operation_name: str):
    """Decorator to add consistent error handling to route functions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                raise ErrorHandler.handle_error(e, operation_name)
        return wrapper
    return decorator
