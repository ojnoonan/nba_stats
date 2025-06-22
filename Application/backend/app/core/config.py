"""
Configuration management for NBA Stats application.
Handles environment variables and application settings.
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import secrets
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database Configuration
    database_url: str = "sqlite:///./nba_stats.db"
    nba_stats_data_dir: str = "./"
    
    # API Configuration
    cors_origins: List[str] = ["http://localhost:7779", "http://127.0.0.1:7779"]
    debug: bool = False
    log_level: str = "INFO"
    
    # Server Configuration
    frontend_port: int = 7779
    backend_port: int = 7778
    
    # NBA API Configuration
    nba_api_rate_limit: float = 2.0
    max_retries: int = 5
    request_timeout: int = 180
    read_timeout: int = 120
    connect_timeout: int = 60
    
    # Security Configuration
    secret_key: str = ""
    cors_allow_credentials: bool = False
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = 30
    rate_limit_burst: int = 10
    
    # Environment
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment
    
    def __init__(self, **kwargs):
        """Initialize settings with proper secret key handling."""
        super().__init__(**kwargs)
        
        # Validate and handle secret key
        if not self.secret_key:
            if self.environment == "production":
                raise ValueError(
                    "SECRET_KEY environment variable must be set in production. "
                    "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )
            else:
                # Generate a random key for development if not provided
                self.secret_key = secrets.token_urlsafe(32)
                logger.warning(
                    "No SECRET_KEY provided. Generated a random key for development. "
                    "Set SECRET_KEY environment variable for production."
                )
        
        # Validate secret key length (minimum 32 characters for security)
        if len(self.secret_key) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long for security. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings."""
    return settings
