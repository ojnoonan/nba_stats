#!/usr/bin/env python3
"""
Fix free agent issue by assigning players to their last team based on game data.
Since we're going off players' last team for the season, no player should be a free agent.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.database import SessionLocal
from app.models.models import Player, PlayerGameStats, Game
from sqlalchemy import desc
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_free_agents():
    """
    Fix players who are marked as free agents by assigning them to their last team
    based on their most recent game stats.
    """
    db = SessionLocal()
    try:
        logger.info("Starting free agent fix...")
        
        # Get all players without a current team
        free_agents = db.query(Player).filter(Player.current_team_id.is_(None)).all()
        
        if not free_agents:
            logger.info("No free agents found!")
            return
        
        logger.info(f"Found {len(free_agents)} players without team assignments")
        
        fixed_count = 0
        not_found_count = 0
        
        for player in free_agents:
            try:
                # Find the player's most recent game stats
                most_recent_game = (
                    db.query(PlayerGameStats, Game)
                    .join(Game, PlayerGameStats.game_id == Game.game_id)
                    .filter(PlayerGameStats.player_id == player.player_id)
                    .order_by(desc(Game.game_date_utc))
                    .first()
                )
                
                if most_recent_game:
                    stats, game = most_recent_game
                    
                    # Update player's current team to their most recent team
                    player.current_team_id = stats.team_id
                    player.last_updated = datetime.utcnow()
                    
                    logger.info(f"Assigned {player.full_name} to team {stats.team_id} based on game {game.game_id}")
                    fixed_count += 1
                else:
                    logger.warning(f"No game stats found for {player.full_name} (ID: {player.player_id})")
                    not_found_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing player {player.full_name}: {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Free agent fix completed!")
        logger.info(f"Players fixed: {fixed_count}")
        logger.info(f"Players without game data: {not_found_count}")
        
        # Verify the fix
        remaining_free_agents = db.query(Player).filter(Player.current_team_id.is_(None)).count()
        logger.info(f"Remaining free agents: {remaining_free_agents}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in fix_free_agents: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

async def main():
    """Main function to run the free agent fix"""
    await fix_free_agents()

if __name__ == "__main__":
    asyncio.run(main())
