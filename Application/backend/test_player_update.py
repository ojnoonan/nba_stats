import asyncio
from app.services.nba_data_service import NBADataService
from app.database.database import SessionLocal

async def test_player_update():
    service = NBADataService(SessionLocal())
    await service.update_team_players('1610612737')  # Atlanta Hawks ID

if __name__ == "__main__":
    asyncio.run(test_player_update())