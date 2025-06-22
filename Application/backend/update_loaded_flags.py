#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.database import SessionLocal
from app.models.models import Game, PlayerGameStats
from sqlalchemy import text

def update_loaded_flags():
    print('Starting update of is_loaded flags...')
    db = SessionLocal()
    try:
        print('Database connection established')
        # Find games that have player stats but is_loaded=False
        query = text("""
            SELECT 
                g.game_id, 
                g.status, 
                g.is_loaded, 
                COUNT(ps.player_id) as player_count
            FROM games g
            LEFT JOIN player_game_stats ps ON g.game_id = ps.game_id
            WHERE g.is_loaded = 0
            GROUP BY g.game_id, g.status, g.is_loaded
            HAVING COUNT(ps.player_id) > 0
            ORDER BY COUNT(ps.player_id) DESC
        """)
        
        print('Executing query...')
        result = db.execute(query)
        rows = result.fetchall()
        print(f'Query returned {len(rows)} rows')
        
        print(f'Found {len(rows)} games with player stats but is_loaded=False')
        print('Game ID      | Status    | Players')
        print('-' * 40)
        
        updated_count = 0
        for row in rows:
            game_id, status, is_loaded, player_count = row
            print(f'{game_id:<12} | {status:<8} | {player_count}')
            
            # Update the is_loaded flag
            game = db.query(Game).filter(Game.game_id == game_id).first()
            if game:
                game.is_loaded = True
                updated_count += 1
        
        # Commit the changes
        db.commit()
        print(f'\nUpdated is_loaded=True for {updated_count} games')
        
        # Check remaining problematic games
        remaining_query = text("""
            SELECT COUNT(*) 
            FROM games g
            WHERE (g.status = 'Upcoming' OR g.is_loaded = 0) 
                AND g.game_date_utc < date('now')
        """)
        
        remaining_count = db.execute(remaining_query).scalar()
        print(f'Remaining problematic games: {remaining_count}')
        
    finally:
        db.close()

if __name__ == "__main__":
    update_loaded_flags()
