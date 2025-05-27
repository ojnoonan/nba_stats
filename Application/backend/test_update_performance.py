#!/usr/bin/env python
# Test script to analyze the performance of the update processes

import asyncio
import logging
import sys
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.database.database import Base, engine, get_db
from app.models.models import DataUpdateStatus, Game, Player, Team
from app.services.nba_data_service import NBADataService

pytest.skip(
    "Skipping performance integration tests until core functionality is stable",
    allow_module_level=True,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("TestUpdate")


async def measure_update_performance():
    """Measure the performance of update processes"""
    # Clear existing test status
    session = next(get_db())
    status = session.query(DataUpdateStatus).first()
    if status:
        status.is_updating = False
        status.current_phase = None
        status.cancellation_requested = False
        session.commit()

    # Create NBA data service
    service = NBADataService(session)

    # Test player update performance
    logger.info("=== Testing player update performance ===")
    start_time = datetime.now()

    # Get first few teams to test with
    teams = session.query(Team).limit(3).all()

    if not teams:
        logger.error("No teams found in database. Run a full update first.")
        return

    for i, team in enumerate(teams):
        logger.info(f"Updating players for team {team.name} ({i+1}/{len(teams)})")
        before = datetime.now()
        await service.update_team_players(team.team_id)
        after = datetime.now()
        duration = (after - before).total_seconds()
        logger.info(f"Team {team.name} player update took {duration:.2f} seconds")

    total_duration = (datetime.now() - start_time).total_seconds()
    logger.info(
        f"Total player update for {len(teams)} teams took {total_duration:.2f} seconds"
    )
    logger.info(f"Average time per team: {total_duration/len(teams):.2f} seconds")

    # Test game update performance
    logger.info("\n=== Testing game update performance ===")
    start_time = datetime.now()

    await service.update_games()

    total_duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"Game update took {total_duration:.2f} seconds")

    # Check status
    status = session.query(DataUpdateStatus).first()
    if status:
        logger.info(f"Status after tests: {status.__dict__}")

    # Close the session
    session.close()


if __name__ == "__main__":
    logger.info("Starting update performance test")
    asyncio.run(measure_update_performance())
    logger.info("Test completed")
