import logging
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from app.database.database import get_async_db
from app.services.nba_data_service import NBADataService
from app.models.models import DataUpdateStatus

logger = logging.getLogger(__name__)

async def update_nba_data():
    """Update NBA data in the database"""
    logger.info("Starting NBA data update...")
    try:
        async with get_async_db() as db:
            service = NBADataService(db)
            
            # Update status to indicate job is running
            status = db.query(DataUpdateStatus).first()
            if not status:
                status = DataUpdateStatus()
                db.add(status)
            status.is_updating = True
            status.current_phase = 'starting'
            db.commit()
            
            try:
                # Run the update
                await service.update_all_data()
                logger.info("NBA data update completed successfully")
                
            except asyncio.CancelledError:
                logger.warning("NBA data update was cancelled")
                status = db.query(DataUpdateStatus).first()
                if status:
                    status.is_updating = False
                    status.last_error = "Job was cancelled"
                    status.last_error_time = datetime.utcnow()
                    db.commit()
                raise
                
            except Exception as e:
                logger.error(f"Error during NBA data update: {str(e)}")
                status = db.query(DataUpdateStatus).first()
                if status:
                    status.is_updating = False
                    status.last_error = str(e)
                    status.last_error_time = datetime.utcnow()
                    db.commit()
                raise
                
    except Exception as e:
        logger.error(f"Error during NBA data update: {str(e)}")
        raise

def job_listener(event):
    """Listen for job events to handle errors"""
    if event.exception:
        logger.error(f'Job {event.job_id} failed: {event.exception}')
    else:
        logger.info(f'Job {event.job_id} completed successfully')

def start_scheduler():
    """Start the scheduler for periodic NBA data updates"""
    try:
        scheduler = AsyncIOScheduler()
        
        # Add event listeners
        scheduler.add_listener(job_listener, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)
        
        # Schedule the update_nba_data job to run every 6 hours
        scheduler.add_job(
            update_nba_data,
            trigger='interval',
            hours=6,
            id='update_nba_data',
            next_run_time=datetime.now(),  # Run immediately on startup
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600  # Allow job to be 1 hour late
        )
        
        scheduler.start()
        logger.info("NBA data update scheduler started successfully")
        return scheduler
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        raise