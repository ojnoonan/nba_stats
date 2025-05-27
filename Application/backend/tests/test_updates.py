import asyncio
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.models.models import DataUpdateStatus, Game, Player, Team


@pytest.mark.asyncio
async def test_update_single_team(client, test_team, db):
    """Test updating a single team"""
    # Get initial team state
    response = client.get(f"/teams/{test_team.team_id}")
    assert response.status_code == 200
    initial_team = response.json()
    assert not initial_team.get(
        "roster_loaded", True
    ), "Team roster should not be loaded initially"

    # Set up mock service
    with patch("app.routers.teams.NBADataService") as mock_nba_service:

        async def mock_update_team_players(team_id):
            # Update the team status
            stmt = (
                update(Team)
                .where(Team.team_id == test_team.team_id)
                .values(roster_loaded=True)
            )
            await db.execute(stmt)
            await db.commit()

        mock_service = AsyncMock()
        mock_service.update_team_players.side_effect = mock_update_team_players
        mock_nba_service.return_value = mock_service

        # Trigger update for the test team
        response = client.post(f"/teams/{test_team.team_id}/update")
        assert response.status_code == 200

        # Wait for team update to complete
        max_attempts = 30
        for attempt in range(max_attempts):
            response = client.get(f"/teams/{test_team.team_id}")
            assert response.status_code == 200
            team = response.json()

            if team.get("roster_loaded", False):
                status_response = client.get("/admin/status")
                status = status_response.json()
                assert not status[
                    "is_updating"
                ], "Update should be complete when team is loaded"
                break

            await asyncio.sleep(0.5)  # Short wait between checks
        else:
            final_team = client.get(f"/teams/{test_team.team_id}").json()
            final_status = client.get("/admin/status").json()
            raise AssertionError(
                f"Team was not marked as loaded after update.\n"
                f"Team ID: {test_team.team_id}\n"
                f"Team state: {final_team}\n"
                f"Final status: {final_status}"
            )


@pytest.mark.asyncio
async def test_update_single_player(client, test_player, test_team, db):
    """Test updating a single player"""
    # Get initial player state
    response = client.get(f"/players/{test_player.player_id}")
    assert response.status_code == 200
    initial_player = response.json()
    assert not initial_player.get(
        "is_loaded", True
    ), "Player should not be loaded initially"

    # Set up mock service
    with patch("app.routers.teams.NBADataService") as mock_nba_service:

        async def mock_update_team_players(team_id):
            # Update only the test player status
            stmt = (
                update(Player)
                .where(Player.player_id == test_player.player_id)
                .values(is_loaded=True)
            )
            await db.execute(stmt)
            await db.commit()

            # Update the status table
            stmt = select(DataUpdateStatus)
            result = await db.execute(stmt)
            status = result.scalar_one_or_none()
            if status:
                status.players_updated = True
                status.players_last_update = datetime.now(timezone.utc)
                status.players_percent_complete = 100
                status.is_updating = False
            await db.commit()

        mock_service = AsyncMock()
        mock_service.update_team_players.side_effect = mock_update_team_players
        mock_nba_service.return_value = mock_service

        # Trigger update for the team containing our test player
        response = client.post(f"/teams/{test_team.team_id}/update")
        assert response.status_code == 200

        # Wait for player update to complete
        max_attempts = 30
        for attempt in range(max_attempts):
            response = client.get(f"/players/{test_player.player_id}")
            assert response.status_code == 200
            player = response.json()

            if player.get("is_loaded", False):
                status_response = client.get("/admin/status")
                status = status_response.json()
                assert not status[
                    "is_updating"
                ], "Update should be complete when player is loaded"
                break

            await asyncio.sleep(0.5)  # Short wait between checks
        else:
            final_player = client.get(f"/players/{test_player.player_id}").json()
            final_status = client.get("/admin/status").json()
            raise AssertionError(
                f"Player was not marked as loaded after update.\n"
                f"Player ID: {test_player.player_id}\n"
                f"Player state: {final_player}\n"
                f"Final status: {final_status}"
            )


@pytest.mark.asyncio
async def test_update_single_game(client, test_game, db):
    """Test updating a single game"""
    # Get initial game state
    response = client.get(f"/games/{test_game.game_id}")
    assert response.status_code == 200
    initial_game = response.json()
    assert not initial_game.get(
        "is_loaded", True
    ), "Game should not be loaded initially"

    # Set up mock service
    with patch("app.services.nba_data_service.NBADataService") as mock_nba_service:

        async def mock_update_game(game_id):
            # Update the game status
            stmt = (
                update(Game)
                .where(Game.game_id == test_game.game_id)
                .values(is_loaded=True)
            )
            await db.execute(stmt)

            # Update the status table
            stmt = select(DataUpdateStatus)
            result = await db.execute(stmt)
            status = result.scalar_one_or_none()
            if status:
                status.games_updated = True
                status.games_last_update = datetime.now(timezone.utc)
                status.games_percent_complete = 100
                status.is_updating = False
            await db.commit()

        mock_service = AsyncMock()
        mock_service.update_game.side_effect = mock_update_game
        mock_nba_service.return_value = mock_service

        # Trigger update for the test game
        response = client.post(f"/games/{test_game.game_id}/update")
        assert response.status_code == 200

        # Wait for game update to complete
        max_attempts = 30
        for attempt in range(max_attempts):
            response = client.get(f"/games/{test_game.game_id}")
            assert response.status_code == 200
            game = response.json()

            if game.get("is_loaded", False):
                status_response = client.get("/admin/status")
                status = status_response.json()
                assert not status[
                    "is_updating"
                ], "Update should be complete when game is loaded"
                break

            await asyncio.sleep(0.5)  # Short wait between checks
        else:
            final_game = client.get(f"/games/{test_game.game_id}").json()
            final_status = client.get("/admin/status").json()
            raise AssertionError(
                f"Game was not marked as loaded after update.\n"
                f"Game ID: {test_game.game_id}\n"
                f"Game state: {final_game}\n"
                f"Final status: {final_status}"
            )


@pytest.mark.asyncio
async def test_update_error_handling(client, test_game, test_team, test_player, db):
    """Test error handling during single item updates"""

    # Test game update error
    with patch("app.services.nba_data_service.NBADataService") as mock_nba_service:
        mock_service = AsyncMock()
        mock_service.update_game.side_effect = ValueError("Test game update error")
        mock_nba_service.return_value = mock_service

        response = client.post(f"/games/{test_game.game_id}/update")
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()

    # Test team update error
    with patch("app.routers.teams.NBADataService") as mock_nba_service:
        mock_service = AsyncMock()
        mock_service.update_team_players.side_effect = ValueError(
            "Test team update error"
        )
        mock_nba_service.return_value = mock_service

        response = client.post(f"/teams/{test_team.team_id}/update")
        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()

    # Verify error states are properly recorded
    response = client.get("/admin/status")
    assert response.status_code == 200
    status = response.json()
    assert not status[
        "is_updating"
    ], "Update should not be marked as in progress after errors"
