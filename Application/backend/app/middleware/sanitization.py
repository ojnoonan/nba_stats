"""
Data sanitization middleware for the NBA Stats API.
Provides comprehensive input sanitization and validation.
"""

import html
import re
from typing import Any, Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class DataSanitizationMiddleware(BaseHTTPMiddleware):
    """Middleware to sanitize request data."""

    def __init__(self, app):
        super().__init__(app)
        # Patterns for potentially malicious content
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"onmouseover\s*=",
            r"onfocus\s*=",
            r"onblur\s*=",
            r"onchange\s*=",
            r"onsubmit\s*=",
        ]

        # SQL injection patterns
        self.sql_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"(-{2}|\/\*|\*\/)",  # SQL comments
            r"(\b(or|and)\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?)",  # 1=1 patterns
            r"(\b(or|and)\s+['\"][^'\"]*['\"]?\s*=\s*['\"][^'\"]*['\"]?)",
        ]

    async def dispatch(self, request: Request, call_next):
        """Process request and sanitize data."""

        # Skip sanitization for certain paths
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Sanitize query parameters
        if request.query_params:
            sanitized_params = {}
            for key, value in request.query_params.items():
                sanitized_params[key] = self._sanitize_string(value)

            # Replace query params in request scope if any changes were made
            if sanitized_params != dict(request.query_params):
                request.scope["query_string"] = "&".join(
                    f"{key}={value}" for key, value in sanitized_params.items()
                ).encode()

        # Sanitize JSON body for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.body()
                    if body:
                        import json

                        data = json.loads(body)
                        sanitized_data = self._sanitize_json_data(data)

                        # Update request body if sanitization occurred
                        if sanitized_data != data:
                            sanitized_body = json.dumps(sanitized_data).encode()
                            request._body = sanitized_body
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Invalid JSON, let the endpoint handle the error
                    pass

        response = await call_next(request)
        return response

    def _sanitize_string(self, value: str, max_length: int = 500) -> str:
        """Sanitize a string value."""
        if not isinstance(value, str):
            return str(value)[:max_length]

        # Truncate to max length
        sanitized = value[:max_length]

        # HTML encode to prevent XSS
        sanitized = html.escape(sanitized, quote=True)

        # Remove null bytes and control characters
        sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", sanitized)

        # Check for XSS patterns
        for pattern in self.xss_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                # Remove the entire string if XSS detected
                return ""

        # Check for SQL injection patterns
        for pattern in self.sql_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                # Remove SQL keywords and dangerous characters
                sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        # Remove excessive whitespace
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        return sanitized

    def _sanitize_json_data(self, data: Any) -> Any:
        """Recursively sanitize JSON data."""
        if isinstance(data, dict):
            return {
                key: self._sanitize_json_data(value)
                for key, value in data.items()
                if isinstance(key, str) and len(key) <= 100  # Limit key length
            }
        elif isinstance(data, list):
            return [
                self._sanitize_json_data(item) for item in data[:1000]
            ]  # Limit array size
        elif isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, (int, float, bool)) or data is None:
            return data
        else:
            # Convert unknown types to string and sanitize
            return self._sanitize_string(str(data))


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Additional input validation middleware."""

    def __init__(self, app):
        super().__init__(app)
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        self.max_query_params = 50
        self.max_header_size = 8192

    async def dispatch(self, request: Request, call_next):
        """Validate request size and structure."""

        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            return Response(
                content='{"error": "REQUEST_TOO_LARGE", "message": "Request body too large"}',
                status_code=413,
                media_type="application/json",
            )

        # Check number of query parameters
        if len(request.query_params) > self.max_query_params:
            return Response(
                content='{"error": "TOO_MANY_PARAMS", "message": "Too many query parameters"}',
                status_code=400,
                media_type="application/json",
            )

        # Check header sizes
        total_header_size = sum(
            len(key) + len(value) for key, value in request.headers.items()
        )
        if total_header_size > self.max_header_size:
            return Response(
                content='{"error": "HEADERS_TOO_LARGE", "message": "Request headers too large"}',
                status_code=400,
                media_type="application/json",
            )

        return await call_next(request)
