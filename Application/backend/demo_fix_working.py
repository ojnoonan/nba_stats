#!/usr/bin/env python3
"""
Demonstration script showing the fix_free_agent_teams method working
Creates a temporary free agent and then fixes it to prove the integration works
"""

import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Player, PlayerGameStats, Game
from app.services.nba_data_service import NBADataService

# Database setup
DATABASE_URL = 'sqlite:///nba_stats.db'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def demonstrate_fix():
    """Demonstrate the fix working by creating and fixing a temporary free agent"""
    db = SessionLocal()
    
    try:
        # Find a player who currently has a team and recent game stats
        player_with_team = (
            db.query(Player)
            .filter(Player.current_team_id.isnot(None))
            .join(PlayerGameStats, Player.player_id == PlayerGameStats.player_id)
            .first()
        )
        
        if not player_with_team:
            print("❌ No players with team assignments found for demonstration")
            return
            
        original_team_id = player_with_team.current_team_id
        player_name = player_with_team.full_name
        player_id = player_with_team.player_id
        
        print(f"🎯 Demo: Temporarily making {player_name} a free agent")
        print(f"   Original team ID: {original_team_id}")
        
        # Temporarily remove team assignment
        player_with_team.current_team_id = None
        db.commit()
        
        # Verify they are now a free agent
        free_agents_before = db.query(Player).filter(Player.current_team_id.is_(None)).count()
        print(f"   Free agents before fix: {free_agents_before}")
        
        # Create NBA Data Service and run the fix
        data_service = NBADataService(db)
        
        print(f"\n🔧 Running fix_free_agent_teams...")
        await data_service.fix_free_agent_teams()
        
        # Check if the player was fixed
        db.refresh(player_with_team)
        fixed_team_id = player_with_team.current_team_id
        free_agents_after = db.query(Player).filter(Player.current_team_id.is_(None)).count()
        
        print(f"\n📊 Results:")
        print(f"   Free agents after fix: {free_agents_after}")
        print(f"   {player_name} team ID: {fixed_team_id}")
        
        if fixed_team_id is not None:
            print(f"✅ SUCCESS! Player was automatically assigned to team {fixed_team_id}")
            if fixed_team_id == original_team_id:
                print(f"✅ PERFECT! Assigned to correct original team {original_team_id}")
            else:
                print(f"ℹ️  Assigned to team {fixed_team_id} (their most recent team based on game stats)")
        else:
            print(f"❌ FAILED! Player is still a free agent")
            
    except Exception as e:
        print(f"❌ Error during demonstration: {str(e)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(demonstrate_fix())
