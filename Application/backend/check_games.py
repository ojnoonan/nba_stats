#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.database import SessionLocal
from app.models.models import Game, PlayerGameStats
from sqlalchemy import text

def check_problematic_games():
    print('Checking current status of problematic games...')
    db = SessionLocal()
    try:
        # Query for games that are completed but not loaded or missing scores
        query = text("""
            SELECT 
                g.game_id, 
                g.status, 
                g.is_loaded, 
                g.home_score, 
                g.away_score,
                COUNT(ps.player_id) as player_count
            FROM games g
            LEFT JOIN player_stats ps ON g.game_id = ps.game_id
            WHERE (g.status = 'Upcoming' OR g.is_loaded = 0) 
                AND g.game_date < date('now')
            GROUP BY g.game_id, g.status, g.is_loaded, g.home_score, g.away_score
            ORDER BY g.game_date DESC 
            LIMIT 10
        """)
        
        result = db.execute(query)
        rows = result.fetchall()
        
        print('Game ID      | Status    | Loaded | Home | Away | Players')
        print('-' * 60)
        
        for row in rows:
            print(f'{row[0]:<12} | {row[1]:<8} | {row[2]:<6} | {str(row[3]):<4} | {str(row[4]):<4} | {row[5]}')
            
        print(f'\nFound {len(rows)} problematic games')
        
        # Check specific games
        specific_games = ['0042400306', '0042400315']
        print('\nSpecific games status:')
        for game_id in specific_games:
            game = db.query(Game).filter(Game.game_id == game_id).first()
            if game:
                player_count = db.query(PlayerGameStats).filter(PlayerGameStats.game_id == game_id).count()
                print(f'{game_id}: status={game.status}, is_loaded={game.is_loaded}, '
                      f'home_score={game.home_score}, away_score={game.away_score}, players={player_count}')
            else:
                print(f'{game_id}: NOT FOUND')
                
    finally:
        db.close()

if __name__ == "__main__":
    check_problematic_games()
