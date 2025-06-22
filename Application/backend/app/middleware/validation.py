"""
Input validation middleware for security and data integrity.
Provides global input validation and sanitization.
"""
import logging
import re
from typing import Any, Dict, List, Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import json

logger = logging.getLogger(__name__)

class ValidationMiddleware:
    """Middleware for input validation and sanitization."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Skip validation for certain paths
            if self._should_skip_validation(request.url.path):
                await self.app(scope, receive, send)
                return
            
            try:
                # Validate query parameters
                if request.query_params:
                    self._validate_query_params(dict(request.query_params))
                
                # Validate request body for POST/PUT/PATCH requests
                if request.method in ["POST", "PUT", "PATCH"]:
                    await self._validate_request_body(request)
                
                # Validate path parameters
                if "path_params" in scope and scope["path_params"]:
                    self._validate_path_params(scope["path_params"])
                
            except ValueError as e:
                response = JSONResponse(
                    status_code=400,
                    content={"error": "Validation error", "detail": str(e)}
                )
                await response(scope, receive, send)
                return
            except Exception as e:
                logger.error(f"Validation middleware error: {str(e)}")
                response = JSONResponse(
                    status_code=500,
                    content={"error": "Internal server error"}
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)
    
    def _should_skip_validation(self, path: str) -> bool:
        """Check if validation should be skipped for this path."""
        skip_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/status",
            "/health"
        ]
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def _validate_query_params(self, params: Dict[str, Any]) -> None:
        """Validate query parameters."""
        for key, value in params.items():
            # Sanitize parameter name
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                raise ValueError(f"Invalid parameter name: {key}")
            
            # Validate parameter value
            if isinstance(value, str):
                self._validate_string_parameter(key, value)
            elif isinstance(value, (int, float)):
                self._validate_numeric_parameter(key, value)
    
    def _validate_string_parameter(self, name: str, value: str) -> None:
        """Validate string parameters."""
        # Check for null bytes and control characters
        if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', value):
            raise ValueError(f"Invalid characters in parameter {name}")
        
        # Check for potential SQL injection patterns
        sql_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"('|(\\x27)|(\\x2D)|(\\x2D\\x2D))",
            r"((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",
            r"((\%27)|(\'))((\%75)|u|(\%55))((\%6E)|n|(\%4E))((\%69)|i|(\%49))((\%6F)|o|(\%4F))((\%6E)|n|(\%4E))"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential SQL injection attempt in parameter {name}: {value}")
                raise ValueError(f"Invalid characters detected in parameter {name}")
        
        # Check for XSS patterns
        xss_patterns = [
            r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe\b",
            r"<object\b",
            r"<embed\b"
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential XSS attempt in parameter {name}: {value}")
                raise ValueError(f"Invalid content detected in parameter {name}")
        
        # Length validation
        if len(value) > 1000:  # Reasonable limit
            raise ValueError(f"Parameter {name} exceeds maximum length")
    
    def _validate_numeric_parameter(self, name: str, value: Union[int, float]) -> None:
        """Validate numeric parameters."""
        # Check for reasonable bounds
        if isinstance(value, int):
            if value < -2147483648 or value > 2147483647:  # 32-bit integer bounds
                raise ValueError(f"Parameter {name} out of range")
        elif isinstance(value, float):
            if abs(value) > 1e308:  # Reasonable float bounds
                raise ValueError(f"Parameter {name} out of range")
    
    async def _validate_request_body(self, request: Request) -> None:
        """Validate request body content."""
        try:
            # Get content type
            content_type = request.headers.get("content-type", "")
            
            if content_type.startswith("application/json"):
                # Read body only once to avoid consuming the stream
                body = await request.body()
                if body:
                    try:
                        data = json.loads(body.decode())
                        self._validate_json_data(data)
                    except json.JSONDecodeError:
                        raise ValueError("Invalid JSON format")
            
            # Check content length
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                raise ValueError("Request body too large")
                
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            logger.error(f"Error validating request body: {str(e)}")
            raise ValueError("Invalid request body")
    
    def _validate_json_data(self, data: Any, max_depth: int = 10, current_depth: int = 0) -> None:
        """Recursively validate JSON data."""
        if current_depth > max_depth:
            raise ValueError("JSON nesting too deep")
        
        if isinstance(data, dict):
            if len(data) > 100:  # Reasonable limit for object keys
                raise ValueError("Too many keys in JSON object")
            
            for key, value in data.items():
                if not isinstance(key, str):
                    raise ValueError("JSON object keys must be strings")
                
                if len(key) > 100:  # Reasonable key length limit
                    raise ValueError("JSON object key too long")
                
                self._validate_json_data(value, max_depth, current_depth + 1)
        
        elif isinstance(data, list):
            if len(data) > 1000:  # Reasonable array size limit
                raise ValueError("JSON array too large")
            
            for item in data:
                self._validate_json_data(item, max_depth, current_depth + 1)
        
        elif isinstance(data, str):
            if len(data) > 10000:  # Reasonable string length limit
                raise ValueError("JSON string too long")
            
            # Check for dangerous patterns
            self._validate_string_parameter("json_value", data)
    
    def _validate_path_params(self, params: Dict[str, Any]) -> None:
        """Validate path parameters."""
        for key, value in params.items():
            if isinstance(value, str):
                # Path parameters should be more restrictive
                if not re.match(r'^[a-zA-Z0-9\-_.]+$', value):
                    raise ValueError(f"Invalid path parameter: {key}")
                
                if len(value) > 100:  # Reasonable length for path params
                    raise ValueError(f"Path parameter {key} too long")
            
            elif isinstance(value, int):
                # Validate integer path parameters (like IDs)
                if value < 0 or value > 999999999:  # Reasonable ID bounds
                    raise ValueError(f"Invalid ID in path: {key}")
