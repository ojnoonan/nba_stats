import pytest
from fastapi.testclient import TestClient

from app.models.models import Game, Player, Team


@pytest.mark.asyncio
async def test_search_players(client: TestClient, db):
    """Test searching for players"""
    # Create test players
    players = [
        Player(player_id=1, full_name="LeBron James", is_active=True),
        Player(player_id=2, full_name="James Harden", is_active=True),
        Player(player_id=3, full_name="Kevin Durant", is_active=True),
    ]
    for player in players:
        db.add(player)
    await db.commit()

    # Test exact match
    response = client.get("/search?q=LeBron James")
    assert response.status_code == 200
    results = response.json()
    assert len(results["players"]) == 1
    assert results["players"][0]["full_name"] == "LeBron James"

    # Test partial match
    response = client.get("/search?q=James")
    assert response.status_code == 200
    results = response.json()
    assert len(results["players"]) == 2
    assert all("James" in p["full_name"] for p in results["players"])


@pytest.mark.asyncio
async def test_search_teams(client: TestClient, db):
    """Test searching for teams"""
    # Create test teams
    teams = [
        Team(team_id=1, name="Los Angeles Lakers", abbreviation="LAL"),
        Team(team_id=2, name="LA Clippers", abbreviation="LAC"),
        Team(team_id=3, name="Boston Celtics", abbreviation="BOS"),
    ]
    for team in teams:
        db.add(team)
    await db.commit()

    # Test city search
    response = client.get("/search?q=Los Angeles")
    assert response.status_code == 200
    results = response.json()
    assert len(results["teams"]) == 1
    assert results["teams"][0]["name"] == "Los Angeles Lakers"

    # Test abbreviation search
    response = client.get("/search?q=LAL")
    assert response.status_code == 200
    results = response.json()
    assert len(results["teams"]) == 1
    assert results["teams"][0]["abbreviation"] == "LAL"


@pytest.mark.asyncio
async def test_combined_search(client: TestClient, db):
    """Test searching across all entities"""
    # Create test data
    player = Player(player_id=1, full_name="Stephen Curry", is_active=True)
    team = Team(team_id=1, name="Golden State Warriors", abbreviation="GSW")
    db.add(player)
    db.add(team)
    await db.commit()

    # Search for "Golden"
    response = client.get("/search?q=Golden")
    assert response.status_code == 200
    results = response.json()
    assert len(results["teams"]) == 1
    assert len(results["players"]) == 0
    assert results["teams"][0]["name"] == "Golden State Warriors"


@pytest.mark.asyncio
async def test_empty_search(client: TestClient):
    """Test empty search query handling"""
    response = client.get("/search?q=")
    assert response.status_code == 400
    assert response.json()["detail"] == "Search query cannot be empty"


@pytest.mark.asyncio
async def test_minimum_query_length(client: TestClient):
    """Test minimum query length requirement"""
    response = client.get("/search?q=a")
    assert response.status_code == 400
    assert "minimum length" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_search_inactive_players(client: TestClient, db):
    """Test searching for inactive players"""
    players = [
        Player(player_id=1, full_name="Active Player", is_active=True),
        Player(player_id=2, full_name="Inactive Player", is_active=False),
    ]
    for player in players:
        db.add(player)
    await db.commit()

    # Test with include_inactive=false (default)
    response = client.get("/search?q=Player")
    assert response.status_code == 200
    results = response.json()
    assert len(results["players"]) == 1
    assert results["players"][0]["full_name"] == "Active Player"

    # Test with include_inactive=true
    response = client.get("/search?q=Player&include_inactive=true")
    assert response.status_code == 200
    results = response.json()
    assert len(results["players"]) == 2


@pytest.mark.asyncio
async def test_search_pagination(client: TestClient, db):
    """Test search results pagination"""
    # Create multiple test players
    players = []
    for i in range(5):
        player = Player(player_id=i, full_name=f"Test Player {i}", is_active=True)
        db.add(player)
    await db.commit()

    # Test with limit
    response = client.get("/search?q=Test&limit=3")
    assert response.status_code == 200
    results = response.json()
    assert len(results["players"]) == 3

    # Test with skip
    response = client.get("/search?q=Test&skip=2&limit=2")
    assert response.status_code == 200
    results = response.json()
    assert len(results["players"]) == 2
    assert results["players"][0]["full_name"] == "Test Player 2"


@pytest.mark.asyncio
async def test_case_insensitive_search(client: TestClient, db):
    """Test case-insensitive search"""
    player = Player(player_id=1, full_name="LeBron James", is_active=True)
    db.add(player)
    await db.commit()

    queries = ["lebron", "LEBRON", "LeBron", "lEbRoN"]
    for query in queries:
        response = client.get(f"/search?q={query}")
        assert response.status_code == 200
        results = response.json()
        assert len(results["players"]) == 1
        assert results["players"][0]["full_name"] == "LeBron James"
