import asyncio
import argparse
from datetime import datetime, timedelta
from app.database.database import SessionLocal
from app.services.nba_data_service import NBADataService
from app.models.models import Game, Team, Player, DataUpdateStatus
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def update_with_params(params=None):
    """Update database with specified parameters"""
    db = SessionLocal()
    try:
        service = NBADataService(db)
        status = db.query(DataUpdateStatus).first()
        
        if not status:
            status = DataUpdateStatus()
            db.add(status)
        
        if status.is_updating:
            logger.error("An update is already in progress")
            return

        status.is_updating = True
        status.current_phase = 'starting'
        db.commit()

        try:
            # Always check if teams need updating when updating players
            teams_need_update = not status.teams_updated or \
                (status.last_successful_update and 
                 datetime.utcnow() - status.last_successful_update > timedelta(hours=6))
            
            if teams_need_update and (not params or 'teams' in params or 'players' in params):
                status.current_phase = 'teams'
                db.commit()
                logger.info("Updating teams data...")
                await service.update_teams()
                status.teams_updated = True
                db.commit()
            elif teams_need_update and 'players' in params:
                logger.warning("Teams data is out of date. Updating teams before players.")
                status.current_phase = 'teams'
                db.commit()
                await service.update_teams()
                status.teams_updated = True
                db.commit()

            if not params or 'players' in params:
                status.current_phase = 'players'
                db.commit()
                logger.info("Updating players data...")
                teams_query = db.query(Team)
                if status.last_successful_update:
                    teams_query = teams_query.filter(
                        (Team.last_updated == None) |
                        (Team.last_updated <= datetime.utcnow() - timedelta(hours=6))
                    )
                
                total_teams = teams_query.count()
                for i, team in enumerate(teams_query.all(), 1):
                    logger.info(f"Updating players for team {team.name} ({i}/{total_teams})")
                    await service.update_team_players(team.team_id)
                
                status.players_updated = True
                db.commit()

            if not params or 'games' in params:
                status.current_phase = 'games'
                db.commit()
                logger.info("Updating games data...")
                await service.update_games()
                status.games_updated = True
                db.commit()

            status.current_phase = None
            status.last_successful_update = datetime.utcnow()
            status.next_scheduled_update = datetime.utcnow() + timedelta(hours=6)
            status.is_updating = False
            db.commit()

            # Print summary
            games_count = db.query(Game).count()
            teams_count = db.query(Team).count()
            players_count = db.query(Player).count()
            logger.info("Update completed successfully!")
            logger.info(f"Database contains: {teams_count} teams, {players_count} players, {games_count} games")

        except Exception as e:
            status.last_error = str(e)
            status.last_error_time = datetime.utcnow()
            status.is_updating = False
            db.commit()
            logger.error(f"Error during update: {str(e)}")
            raise e

    finally:
        db.close()

async def main():
    parser = argparse.ArgumentParser(
        description='Update NBA stats database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                     # Update all data
  %(prog)s --games            # Update only games
  %(prog)s --teams --players  # Update teams and players
  %(prog)s --all             # Update all data (same as no arguments)
        """
    )
    parser.add_argument('--teams', action='store_true', help='Update teams data')
    parser.add_argument('--players', action='store_true', help='Update players data')
    parser.add_argument('--games', action='store_true', help='Update games data')
    parser.add_argument('--all', action='store_true', help='Update all data (default)')
    
    args = parser.parse_args()
    params = []
    
    if args.all or not any([args.teams, args.players, args.games]):
        # If --all is specified or no arguments given, update everything
        params = None
    else:
        if args.teams:
            params.append('teams')
        if args.players:
            params.append('players')
        if args.games:
            params.append('games')
    
    try:
        await update_with_params(params)
    except Exception as e:
        logger.error(f"Update failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
