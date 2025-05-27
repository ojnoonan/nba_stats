from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db, get_session_factory
from app.middleware.admin_security import (
    check_admin_rate_limit,
    get_admin_credentials,
    log_admin_action,
)
from app.models.models import DataUpdateStatus, Team
from app.schemas.validation import AdminKeyValidation
from app.services.nba_data_service import NBADataService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/status")
async def get_admin_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_key: Optional[str] = Depends(get_admin_credentials),
    _rate_limit: None = Depends(check_admin_rate_limit),
):
    """Get detailed status of all data components"""
    log_admin_action(request, "get_status")

    stmt = select(DataUpdateStatus)
    result = await db.execute(stmt)
    status = result.scalar_one_or_none()

    if not status:
        status = DataUpdateStatus(
            is_updating=False,
            current_phase=None,
            last_successful_update=None,
            next_scheduled_update=None,
        )
        db.add(status)
        await db.commit()

    return {
        "last_update": status.last_successful_update,
        "next_update": status.next_scheduled_update,
        "is_updating": status.is_updating,
        "cancellation_requested": status.cancellation_requested,
        "current_phase": status.current_phase,
        "components": {
            "teams": {
                "updated": status.teams_updated,
                "last_error": (
                    status.last_error if status.current_phase == "teams" else None
                ),
            },
            "players": {
                "updated": status.players_updated,
                "last_error": (
                    status.last_error if status.current_phase == "players" else None
                ),
            },
            "games": {
                "updated": status.games_updated,
                "last_error": (
                    status.last_error if status.current_phase == "games" else None
                ),
            },
        },
    }


@router.post("/update/all")
async def trigger_full_update(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    admin_key: Optional[str] = Depends(get_admin_credentials),
    _rate_limit: None = Depends(check_admin_rate_limit),
):
    """Trigger a full update of all data"""
    log_admin_action(request, "trigger_full_update")

    stmt = select(DataUpdateStatus)
    result = await db.execute(stmt)
    status = result.scalar_one_or_none()

    if status and status.is_updating:
        raise HTTPException(status_code=400, detail="Update already in progress")

    if not status:
        status = DataUpdateStatus()
        db.add(status)

    status.is_updating = True
    status.current_phase = "teams"
    await db.commit()

    async def update_all():
        session_factory = get_session_factory()
        async with session_factory() as session:
            service = NBADataService(session)
            try:
                await service.update_all_data()
            except Exception as e:
                # Get status to update error information
                stmt = select(DataUpdateStatus)
                result = await session.execute(stmt)
                status = result.scalar_one_or_none()
                if status:
                    status.is_updating = False
                    status.last_error = str(e)
                    status.last_error_time = datetime.utcnow()
                    await session.commit()
                raise

    background_tasks.add_task(update_all)
    return {"message": "Full update initiated"}


@router.post("/update/cancel")
async def cancel_current_update(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_key: Optional[str] = Depends(get_admin_credentials),
    _rate_limit: None = Depends(check_admin_rate_limit),
):
    """Cancel any ongoing data update"""
    log_admin_action(request, "cancel_update")
    stmt = select(DataUpdateStatus)
    result = await db.execute(stmt)
    status = result.scalar_one_or_none()

    if not status:
        status = DataUpdateStatus()
        db.add(status)

    if status.is_updating:
        status.is_updating = False
        status.cancellation_requested = True
        # Decide if we want to mark the current_phase as errored or just clear it
        # For now, let's clear it and set a general last_error
        status.last_error = (
            f"Update of {status.current_phase or 'all components'} cancelled by user."
        )
        status.last_error_time = datetime.utcnow()
        status.current_phase = None  # Clear the current phase
        # Optionally, reset specific component updated flags if needed
        # status.teams_updated = False # Example, if cancelling mid-teams update
        # status.players_updated = False
        # status.games_updated = False
        await db.commit()
        # It might be good to also attempt to cancel the background task itself if possible,
        # but FastAPI's BackgroundTasks are fire-and-forget.
        # For true cancellation, a more robust task queue (Celery, RQ) would be needed.
        return {
            "message": "Update cancellation request processed. The running task will attempt to stop gracefully if designed to do so, or will complete its current step."
        }
    else:
        return {"message": "No update is currently in progress."}


@router.post("/update/{component}")
async def trigger_component_update(
    component: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    admin_key: Optional[str] = Depends(get_admin_credentials),
    _rate_limit: None = Depends(check_admin_rate_limit),
):
    """Trigger update for a specific component (teams, players, or games)"""
    if component not in ["teams", "players", "games"]:
        raise HTTPException(status_code=400, detail="Invalid component specified")

    log_admin_action(request, f"trigger_component_update", f"component: {component}")

    stmt = select(DataUpdateStatus)
    result = await db.execute(stmt)
    status = result.scalar_one_or_none()

    if status and status.is_updating:
        raise HTTPException(status_code=400, detail="Update already in progress")

    if not status:
        status = DataUpdateStatus()
        db.add(status)

    status.is_updating = True
    status.current_phase = component
    await db.commit()

    async def update_component():
        session_factory = get_session_factory()
        async with session_factory() as session:
            service = NBADataService(session)
            status = None
            try:
                # Refresh status in this session
                stmt = select(DataUpdateStatus)
                result = await session.execute(stmt)
                status = result.scalar_one_or_none()
                if not status:
                    status = DataUpdateStatus()
                    session.add(status)

                if component == "teams":
                    await service.update_teams()
                    status.teams_updated = True
                elif component == "players":
                    stmt = select(Team)
                    result = await session.execute(stmt)
                    teams = result.scalars().all()
                    for team in teams:
                        await service.update_team_players(team.team_id)
                    status.players_updated = True
                elif component == "games":
                    await service.update_games()
                    status.games_updated = True

                status.is_updating = False
                status.current_phase = None
                status.last_successful_update = datetime.utcnow()
                await session.commit()
            except Exception as e:
                if status:
                    status.is_updating = False
                    status.last_error = str(e)
                    status.last_error_time = datetime.utcnow()
                    await session.commit()
                raise

    background_tasks.add_task(update_component)
    return {"message": f"{component} update initiated"}
