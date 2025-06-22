#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.database import SessionLocal
from app.services.nba_data_service import NBADataService
from app.models.models import Game, PlayerGameStats
import asyncio

async def investigate_specific_games():
    print('Investigating specific problematic games...')
    db = SessionLocal()
    try:
        print('Database connection established')
        service = NBADataService(db)
        print('NBADataService created')
        
        # The two problematic games
        problem_games = ['0042400306', '0042400315']
        
        for game_id in problem_games:
            print(f'\n=== INVESTIGATING GAME {game_id} ===')
            
            # Get current game info
            game = db.query(Game).filter(Game.game_id == game_id).first()
            if game:
                print(f'Current status: {game.status}')
                print(f'Is loaded: {game.is_loaded}')
                print(f'Home score: {game.home_score}')
                print(f'Away score: {game.away_score}')
                print(f'Game date: {game.game_date_utc}')
                
                # Check current player stats
                current_stats = db.query(PlayerGameStats).filter(
                    PlayerGameStats.game_id == game_id
                ).count()
                print(f'Current player stats: {current_stats}')
                
                # Try to reprocess the game
                print(f'Attempting to reprocess game {game_id}...')
                try:
                    # Create proper game_data dict and season for _process_game
                    game_data = {
                        'GAME_ID': game_id,
                        'GAME_DATE': game.game_date_utc.strftime("%Y-%m-%d"),
                        'HOME_TEAM_ID': game.home_team_id,
                        'AWAY_TEAM_ID': game.away_team_id
                    }
                    season = game.season_year
                    
                    result = await service._process_game(game_id, game_data, season)
                    print(f'Reprocessing result: {result}')
                    
                    # Check player stats after reprocessing
                    new_stats = db.query(PlayerGameStats).filter(
                        PlayerGameStats.game_id == game_id
                    ).count()
                    print(f'Player stats after reprocessing: {new_stats}')
                    
                    # Update game info
                    db.refresh(game)
                    print(f'Updated status: {game.status}')
                    print(f'Updated is_loaded: {game.is_loaded}')
                    print(f'Updated home score: {game.home_score}')
                    print(f'Updated away score: {game.away_score}')
                    
                except Exception as e:
                    print(f'Error reprocessing game {game_id}: {e}')
                    import traceback
                    print(f'Full traceback: {traceback.format_exc()}')
            else:
                print(f'Game {game_id} not found in database')
                
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(investigate_specific_games())
