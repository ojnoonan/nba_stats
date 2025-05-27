from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.models.models import Game, Player, PlayerGameStats, Team


@pytest.fixture
def test_game():
    return Game(
        game_id="test123",
        game_date_utc=datetime(2025, 5, 1, tzinfo=timezone.utc),
        home_team_id=1,
        away_team_id=2,
        home_score=100,
        away_score=95,
        status="Final",
        season_year="2024-25",
    )


@pytest.mark.asyncio
async def test_get_games_pagination(client: TestClient, db):
    """Test games list pagination"""
    # Create multiple test games
    games = []
    base_date = datetime(2025, 5, 1, tzinfo=timezone.utc)
    for i in range(5):
        game = Game(
            game_id=str(i),
            game_date_utc=base_date + timedelta(days=i),
            home_team_id=1,
            away_team_id=2,
            home_score=100 + i,
            away_score=95 + i,
            status="Final",
            season_year="2024-25",  # Added season_year
        )
        db.add(game)
    await db.commit()

    # Test skip and limit
    response = client.get("/games?skip=2&limit=2")
    assert response.status_code == 200
    games = response.json()
    assert len(games) == 2
    assert games[0]["game_id"] == "2"


@pytest.mark.asyncio
async def test_get_games_date_filter(client: TestClient, db):
    """Test filtering games by date"""
    # Create games on different dates
    dates = [
        datetime(2025, 5, 1, tzinfo=timezone.utc),
        datetime(2025, 5, 2, tzinfo=timezone.utc),
        datetime(2025, 5, 3, tzinfo=timezone.utc),
    ]
    for i, date in enumerate(dates):
        game = Game(
            game_id=str(i),
            game_date_utc=date,
            home_team_id=1,
            away_team_id=2,
            status="Final",
            season_year="2024-25",  # Added season_year
        )
        db.add(game)
    await db.commit()

    # Test date filter
    response = client.get("/games?date=2025-05-02")
    assert response.status_code == 200
    games = response.json()
    assert len(games) == 1
    assert games[0]["game_id"] == "1"


@pytest.mark.asyncio
async def test_get_game_by_id(client: TestClient, db):
    """Test getting a specific game"""
    # Create a test game
    game = Game(
        game_id="test123",
        game_date_utc=datetime(2025, 5, 1, tzinfo=timezone.utc),
        home_team_id=1,
        away_team_id=2,
        home_score=100,
        away_score=95,
        status="Final",
        season_year="2024-25",  # Added season_year
    )
    db.add(game)
    await db.commit()

    response = client.get("/games/test123")
    assert response.status_code == 200
    game_data = response.json()
    assert game_data["game_id"] == "test123"
    assert game_data["home_score"] == 100
    assert game_data["away_score"] == 95


@pytest.mark.asyncio
async def test_get_game_stats(client: TestClient, db):
    """Test getting game statistics"""
    # Create necessary test data
    game = Game(
        game_id="test123",
        game_date_utc=datetime(2025, 5, 1, tzinfo=timezone.utc),
        home_team_id=1,
        away_team_id=2,
        status="Final",
        season_year="2024-25",  # Added season_year
    )
    db.add(game)

    # Create some players
    players = [
        Player(player_id=1, full_name="Home Player"),
        Player(player_id=2, full_name="Away Player"),
    ]
    for player in players:
        db.add(player)

    # Create player stats for the game
    stats = [
        PlayerGameStats(
            game_id="test123",
            player_id=1,
            team_id=1,
            minutes="32:00",
            points=20,
            rebounds=10,
            assists=5,
        ),
        PlayerGameStats(
            game_id="test123",
            player_id=2,
            team_id=2,
            minutes="30:00",
            points=15,
            rebounds=8,
            assists=4,
        ),
    ]
    for stat in stats:
        db.add(stat)

    await db.commit()

    response = client.get("/games/test123/stats")
    assert response.status_code == 200
    stats = response.json()
    assert len(stats) == 2
    assert stats[0]["points"] == 20
    assert stats[1]["points"] == 15


@pytest.mark.asyncio
async def test_get_games_by_team(client: TestClient, db):
    """Test getting games for a specific team"""
    # Create a test team first
    team_id = 1
    team = Team(
        team_id=team_id,
        name="Test Team",
        abbreviation="TST",
        games_loaded=True,  # Important: set games_loaded to True
        wins=0,
        losses=0,
        loading_progress=0,
        roster_loaded=False,
    )
    db.add(team)

    # Create another team for away games
    away_team = Team(
        team_id=2,
        name="Away Team",
        abbreviation="AWAY",
        games_loaded=True,
        wins=0,
        losses=0,
        loading_progress=0,
        roster_loaded=False,
    )
    db.add(away_team)

    # Create a third team
    third_team = Team(
        team_id=3,
        name="Third Team",
        abbreviation="THRD",
        games_loaded=True,
        wins=0,
        losses=0,
        loading_progress=0,
        roster_loaded=False,
    )
    db.add(third_team)

    # Create a fourth team
    fourth_team = Team(
        team_id=4,
        name="Fourth Team",
        abbreviation="FRTH",
        games_loaded=True,
        wins=0,
        losses=0,
        loading_progress=0,
        roster_loaded=False,
    )
    db.add(fourth_team)

    games = [
        # Home game
        Game(
            game_id="1",
            game_date_utc=datetime(2025, 5, 1, tzinfo=timezone.utc),
            home_team_id=team_id,
            away_team_id=2,
            status="Final",
            season_year="2024-25",  # Added season_year
        ),
        # Away game
        Game(
            game_id="2",
            game_date_utc=datetime(2025, 5, 2, tzinfo=timezone.utc),
            home_team_id=2,
            away_team_id=team_id,
            status="Final",
            season_year="2024-25",  # Added season_year
        ),
        # Game not involving the team
        Game(
            game_id="3",
            game_date_utc=datetime(2025, 5, 3, tzinfo=timezone.utc),
            home_team_id=3,
            away_team_id=4,
            status="Final",
            season_year="2024-25",  # Added season_year
        ),
    ]
    for game in games:
        db.add(game)
    await db.commit()

    response = client.get(f"/games?team_id={team_id}")
    assert response.status_code == 200
    games = response.json()
    assert len(games) == 2  # Should only get games involving team_id


@pytest.mark.asyncio
async def test_game_not_found(client: TestClient):
    """Test 404 response for non-existent game"""
    response = client.get("/games/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Game not found"

    response = client.get("/games/nonexistent/stats")
    assert response.status_code == 404
    assert response.json()["detail"] == "Game not found"


@pytest.mark.asyncio
async def test_invalid_date_format(client: TestClient):
    """Test invalid date format handling"""
    response = client.get("/games?date=invalid-date")
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_pagination_validation(client: TestClient):
    """Test pagination parameter validation"""
    # Test invalid skip
    response = client.get("/games?skip=-1")
    assert response.status_code == 422

    # Test invalid limit
    response = client.get("/games?limit=1001")
    assert response.status_code == 422
