import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database.database import get_db
from app.models.models import DataUpdateStatus, Game, Player, PlayerGameStats, Team


@pytest.mark.asyncio
async def test_game_update_completeness(client, test_team, test_away_team, db):
    """Test that game updates properly update all required data"""

    # Create test players for both teams
    home_player = Player(
        player_id=101,
        full_name="Home Player 1",
        first_name="Home",
        last_name="Player 1",
        current_team_id=test_team.team_id,
        position="G",
        jersey_number="1",
        is_active=True,
        is_loaded=False,
        headshot_url="https://example.com/home-player-1.png",
    )
    away_player = Player(
        player_id=102,
        full_name="Away Player 1",
        first_name="Away",
        last_name="Player 1",
        current_team_id=test_away_team.team_id,
        position="F",
        jersey_number="2",
        is_active=True,
        is_loaded=False,
        headshot_url="https://example.com/away-player-1.png",
    )
    db.add(home_player)
    db.add(away_player)
    await db.commit()

    # Get or create initial DataUpdateStatus record with teams and players loaded
    from sqlalchemy import select

    stmt = select(DataUpdateStatus).filter_by(id=1)
    result = await db.execute(stmt)
    status = result.scalar_one_or_none()

    if not status:
        status = DataUpdateStatus(
            id=1,
            is_updating=False,
            current_phase=None,
            cancellation_requested=False,
            last_successful_update=datetime.now(timezone.utc),
            next_scheduled_update=None,
            teams_updated=True,  # Team data should be loaded
            players_updated=True,  # Player data should be loaded
            games_updated=False,
            teams_percent_complete=100,
            players_percent_complete=100,
            games_percent_complete=0,
            current_detail=None,
            last_error=None,
            last_error_time=None,
            teams_last_update=datetime.now(timezone.utc),
            players_last_update=datetime.now(timezone.utc),
            games_last_update=None,
            components={
                "teams": {
                    "updated": True,
                    "percent_complete": 100,
                    "last_error": None,
                    "last_update": datetime.now(timezone.utc),
                },
                "players": {
                    "updated": True,
                    "percent_complete": 100,
                    "last_error": None,
                    "last_update": datetime.now(timezone.utc),
                },
            },
        )
        db.add(status)
    else:
        # Update existing status to our test requirements
        status.is_updating = False
        status.current_phase = None
        status.cancellation_requested = False
        status.teams_updated = True
        status.players_updated = True
        status.games_updated = False
        status.teams_percent_complete = 100
        status.players_percent_complete = 100
        status.games_percent_complete = 0
        status.components = {
            "teams": {
                "updated": True,
                "percent_complete": 100,
                "last_error": None,
                "last_update": datetime.now(timezone.utc),
            },
            "players": {
                "updated": True,
                "percent_complete": 100,
                "last_error": None,
                "last_update": datetime.now(timezone.utc),
            },
        }
    await db.commit()

    # Create test games
    games = []
    now = datetime.now(timezone.utc)
    for i in range(3):
        game = Game(
            game_id=f"2025{i:02d}",
            game_date_utc=now + timedelta(days=i),
            home_team_id=test_team.team_id,
            away_team_id=test_away_team.team_id,
            status="Final" if i == 0 else "Scheduled",
            home_score=100 + i if i == 0 else None,
            away_score=98 + i if i == 0 else None,
            is_loaded=False,
        )
        db.add(game)
        games.append(game)
    await db.commit()

    # Set up mock service
    with patch("app.routers.teams.NBADataService") as mock_nba_service:

        async def mock_update_team_games(team_id):
            # Get current status
            stmt = select(DataUpdateStatus)
            result = await db.execute(stmt)
            status = result.scalar_one_or_none()
            if status:
                status.is_updating = True
                status.current_phase = "games"
                # Initialize components if needed
                status.components = getattr(status, "components", {})
                if "games" not in status.components:
                    status.components["games"] = {}
                status.components["games"].update(
                    {
                        "updated": False,
                        "percent_complete": 0,
                        "last_error": None,
                        "last_update": None,
                    }
                )
            await db.commit()

            # Update each game
            for idx, game in enumerate(games):
                game.is_loaded = True
                game.last_updated = datetime.now(timezone.utc)

                # For completed games, add some player stats
                if game.status == "Final":
                    for team_id in [test_team.team_id, test_away_team.team_id]:
                        player_stmt = select(Player).filter(
                            Player.current_team_id == team_id
                        )
                        players = (await db.execute(player_stmt)).scalars().all()
                        for player in players:
                            stats = PlayerGameStats(
                                player_id=player.player_id,
                                game_id=game.game_id,
                                team_id=team_id,
                                minutes="25:00",
                                points=10,
                                rebounds=5,
                                assists=3,
                                steals=1,
                                blocks=1,
                                turnovers=2,
                                fgm=4,
                                fga=8,
                                tpm=1,
                                tpa=3,
                                ftm=1,
                                fta=2,
                            )
                            db.add(stats)

                if status:
                    percent = int(((idx + 1) / len(games)) * 100)
                    status.games_percent_complete = percent
                    status.components["games"].update(
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
                    team.games_loaded = True
                    team.last_updated = now

                # Update global status
                status.is_updating = False
                status.games_updated = True
                status.games_last_update = now
                status.games_percent_complete = 100
                status.current_phase = None
                status.components["games"].update(
                    {
                        "updated": True,
                        "last_update": now,
                        "percent_complete": 100,
                        "last_error": None,
                    }
                )
            await db.commit()

        mock_service = AsyncMock()
        mock_service.update_team_games.side_effect = mock_update_team_games
        mock_nba_service.return_value = mock_service

        # Trigger the update
        response = client.post(f"/teams/{test_team.team_id}/update/games")
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
                assert status["components"]["games"]["updated"]
                assert status["components"]["games"]["percent_complete"] == 100
                assert not status["components"]["games"]["last_error"]
                break

            time.sleep(0.5)
        else:
            raise AssertionError("Update did not complete in time")

        # Verify all games are properly marked as loaded and have correct data
        for game in games:
            response = client.get(f"/games/{game.game_id}")
            assert response.status_code == 200
            game_data = response.json()

            # Verify core game data
            assert game_data["is_loaded"], f"Game {game.game_id} not marked as loaded"
            assert game_data[
                "last_updated"
            ], f"Game {game.game_id} missing last_updated timestamp"
            assert (
                game_data["home_team_id"] == test_team.team_id
            ), f"Game {game.game_id} home team mismatch"
            assert (
                game_data["away_team_id"] == test_away_team.team_id
            ), f"Game {game.game_id} away team mismatch"
            assert (
                game_data["status"] == game.status
            ), f"Game {game.game_id} status mismatch"

            # Verify scores for completed games
            if game.status == "Final":
                assert (
                    game_data["home_score"] == game.home_score
                ), f"Game {game.game_id} home score mismatch"
                assert (
                    game_data["away_score"] == game.away_score
                ), f"Game {game.game_id} away score mismatch"

                # Verify player stats exist
                stats_response = client.get(f"/games/{game.game_id}/stats")
                assert stats_response.status_code == 200
                stats_data = stats_response.json()
                assert len(stats_data) > 0, f"Game {game.game_id} missing player stats"

        # Verify team games endpoint returns all games
        response = client.get(f"/teams/{test_team.team_id}/schedule")
        assert response.status_code == 200
        team_games = response.json()
        assert len(team_games) == len(
            games
        ), "Not all games returned in team schedule endpoint"

        # Verify upcoming games endpoint
        upcoming_response = client.get("/games/upcoming")
        assert upcoming_response.status_code == 200
        upcoming_games = upcoming_response.json()
        expected_upcoming = len([g for g in games if g.status == "Scheduled"])
        assert (
            len(upcoming_games) == expected_upcoming
        ), "Incorrect number of upcoming games"

        # Verify game stats for completed games
        completed_games = [g for g in games if g.status == "Final"]
        for game in completed_games:
            stats_response = client.get(f"/games/{game.game_id}/box_score")
            assert stats_response.status_code == 200
            box_score = stats_response.json()
            assert (
                "home_team" in box_score
            ), f"Game {game.game_id} missing home team stats"
            assert (
                "away_team" in box_score
            ), f"Game {game.game_id} missing away team stats"
            assert (
                len(box_score["home_team"]["players"]) > 0
            ), f"Game {game.game_id} missing home team player stats"
            assert (
                len(box_score["away_team"]["players"]) > 0
            ), f"Game {game.game_id} missing away team player stats"

    # Cleanup test players
    from sqlalchemy.sql import text

    await db.execute(
        text("DELETE FROM player_game_stats WHERE player_id IN (101, 102)")
    )
    await db.execute(text("DELETE FROM players WHERE player_id IN (101, 102)"))
    await db.commit()
