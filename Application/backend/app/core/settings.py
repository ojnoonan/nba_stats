"""
Core configuration settings for the NBA Stats application.
This module provides centralized configuration management with environment variable support.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="NBA_STATS_DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database file configuration
    file_path: Optional[str] = Field(
        default=None,
        description="Full path to the database file",
        validation_alias="NBA_STATS_DB_FILE",
    )
    data_dir: Optional[str] = Field(
        default=None,
        description="Directory containing the database file",
        validation_alias="NBA_STATS_DATA_DIR",
    )
    echo: bool = Field(default=False, description="Enable SQLAlchemy logging")
    pool_size: int = Field(default=5, description="Database connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")

    @property
    def url(self) -> str:
        """Get the database URL."""
        db_file = self._get_db_file_path()
        return f"sqlite+aiosqlite:///{db_file}"

    def _get_db_file_path(self) -> str:
        """Determine the database file path based on configuration."""
        if self.file_path:
            return self.file_path

        if self.data_dir:
            data_dir = Path(self.data_dir)
            data_dir.mkdir(parents=True, exist_ok=True)
            return str(data_dir / "nba_stats.db")

        # Default to backend root directory
        backend_root = Path(__file__).parent.parent.parent
        return str(backend_root / "nba_stats.db")


class APISettings(BaseSettings):
    """API configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="NBA_STATS_API_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    title: str = Field(default="NBA Stats API", description="API title")
    version: str = Field(default="1.0.0", description="API version")
    description: str = Field(
        default="FastAPI application for NBA statistics data",
        description="API description",
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    docs_url: str = Field(default="/docs", description="Swagger UI docs URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc URL")

    # Rate limiting
    rate_limit_requests: int = Field(default=100, description="Requests per minute")
    rate_limit_window: int = Field(
        default=60, description="Rate limit window in seconds"
    )

    # Testing rate limits (more lenient)
    test_rate_limit_requests: int = Field(
        default=10000, description="Test requests per minute"
    )
    test_rate_limit_window: int = Field(
        default=60, description="Test rate limit window in seconds"
    )

    # CORS settings
    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origins")
    cors_methods: list[str] = Field(default=["*"], description="Allowed CORS methods")
    cors_headers: list[str] = Field(default=["*"], description="Allowed CORS headers")


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="NBA_STATS_SECURITY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # JWT settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens",
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes"
    )

    # Admin settings
    admin_enabled: bool = Field(default=True, description="Enable admin endpoints")
    admin_api_key: Optional[str] = Field(
        default=None, description="API key for admin endpoints"
    )

    # Input validation settings
    max_request_size: int = Field(
        default=10 * 1024 * 1024, description="Maximum request size in bytes (10MB)"
    )
    max_query_params: int = Field(
        default=50, description="Maximum number of query parameters"
    )
    max_header_size: int = Field(
        default=8192, description="Maximum total header size in bytes"
    )
    max_string_length: int = Field(
        default=500, description="Maximum string length for input sanitization"
    )

    # Rate limiting for admin endpoints
    admin_rate_limit_requests: int = Field(
        default=10, description="Admin requests per minute"
    )
    admin_rate_limit_window: int = Field(
        default=60, description="Admin rate limit window in seconds"
    )

    # Security headers
    enable_security_headers: bool = Field(
        default=True, description="Enable security headers"
    )
    enable_csp: bool = Field(default=True, description="Enable Content Security Policy")

    # Data sanitization
    enable_xss_protection: bool = Field(
        default=True, description="Enable XSS protection"
    )
    enable_sql_injection_protection: bool = Field(
        default=True, description="Enable SQL injection protection"
    )

    # Audit logging
    enable_admin_audit_logging: bool = Field(
        default=True, description="Enable admin action audit logging"
    )


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="NBA_STATS_LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    file_path: Optional[str] = Field(
        default=None, description="Log file path (console only if None)"
    )
    max_file_size: int = Field(
        default=10 * 1024 * 1024, description="Max log file size in bytes"
    )
    backup_count: int = Field(default=5, description="Number of backup log files")


class NBAAPISettings(BaseSettings):
    """NBA API configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="NBA_STATS_NBA_API_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    timeout: int = Field(default=30, description="API request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    retry_delay: int = Field(default=1, description="Delay between retries in seconds")
    rate_limit_delay: float = Field(
        default=0.6, description="Delay between requests to respect rate limits"
    )


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    environment: str = Field(
        default="development",
        description="Application environment",
        validation_alias="NBA_STATS_ENVIRONMENT",
    )

    # Sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    api: APISettings = Field(default_factory=APISettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    nba_api: NBAAPISettings = Field(default_factory=NBAAPISettings)

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() in ("development", "dev")

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() in ("production", "prod")

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment.lower() in ("testing", "test")


# Global settings instance
settings = Settings()


def reload_settings() -> Settings:
    """Reload settings from environment variables. Useful for testing."""
    global settings
    settings = Settings()
    return settings
