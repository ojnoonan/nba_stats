from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Path
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.core.config import settings
from app.schemas.validation import TeamIdSchema, validate_nba_team_id
from app.models.models import Team as TeamModel, DataUpdateStatus
from app.database.database import get_db, get_async_db
from app.services.nba_data_service import NBADataService

router = APIRouter(
    prefix="/teams",
    tags=["teams"]
)

logger = logging.getLogger(__name__)

@router.get("")  # Changed from "/"
def get_teams(db: Session = Depends(get_db)):
    """Get all teams"""
    try:
        teams = db.query(TeamModel).all()
        return teams
    except Exception as e:
        logger.error(f"Error fetching teams: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{team_id}")
def get_team(
    team_id: int = Path(..., ge=1, le=1611661399, description="NBA team ID"),
    db: Session = Depends(get_db)
):
    """Get a specific team by ID"""
    try:
        # Additional validation
        validate_nba_team_id(team_id)
        
        team = db.query(TeamModel).filter(TeamModel.team_id == team_id).first()
        if team is None:
            raise HTTPException(status_code=404, detail="Team not found")
        return team
    except ValueError as ve:
        logger.warning(f"Validation error in get_team: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{team_id}/update")
async def update_team(
    team_id: int = Path(..., ge=1, le=1611661399, description="NBA team ID"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Trigger an update for a specific team's data"""
    try:
        # Validate team ID
        validate_nba_team_id(team_id)
        
        # First check if the team exists
        team = db.query(TeamModel).filter(TeamModel.team_id == team_id).first()
        if team is None:
            raise HTTPException(status_code=404, detail="Team not found")

        # Check if an update is already in progress
        status = db.query(DataUpdateStatus).first()
        if status and status.is_updating:
            raise HTTPException(status_code=400, detail="An update is already in progress")

        # Create a background task to update the team data
        async def update_team_data():
            async with get_async_db() as db:
                try:
                    service = NBADataService(db)
                    await service.update_team_players(team_id)
                except Exception as e:
                    # Update status on error
                    status = db.query(DataUpdateStatus).first()
                    if status:
                        status.last_error = str(e)
                        status.last_error_time = datetime.utcnow()
                        status.is_updating = False
                        db.commit()
                    raise e

        background_tasks.add_task(update_team_data)
        return {"message": f"Update initiated for team {team_id}"}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))