from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.database.database import get_db
from app.models.models import DataUpdateStatus, Team  # Import Team
from app.services.nba_data_service import NBADataService

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

@router.get("/status")
async def get_admin_status(db: Session = Depends(get_db)):
    """Get detailed status of all data components"""
    status = db.query(DataUpdateStatus).first()
    if not status:
        status = DataUpdateStatus(
            is_updating=False,
            current_phase=None,
            last_successful_update=None,
            next_scheduled_update=None
        )
        db.add(status)
        db.commit()
    
    return {
        "last_update": status.last_successful_update,
        "next_update": status.next_scheduled_update,
        "is_updating": status.is_updating,
        "current_phase": status.current_phase,
        "components": {
            "teams": {
                "updated": status.teams_updated,
                "last_error": status.last_error if status.current_phase == "teams" else None
            },
            "players": {
                "updated": status.players_updated,
                "last_error": status.last_error if status.current_phase == "players" else None
            },
            "games": {
                "updated": status.games_updated,
                "last_error": status.last_error if status.current_phase == "games" else None
            }
        }
    }

@router.post("/update/all")
async def trigger_full_update(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger a full update of all data"""
    status = db.query(DataUpdateStatus).first()
    if status and status.is_updating:
        raise HTTPException(status_code=400, detail="Update already in progress")
    
    if not status:
        status = DataUpdateStatus()
        db.add(status)
    
    status.is_updating = True
    status.current_phase = "teams"
    db.commit()
    
    async def update_all():
        service = NBADataService(db)
        try:
            # Update teams
            await service.update_teams()
            status.teams_updated = True
            status.current_phase = "players"
            db.commit()

            # Update players
            teams = db.query(Team).all()
            for team in teams:
                await service.update_team_players(team.team_id)
            status.players_updated = True
            status.current_phase = "games"
            db.commit()

            # Update games
            await service.update_games()
            status.games_updated = True
            
            # Update status
            status.is_updating = False
            status.current_phase = None
            status.last_successful_update = datetime.utcnow()
            db.commit()
        except Exception as e:
            status.is_updating = False
            status.last_error = str(e)
            status.last_error_time = datetime.utcnow()
            db.commit()
            raise
    
    background_tasks.add_task(update_all)
    return {"message": "Full update initiated"}

@router.post("/update/cancel")
async def cancel_current_update(db: Session = Depends(get_db)):
    """Cancel any ongoing data update"""
    status = db.query(DataUpdateStatus).first()
    if not status:
        status = DataUpdateStatus()
        db.add(status)

    if status.is_updating:
        status.is_updating = False
        # Decide if we want to mark the current_phase as errored or just clear it
        # For now, let's clear it and set a general last_error
        status.last_error = f"Update of {status.current_phase or 'all components'} cancelled by user."
        status.last_error_time = datetime.utcnow()
        status.current_phase = None # Clear the current phase
        # Optionally, reset specific component updated flags if needed
        # status.teams_updated = False # Example, if cancelling mid-teams update
        # status.players_updated = False
        # status.games_updated = False
        db.commit()
        # It might be good to also attempt to cancel the background task itself if possible,
        # but FastAPI's BackgroundTasks are fire-and-forget.
        # For true cancellation, a more robust task queue (Celery, RQ) would be needed.
        return {"message": "Update cancellation request processed. The running task will attempt to stop gracefully if designed to do so, or will complete its current step."}
    else:
        return {"message": "No update is currently in progress."}

@router.post("/update/{component}")
async def trigger_component_update(
    component: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger update for a specific component (teams, players, or games)"""
    if component not in ["teams", "players", "games"]:
        raise HTTPException(status_code=400, detail="Invalid component specified")
    
    status = db.query(DataUpdateStatus).first()
    if status and status.is_updating:
        raise HTTPException(status_code=400, detail="Update already in progress")
    
    if not status:
        status = DataUpdateStatus()
        db.add(status)
    
    status.is_updating = True
    status.current_phase = component
    db.commit()
    
    async def update_component():
        service = NBADataService(db)
        try:
            if component == "teams":
                await service.update_teams()
                status.teams_updated = True
            elif component == "players":
                teams = db.query(Team).all()
                for team in teams:
                    await service.update_team_players(team.team_id)
                status.players_updated = True
            elif component == "games":
                await service.update_games()
                status.games_updated = True
            
            status.is_updating = False
            status.current_phase = None
            status.last_successful_update = datetime.utcnow()
            db.commit()
        except Exception as e:
            status.is_updating = False
            status.last_error = str(e)
            status.last_error_time = datetime.utcnow()
            db.commit()
            raise
    
    background_tasks.add_task(update_component)
    return {"message": f"{component} update initiated"}
