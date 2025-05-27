import asyncio

import pytest

from app.database.database import AsyncSessionLocal
from app.services.nba_data_service import NBADataService

pytest.skip(
    "Skipping player update integration test until service is refactored",
    allow_module_level=True,
)


async def test_player_update():
    async with AsyncSessionLocal() as session:
        service = NBADataService(session)
        await service.update_team_players(1610612737)  # Atlanta Hawks ID


if __name__ == "__main__":
    asyncio.run(test_player_update())
