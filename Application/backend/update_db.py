import argparse
import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select

from app.database.database import AsyncSessionLocal
from app.models.models import DataUpdateStatus, Game, Player, Team
from app.services.nba_data_service import NBADataService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def update_data(params: Optional[Dict[str, Any]] = None) -> None:
    """Update NBA data based on specified parameters"""
    async with AsyncSessionLocal() as session:
        nba_service = NBADataService(session)

        try:
            # Get current update status
            result = await session.execute(select(DataUpdateStatus))
            status = result.scalar_one_or_none()

            if not status:
                status = DataUpdateStatus()
                session.add(status)
                await session.commit()

            # Check for existing updates
            if status.is_updating:
                logger.warning("Update already in progress")
                return

            # Determine what needs updating
            games_need_update = not status.games_updated
            teams_need_update = not status.teams_updated

            # Parse parameters
            if params:
                if "full" in params:
                    # Full update requested
                    await nba_service.update_all_data()
                elif teams_need_update and params.get("teams", False):
                    # Teams update needed and requested
                    await nba_service.update_teams()
                    if params.get("players", False):
                        # Players update requested with teams
                        result = await session.execute(select(Team))
                        teams = result.scalars().all()
                        for team in teams:
                            await nba_service.update_team_players(team.team_id)
                elif params.get("games", False):
                    await nba_service.update_games()
            else:
                # No params, do what's needed
                if games_need_update:
                    await nba_service.update_games()
                elif teams_need_update:
                    await nba_service.update_teams()

        except Exception as e:
            logger.error(f"Error during update: {str(e)}")
            raise


def main():
    parser = argparse.ArgumentParser(description="Update NBA statistics data")
    parser.add_argument("--full", action="store_true", help="Perform full update")
    parser.add_argument("--games", action="store_true", help="Update games only")
    parser.add_argument("--teams", action="store_true", help="Update teams only")
    parser.add_argument(
        "--players", action="store_true", help="Update players (requires --teams)"
    )
    args = parser.parse_args()

    params = {}
    if args.full:
        params["full"] = True
    if args.games:
        params["games"] = True
    if args.teams:
        params["teams"] = True
    if args.players:
        params["players"] = True

    asyncio.run(update_data(params if params else None))


if __name__ == "__main__":
    main()
