from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Body, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.models.models import DataUpdateStatus, Team
from app.database.database import get_db, get_async_db, engine, Base, SessionLocal
from app.database.init_db import init_db
from app.services.nba_data_service import NBADataService
from app.services.scheduler import start_scheduler, stop_scheduler, get_scheduler
from app.routers import teams, players, games, search, admin
from app.middleware.validation import ValidationMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Global scheduler instance for lifecycle management
scheduler_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan including scheduler"""
    global scheduler_instance
    
    try:
        # Startup
        logger.info("Starting application with scheduler...")
        
        # Initialize database tables
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
        
        # Start the scheduler
        scheduler_instance = await start_scheduler()
        logger.info("Scheduler started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down application...")
        if scheduler_instance:
            await stop_scheduler()
            logger.info("Scheduler stopped successfully")

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
    nba_service = None
    try:
        nba_service = get_nba_service()
        
        # Get or create status record
        status = nba_service.db.query(DataUpdateStatus).first()
        if not status:
            status = DataUpdateStatus()
            nba_service.db.add(status)
        
        # Check if update is already in progress
        if getattr(status, 'is_updating', False):
            logger.warning("Update already in progress, skipping")
            return
        
        if update_types:
            # Set updating status
            setattr(status, 'is_updating', True)
            nba_service.db.commit()
            
            try:
                for update_type in update_types:
                    if update_type == "games":
                        setattr(status, 'current_phase', 'games')
                        nba_service.db.commit()
                        await nba_service.update_games()
                        setattr(status, 'games_updated', True)
                    elif update_type == "teams":
                        setattr(status, 'current_phase', 'teams')
                        nba_service.db.commit()
                        await nba_service.update_teams()
                        setattr(status, 'teams_updated', True)
                    elif update_type == "players":
                        setattr(status, 'current_phase', 'players')
                        nba_service.db.commit()
                        teams = nba_service.db.query(Team).all()
                        for team in teams:
                            await nba_service.update_team_players(getattr(team, 'team_id'))
                        setattr(status, 'players_updated', True)
                
                # Update final status
                setattr(status, 'current_phase', None)
                setattr(status, 'is_updating', False)
                setattr(status, 'last_successful_update', datetime.utcnow())
                nba_service.db.commit()
                
            except Exception as e:
                # Reset status on error
                setattr(status, 'is_updating', False)
                setattr(status, 'current_phase', None)
                setattr(status, 'last_error', str(e))
                setattr(status, 'last_error_time', datetime.utcnow())
                nba_service.db.commit()
                raise
        else:
            await nba_service.update_all_data()
    except Exception as e:
        logger.error(f"Error in background data update: {str(e)}")
        if nba_service and nba_service.db:
            try:
                status = nba_service.db.query(DataUpdateStatus).first()
                if status:
                    setattr(status, 'is_updating', False)
                    setattr(status, 'current_phase', None)
                    nba_service.db.commit()
            except:
                pass
        raise
    finally:
        if nba_service and nba_service.db:
            nba_service.db.close()

# Create FastAPI app
app = FastAPI(
    title="NBA Stats API",
    docs_url="/docs",
    redoc_url="/redoc",
    # Disable automatic redirect for trailing slashes
    redirect_slashes=False,
    lifespan=lifespan
)

# Set up rate limiter
app.state.limiter = limiter

# Custom rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    response = {
        "error": "Rate limit exceeded",
        "detail": f"Rate limit exceeded: {exc.detail}"
    }
    return JSONResponse(
        status_code=429, 
        content=response
    )

# Add security middleware
if settings.environment == "production":
    # Add HTTPS redirect and trusted host middleware for production
    from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["your-domain.com"])
else:
    # Allow localhost for development
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "*"])

# Add validation middleware (first in chain for security)
app.add_middleware(ValidationMiddleware)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    # Allow following redirects
    expose_headers=["location"]
)

# Create API router
api_router = APIRouter()

# Health check endpoint
@api_router.get("/status")
@limiter.limit(f"{settings.rate_limit_requests_per_minute}/minute")
def get_status(request: Request, db: Session = Depends(get_db)):
    """Get the current data update status"""
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
    
    return {
        "last_update": getattr(status, 'last_successful_update'),
        "next_update": getattr(status, 'next_scheduled_update'),
        "is_updating": getattr(status, 'is_updating'),
        "current_phase": getattr(status, 'current_phase'),
        "teams_updated": getattr(status, 'teams_updated'),
        "players_updated": getattr(status, 'players_updated'),
        "games_updated": getattr(status, 'games_updated'),
        "last_error": getattr(status, 'last_error'),
        "last_error_time": getattr(status, 'last_error_time')
    }

@api_router.post("/update")
@limiter.limit("5/minute")  # Stricter limit for update endpoint
async def trigger_update(
    request: Request,
    update_request: Optional[dict] = Body(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Trigger data update for specified types or all data"""
    # Extract update types from request body
    update_types = []
    if update_request and "update_types" in update_request:
        update_types = update_request["update_types"]
    
    # If no specific types provided, update all
    if not update_types:
        update_types = ["teams", "players", "games"]
    
    # Validate update types
    valid_types = {"teams", "players", "games"}
    for update_type in update_types:
        if update_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid update type: {update_type}")
    
    # Check if update is already in progress
    status = db.query(DataUpdateStatus).first()
    if status and getattr(status, 'is_updating'):
        raise HTTPException(status_code=400, detail="Update already in progress")
    
    # Start the background update
    background_tasks.add_task(background_data_update, update_types)
    
    return {"message": f"Update triggered for: {', '.join(update_types)}"}

# Include all routers under the API router
api_router.include_router(teams.router)
api_router.include_router(players.router)
api_router.include_router(games.router)
api_router.include_router(search.router)
api_router.include_router(admin.router)

@api_router.get("/scheduler/status")
async def get_scheduler_status():
    """Get the current scheduler status and next run times"""
    try:
        scheduler = await get_scheduler()
        if scheduler and scheduler.scheduler.running:
            next_runs = scheduler.get_next_run_times()
            return {
                "running": True,
                "jobs": next_runs
            }
        else:
            return {
                "running": False,
                "jobs": []
            }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/scheduler/trigger/{update_type}")
async def trigger_scheduler_update(update_type: str):
    """Manually trigger a scheduled update"""
    try:
        scheduler = await get_scheduler()
        if not scheduler:
            raise HTTPException(status_code=500, detail="Scheduler not available")
        
        if update_type not in ['full', 'games', 'weekly']:
            raise HTTPException(status_code=400, detail="Invalid update type. Use 'full', 'games', or 'weekly'")
        
        await scheduler.trigger_immediate_update(update_type)
        return {"message": f"Triggered {update_type} update successfully"}
    except Exception as e:
        logger.error(f"Error triggering scheduler update: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/reset-update-status")
async def reset_update_status(db: Session = Depends(get_db)):
    """Reset a stuck update status"""
    try:
        status = db.query(DataUpdateStatus).first()
        if status:
            setattr(status, 'is_updating', False)
            setattr(status, 'current_phase', None)
            db.commit()
        return {"message": "Update status reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting update status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount all routes
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7778)