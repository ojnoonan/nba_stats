"""
Enhanced error handling and logging system for NBA Stats application.
Provides structured error handling, logging configuration, and monitoring.
"""
import logging
import logging.handlers
import sys
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
import json
from functools import wraps

from app.core.config import settings

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add custom fields
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
            
        return json.dumps(log_entry)

def setup_logging():
    """Configure logging for the application."""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for general logs
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "nba_stats.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = StructuredFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # API access log handler
    access_logger = logging.getLogger("api.access")
    access_handler = logging.handlers.RotatingFileHandler(
        log_dir / "api_access.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    access_handler.setFormatter(file_formatter)
    access_logger.addHandler(access_handler)
    access_logger.propagate = False

class ErrorHandler:
    """Centralized error handling system."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log an error with context information."""
        extra = {
            'operation': context.get('operation') if context else 'unknown',
            'user_id': context.get('user_id') if context else None,
            'request_id': context.get('request_id') if context else None
        }
        
        self.logger.error(
            f"Error in {context.get('operation', 'unknown')}: {str(error)}",
            exc_info=True,
            extra=extra
        )
    
    def log_api_error(self, endpoint: str, error: Exception, request_data: Optional[Dict] = None):
        """Log API-specific errors."""
        context = {
            'operation': f'API:{endpoint}',
            'request_data': request_data
        }
        self.log_error(error, context)
    
    def log_database_error(self, operation: str, error: Exception, query: Optional[str] = None):
        """Log database-specific errors."""
        context = {
            'operation': f'DB:{operation}',
            'query': query
        }
        self.log_error(error, context)
    
    def log_nba_api_error(self, endpoint: str, error: Exception, params: Optional[Dict] = None):
        """Log NBA API-specific errors."""
        context = {
            'operation': f'NBA_API:{endpoint}',
            'params': params
        }
        self.log_error(error, context)

# Global error handler instance
error_handler = ErrorHandler()

def handle_exceptions(operation: str):
    """Decorator for handling exceptions in functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.log_error(e, {'operation': operation})
                raise
        return wrapper
    return decorator

def handle_async_exceptions(operation: str):
    """Decorator for handling exceptions in async functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_handler.log_error(e, {'operation': operation})
                raise
        return wrapper
    return decorator

class DatabaseErrorHandler:
    """Specialized error handler for database operations."""
    
    @staticmethod
    def handle_connection_error(error: Exception, operation: str):
        """Handle database connection errors."""
        error_handler.log_database_error(
            operation,
            error,
            "Database connection failed"
        )
        return {"error": "Database temporarily unavailable", "code": "DB_CONNECTION_ERROR"}
    
    @staticmethod
    def handle_integrity_error(error: Exception, operation: str):
        """Handle database integrity constraint violations."""
        error_handler.log_database_error(
            operation,
            error,
            "Integrity constraint violation"
        )
        return {"error": "Data integrity violation", "code": "DB_INTEGRITY_ERROR"}
    
    @staticmethod
    def handle_timeout_error(error: Exception, operation: str):
        """Handle database timeout errors."""
        error_handler.log_database_error(
            operation,
            error,
            "Database operation timeout"
        )
        return {"error": "Database operation timed out", "code": "DB_TIMEOUT_ERROR"}

class APIErrorHandler:
    """Specialized error handler for API operations."""
    
    @staticmethod
    def handle_validation_error(error: Exception, endpoint: str):
        """Handle request validation errors."""
        error_handler.log_api_error(endpoint, error)
        return {"error": "Invalid request data", "code": "VALIDATION_ERROR"}
    
    @staticmethod
    def handle_rate_limit_error(endpoint: str):
        """Handle rate limiting errors."""
        error_handler.log_api_error(endpoint, Exception("Rate limit exceeded"))
        return {"error": "Rate limit exceeded", "code": "RATE_LIMIT_ERROR"}
    
    @staticmethod
    def handle_authentication_error(endpoint: str):
        """Handle authentication errors."""
        error_handler.log_api_error(endpoint, Exception("Authentication failed"))
        return {"error": "Authentication required", "code": "AUTH_ERROR"}

# Initialize logging when module is imported
setup_logging()
