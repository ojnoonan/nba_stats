import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import (
    APIError,
    api_error_handler,
    general_exception_handler,
    http_exception_handler,
    sqlalchemy_error_handler,
    validation_error_handler,
)
from app.core.security import RateLimitMiddleware, SecurityHeadersMiddleware
from app.core.settings import settings
from app.database.database import (
    SQLALCHEMY_DATABASE_FILE_TO_USE,
    Base,
    engine,
    get_db,
    get_session_factory,
)
from app.database.init_db import init_db
from app.middleware import DataSanitizationMiddleware, InputValidationMiddleware
from app.middleware.error_middleware import (
    ErrorHandlingMiddleware,
    setup_error_handlers,
)
from app.models.models import DataUpdateStatus, Team
from app.routers import admin, games, health, players, search, teams
from app.services.nba_data_service import NBADataService

# Configure logging using settings
logging.basicConfig(
    level=getattr(logging, settings.logging.level.upper()),
    format=settings.logging.format,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def get_nba_service(session: AsyncSession) -> NBADataService:
    """Get an instance of the NBA data service with a database session"""
    return NBADataService(session)


async def background_data_update(update_types: Optional[List[str]] = None):
    """Background task to update NBA data"""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            nba_service = get_nba_service(session)

            if update_types:
                for update_type in update_types:
                    if update_type == "games":
                        await nba_service.update_games()
                    elif update_type == "teams":
                        await nba_service.update_teams()
                    elif update_type == "players":
                        stmt = select(Team)
                        result = await session.execute(stmt)
                        teams = result.scalars().all()
                        for team in teams:
                            await nba_service.update_team_players(team.team_id)
            else:
                await nba_service.update_all_data()
        except Exception as e:
            logger.error(f"Error in background data update: {str(e)}")
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application startup and shutdown events"""
    try:
        # Initialize database tables
        await init_db()
        logger.info("Database tables initialized successfully")
        logger.info(f"Using database at: {SQLALCHEMY_DATABASE_FILE_TO_USE}")

        session_factory = get_session_factory()
        async with session_factory() as session:
            try:
                # Get or create the single DataUpdateStatus row, ensuring no duplicates
                stmt = select(DataUpdateStatus)
                result = await session.execute(stmt)
                all_status = result.scalars().all()

                # If we have multiple statuses, keep the first one and delete the rest
                if len(all_status) > 1:
                    logger.warning(
                        f"Found {len(all_status)} status rows, cleaning up duplicates..."
                    )
                    status = all_status[0]
                    # Delete extra rows one by one
                    for extra_status in all_status[1:]:
                        await session.delete(extra_status)
                    await session.commit()  # commit the deletes
                elif len(all_status) == 1:
                    status = all_status[0]
                else:
                    status = None

                if not status:
                    # Create new status row if none exists
                    logger.info("Creating new DataUpdateStatus row")
                    status = DataUpdateStatus(
                        id=1,  # Ensure single row with primary key constraint
                        is_updating=False,
                        current_phase=None,
                        cancellation_requested=False,
                        last_successful_update=None,
                        next_scheduled_update=None,
                        teams_updated=False,
                        players_updated=False,
                        games_updated=False,
                        teams_percent_complete=0,
                        players_percent_complete=0,
                        games_percent_complete=0,
                        current_detail=None,
                        last_error=None,
                        last_error_time=None,
                        teams_last_update=None,
                        players_last_update=None,
                        games_last_update=None,
                    )
                    session.add(status)
                    await session.commit()

                # Reset update flags on startup
                if status.is_updating or status.cancellation_requested:
                    logger.info("Resetting update flags from previous run")
                    status.is_updating = False
                    status.cancellation_requested = False
                    await session.commit()

                # Log any previous errors
                if status.last_error:
                    logger.info(
                        f"Previous error: {status.last_error} at {status.last_error_time}"
                    )

            except Exception as e:
                logger.error(f"Error during startup processing: {str(e)}")
                raise
            finally:
                await session.close()

        logger.info("Startup process completed successfully")

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        logger.error(f"Database location: {SQLALCHEMY_DATABASE_FILE_TO_USE}")
        raise

    yield  # Server is running

    # Cleanup code here (if any)
    logger.info("Shutting down...")


# Create FastAPI app using settings
app = FastAPI(
    title=settings.api.title,
    version=settings.api.version,
    description=settings.api.description,
    docs_url=settings.api.docs_url,
    redoc_url=settings.api.redoc_url,
    redirect_slashes=False,
    lifespan=lifespan,
    debug=settings.api.debug,
)

# Add CORS middleware using settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=settings.api.cors_methods,
    allow_headers=settings.api.cors_headers,
    expose_headers=["location"],
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(DataSanitizationMiddleware)
app.add_middleware(InputValidationMiddleware)
# Always add rate limiting to ensure tests can verify headers
app.add_middleware(RateLimitMiddleware)

# Add error handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Setup enhanced error handlers
setup_error_handlers(app)

# Create API router
api_router = APIRouter()


# Health check and status endpoint
@api_router.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    """Get the current update status"""
    # Get the DataUpdateStatus row with id=1
    stmt = select(DataUpdateStatus).filter_by(id=1)
    result = await db.execute(stmt)
    status = result.scalar_one_or_none()

    if not status:
        logger.critical(
            "CRITICAL: DataUpdateStatus with id=1 not found. Application may be in an inconsistent state."
        )
        raise HTTPException(status_code=500, detail="Update status record not found")

    # Convert to dict for JSON response, excluding SQLAlchemy-specific attributes
    return {
        "is_updating": status.is_updating,
        "current_phase": status.current_phase,
        "cancellation_requested": status.cancellation_requested,
        "last_successful_update": status.last_successful_update,
        "next_scheduled_update": status.next_scheduled_update,
        "teams_updated": status.teams_updated,
        "players_updated": status.players_updated,
        "games_updated": status.games_updated,
        "teams_percent_complete": status.teams_percent_complete,
        "players_percent_complete": status.players_percent_complete,
        "games_percent_complete": status.games_percent_complete,
        "current_detail": status.current_detail,
        "last_error": status.last_error,
        "last_error_time": status.last_error_time,
        "teams_last_update": status.teams_last_update,
        "players_last_update": status.players_last_update,
        "games_last_update": status.games_last_update,
    }


@api_router.post("/update")
async def trigger_update(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    update_types: List[str] = Body(default=None, embed=True),
):
    """Trigger a data update"""
    # Get the current status
    stmt = select(DataUpdateStatus)
    result = await db.execute(stmt)
    status = result.scalars().first()

    # Prevent concurrent updates
    if status and status.is_updating:
        raise HTTPException(status_code=400, detail="Update already in progress")

    # Start background task
    background_tasks.add_task(background_data_update, update_types)
    return {
        "message": "Update started",
        "types": update_types if update_types else "all",
    }


@api_router.post("/update/games")
async def trigger_games_update(
    background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    """Trigger a games-only update"""
    # Get the current status
    stmt = select(DataUpdateStatus)
    result = await db.execute(stmt)
    status = result.scalars().first()

    # Prevent concurrent updates
    if status and status.is_updating:
        raise HTTPException(status_code=400, detail="Update already in progress")

    # Start background task for games only
    background_tasks.add_task(background_data_update, ["games"])
    return {"message": "Games update started"}


@api_router.post("/reset-update-status")
async def reset_update_status(db: AsyncSession = Depends(get_db)):
    """Reset a stuck update status"""
    # Get the current status
    stmt = select(DataUpdateStatus)
    result = await db.execute(stmt)
    status = result.scalars().first()

    # Reset the flags
    if status:
        status.is_updating = False
        status.current_phase = None
        status.cancellation_requested = False
        await db.commit()

    return {"message": "Update status reset"}


# Include all routers under the API router
api_router.include_router(teams.router)
api_router.include_router(players.router)
api_router.include_router(games.router)
api_router.include_router(search.router)
api_router.include_router(admin.router)
api_router.include_router(health.router)

# Mount all routes
app.include_router(api_router)
