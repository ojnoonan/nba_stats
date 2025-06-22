#!/usr/bin/env python3
"""
Test script for NBA Data Scheduler integration
"""
import asyncio
import sys
import logging
from datetime import datetime
from app.database.database import SessionLocal
from app.models.models import DataUpdateStatus
from app.services.scheduler import start_scheduler, stop_scheduler, get_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def test_scheduler():
    """Test the scheduler functionality"""
    db = SessionLocal()
    
    try:
        logger.info("=== NBA Data Scheduler Test ===")
        
        # Check initial database status
        status = db.query(DataUpdateStatus).first()
        if status:
            logger.info(f"Current status - Last update: {status.last_successful_update}")
            logger.info(f"Current status - Next scheduled: {status.next_scheduled_update}")
            logger.info(f"Current status - Is updating: {status.is_updating}")
        else:
            logger.info("No status record found")
        
        # Start scheduler
        logger.info("\n--- Starting Scheduler ---")
        scheduler = await start_scheduler()
        
        # Check scheduler status
        if scheduler and scheduler.scheduler.running:
            logger.info("✅ Scheduler started successfully")
            
            # Get job information
            jobs = scheduler.get_next_run_times()
            logger.info(f"Scheduled jobs ({len(jobs)}):")
            for job in jobs:
                logger.info(f"  - {job['name']} (ID: {job['id']}): next run at {job['next_run_time']}")
            
            # Check database status after scheduler start
            db.refresh(status) if status else None
            status = db.query(DataUpdateStatus).first()
            if status:
                logger.info(f"\nUpdated status - Next scheduled: {status.next_scheduled_update}")
        
        else:
            logger.error("❌ Failed to start scheduler")
        
        # Test scheduler stop
        logger.info("\n--- Stopping Scheduler ---")
        await stop_scheduler()
        logger.info("✅ Scheduler stopped successfully")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_scheduler())
