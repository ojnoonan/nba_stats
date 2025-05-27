from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.models.models import Game, Player, PlayerGameStats


@pytest.mark.asyncio
async def test_get_players_pagination(client: TestClient, db):
    """Test player list pagination"""
    # Create multiple test players
    players = []
    for i in range(5):
        player = Player(
            player_id=i, full_name=f"Test Player {i}", is_active=True, current_team_id=1
        )
        db.add(player)
    await db.commit()

    # Test skip and limit
    response = client.get("/players?skip=2&limit=2")
    assert response.status_code == 200
    players = response.json()
    assert len(players) == 2
    assert players[0]["full_name"] == "Test Player 2"


@pytest.mark.asyncio
async def test_get_players_team_filter(client: TestClient, db):
    """Test filtering players by team"""
    # Create players on different teams
    players = [
        Player(
            player_id=1, full_name="Player Team 1", current_team_id=1, is_active=True
        ),
        Player(
            player_id=2, full_name="Player Team 2", current_team_id=2, is_active=True
        ),
    ]
    for player in players:
        db.add(player)
    await db.commit()

    response = client.get("/players?team_id=1")
    assert response.status_code == 200
    players = response.json()
    assert len(players) == 1
    assert players[0]["full_name"] == "Player Team 1"


@pytest.mark.asyncio
async def test_get_active_players_only(client: TestClient, db):
    """Test filtering active players"""
    players = [
        Player(player_id=1, full_name="Active Player", is_active=True),
        Player(player_id=2, full_name="Inactive Player", is_active=False),
    ]
    for player in players:
        db.add(player)
    await db.commit()

    response = client.get("/players/active")
    assert response.status_code == 200
    players = response.json()
    assert len(players) == 1
    assert players[0]["full_name"] == "Active Player"


@pytest.mark.asyncio
async def test_get_player_stats_ordering(client: TestClient, db):
    """Test player stats are properly ordered by date"""
    # Create a player
    player = Player(player_id=1, full_name="Test Player", is_active=True)
    db.add(player)

    # Create two games on different dates
    games = [
        Game(
            game_id="1",
            game_date_utc=datetime(2025, 5, 1, tzinfo=timezone.utc),
            home_team_id=1,
            away_team_id=2,
            status="Final",
            season_year="2024-25",
        ),
        Game(
            game_id="2",
            game_date_utc=datetime(2025, 5, 2, tzinfo=timezone.utc),
            home_team_id=1,
            away_team_id=2,
            status="Final",
            season_year="2024-25",
        ),
    ]
    for game in games:
        db.add(game)

    # Create stats for each game
    stats = [
        PlayerGameStats(player_id=1, game_id="1", points=10, team_id=1),
        PlayerGameStats(player_id=1, game_id="2", points=20, team_id=1),
    ]
    for stat in stats:
        db.add(stat)

    await db.commit()

    response = client.get("/players/1/stats")
    assert response.status_code == 200
    stats = response.json()
    assert len(stats) == 2
    # Should be ordered by newest first
    assert stats[0]["points"] == 20
    assert stats[1]["points"] == 10


@pytest.mark.asyncio
async def test_last_x_games_calculation(client: TestClient, db):
    """Test last X games statistics calculation"""
    # Create a player
    player = Player(player_id=1, full_name="Test Player", is_active=True)
    db.add(player)

    # Create games and stats
    for i in range(3):
        game = Game(
            game_id=str(i + 1),
            game_date_utc=datetime(2025, 5, i + 1, tzinfo=timezone.utc),
            home_team_id=1,
            away_team_id=2,
            status="Final",
            season_year="2024-25",  # Added season_year
        )
        db.add(game)

        stats = PlayerGameStats(
            player_id=1,
            game_id=str(i + 1),
            points=10 * (i + 1),
            rebounds=5 * (i + 1),
            assists=2 * (i + 1),
            team_id=1,  # Added team_id
        )
        db.add(stats)

    await db.commit()

    # Test with count=2 (last 2 games)
    response = client.get("/players/1/last_x_games?count=2")
    assert response.status_code == 200
    result = response.json()
    assert result["games_analyzed"] == 2
    # Average of last 2 games (20 and 30 points)
    assert result["stats"]["avg_points"] == 25.0
    # Average of last 2 games (10 and 15 rebounds)
    assert result["stats"]["avg_rebounds"] == 12.5


@pytest.mark.asyncio
async def test_high_low_games_correct_order(client: TestClient, db):
    """Test high/low games are correctly ordered"""
    # Create a player
    player = Player(player_id=1, full_name="Test Player", is_active=True)
    db.add(player)

    # Create games with various point totals
    points = [15, 30, 5, 25, 10]
    for i, point_total in enumerate(points):
        game = Game(
            game_id=str(i + 1),
            game_date_utc=datetime(2025, 5, i + 1, tzinfo=timezone.utc),
            home_team_id=1,
            away_team_id=2,
            status="Final",
            season_year="2024-25",  # Added season_year
        )
        db.add(game)

        stats = PlayerGameStats(
            player_id=1,
            game_id=str(i + 1),
            points=point_total,
            team_id=1,  # Added team_id
        )
        db.add(stats)

    await db.commit()

    response = client.get("/players/1/high_low_games?count=3")
    assert response.status_code == 200
    result = response.json()

    # Check top 3 (should be 30, 25, 15)
    assert len(result["top_5"]) == 3
    assert [g["points"] for g in result["top_5"]] == [30, 25, 15]

    # Check bottom 3 (should be 5, 10, 15)
    assert len(result["bottom_5"]) == 3
    assert [g["points"] for g in result["bottom_5"]] == [5, 10, 15]


@pytest.mark.asyncio
async def test_player_not_found_responses(client: TestClient):
    """Test 404 responses for non-existent players"""
    player_id = 999  # Non-existent player ID

    # Test all endpoints that take a player_id
    endpoints = [
        f"/players/{player_id}",
        f"/players/{player_id}/stats",
        f"/players/{player_id}/last_x_games",
        f"/players/{player_id}/high_low_games",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 404
        assert response.json()["detail"] == "Player not found"


@pytest.mark.asyncio
async def test_invalid_parameter_responses(client: TestClient, db):
    """Test invalid parameter handling"""
    # Create a test player
    player = Player(player_id=1, full_name="Test Player", is_active=True)
    db.add(player)
    await db.commit()

    # Test invalid skip/limit
    response = client.get("/players?skip=-1")
    assert response.status_code == 422

    response = client.get("/players?limit=1001")
    assert response.status_code == 422

    # Test invalid count for last_x_games
    response = client.get("/players/1/last_x_games?count=21")
    assert response.status_code == 422

    response = client.get("/players/1/last_x_games?count=0")
    assert response.status_code == 422
