from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import logging

from app.database.database import get_db, SessionLocal
from app.models.models import DataUpdateStatus, Team  # Import Team
from app.services.nba_data_service import NBADataService
from app.services.background_task_manager import BackgroundTaskManager, TaskStatus
from app.schemas.validation import AdminUpdateSchema, validate_nba_team_id, sanitize_string
from app.core.exceptions import ErrorHandler, ValidationException

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

logger = logging.getLogger(__name__)

# Global task manager instance
task_manager = BackgroundTaskManager()

@router.get("/status")
async def get_admin_status(db: Session = Depends(get_db)):
    """Get detailed status of all data components"""
    try:
        # Refresh the session to ensure we get the latest committed data
        db.expire_all()
        
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
        
        # Get current running task info
        active_tasks = task_manager.get_active_tasks()
        task_info = None
        if active_tasks:
            # Get the first active task (there should only be one update task at a time)
            task_info = list(active_tasks.values())[0]
        
        return {
            "last_update": getattr(status, 'last_successful_update'),
            "next_update": getattr(status, 'next_scheduled_update'),
            "is_updating": getattr(status, 'is_updating'),
            "current_phase": getattr(status, 'current_phase'),
            "last_error": getattr(status, 'last_error'),
            "last_error_time": getattr(status, 'last_error_time'),
            "task_info": task_info,
            "components": {
                "teams": {
                    "updated": getattr(status, 'teams_updated'),
                    "last_error": getattr(status, 'last_error') if getattr(status, 'current_phase') == "teams" else None
                },
                "players": {
                    "updated": getattr(status, 'players_updated'),
                    "last_error": getattr(status, 'last_error') if getattr(status, 'current_phase') == "players" else None
                },
                "games": {
                    "updated": getattr(status, 'games_updated'),
                    "last_error": getattr(status, 'last_error') if getattr(status, 'current_phase') == "games" else None
                }
            }
        }
    except Exception as e:
        raise ErrorHandler.handle_error(e, "get admin status")

@router.post("/update/all")
async def trigger_full_update(db: Session = Depends(get_db)):
    """Trigger a full update of all data"""
    status = db.query(DataUpdateStatus).first()
    if status and getattr(status, 'is_updating'):
        raise ValidationException("Update already in progress")
    
    # Check if there's already a task running
    active_tasks = task_manager.get_active_tasks()
    if active_tasks:
        raise ValidationException("Background task already in progress")
    
    if not status:
        status = DataUpdateStatus()
        db.add(status)
    
    # Update status using setattr to avoid SQLAlchemy column assignment issues
    setattr(status, 'is_updating', True)
    setattr(status, 'current_phase', "teams")
    db.commit()
    
    async def update_all_task(task_info):
        """Full update task with proper cancellation support"""
        # Create a fresh database session for the background task
        task_db = SessionLocal()
        # Get the status object in this session
        task_status = task_db.query(DataUpdateStatus).first()
        
        try:
            service = NBADataService(task_db)
            total_steps = 3  # teams, players, games
            # Step 1: Update teams
            await task_manager.update_progress(
                task_info.task_id, 
                progress=0,
                message="Updating teams..."
            )
            
            # Check for cancellation
            if task_info.cancellation_token.is_set():
                raise Exception("Task cancelled by user")
            
            await service.update_teams()
            setattr(task_status, 'teams_updated', True)
            setattr(task_status, 'current_phase', "players")
            task_db.commit()

            # Step 2: Update players
            await task_manager.update_progress(
                task_info.task_id, 
                progress=33,
                message="Updating players..."
            )
            
            # Check for cancellation
            if task_info.cancellation_token.is_set():
                raise Exception("Task cancelled by user")

            teams = task_db.query(Team).all()
            for i, team in enumerate(teams):
                # Check for cancellation more frequently during long operations
                if task_info.cancellation_token.is_set():
                    raise Exception("Task cancelled by user")
                
                await service.update_team_players(getattr(team, 'team_id'))
                
                # Update progress within players step
                player_progress = 33 + (33 * (i + 1) / len(teams))
                await task_manager.update_progress(
                    task_info.task_id, 
                    progress=player_progress,
                    message=f"Updated players for {getattr(team, 'name')} ({i+1}/{len(teams)})"
                )
            
            setattr(task_status, 'players_updated', True)
            setattr(task_status, 'current_phase', "games")
            task_db.commit()

            # Step 3: Update games
            await task_manager.update_progress(
                task_info.task_id, 
                progress=66,
                message="Updating games..."
            )
            
            # Check for cancellation
            if task_info.cancellation_token.is_set():
                raise Exception("Task cancelled by user")

            await service.update_games()
            setattr(task_status, 'games_updated', True)
            
            # Complete the task
            await task_manager.update_progress(
                task_info.task_id, 
                progress=100,
                message="Update completed successfully"
            )
            
            # Update status
            setattr(task_status, 'is_updating', False)
            setattr(task_status, 'current_phase', None)
            setattr(task_status, 'last_successful_update', datetime.utcnow())
            task_db.commit()
            
        except Exception as e:
            setattr(task_status, 'is_updating', False)
            setattr(task_status, 'last_error', str(e))
            setattr(task_status, 'last_error_time', datetime.utcnow())
            setattr(task_status, 'current_phase', None)
            task_db.commit()
            raise
        finally:
            task_db.close()
    
    # Start the background task
    task_id = await task_manager.start_task("update_all", "Full Data Update", update_all_task)
    return {"message": "Full update initiated", "task_id": task_id}

@router.post("/update/cancel")
async def cancel_current_update(db: Session = Depends(get_db)):
    """Cancel any ongoing data update"""
    status = db.query(DataUpdateStatus).first()
    if not status:
        status = DataUpdateStatus()
        db.add(status)

    if getattr(status, 'is_updating'):
        setattr(status, 'is_updating', False)
        # Decide if we want to mark the current_phase as errored or just clear it
        # For now, let's clear it and set a general last_error
        setattr(status, 'last_error', f"Update of {getattr(status, 'current_phase') or 'all components'} cancelled by user.")
        setattr(status, 'last_error_time', datetime.utcnow())
        setattr(status, 'current_phase', None) # Clear the current phase
        # Optionally, reset specific component updated flags if needed
        # setattr(status, 'teams_updated', False) # Example, if cancelling mid-teams update
        # setattr(status, 'players_updated', False)
        # setattr(status, 'games_updated', False)
        db.commit()
        
        # Cancel any active background tasks
        active_tasks = task_manager.get_active_tasks()
        for task_id in active_tasks.keys():
            await task_manager.cancel_task(task_id)
        
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
        raise ValidationException("Invalid component specified")
    
    status = db.query(DataUpdateStatus).first()
    if status and getattr(status, 'is_updating'):
        raise ValidationException("Update already in progress")
    
    if not status:
        status = DataUpdateStatus()
        db.add(status)
    
    setattr(status, 'is_updating', True)
    setattr(status, 'current_phase', component)
    db.commit()
    
    async def update_component():
        service = NBADataService(db)
        try:
            if component == "teams":
                await service.update_teams()
                setattr(status, 'teams_updated', True)
            elif component == "players":
                teams = db.query(Team).all()
                for team in teams:
                    await service.update_team_players(getattr(team, 'team_id'))
                # Fix headshot URLs for free agents after updating all team players
                await service.fix_free_agent_headshots()
                setattr(status, 'players_updated', True)
            elif component == "games":
                await service.update_games()
                setattr(status, 'games_updated', True)
            
            setattr(status, 'is_updating', False)
            setattr(status, 'current_phase', None)
            setattr(status, 'last_successful_update', datetime.utcnow())
            db.commit()
        except Exception as e:
            setattr(status, 'is_updating', False)
            setattr(status, 'last_error', str(e))
            setattr(status, 'last_error_time', datetime.utcnow())
            db.commit()
            raise
    
    background_tasks.add_task(update_component)
    return {"message": f"{component} update initiated"}
