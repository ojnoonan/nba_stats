import asyncio
import time

import pytest
from fastapi.testclient import TestClient


def test_get_players(client, test_player):
    """Test getting all players"""
    response = client.get("/players")
    assert response.status_code == 200
    players = response.json()
    assert len(players) == 1
    assert players[0]["player_id"] == test_player.player_id
    assert players[0]["full_name"] == test_player.full_name
    assert players[0]["current_team_id"] == test_player.current_team_id


def test_get_players_by_team(client, test_player, test_team):
    """Test getting players filtered by team"""
    response = client.get(f"/players?team_id={test_team.team_id}")
    assert response.status_code == 200
    players = response.json()
    assert len(players) == 1
    assert players[0]["player_id"] == test_player.player_id
    assert players[0]["current_team_id"] == test_team.team_id


def test_get_player(client, test_player):
    """Test getting a specific player"""
    response = client.get(f"/players/{test_player.player_id}")
    assert response.status_code == 200
    player = response.json()
    assert player["player_id"] == test_player.player_id
    assert player["full_name"] == test_player.full_name
    assert player["first_name"] == test_player.first_name
    assert player["last_name"] == test_player.last_name
    assert player["position"] == test_player.position
    assert player["jersey_number"] == test_player.jersey_number


def test_get_nonexistent_player(client):
    """Test getting a player that doesn't exist"""
    response = client.get("/players/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Player not found"


def test_get_player_stats(client, test_player, test_player_stats):
    """Test getting player statistics"""
    response = client.get(f"/players/{test_player.player_id}/stats")
    assert response.status_code == 200
    stats = response.json()
    assert len(stats) == 1
    assert stats[0]["points"] == test_player_stats.points
    assert stats[0]["rebounds"] == test_player_stats.rebounds
    assert stats[0]["assists"] == test_player_stats.assists


def test_get_player_last_n_games(client, test_player, test_player_stats):
    """Test getting player's last N games statistics"""
    response = client.get(f"/players/{test_player.player_id}/last_x_games?count=5")
    assert response.status_code == 200
    stats = response.json()
    assert stats["games_analyzed"] == 1
    assert stats["stats"]["avg_points"] == test_player_stats.points
    assert stats["stats"]["avg_rebounds"] == test_player_stats.rebounds
    assert stats["stats"]["avg_assists"] == test_player_stats.assists


def test_get_player_high_low_games(client, test_player, test_player_stats):
    """Test getting player's highest and lowest scoring games"""
    response = client.get(f"/players/{test_player.player_id}/high_low_games")
    assert response.status_code == 200
    games = response.json()
    assert len(games["top_5"]) == 1
    assert games["top_5"][0]["points"] == test_player_stats.points
    assert len(games["bottom_5"]) == 1
    assert games["bottom_5"][0]["points"] == test_player_stats.points


from unittest.mock import AsyncMock, patch


@patch("app.routers.teams.NBADataService")
def test_player_update_status(mock_nba_service, client, test_player, test_team, db):
    """Test that a team's player update correctly sets the status"""
    # Get initial status
    initial_status = client.get("/admin/status").json()
    assert not initial_status["is_updating"], "Update already in progress"

    # Set up mock service with custom behavior
    async def mock_update_team_players(team_id):
        import asyncio
        from datetime import datetime, timezone

        from sqlalchemy import select, update

        from app.models.models import DataUpdateStatus, Player

        # Simulate a bit of processing time
        await asyncio.sleep(0.1)

        # Update the player status
        stmt = (
            update(Player)
            .where(Player.player_id == test_player.player_id)
            .values(is_loaded=True)
        )
        await db.execute(stmt)

        # Update the status
        stmt = select(DataUpdateStatus)
        result = await db.execute(stmt)
        status = result.scalar_one_or_none()
        if status:
            status.players_updated = True
            status.players_last_update = datetime.now(timezone.utc)
            status.players_percent_complete = 100
            status.players_updated = True
            status.players_percent_complete = 100
        await db.commit()

    mock_service = AsyncMock()
    mock_service.update_team_players.side_effect = mock_update_team_players
    mock_nba_service.return_value = mock_service

    # Trigger update for the test team
    response = client.post(f"/teams/{test_team.team_id}/update")
    assert response.status_code == 200

    # Wait for a reasonable time for a single player update
    max_attempts = 30  # 30 attempts with shorter backoff
    for attempt in range(max_attempts):
        response = client.get("/admin/status")
        assert response.status_code == 200
        status = response.json()

        # Check if update is complete
        if not status["is_updating"]:
            assert status["components"]["players"]["updated"]
            assert status["components"]["players"]["last_update"] is not None
            assert status["components"]["players"]["percent_complete"] == 100
            assert not status["components"]["players"]["last_error"]
            break

        # If still updating, verify phase and wait
        assert status["current_phase"] == "players"
        time.sleep(0.5)  # Fixed sleep time for single player
    else:
        final_status = client.get("/admin/status").json()
        raise AssertionError(
            f"Single player update did not complete in time.\n"
            f"Player ID: {test_player.player_id}\n"
            f"Final status: {final_status}"
        )


@pytest.mark.asyncio
async def test_player_loaded_flag(client, test_player, test_team, db):
    """Test that a player is correctly marked as loaded after team update"""
    # Get initial player status
    response = client.get(f"/players/{test_player.player_id}")
    assert response.status_code == 200
    initial_player = response.json()
    assert not initial_player.get(
        "is_loaded", False
    ), "Player should not be loaded initially"

    # Set up mock service with custom behavior
    with patch("app.routers.teams.NBADataService") as mock_nba_service:

        async def mock_update_team_players(team_id):
            from sqlalchemy import update

            from app.models.models import Player

            # Update the player status
            stmt = (
                update(Player)
                .where(Player.player_id == test_player.player_id)
                .values(is_loaded=True)
            )
            await db.execute(stmt)
            await db.commit()

        mock_service = AsyncMock()
        mock_service.update_team_players.side_effect = mock_update_team_players
        mock_nba_service.return_value = mock_service

        # Trigger update for the test team
        response = client.post(f"/teams/{test_team.team_id}/update")
        assert response.status_code == 200

        # Wait for a reasonable time for a single player update
        max_attempts = 30  # 30 attempts with fixed interval
        for attempt in range(max_attempts):
            # Check player data
            response = client.get(f"/players/{test_player.player_id}")
            assert response.status_code == 200
            player = response.json()

            # Check if player is loaded
            if player.get("is_loaded", False):
                status_response = client.get("/admin/status")
                status = status_response.json()
                assert not status[
                    "is_updating"
                ], "Update should be complete when player is loaded"
                break

            await asyncio.sleep(0.5)  # Fixed sleep time for single player
        else:
            # Get final state for error reporting
            final_player = client.get(f"/players/{test_player.player_id}").json()
            final_status = client.get("/admin/status").json()
            raise AssertionError(
                f"Player was not marked as loaded after update.\n"
                f"Player ID: {test_player.player_id}\n"
                f"Player state: {final_player}\n"
                f"Final status: {final_status}"
            )
