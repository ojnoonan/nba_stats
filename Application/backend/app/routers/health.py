"""
Health check endpoints for monitoring application and service status.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.database.database import get_db
from app.exceptions import APIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus:
    """Health status constants."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


@router.get("/")
async def basic_health_check():
    """Basic health check endpoint."""
    return {
        "status": HealthStatus.HEALTHY,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.api.version,
        "environment": settings.environment,
    }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with database and service status."""

    checks = {
        "overall": HealthStatus.HEALTHY,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.api.version,
        "environment": settings.environment,
        "services": {},
    }

    # Check database connectivity
    db_status = await _check_database_health(db)
    checks["services"]["database"] = db_status

    # Check configuration
    config_status = _check_configuration_health()
    checks["services"]["configuration"] = config_status

    # Check application metrics
    metrics_status = _check_application_metrics()
    checks["services"]["metrics"] = metrics_status

    # Determine overall health
    service_statuses = [service["status"] for service in checks["services"].values()]

    if any(status == HealthStatus.UNHEALTHY for status in service_statuses):
        checks["overall"] = HealthStatus.UNHEALTHY
    elif any(status == HealthStatus.DEGRADED for status in service_statuses):
        checks["overall"] = HealthStatus.DEGRADED

    # Return appropriate HTTP status
    if checks["overall"] == HealthStatus.UNHEALTHY:
        return checks, status.HTTP_503_SERVICE_UNAVAILABLE
    elif checks["overall"] == HealthStatus.DEGRADED:
        return checks, status.HTTP_200_OK  # Still return 200 for degraded
    else:
        return checks, status.HTTP_200_OK


@router.get("/database")
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """Database-specific health check."""
    db_health = await _check_database_health(db)

    if db_health["status"] == HealthStatus.UNHEALTHY:
        return db_health, status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        return db_health, status.HTTP_200_OK


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Kubernetes-style readiness probe."""
    try:
        # Quick database connectivity check
        await db.execute(text("SELECT 1"))

        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return {
            "status": "not ready",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }, status.HTTP_503_SERVICE_UNAVAILABLE


@router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness probe."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": _get_uptime_seconds(),
    }


async def _check_database_health(db: AsyncSession) -> Dict:
    """Check database connectivity and performance."""
    start_time = datetime.utcnow()

    try:
        # Test basic connectivity
        await db.execute(text("SELECT 1"))

        # Test a more complex query (check if main tables exist)
        tables_query = text(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('teams', 'players', 'games', 'player_game_stats')
        """
        )
        result = await db.execute(tables_query)
        tables = result.fetchall()

        # Calculate response time
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Check if all required tables exist
        required_tables = {"teams", "players", "games", "player_game_stats"}
        existing_tables = {row[0] for row in tables}
        missing_tables = required_tables - existing_tables

        if missing_tables:
            return {
                "status": HealthStatus.DEGRADED,
                "message": f"Missing tables: {', '.join(missing_tables)}",
                "response_time_ms": response_time,
                "tables_found": len(existing_tables),
                "tables_expected": len(required_tables),
            }

        # Determine status based on response time
        if response_time > 1000:  # 1 second
            db_status = HealthStatus.DEGRADED
            message = "Database responding slowly"
        else:
            db_status = HealthStatus.HEALTHY
            message = "Database connection healthy"

        return {
            "status": db_status,
            "message": message,
            "response_time_ms": response_time,
            "tables_found": len(existing_tables),
            "database_url": settings.database.url.split("///")[0] + "///[REDACTED]",
        }

    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"Database connection failed: {str(e)}",
            "error": str(e),
        }


def _check_configuration_health() -> Dict:
    """Check configuration settings."""
    try:
        issues = []

        # Check critical settings
        if settings.security.secret_key == "your-secret-key-change-in-production":
            issues.append("Default secret key detected")

        if settings.is_production and settings.api.debug:
            issues.append("Debug mode enabled in production")

        if not settings.database.url:
            issues.append("Database URL not configured")

        # Determine status
        if issues:
            return {
                "status": HealthStatus.DEGRADED,
                "message": "Configuration issues detected",
                "issues": issues,
                "environment": settings.environment,
            }
        else:
            return {
                "status": HealthStatus.HEALTHY,
                "message": "Configuration is valid",
                "environment": settings.environment,
                "debug_mode": settings.api.debug,
            }

    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"Configuration check failed: {str(e)}",
            "error": str(e),
        }


def _check_application_metrics() -> Dict:
    """Check application-level metrics."""
    try:
        import sys

        import psutil

        # Get memory usage
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024

        # Get CPU usage
        cpu_percent = process.cpu_percent()

        # Check thresholds
        issues = []
        if memory_mb > 512:  # 512 MB threshold
            issues.append(f"High memory usage: {memory_mb:.1f}MB")

        if cpu_percent > 80:  # 80% CPU threshold
            issues.append(f"High CPU usage: {cpu_percent:.1f}%")

        status = HealthStatus.DEGRADED if issues else HealthStatus.HEALTHY

        return {
            "status": status,
            "message": "Application metrics collected",
            "metrics": {
                "memory_mb": round(memory_mb, 1),
                "cpu_percent": cpu_percent,
                "python_version": sys.version.split()[0],
                "process_id": process.pid,
            },
            "issues": issues,
        }

    except ImportError:
        # psutil not available
        return {
            "status": HealthStatus.HEALTHY,
            "message": "Metrics collection unavailable (psutil not installed)",
            "metrics": {},
        }
    except Exception as e:
        return {
            "status": HealthStatus.DEGRADED,
            "message": f"Metrics collection failed: {str(e)}",
            "error": str(e),
        }


def _get_uptime_seconds() -> float:
    """Get application uptime in seconds."""
    try:
        import psutil

        process = psutil.Process()
        return psutil.time.time() - process.create_time()
    except ImportError:
        return 0.0
