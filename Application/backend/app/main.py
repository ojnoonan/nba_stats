from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Body, APIRouter
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
from app.routers import teams, players, games, search, admin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def get_nba_service():
    """Get an instance of the NBA data service with a database session"""
    db = SessionLocal()
    try:
        return NBADataService(db)
    except Exception as e:
        db.close()
        raise e

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

# Create FastAPI app
app = FastAPI(
    title="NBA Stats API",
    docs_url="/docs",
    redoc_url="/redoc",
    # Disable automatic redirect for trailing slashes
    redirect_slashes=False
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Allow following redirects
    expose_headers=["location"]
)

# Create API router
api_router = APIRouter()

# Health check endpoint
@api_router.get("/status")
def health_check():
    """A simple health check endpoint"""
    return {"status": "ok", "timestamp": datetime.utcnow()}

# Include all routers under the API router
api_router.include_router(teams.router)
api_router.include_router(players.router)
api_router.include_router(games.router)
api_router.include_router(search.router)
api_router.include_router(admin.router)

# Mount all routes
app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    """Initialize database tables only on startup"""
    try:
        # Only initialize database tables, no data loading
        init_db()
        logger.info("Database tables initialized successfully")
        
        # Initialize empty status if needed
        db = SessionLocal()
        try:
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
                logger.info("Initialized empty status record")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@api_router.post("/update")
async def trigger_update(
    background_tasks: BackgroundTasks,
    update_types: List[str] = Body(default=None, embed=True)
):
    """Trigger a data update"""
    try:
        background_tasks.add_task(background_data_update, update_types)
        return {"message": "Update initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/reset-update-status")
async def reset_update_status(db: Session = Depends(get_db)):
    """Reset a stuck update status"""
    try:
        status = db.query(DataUpdateStatus).first()
        if status:
            status.is_updating = False
            status.current_phase = None
            db.commit()
        return {"message": "Update status reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting update status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7778)