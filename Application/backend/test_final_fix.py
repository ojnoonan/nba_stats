#!/usr/bin/env python3

"""
Test script to verify that the data type conversion fixes work correctly
for the problematic games identified in the conversation summary.
"""

import sys
import os
import asyncio
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from app.services.nba_data_service import NBADataService
from app.models.models import Game, PlayerGameStats

def test_specific_games():
    """Test processing of specific problematic games"""
    
    # Create database session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Create NBADataService instance
    service = NBADataService(db)
    
    # Test games from conversation summary
    test_games = [
        {
            'game_id': '0042400315',  # MIN @ OKC playoff game
            'description': 'Minnesota Timberwolves @ Oklahoma City Thunder - Playoff Game'
        },
        {
            'game_id': '0042400306',  # NYK @ IND playoff game  
            'description': 'New York Knicks @ Indiana Pacers - Playoff Game'
        }
    ]
    
    print("Testing data type conversion fixes for problematic games...")
    print()
    
    for game_info in test_games:
        game_id = game_info['game_id']
        description = game_info['description']
        
        print(f"Testing Game {game_id}: {description}")
        print("-" * 60)
        
        try:
            # Check if game exists in database
            existing_game = db.query(Game).filter_by(game_id=game_id).first()
            if existing_game:
                print(f"✓ Game {game_id} found in database")
                print(f"  Status: {getattr(existing_game, 'status', 'Unknown')}")
                print(f"  Is Loaded: {getattr(existing_game, 'is_loaded', 'Unknown')}")
                
                # Check existing player stats
                existing_stats_count = db.query(PlayerGameStats).filter_by(game_id=game_id).count()
                print(f"  Existing player stats: {existing_stats_count}")
                
                if existing_stats_count == 0 and getattr(existing_game, 'status', None) == 'Completed':
                    print(f"  → Game is completed but has no player stats - needs reprocessing")
                    
                    # Test _safe_int function with sample NBA API values
                    print(f"  Testing _safe_int with sample NBA API values:")
                    test_values = ['20.000000', '15.0', '0', '', None, '12', 25.5]
                    for val in test_values:
                        try:
                            result = service._safe_int(val)
                            print(f"    _safe_int({val!r}) = {result}")
                        except Exception as e:
                            print(f"    _safe_int({val!r}) failed: {e}")
                
            else:
                print(f"✗ Game {game_id} not found in database")
            
        except Exception as e:
            print(f"✗ Error checking game {game_id}: {str(e)}")
        
        print()
    
    # Test the enhanced fix method
    print("Testing enhanced fix_upcoming_past_games method...")
    print("-" * 60)
    
    try:
        # Run the enhanced fix method
        result = asyncio.run(service.fix_upcoming_past_games())
        print(f"✓ Enhanced fix method completed successfully")
        if result:
            print(f"  Games processed: {result.get('games_processed', 'Unknown')}")
            print(f"  Successfully updated: {result.get('games_updated', 'Unknown')}")
            print(f"  Errors: {result.get('errors', 'Unknown')}")
        
        # Check if problematic games were processed
        for game_info in test_games:
            game_id = game_info['game_id']
            game = db.query(Game).filter_by(game_id=game_id).first()
            if game:
                stats_count = db.query(PlayerGameStats).filter_by(game_id=game_id).count()
                is_loaded = getattr(game, 'is_loaded', False)
                print(f"  Game {game_id}: {stats_count} player stats, is_loaded={is_loaded}")
        
    except Exception as e:
        print(f"✗ Error running enhanced fix method: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_specific_games()
