#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.database import SessionLocal
from app.services.nba_data_service import NBADataService
from app.models.models import Game, PlayerGameStats
import asyncio

async def test_enhanced_fix():
    print('Starting test...')
    db = SessionLocal()
    try:
        print('Database connection established')
        service = NBADataService(db)
        print('NBADataService created')
        print('Testing enhanced fix_upcoming_past_games method...')
        result = await service.fix_upcoming_past_games()
        print(f'Fix result: {result}')
        
        # Check the specific games
        problematic_games = db.query(Game).filter(
            Game.game_id.in_(['0042400315', '0042400306'])
        ).all()
        
        print('\nGame status after fix:')
        for game in problematic_games:
            print(f'Game {game.game_id}: status={game.status}, home_score={game.home_score}, away_score={game.away_score}, is_loaded={game.is_loaded}')
            
            # Check if player stats exist
            player_stats_count = db.query(PlayerGameStats).filter(
                PlayerGameStats.game_id == game.game_id
            ).count()
            print(f'  Player stats count: {player_stats_count}')
        
        # Show all problematic games
        print('\nAll problematic games (status=Upcoming or is_loaded=False for past games):')
        from sqlalchemy import text
        query = text("""
            SELECT 
                g.game_id, 
                g.status, 
                g.is_loaded, 
                g.home_score, 
                g.away_score,
                COUNT(ps.player_id) as player_count
            FROM games g
            LEFT JOIN player_game_stats ps ON g.game_id = ps.game_id
            WHERE (g.status = 'Upcoming' OR g.is_loaded = 0) 
                AND g.game_date_utc < date('now')
            GROUP BY g.game_id, g.status, g.is_loaded, g.home_score, g.away_score
            ORDER BY g.game_date_utc DESC 
            LIMIT 5
        """)
        
        result = db.execute(query)
        rows = result.fetchall()
        
        print('Game ID      | Status    | Loaded | Home | Away | Players')
        print('-' * 60)
        
        for row in rows:
            print(f'{row[0]:<12} | {row[1]:<8} | {row[2]:<6} | {str(row[3]):<4} | {str(row[4]):<4} | {row[5]}')
            
        print(f'\nTotal problematic games shown: {len(rows)}')
        
        # Get total count of all problematic games
        count_query = text("""
            SELECT COUNT(*) 
            FROM games g
            WHERE (g.status = 'Upcoming' OR g.is_loaded = 0) 
                AND g.game_date_utc < date('now')
        """)
        
        total_count = db.execute(count_query).scalar()
        print(f'Total problematic games in database: {total_count}')
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_enhanced_fix())
