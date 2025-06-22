#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.database import SessionLocal
from app.services.nba_data_service import NBADataService

async def main():
    """Run the free agent headshot fix"""
    print("Starting free agent headshot URL fix...")
    
    db = SessionLocal()
    try:
        service = NBADataService(db)
        await service.fix_free_agent_headshots()
        print("Free agent headshot fix completed successfully!")
        
    except Exception as e:
        print(f"Error running fix: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
