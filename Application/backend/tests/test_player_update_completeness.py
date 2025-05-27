import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.database import get_db
from app.models.models import DataUpdateStatus, Player, Team


@pytest.mark.asyncio
async def test_player_update_completeness(client, test_team, db):
    """Test that player updates properly update all required data"""

    # Update the existing DataUpdateStatus record with team data already loaded
    status_query = await db.execute(select(DataUpdateStatus).filter_by(id=1))
    status = status_query.scalar_one()
    now = datetime.now(timezone.utc)

    status.is_updating = False
    status.current_phase = None
    status.cancellation_requested = False
    status.last_successful_update = now
    status.teams_updated = True  # Team data should be loaded
    status.players_updated = False
    status.games_updated = False
    status.teams_percent_complete = 100  # Team data complete
    status.players_percent_complete = 0
    status.games_percent_complete = 0
    status.current_detail = None
    status.last_error = None
    status.last_error_time = None
    status.teams_last_update = now
    status.players_last_update = None
    status.games_last_update = None
    status.components = {
        "teams": {
            "updated": True,
            "percent_complete": 100,
            "last_error": None,
            "last_update": now.isoformat(),
        }
    }
    await db.commit()

    # Update test team status
    test_team.roster_loaded = False
    test_team.loading_progress = 0
    test_team.last_updated = None
    await db.commit()

    # Create multiple test players
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

    # Set up mock service
    with patch("app.routers.teams.NBADataService") as mock_nba_service:

        async def mock_update_team_players(team_id):
            # Get current status
            stmt = select(DataUpdateStatus)
            result = await db.execute(stmt)
            status = result.scalar_one_or_none()
            if status:
                status.is_updating = True
                status.current_phase = "players"
                # Initialize components if needed
                status.components = getattr(status, "components", {})
                if "players" not in status.components:
                    status.components["players"] = {}
                status.components["players"].update(
                    {
                        "updated": False,
                        "percent_complete": 0,
                        "last_error": None,
                        "last_update": None,
                    }
                )
            await db.commit()

            # Update each player
            for idx, player in enumerate(players):
                player.is_loaded = True
                player.last_updated = datetime.now(timezone.utc)
                if status:
                    percent = int(((idx + 1) / len(players)) * 100)
                    status.players_percent_complete = percent
                    status.components = getattr(status, "components", {})
                    if "players" not in status.components:
                        status.components["players"] = {}
                    status.components["players"].update(
                        {
                            "percent_complete": percent,
                            "last_error": None,
                            "updated": percent == 100,
                        }
                    )
                await db.commit()

            # Final status update
            if status:
                now = datetime.now(timezone.utc)

                # Update team status
                team_stmt = select(Team).filter(Team.team_id == team_id)
                team_result = await db.execute(team_stmt)
                team = team_result.scalar_one_or_none()
                if team:
                    team.roster_loaded = True
                    team.loading_progress = 100
                    team.last_updated = now

                # Update global status
                status.is_updating = False
                status.players_updated = True
                status.players_last_update = now
                status.players_percent_complete = 100
                status.current_phase = None
                status.components = getattr(status, "components", {})
                if "players" not in status.components:
                    status.components["players"] = {}
                status.components["players"].update(
                    {
                        "updated": True,
                        "last_update": now,
                        "percent_complete": 100,
                        "last_error": None,
                    }
                )
            await db.commit()

        mock_service = AsyncMock()
        mock_service.update_team_players.side_effect = mock_update_team_players
        mock_nba_service.return_value = mock_service

        # Trigger the update
        response = client.post(f"/teams/{test_team.team_id}/update")
        assert response.status_code == 200

        # Wait for update to complete
        max_attempts = 30
        for attempt in range(max_attempts):
            # Check admin status
            status_response = client.get("/admin/status")
            assert status_response.status_code == 200
            status = status_response.json()

            if not status["is_updating"]:
                # Verify status is correct
                assert status["components"]["players"]["updated"]
                assert status["components"]["players"]["percent_complete"] == 100
                assert not status["components"]["players"]["last_error"]
                break

            time.sleep(0.5)
        else:
            raise AssertionError("Update did not complete in time")

        # Verify all players are properly marked as loaded and have correct data
        for player in players:
            response = client.get(f"/players/{player.player_id}")
            assert response.status_code == 200
            player_data = response.json()

            # Verify core player data
            assert player_data[
                "is_loaded"
            ], f"Player {player.player_id} not marked as loaded"
            assert player_data[
                "last_updated"
            ], f"Player {player.player_id} missing last_updated timestamp"
            assert (
                player_data["full_name"] == player.full_name
            ), f"Player {player.player_id} name mismatch"
            assert (
                player_data["current_team_id"] == test_team.team_id
            ), f"Player {player.player_id} team mismatch"
            assert (
                player_data["position"] == player.position
            ), f"Player {player.player_id} position mismatch"
            assert (
                player_data["jersey_number"] == player.jersey_number
            ), f"Player {player.player_id} jersey number mismatch"
            assert (
                player_data["is_active"] == player.is_active
            ), f"Player {player.player_id} active status mismatch"

        # Verify team players endpoint returns all players with correct data
        response = client.get(f"/teams/{test_team.team_id}/players")
        assert response.status_code == 200
        team_players = response.json()
        assert len(team_players) == len(
            players
        ), "Not all players returned in team players endpoint"

        # Verify each player in the team response
        for player_data in team_players:
            matching_player = next(
                (p for p in players if p.player_id == player_data["player_id"]), None
            )
            assert (
                matching_player is not None
            ), f"Unknown player {player_data['player_id']} in team response"
            assert player_data[
                "is_loaded"
            ], f"Player {player_data['player_id']} not marked as loaded in team response"
            assert (
                player_data["full_name"] == matching_player.full_name
            ), f"Player {player_data['player_id']} name mismatch in team response"
            assert (
                player_data["position"] == matching_player.position
            ), f"Player {player_data['player_id']} position mismatch in team response"

        # Verify team status and data completeness
        team_response = client.get(f"/teams/{test_team.team_id}")
        assert team_response.status_code == 200
        team_data = team_response.json()

        # Verify team metadata
        assert team_data["roster_loaded"], "Team not marked as roster loaded"
        assert team_data["loading_progress"] == 100, "Team loading progress not 100%"
        assert (
            team_data["last_updated"] is not None
        ), "Team missing last_updated timestamp"

        # Verify team core data
        assert team_data["team_id"] == test_team.team_id, "Team ID mismatch"
        assert team_data["name"] == test_team.name, "Team name mismatch"
        assert (
            team_data["abbreviation"] == test_team.abbreviation
        ), "Team abbreviation mismatch"

        # Verify API endpoints for different views of team data
        # Team roster view
        roster_response = client.get(f"/teams/{test_team.team_id}/roster")
        assert roster_response.status_code == 200
        roster_data = roster_response.json()
        assert len(roster_data) == len(players), "Roster size mismatch"

        # Active players only view
        active_response = client.get(
            f"/teams/{test_team.team_id}/roster?active_only=true"
        )
        assert active_response.status_code == 200
        active_data = active_response.json()
        assert len(active_data) == len(
            [p for p in players if p.is_active]
        ), "Active roster size mismatch"

        # Verify admin status endpoint shows team as complete
        admin_response = client.get("/admin/status")
        assert admin_response.status_code == 200
        admin_status = admin_response.json()
        assert admin_status[
            "teams_updated"
        ], "Teams not marked as updated in admin status"
        assert admin_status["components"]["teams"][
            "updated"
        ], "Teams component not marked as updated"
        assert (
            admin_status["components"]["teams"]["percent_complete"] == 100
        ), "Teams component not at 100%"
