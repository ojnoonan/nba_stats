#!/usr/bin/env python3
"""
Test script to verify the fix_free_agent_teams integration
"""

import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Player
from app.services.nba_data_service import NBADataService

# Database setup
DATABASE_URL = 'sqlite:///nba_stats.db'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_fix_integration():
    """Test the integrated fix_free_agent_teams method"""
    db = SessionLocal()
    
    try:
        # Check initial state
        total_players = db.query(Player).count()
        free_agents_before = db.query(Player).filter(Player.current_team_id.is_(None)).count()
        
        print(f"Before fix:")
        print(f"  Total players: {total_players}")
        print(f"  Free agents: {free_agents_before}")
        print(f"  Players with teams: {total_players - free_agents_before}")
        
        # Create NBA Data Service and run the fix
        data_service = NBADataService(db)
        
        print("\nRunning fix_free_agent_teams...")
        await data_service.fix_free_agent_teams()
        
        # Check final state
        free_agents_after = db.query(Player).filter(Player.current_team_id.is_(None)).count()
        
        print(f"\nAfter fix:")
        print(f"  Total players: {total_players}")
        print(f"  Free agents: {free_agents_after}")
        print(f"  Players with teams: {total_players - free_agents_after}")
        
        # Show the difference
        fixed_players = free_agents_before - free_agents_after
        print(f"\nResult: {fixed_players} players were assigned to teams")
        
        if fixed_players > 0:
            print("✅ Fix method is working correctly!")
        else:
            print("ℹ️  No players needed fixing (database already in good state)")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_fix_integration())
