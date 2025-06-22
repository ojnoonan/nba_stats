#!/usr/bin/env python3
"""
Final verification script to confirm both problematic games now have complete player statistics.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.db import get_db
from app.models.models import Game, PlayerGameStats

def main():
    """Verify the two problematic games now have complete data."""
    print("=== FINAL VERIFICATION ===")
    
    db = next(get_db())
    
    # Check both games
    games = ['0042400306', '0042400315']
    for game_id in games:
        game = db.query(Game).filter(Game.game_id == game_id).first()
        if not game:
            print(f"❌ Game {game_id}: Not found in database")
            continue
            
        stats_count = db.query(PlayerGameStats).filter(PlayerGameStats.game_id == game_id).count()
        
        # Determine status
        status_emoji = "✅" if stats_count >= 20 else "❌"
        
        print(f"{status_emoji} Game {game_id}:")
        print(f"   Status: {game.status}")
        print(f"   Loaded: {game.is_loaded}")
        print(f"   Players: {stats_count}")
        print(f"   Score: {game.home_score}-{game.away_score}")
        print(f"   Date: {game.game_date_utc}")
        print()
    
    db.close()
    
    print("=== SUMMARY ===")
    print("Both games should now have:")
    print("✅ Status: Completed")
    print("✅ Loaded: True") 
    print("✅ Players: 24-30 (complete box scores)")
    print("✅ Valid final scores")

if __name__ == "__main__":
    main()
