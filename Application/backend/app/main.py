from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio
import logging
import os
import sys

from app.models.models import DataUpdateStatus, Team
from app.database.database import get_db, get_async_db, engine, Base, SessionLocal
from app.database.init_db import init_db
from app.services.nba_data_service import NBADataService
from app.routers import teams, players, games, search

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def get_nba_service():
    """Get an instance of the NBA data service with a database session"""
    db = SessionLocal()
    try:
        yield NBADataService(db)
    finally:
        db.close()

# Create FastAPI app
app = FastAPI(
    title="NBA Stats API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware with specific allowed origins
allowed_origins = [
    "http://localhost:7779",
    "http://127.0.0.1:7779",
    "http://192.168.1.89:7779",  # Add your local IP
    "http://192.168.1.89"        # Add your local IP without port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Range"]
)

# Initialize database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")
    raise

async def background_data_update(update_types: Optional[List[str]] = None):
    """Background task to update NBA data"""
    try:
        nba_service = get_nba_service()
        if update_types:
            for update_type in update_types:
                if update_type == "games":
                    await nba_service.update_games()
                elif update_type == "teams":
                    await nba_service.update_teams()
                elif update_type == "players":
                    for team in nba_service.db.query(Team).all():
                        await nba_service.update_team_players(team.team_id)
        else:
            await nba_service.update_all_data()
    except Exception as e:
        logger.error(f"Error in background data update: {str(e)}")
        raise

# Initialize scheduler and data
@app.on_event("startup")
async def startup_event():
    try:
        # Create initial status record if it doesn't exist
        db = next(get_db())
        try:
            status = db.query(DataUpdateStatus).first()
            if not status:
                status = DataUpdateStatus(
                    is_updating=False,
                    current_phase=None,
                    last_successful_update=None,
                    next_scheduled_update=datetime.utcnow() + timedelta(hours=6)
                )
                db.add(status)
                db.commit()

            # Check if we need to do initial data load
            teams_count = db.query(Team).count()
            if teams_count == 0:
                logger.info("No teams found in database. Starting initial data load...")
                background_tasks = BackgroundTasks()
                background_tasks.add_task(background_data_update)
                status.is_updating = True
                status.current_phase = 'initializing'
                db.commit()
                
        except Exception as e:
            logger.error(f"Error creating initial status: {str(e)}")
        finally:
            db.close()
            
        # Try to start the scheduler if available
        try:
            from app.services.scheduler import start_scheduler
            scheduler = start_scheduler()
            logger.info("Scheduler started successfully")
        except ImportError:
            logger.warning("Scheduler not available - automatic updates disabled")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

# Include routers
app.include_router(teams.router)
app.include_router(players.router)
app.include_router(games.router)
app.include_router(search.router)

@app.get("/")
async def root():
    return {"message": "Welcome to NBA Stats API"}

@app.get("/status")
async def get_status(db: Session = Depends(get_db)):
    try:
        status = db.query(DataUpdateStatus).first()
        if not status:
            status = DataUpdateStatus(
                is_updating=True,
                current_phase='initializing',
                last_successful_update=datetime.utcnow(),
                next_scheduled_update=datetime.utcnow() + timedelta(hours=6)
            )
            db.add(status)
            db.commit()
        
        return {
            "last_update": status.last_successful_update,
            "next_update": status.next_scheduled_update,
            "is_updating": status.is_updating,
            "current_phase": status.current_phase,
            "teams_updated": status.teams_updated,
            "players_updated": status.players_updated,
            "games_updated": status.games_updated,
            "last_error": status.last_error,
            "last_error_time": status.last_error_time
        }
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update")
async def trigger_update(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    update_types: List[str] = Body(default=None, embed=True)
):
    """
    Trigger a data update. Can specify which types of data to update.
    Valid update_types: ["teams", "players", "games"]
    If no types specified, updates everything.
    """
    try:
        status = db.query(DataUpdateStatus).first()
        if status and status.is_updating:
            raise HTTPException(status_code=400, detail="Update already in progress")
        
        if update_types:
            valid_types = {"teams", "players", "games"}
            invalid_types = set(update_types) - valid_types
            if invalid_types:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid update types: {invalid_types}. Valid types are: {valid_types}"
                )
            
        background_tasks.add_task(background_data_update, update_types)
        return {"message": f"Update initiated for: {update_types if update_types else 'all data'}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset-update-status")
async def reset_update_status(db: Session = Depends(get_db)):
    """Reset the update status if it's stuck"""
    try:
        status = db.query(DataUpdateStatus).first()
        if not status:
            status = DataUpdateStatus()
            db.add(status)
        
        # Reset all flags
        status.is_updating = False
        status.teams_updated = False
        status.players_updated = False
        status.games_updated = False
        status.current_phase = None
        status.last_error = "Status reset manually"
        status.last_error_time = datetime.utcnow()
        status.last_successful_update = datetime.utcnow() - timedelta(hours=6)
        status.next_scheduled_update = datetime.utcnow()
        
        db.commit()
        return {"message": "Update status reset successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resetting status: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)