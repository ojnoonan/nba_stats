#!/usr/bin/env python3
"""
Test script to fix free agent headshot URLs
"""
import asyncio
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import SessionLocal
from app.services.nba_data_service import NBADataService
from app.models.models import Player

async def test_fix_free_agent_headshots():
    """Test the free agent headshot fix function"""
    db = SessionLocal()
    try:
        # Print initial state
        total_players = db.query(Player).count()
        free_agents = db.query(Player).filter(Player.current_team_id.is_(None)).count()
        free_agents_null_headshots = db.query(Player).filter(
            Player.current_team_id.is_(None),
            Player.headshot_url.is_(None)
        ).count()
        
        print(f"Initial state:")
        print(f"  Total players: {total_players}")
        print(f"  Free agents: {free_agents}")
        print(f"  Free agents with NULL headshots: {free_agents_null_headshots}")
        
        if free_agents_null_headshots == 0:
            print("No free agents with NULL headshots found. Nothing to fix.")
            return
        
        # Sample some free agents before fix
        sample_before = db.query(Player).filter(
            Player.current_team_id.is_(None),
            Player.headshot_url.is_(None)
        ).limit(5).all()
        
        print(f"\nSample free agents before fix:")
        for player in sample_before:
            print(f"  {player.full_name} (ID: {player.player_id}) - headshot_url: {player.headshot_url}")
        
        # Run the fix
        print(f"\nRunning free agent headshot fix...")
        service = NBADataService(db)
        await service.fix_free_agent_headshots()
        
        # Check final state
        free_agents_null_headshots_after = db.query(Player).filter(
            Player.current_team_id.is_(None),
            Player.headshot_url.is_(None)
        ).count()
        
        print(f"\nFinal state:")
        print(f"  Free agents with NULL headshots: {free_agents_null_headshots_after}")
        
        # Sample some free agents after fix
        sample_after = db.query(Player).filter(
            Player.current_team_id.is_(None),
            Player.headshot_url.is_not(None)
        ).limit(5).all()
        
        print(f"\nSample free agents after fix:")
        for player in sample_after:
            print(f"  {player.full_name} (ID: {player.player_id}) - headshot_url: {player.headshot_url}")
        
        print(f"\nSuccess! Fixed {free_agents_null_headshots - free_agents_null_headshots_after} free agent headshot URLs")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_fix_free_agent_headshots())
