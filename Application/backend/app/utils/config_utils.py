"""
Configuration validation and secrets management utilities.
"""

import os
import secrets
import string
from pathlib import Path
from typing import Dict, List, Optional

from app.core.settings import settings
from app.exceptions import ConfigurationError


class ConfigValidator:
    """Validates configuration settings and provides security recommendations."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.recommendations: List[str] = []

    def validate_all(self) -> Dict[str, List[str]]:
        """Run all configuration validations."""
        self.errors.clear()
        self.warnings.clear()
        self.recommendations.clear()

        self._validate_security_settings()
        self._validate_database_settings()
        self._validate_api_settings()
        self._validate_environment_settings()

        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
        }

    def _validate_security_settings(self):
        """Validate security-related settings."""
        # Check secret key
        if settings.security.secret_key == "your-secret-key-change-in-production":
            if settings.is_production:
                self.errors.append(
                    "Default secret key detected in production environment"
                )
            else:
                self.warnings.append("Using default secret key (change for production)")

        # Check secret key strength
        if len(settings.security.secret_key) < 32:
            self.warnings.append("Secret key should be at least 32 characters long")

        # Check admin API key
        if settings.security.admin_enabled and not settings.security.admin_api_key:
            self.warnings.append("Admin endpoints enabled without API key")

        # Check production security settings
        if settings.is_production:
            if settings.api.debug:
                self.errors.append("Debug mode should be disabled in production")

            if "*" in settings.api.cors_origins:
                self.warnings.append("CORS allows all origins in production")

            if not settings.security.enable_security_headers:
                self.warnings.append("Security headers should be enabled in production")

    def _validate_database_settings(self):
        """Validate database-related settings."""
        try:
            db_file = Path(settings.database._get_db_file_path())

            # Check if database directory exists
            if not db_file.parent.exists():
                self.warnings.append(
                    f"Database directory does not exist: {db_file.parent}"
                )

            # Check database file permissions (if it exists)
            if db_file.exists():
                stat = db_file.stat()
                # Check if file is readable/writable
                if not os.access(db_file, os.R_OK | os.W_OK):
                    self.errors.append(f"Database file permissions issue: {db_file}")

        except Exception as e:
            self.errors.append(f"Database configuration error: {str(e)}")

    def _validate_api_settings(self):
        """Validate API-related settings."""
        # Check rate limiting
        if settings.api.rate_limit_requests <= 0:
            self.warnings.append("Rate limiting is effectively disabled")

        # Check API version format
        if not settings.api.version:
            self.warnings.append("API version not specified")

        # Check CORS settings
        if not settings.api.cors_origins:
            self.warnings.append("No CORS origins configured")

    def _validate_environment_settings(self):
        """Validate environment-specific settings."""
        valid_environments = {
            "development",
            "dev",
            "production",
            "prod",
            "testing",
            "test",
        }

        if settings.environment.lower() not in valid_environments:
            self.warnings.append(f"Unknown environment: {settings.environment}")

        # Check for required environment variables
        required_env_vars = [
            "NBA_STATS_ENVIRONMENT",
        ]

        for env_var in required_env_vars:
            if not os.getenv(env_var):
                self.recommendations.append(
                    f"Consider setting {env_var} environment variable"
                )


class SecretsManager:
    """Manages application secrets and provides secure defaults."""

    @staticmethod
    def generate_secret_key(length: int = 64) -> str:
        """Generate a cryptographically secure secret key."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(length)

    @staticmethod
    def validate_secret_strength(secret: str) -> Dict[str, bool]:
        """Validate the strength of a secret."""
        return {
            "min_length": len(secret) >= 32,
            "has_uppercase": any(c.isupper() for c in secret),
            "has_lowercase": any(c.islower() for c in secret),
            "has_digits": any(c.isdigit() for c in secret),
            "has_special": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in secret),
        }

    @staticmethod
    def create_env_template() -> str:
        """Create a .env template with secure defaults."""
        template = f"""# NBA Stats Application Environment Configuration
# Copy this file to .env and update the values

# Environment
NBA_STATS_ENVIRONMENT=development

# Database Configuration
NBA_STATS_DB_FILE=nba_stats.db
NBA_STATS_DB_ECHO=false

# API Configuration
NBA_STATS_API_TITLE=NBA Stats API
NBA_STATS_API_VERSION=1.0.0
NBA_STATS_API_DEBUG=false
NBA_STATS_API_DOCS_URL=/docs
NBA_STATS_API_REDOC_URL=/redoc

# Security Configuration
NBA_STATS_SECURITY_SECRET_KEY={SecretsManager.generate_secret_key()}
NBA_STATS_SECURITY_ALGORITHM=HS256
NBA_STATS_SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES=30
NBA_STATS_SECURITY_ADMIN_ENABLED=true
NBA_STATS_SECURITY_ADMIN_API_KEY={SecretsManager.generate_api_key()}

# Rate Limiting
NBA_STATS_API_RATE_LIMIT_REQUESTS=100
NBA_STATS_API_RATE_LIMIT_WINDOW=60

# Logging
NBA_STATS_LOG_LEVEL=INFO
NBA_STATS_LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# NBA API Configuration
NBA_STATS_NBA_API_TIMEOUT=30
NBA_STATS_NBA_API_MAX_RETRIES=3
NBA_STATS_NBA_API_RETRY_DELAY=1
NBA_STATS_NBA_API_RATE_LIMIT_DELAY=0.6
"""
        return template

    @staticmethod
    def save_env_template(file_path: str = ".env.example") -> None:
        """Save the environment template to a file."""
        template = SecretsManager.create_env_template()

        with open(file_path, "w") as f:
            f.write(template)

        print(f"Environment template saved to {file_path}")
        print("Copy this file to .env and update the values as needed.")


def validate_configuration() -> None:
    """Validate the current configuration and raise errors for critical issues."""
    validator = ConfigValidator()
    results = validator.validate_all()

    if results["errors"]:
        error_msg = "Configuration validation failed:\n" + "\n".join(results["errors"])
        raise ConfigurationError(error_msg)

    # Log warnings and recommendations
    if results["warnings"]:
        import logging

        logger = logging.getLogger(__name__)
        for warning in results["warnings"]:
            logger.warning(f"Configuration warning: {warning}")

    if results["recommendations"]:
        import logging

        logger = logging.getLogger(__name__)
        for recommendation in results["recommendations"]:
            logger.info(f"Configuration recommendation: {recommendation}")


def ensure_secure_defaults() -> None:
    """Ensure secure defaults are in place for production."""
    if settings.is_production:
        issues = []

        if settings.security.secret_key == "your-secret-key-change-in-production":
            issues.append("Secret key must be changed for production")

        if settings.api.debug:
            issues.append("Debug mode must be disabled for production")

        if "*" in settings.api.cors_origins:
            issues.append("CORS should not allow all origins in production")

        if issues:
            raise ConfigurationError(
                f"Production security requirements not met: {'; '.join(issues)}"
            )
