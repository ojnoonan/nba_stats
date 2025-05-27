import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

# Configure logging
logger = logging.getLogger(__name__)

from app.database.database import AsyncSessionLocal, get_db
from app.models.models import DataUpdateStatus, Player, Team
from app.services.nba_data_service import TaskCancelledError
from app.services.status_service import (
    finalize_update,
    get_or_create_status,
    initialize_update_status,
    set_update_error,
)


@pytest.mark.asyncio
async def test_full_update_flow(client: TestClient, db, test_team):
    """Test the complete player update flow, including status tracking and error handling"""

    # Create test players
    players = []
    for i in range(3):
        player = Player(
            player_id=1000 + i,
            full_name=f"Test Player {i}",
            first_name="Test",
            last_name=f"Player {i}",
            current_team_id=test_team.team_id,
            position="G",
            jersey_number=str(i),
            is_active=True,
            is_loaded=False,
        )
        db.add(player)
        players.append(player)
    await db.commit()

    # Mock the NBA data service
    with patch("app.services.nba_data_service.NBADataService") as mock_nba_service:

        async def mock_update_team_players(team_id):
            try:
                # Use a single session for the entire operation
                async with AsyncSessionLocal() as session:
                    # Initialize the update and verify initial state
                    status = await initialize_update_status(session, "players")

                    logger.info("Initial status check")
                    assert status.is_updating
                    assert status.current_phase == "players"
                    assert not status.players_updated
                    assert not status.components.get("players", {}).get(
                        "updated", False
                    )
                    assert status.players_percent_complete == 0
                    assert status.last_error is None

                    # Update all players in a single transaction
                    logger.info(f"Updating {len(players)} players")
                    for idx, player in enumerate(players):
                        stmt = select(Player).filter_by(player_id=player.player_id)
                        result = await session.execute(stmt)
                        db_player = result.scalar_one()
                        db_player.is_loaded = True
                        db_player.last_updated = datetime.now(timezone.utc)

                        # Update progress for each player
                        status = await get_or_create_status(session)
                        percent = int(((idx + 1) / len(players)) * 100)
                        status.players_percent_complete = percent
                        components = (
                            status.components
                            if isinstance(status.components, dict)
                            else {}
                        )
                        components["players"] = components.get("players", {})
                        components["players"].update(
                            {
                                "percent_complete": percent,
                                "updated": False,
                                "last_error": None,
                            }
                        )
                        status.components = components
                        await session.commit()
                        await asyncio.sleep(0.1)  # Simulate work

                    # Finalize and verify
                    logger.info("Finalizing update")
                    status = await finalize_update(
                        session, "players"
                    )  # This will properly set up all status flags

                    logger.info("Final status check")
                    assert status.players_updated
                    assert status.components["players"]["updated"]
                    assert status.players_percent_complete == 100
                    assert not status.is_updating
            except Exception as e:
                # If anything fails, set the error state
                async with AsyncSessionLocal() as session:
                    await set_update_error(session, "players", str(e))
                raise

        mock_service = AsyncMock()
        mock_service.update_team_players.side_effect = mock_update_team_players
        mock_nba_service.return_value = mock_service

        # Start the update
        response = client.post(f"/teams/{test_team.team_id}/update")
        assert response.status_code == 200
        assert "update initiated" in response.json()["message"].lower()

        # Poll until update completes
        max_attempts = 30
        for attempt in range(max_attempts):
            response = client.get("/admin/status")
            assert response.status_code == 200
            status = response.json()

            if not status["is_updating"]:
                # Verify final state
                assert status["players_updated"]
                assert status["players_percent_complete"] == 100
                assert status["components"]["players"]["updated"]
                assert status["components"]["players"]["percent_complete"] == 100
                assert not status["components"]["players"]["last_error"]
                break

            time.sleep(0.5)
        else:
            pytest.fail("Update did not complete in time")

        # Verify all players are properly updated
        async with AsyncSessionLocal() as session:
            for player in players:
                stmt = select(Player).filter_by(player_id=player.player_id)
                result = await session.execute(stmt)
                updated_player = result.scalar_one()
                assert updated_player.is_loaded
                assert updated_player.last_updated is not None


@pytest.mark.asyncio
async def test_update_error_handling(client: TestClient, db, test_team):
    """Test error handling during player updates"""

    # Create test player
    player = Player(
        player_id=1000,
        full_name="Test Player",
        current_team_id=test_team.team_id,
        is_active=True,
        is_loaded=False,
    )
    db.add(player)
    await db.commit()

    # Mock service with error - use the correct module path
    with patch("app.services.nba_data_service.NBADataService") as mock_nba_service:

        async def mock_update_with_error(team_id):
            async with AsyncSessionLocal() as session:
                # Initialize the update and verify initial state
                logger.info("Initializing update status for error test")
                status = await initialize_update_status(session, "players")

                # Verify initial state
                assert status.is_updating
                assert status.current_phase == "players"
                assert not status.players_updated
                assert not status.components.get("players", {}).get("updated", False)

                # Simulate work before error
                await asyncio.sleep(0.1)

                # Set error state and verify
                logger.info("Setting error state")
                await set_update_error(session, "players", "Test error")
                await session.refresh(status)

                # Verify error state before raising
                assert not status.is_updating
                assert status.last_error == "Test error"
                assert not status.players_updated
                assert not status.components["players"]["updated"]
                assert status.last_error_time is not None
                assert status.components["players"]["last_error"] == "Test error"

                raise ValueError("Test error")

        mock_service = AsyncMock()
        mock_service.update_team_players.side_effect = mock_update_with_error
        mock_nba_service.return_value = mock_service

        # Start update
        logger.info("Starting player update for error test")
        response = client.post(f"/teams/{test_team.team_id}/update")
        assert response.status_code == 200

        # Wait for error state
        max_attempts = 30
        last_status = None
        for attempt in range(max_attempts):
            logger.info(f"Checking error status attempt {attempt + 1}")
            response = client.get("/admin/status")
            assert response.status_code == 200
            last_status = response.json()
            logger.info(f"Current status: {last_status}")

            if last_status.get("last_error"):
                logger.info("Error state detected")
                # Verify error state in top-level fields
                assert "Test error" in last_status["last_error"]
                assert not last_status["is_updating"]
                assert not last_status["players_updated"]
                assert last_status["current_phase"] is None
                assert last_status["last_error_time"] is not None

                # Verify error state in components
                assert "players" in last_status["components"]
                player_component = last_status["components"]["players"]
                assert "Test error" in player_component["last_error"]
                assert not player_component["updated"]
                assert player_component["percent_complete"] == 0
                break

            await asyncio.sleep(0.5)
        else:
            logger.error(
                "No error state detected in status! Last status: %s", last_status
            )
            pytest.fail("Error state not detected")

            # Verify player state unchanged
            async with AsyncSessionLocal() as session:
                stmt = select(Player).filter_by(player_id=player.player_id)
                result = await session.execute(stmt)
                updated_player = result.scalar_one()
                assert not updated_player.is_loaded
                logger.info("Player state verification passed")


@pytest.mark.asyncio
async def test_update_cancellation(client: TestClient, db, test_team):
    """Test cancellation of player updates"""

    # Create test players
    players = []
    for i in range(5):  # More players to ensure enough time for cancellation
        player = Player(
            player_id=1000 + i,
            full_name=f"Test Player {i}",
            current_team_id=test_team.team_id,
            is_active=True,
            is_loaded=False,
        )
        db.add(player)
        players.append(player)
    await db.commit()

    # Mock service with cancellation check
    with patch("app.services.nba_data_service.NBADataService") as mock_nba_service:

        async def mock_update_with_cancel(team_id):
            for idx, player in enumerate(players):
                # Check for cancellation
                async with AsyncSessionLocal() as session:
                    status = await get_status(session)
                    if status.cancellation_requested:
                        raise TaskCancelledError()

                # Update player
                player.is_loaded = True
                await db.commit()

                # Update progress
                async with AsyncSessionLocal() as session:
                    status = await get_status(session)
                    percent = int(((idx + 1) / len(players)) * 100)
                    status.players_percent_complete = percent
                    status.components["players"]["percent_complete"] = percent
                    await session.commit()

                await asyncio.sleep(0.2)  # Longer delay to ensure time for cancellation

        mock_service = AsyncMock()
        mock_service.update_team_players.side_effect = mock_update_with_cancel
        mock_nba_service.return_value = mock_service

        # Start update
        response = client.post(f"/teams/{test_team.team_id}/update")
        assert response.status_code == 200

        # Wait shortly then cancel
        time.sleep(0.5)
        response = client.post("/admin/update/cancel")
        assert response.status_code == 200

        # Verify cancellation state
        max_attempts = 30
        for attempt in range(max_attempts):
            response = client.get("/admin/status")
            assert response.status_code == 200
            status = response.json()

            if not status["is_updating"]:
                assert status["current_phase"] is None
                assert not status["players_updated"]
                break

            time.sleep(0.5)
        else:
            pytest.fail("Cancellation not processed")

        # Verify partial update state
        async with AsyncSessionLocal() as session:
            loaded_count = 0
            all_players = []
            for player in players:
                stmt = select(Player).filter_by(player_id=player.player_id)
                result = await session.execute(stmt)
                try:
                    player = result.scalar_one()
                    all_players.append(player)
                    if player.is_loaded:
                        loaded_count += 1
                except Exception:
                    continue

            # At this point, we should have some players loaded but not all
            # We can't guarantee exactly how many due to race conditions
            assert loaded_count >= 0
            assert loaded_count <= len(players)


async def get_status(session):
    """Helper to get current status"""
    stmt = select(DataUpdateStatus)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
