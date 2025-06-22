import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.asyncio import AsyncIOExecutor
from contextlib import asynccontextmanager

from app.database.database import SessionLocal
from app.models.models import DataUpdateStatus
from app.services.nba_data_service import NBADataService

logger = logging.getLogger(__name__)

class NBADataScheduler:
    def __init__(self):
        # Configure scheduler with AsyncIO executor
        executors = {
            'default': AsyncIOExecutor()
        }
        
        job_defaults = {
            'coalesce': True,
            'max_instances': 1,  # Prevent multiple instances of the same job
            'misfire_grace_time': 300  # 5 minutes grace time for missed jobs
        }
        
        self.scheduler = AsyncIOScheduler(
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
    async def start(self):
        """Start the scheduler and add jobs"""
        try:
            logger.info("Starting NBA Data Scheduler...")
            
            # Add scheduled jobs
            await self._add_scheduled_jobs()
            
            # Start the scheduler
            self.scheduler.start()
            logger.info("NBA Data Scheduler started successfully")
            
            # Set initial next_scheduled_update
            await self._update_next_scheduled_time()
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                logger.info("NBA Data Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
    
    async def _add_scheduled_jobs(self):
        """Add all scheduled jobs"""
        
        # Daily full update at 6 AM UTC (2 AM EDT / 11 PM PDT)
        self.scheduler.add_job(
            func=self._scheduled_full_update,
            trigger=CronTrigger(hour=6, minute=0),
            id='daily_full_update',
            name='Daily Full NBA Data Update',
            replace_existing=True
        )
        
        # Games update every 2 hours during the day (when games might be happening)
        self.scheduler.add_job(
            func=self._scheduled_games_update,
            trigger=CronTrigger(hour='10,12,14,16,18,20,22,0,2', minute=0),
            id='frequent_games_update',
            name='Frequent Games Update',
            replace_existing=True
        )
        
        # Weekly deep update (Sundays at 4 AM UTC)
        self.scheduler.add_job(
            func=self._scheduled_weekly_update,
            trigger=CronTrigger(day_of_week=6, hour=4, minute=0),  # Sunday = 6
            id='weekly_deep_update',
            name='Weekly Deep Update',
            replace_existing=True
        )
        
        logger.info("Scheduled jobs added:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name} (ID: {job.id})")
    
    async def _scheduled_full_update(self):
        """Run a full data update"""
        logger.info("Starting scheduled full data update...")
        
        db = SessionLocal()
        try:
            # Check if an update is already in progress
            status = db.query(DataUpdateStatus).first()
            if status and bool(status.is_updating):
                logger.warning("Skipping scheduled update - another update is in progress")
                return
            
            # Run the update
            service = NBADataService(db)
            await service.update_all_data()
            
            logger.info("Scheduled full data update completed successfully")
            
        except Exception as e:
            logger.error(f"Error in scheduled full update: {str(e)}")
            # Update status with error
            try:
                status = db.query(DataUpdateStatus).first()
                if status:
                    # Create updated status object and merge
                    status_update = DataUpdateStatus(
                        id=status.id,
                        last_error=f"Scheduled update failed: {str(e)}",
                        last_error_time=datetime.utcnow(),
                        is_updating=False,
                        current_phase=None,
                        last_successful_update=status.last_successful_update,
                        next_scheduled_update=status.next_scheduled_update,
                        games_updated=status.games_updated
                    )
                    db.merge(status_update)
                    db.commit()
            except:
                pass
        finally:
            db.close()
            # Update next scheduled time after each run
            await self._update_next_scheduled_time()
    
    async def _scheduled_games_update(self):
        """Run a games-only update"""
        logger.info("Starting scheduled games update...")
        
        db = SessionLocal()
        try:
            # Check if an update is already in progress
            status = db.query(DataUpdateStatus).first()
            if status and bool(status.is_updating):
                logger.warning("Skipping scheduled games update - another update is in progress")
                return
            
            # Set updating status
            if not status:
                status = DataUpdateStatus()
                db.add(status)
            
            # Create updated status object and merge
            status_update = DataUpdateStatus(
                id=getattr(status, 'id', None) if status else None,
                is_updating=True,
                current_phase='games',
                last_successful_update=getattr(status, 'last_successful_update', None) if status else None,
                last_error=getattr(status, 'last_error', None) if status else None,
                last_error_time=getattr(status, 'last_error_time', None) if status else None,
                next_scheduled_update=getattr(status, 'next_scheduled_update', None) if status else None,
                games_updated=getattr(status, 'games_updated', False) if status else False
            )
            db.merge(status_update)
            db.commit()
            
            # Run games update
            service = NBADataService(db)
            await service.update_games()
            
            # Update status - get fresh status object
            status = db.query(DataUpdateStatus).first()
            status_final = DataUpdateStatus(
                id=getattr(status, 'id', None),
                is_updating=False,
                current_phase=None,
                games_updated=True,
                last_successful_update=datetime.utcnow(),
                last_error=getattr(status, 'last_error', None),
                last_error_time=getattr(status, 'last_error_time', None),
                next_scheduled_update=getattr(status, 'next_scheduled_update', None)
            )
            db.merge(status_final)
            db.commit()
            
            logger.info("Scheduled games update completed successfully")
            
            # Update next scheduled time after each run
            await self._update_next_scheduled_time()
            
        except Exception as e:
            logger.error(f"Error in scheduled games update: {str(e)}")
            # Reset status on error
            try:
                status = db.query(DataUpdateStatus).first()
                if status:
                    status_error = DataUpdateStatus(
                        id=getattr(status, 'id', None),
                        is_updating=False,
                        current_phase=None,
                        last_error=f"Scheduled games update failed: {str(e)}",
                        last_error_time=datetime.utcnow(),
                        last_successful_update=getattr(status, 'last_successful_update', None),
                        next_scheduled_update=getattr(status, 'next_scheduled_update', None),
                        games_updated=getattr(status, 'games_updated', False)
                    )
                    db.merge(status_error)
                    db.commit()
            except:
                pass
        finally:
            db.close()
    
    async def _scheduled_weekly_update(self):
        """Run a comprehensive weekly update including cleanup"""
        logger.info("Starting scheduled weekly deep update...")
        
        db = SessionLocal()
        try:
            # Check if an update is already in progress
            status = db.query(DataUpdateStatus).first()
            if status and bool(status.is_updating):
                logger.warning("Skipping scheduled weekly update - another update is in progress")
                return
            
            # Run comprehensive update with cleanup
            service = NBADataService(db)
            
            # Set updating status
            if not status:
                status = DataUpdateStatus()
                db.add(status)
            
            # Create updated status object and merge
            status_update = DataUpdateStatus(
                id=getattr(status, 'id', None) if status else None,
                is_updating=True,
                current_phase='cleanup',
                last_successful_update=getattr(status, 'last_successful_update', None) if status else None,
                last_error=getattr(status, 'last_error', None) if status else None,
                last_error_time=getattr(status, 'last_error_time', None) if status else None,
                next_scheduled_update=getattr(status, 'next_scheduled_update', None) if status else None,
                games_updated=getattr(status, 'games_updated', False) if status else False
            )
            db.merge(status_update)
            db.commit()
            
            # Cleanup old seasons first
            await service.cleanup_old_seasons()
            
            # Then run full update
            await service.update_all_data()
            
            logger.info("Scheduled weekly deep update completed successfully")
            
            # Update next scheduled time after each run
            await self._update_next_scheduled_time()
            
        except Exception as e:
            logger.error(f"Error in scheduled weekly update: {str(e)}")
            # Update status with error
            try:
                status = db.query(DataUpdateStatus).first()
                if status:
                    status_error = DataUpdateStatus(
                        id=getattr(status, 'id', None),
                        last_error=f"Scheduled weekly update failed: {str(e)}",
                        last_error_time=datetime.utcnow(),
                        is_updating=False,
                        current_phase=None,
                        last_successful_update=getattr(status, 'last_successful_update', None),
                        next_scheduled_update=getattr(status, 'next_scheduled_update', None),
                        games_updated=getattr(status, 'games_updated', False)
                    )
                    db.merge(status_error)
                    db.commit()
            except:
                pass
        finally:
            db.close()
    
    async def _update_next_scheduled_time(self):
        """Update the next_scheduled_update timestamp in the database"""
        db = SessionLocal()
        try:
            # Get the next run time from the scheduler
            next_run = None
            jobs = self.scheduler.get_jobs()
            
            if jobs and self.scheduler.running:
                # Find the earliest next run time among all jobs
                next_runs = []
                for job in jobs:
                    if hasattr(job, 'next_run_time') and job.next_run_time:
                        next_runs.append(job.next_run_time)
                
                if next_runs:
                    next_run = min(next_runs)
            
            # Update the database
            status = db.query(DataUpdateStatus).first()
            if not status:
                status = DataUpdateStatus()
                db.add(status)
            
            if next_run:
                # Create updated status object and merge
                status_update = DataUpdateStatus(
                    id=getattr(status, 'id', None) if status else None,
                    next_scheduled_update=next_run.replace(tzinfo=None),  # Store as naive UTC
                    is_updating=getattr(status, 'is_updating', False) if status else False,
                    current_phase=getattr(status, 'current_phase', None) if status else None,
                    last_successful_update=getattr(status, 'last_successful_update', None) if status else None,
                    last_error=getattr(status, 'last_error', None) if status else None,
                    last_error_time=getattr(status, 'last_error_time', None) if status else None,
                    games_updated=getattr(status, 'games_updated', False) if status else False
                )
                db.merge(status_update)
            
            db.commit()
            logger.info(f"Next scheduled update: {next_run}")
            
        except Exception as e:
            logger.error(f"Error updating next scheduled time: {str(e)}")
        finally:
            db.close()
    
    def get_next_run_times(self):
        """Get next run times for all scheduled jobs"""
        jobs_info = []
        for job in self.scheduler.get_jobs():
            next_run = getattr(job, 'next_run_time', None) if hasattr(job, 'next_run_time') else None
            jobs_info.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': next_run
            })
        return jobs_info
    
    async def trigger_immediate_update(self, update_type='full'):
        """Manually trigger an immediate update"""
        if update_type == 'full':
            await self._scheduled_full_update()
        elif update_type == 'games':
            await self._scheduled_games_update()
        elif update_type == 'weekly':
            await self._scheduled_weekly_update()

# Global scheduler instance
_scheduler_instance = None

async def get_scheduler():
    """Get the global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = NBADataScheduler()
    return _scheduler_instance

async def start_scheduler():
    """Start the global scheduler"""
    scheduler = await get_scheduler()
    await scheduler.start()
    return scheduler

async def stop_scheduler():
    """Stop the global scheduler"""
    global _scheduler_instance
    if _scheduler_instance:
        await _scheduler_instance.stop()
        _scheduler_instance = None

@asynccontextmanager
async def scheduler_lifespan():
    """Context manager for scheduler lifecycle"""
    scheduler = None
    try:
        scheduler = await start_scheduler()
        yield scheduler
    finally:
        if scheduler:
            await scheduler.stop()