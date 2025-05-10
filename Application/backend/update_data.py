import asyncio
from app.database.database import SessionLocal
from app.services.nba_data_service import NBADataService
from app.models.models import Game
from sqlalchemy import func

async def main():
    print("Starting data update...")
    db = SessionLocal()
    try:
        print(f"Games before update: {db.query(Game).count()}")
        
        nba_service = NBADataService(db)
        await nba_service.cleanup_old_seasons()
        await nba_service.update_all_data()
        
        print(f"Games after update: {db.query(Game).count()}")
        
        # Print some stats about game statuses
        stats = db.query(Game.status, func.count(Game.game_id)).group_by(Game.status).all()
        print("\nGames by status:")
        for status, count in stats:
            print(f"{status}: {count}")
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())