from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.models.models import Game, Player, Team


@pytest.mark.asyncio
async def test_get_teams_pagination(client: TestClient, db):
    """Test teams list pagination"""
    # Create multiple test teams
    teams = []
    for i in range(5):
        team = Team(
            team_id=i,
            name=f"Test Team {i}",
            abbreviation=f"TT{i}",
            conference="East" if i % 2 == 0 else "West",
        )
        db.add(team)
    await db.commit()

    # Test skip and limit
    response = client.get("/teams?skip=2&limit=2")
    assert response.status_code == 200
    teams = response.json()
    assert len(teams) == 2
    assert teams[0]["name"] == "Test Team 2"


@pytest.mark.asyncio
async def test_get_teams_conference_filter(client: TestClient, db):
    """Test filtering teams by conference"""
    teams = [
        Team(team_id=1, name="East Team", abbreviation="EST", conference="East"),
        Team(team_id=2, name="West Team", abbreviation="WST", conference="West"),
    ]
    for team in teams:
        db.add(team)
    await db.commit()

    response = client.get("/teams?conference=East")
    assert response.status_code == 200
    teams = response.json()
    assert len(teams) == 1
    assert teams[0]["name"] == "East Team"


@pytest.mark.asyncio
async def test_get_team_by_id(client: TestClient, db):
    """Test getting a specific team"""
    team = Team(
        team_id=1,
        name="Test Team",
        abbreviation="TST",
        conference="East",
        division="Atlantic",
        wins=50,
        losses=32,
    )
    db.add(team)
    await db.commit()

    response = client.get("/teams/1")
    assert response.status_code == 200
    team_data = response.json()
    assert team_data["name"] == "Test Team"
    assert team_data["wins"] == 50
    assert team_data["losses"] == 32


@pytest.mark.asyncio
async def test_get_team_roster(client: TestClient, db):
    """Test getting a team's roster"""
    # Create a team
    team = Team(team_id=1, name="Test Team", abbreviation="TST", roster_loaded=True)
    db.add(team)

    # Create players for the team
    players = [
        Player(player_id=1, full_name="Player 1", current_team_id=1, is_active=True),
        Player(player_id=2, full_name="Player 2", current_team_id=1, is_active=True),
        Player(
            player_id=3, full_name="Inactive Player", current_team_id=1, is_active=False
        ),
    ]
    for player in players:
        db.add(player)
    await db.commit()

    # Test getting active roster
    response = client.get("/teams/1/roster?active_only=true")
    assert response.status_code == 200
    roster = response.json()
    assert len(roster) == 2  # Only active players

    # Test getting full roster
    response = client.get("/teams/1/roster?active_only=false")
    assert response.status_code == 200
    roster = response.json()
    assert len(roster) == 3  # All players


@pytest.mark.asyncio
async def test_get_team_schedule(client: TestClient, db):
    """Test getting a team's schedule"""
    # Create a team
    team = Team(team_id=1, name="Test Team", abbreviation="TST", games_loaded=True)
    db.add(team)

    # Create team 2 for away games
    team2 = Team(team_id=2, name="Team 2", abbreviation="TM2", games_loaded=True)
    db.add(team2)

    # Create some games
    base_date = datetime(2025, 5, 1, tzinfo=timezone.utc)
    games = [
        # Home game
        Game(
            game_id="1",
            game_date_utc=base_date,
            home_team_id=1,
            away_team_id=2,
            status="Final",
            home_score=100,
            away_score=95,
            season_year="2024-25",  # Added season_year
        ),
        # Away game
        Game(
            game_id="2",
            game_date_utc=base_date + timedelta(days=1),
            home_team_id=2,
            away_team_id=1,
            status="Scheduled",
            season_year="2024-25",  # Added season_year
        ),
    ]
    for game in games:
        db.add(game)
    await db.commit()

    response = client.get("/teams/1/schedule")
    assert response.status_code == 200
    schedule = response.json()
    assert len(schedule) == 2
    assert schedule[0]["game_id"] == "1"
    assert schedule[0]["home_team_id"] == 1
    assert schedule[1]["game_id"] == "2"
    assert schedule[1]["away_team_id"] == 1


@pytest.mark.asyncio
async def test_get_team_stats(client: TestClient, db):
    """Test getting team statistics"""
    # Create a team
    team = Team(team_id=1, name="Test Team", abbreviation="TST", wins=50, losses=32)
    db.add(team)
    await db.commit()

    response = client.get("/teams/1/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["wins"] == 50
    assert stats["losses"] == 32
    assert stats["win_percentage"] == pytest.approx(0.610, 0.001)


@pytest.mark.asyncio
async def test_team_not_found_responses(client: TestClient):
    """Test 404 responses for non-existent team"""
    team_id = 999  # Non-existent team ID

    endpoints = [
        f"/teams/{team_id}",
        f"/teams/{team_id}/roster",
        f"/teams/{team_id}/schedule",
        f"/teams/{team_id}/stats",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 404
        assert response.json()["detail"] == "Team not found"


@pytest.mark.asyncio
async def test_invalid_parameter_responses(client: TestClient):
    """Test invalid parameter handling"""
    # Test invalid skip/limit
    response = client.get("/teams?skip=-1")
    assert response.status_code == 422

    response = client.get("/teams?limit=1001")
    assert response.status_code == 422

    # Test invalid conference
    response = client.get("/teams?conference=Invalid")
    assert response.status_code == 422
