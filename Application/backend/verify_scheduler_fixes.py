#!/usr/bin/env python3
"""
Comprehensive verification script for NBA Data Scheduler fixes
"""
import asyncio
import sys
import logging
import requests
import json
from datetime import datetime
from app.database.database import SessionLocal
from app.models.models import DataUpdateStatus, Game
from app.services.scheduler import get_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def test_api_endpoints():
    """Test API endpoints"""
    logger.info("=== Testing API Endpoints ===")
    
    base_url = "http://localhost:7778"
    
    # Test main status endpoint
    try:
        response = requests.get(f"{base_url}/status", timeout=10)
        if response.status_code == 200:
            status_data = response.json()
            logger.info("✅ Main status endpoint working")
            logger.info(f"   Last Update: {status_data.get('last_update', 'N/A')}")
            logger.info(f"   Next Update: {status_data.get('next_update', 'N/A')}")
            logger.info(f"   Is Updating: {status_data.get('is_updating', 'N/A')}")
        else:
            logger.error(f"❌ Main status endpoint failed: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Main status endpoint error: {str(e)}")
    
    # Test scheduler status endpoint
    try:
        response = requests.get(f"{base_url}/scheduler/status", timeout=10)
        if response.status_code == 200:
            scheduler_data = response.json()
            logger.info("✅ Scheduler status endpoint working")
            logger.info(f"   Scheduler Running: {scheduler_data.get('running', False)}")
            jobs = scheduler_data.get('jobs', [])
            logger.info(f"   Active Jobs: {len(jobs)}")
            for job in jobs:
                logger.info(f"      - {job['name']}: {job['next_run_time']}")
        else:
            logger.error(f"❌ Scheduler status endpoint failed: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Scheduler status endpoint error: {str(e)}")

def test_database_status():
    """Test database status and game data"""
    logger.info("\n=== Testing Database Status ===")
    
    db = SessionLocal()
    try:
        # Check data update status
        status = db.query(DataUpdateStatus).first()
        if status:
            logger.info("✅ DataUpdateStatus record exists")
            logger.info(f"   Last Successful Update: {status.last_successful_update}")
            logger.info(f"   Next Scheduled Update: {status.next_scheduled_update}")
            logger.info(f"   Currently Updating: {status.is_updating}")
            logger.info(f"   Current Phase: {status.current_phase}")
            
            # Check if timestamps make sense
            if status.next_scheduled_update:
                now = datetime.utcnow()
                if status.next_scheduled_update > now:
                    logger.info("✅ Next scheduled update is in the future")
                else:
                    logger.warning("⚠️ Next scheduled update is in the past")
            else:
                logger.warning("⚠️ No next scheduled update set")
        else:
            logger.error("❌ No DataUpdateStatus record found")
        
        # Check games data
        total_games = db.query(Game).count()
        logger.info(f"✅ Total games in database: {total_games}")
        
        # Check recent games
        recent_games = db.query(Game).filter(
            Game.date >= '2024-10-01'  # Current season
        ).count()
        logger.info(f"✅ Current season games: {recent_games}")
        
    except Exception as e:
        logger.error(f"❌ Database test error: {str(e)}")
    finally:
        db.close()

async def test_scheduler_functionality():
    """Test scheduler functionality"""
    logger.info("\n=== Testing Scheduler Functionality ===")
    
    try:
        scheduler = await get_scheduler()
        if scheduler and scheduler.scheduler.running:
            logger.info("✅ Scheduler instance accessible and running")
            
            jobs = scheduler.scheduler.get_jobs()
            logger.info(f"✅ Scheduler has {len(jobs)} active jobs")
            
            expected_jobs = ['daily_full_update', 'frequent_games_update', 'weekly_deep_update']
            actual_jobs = [job.id for job in jobs]
            
            for expected_job in expected_jobs:
                if expected_job in actual_jobs:
                    logger.info(f"✅ Job '{expected_job}' is scheduled")
                else:
                    logger.error(f"❌ Job '{expected_job}' is missing")
        else:
            logger.error("❌ Scheduler not accessible or not running")
    
    except Exception as e:
        logger.error(f"❌ Scheduler test error: {str(e)}")

async def main():
    """Run all verification tests"""
    logger.info("🏀 Starting NBA Data Scheduler Verification")
    logger.info("=" * 50)
    
    # Test API endpoints
    test_api_endpoints()
    
    # Test database status
    test_database_status()
    
    # Test scheduler functionality
    await test_scheduler_functionality()
    
    logger.info("\n" + "=" * 50)
    logger.info("🏀 NBA Data Scheduler Verification Complete")

if __name__ == "__main__":
    asyncio.run(main())
