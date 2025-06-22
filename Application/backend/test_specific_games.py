#!/usr/bin/env python3

import sys
import os
import asyncio
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.database import get_db
from app.services.nba_data_service import NBADataService
from app.models.models import Game, PlayerGameStats

async def test_specific_games():
    """Test processing specific problematic games"""
    print("Testing specific problematic games...")
    
    try:
        db = next(get_db())
        print("Database connection established")
        
        nba_service = NBADataService(db)
        print("NBADataService created")
        
        # Test the two problematic games
        games_to_test = [
            ('0042400306', 'NYK @ IND'),  # No scores
            ('0042400315', 'MIN @ OKC'),  # Has scores but no player stats
        ]
        
        for game_id, description in games_to_test:
            print(f"\n=== Testing {game_id} ({description}) ===")
            
            # Get current state
            game = db.query(Game).filter_by(game_id=game_id).first()
            if not game:
                print(f"Game {game_id} not found!")
                continue
                
            player_count_before = db.query(PlayerGameStats).filter_by(game_id=game_id).count()
            print(f"Before: Status={game.status}, Home={game.home_score}, Away={game.away_score}, is_loaded={game.is_loaded}, player_stats={player_count_before}")
            
            # Manually process the game
            try:
                game_data = {
                    'GAME_ID': game_id,
                    'GAME_DATE': game.game_date_utc.strftime('%Y-%m-%d'),
                    'HOME_TEAM_ID': game.home_team_id,
                    'AWAY_TEAM_ID': game.away_team_id
                }
                
                # Set is_loaded back to False so it processes player stats
                setattr(game, 'is_loaded', False)
                db.commit()
                
                print(f"Processing game {game_id}...")
                await nba_service._process_game(game_id, game_data, '2024-25')
                
                # Check state after processing
                db.refresh(game)
                player_count_after = db.query(PlayerGameStats).filter_by(game_id=game_id).count()
                print(f"After: Status={game.status}, Home={game.home_score}, Away={game.away_score}, is_loaded={game.is_loaded}, player_stats={player_count_after}")
                
            except Exception as e:
                print(f"Error processing game {game_id}: {str(e)}")
                import traceback
                traceback.print_exc()
                db.rollback()
        
        db.close()
        print("\nTest completed.")
        
    except Exception as e:
        print(f"Error in test setup: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_specific_games())
