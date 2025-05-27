from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient


def test_search_team(client, test_team):
    """Test searching for a team"""
    response = client.get("/search?q=Test")
    assert response.status_code == 200
    results = response.json()
    assert len(results["teams"]) == 1
    assert results["teams"][0]["team_id"] == test_team.team_id
    assert results["teams"][0]["name"] == test_team.name


def test_search_player(client, test_player, test_team):
    """Test searching for a player"""
    response = client.get("/search?q=Test")
    assert response.status_code == 200
    results = response.json()
    assert len(results["players"]) == 1
    assert results["players"][0]["player_id"] == test_player.player_id
    assert results["players"][0]["full_name"] == test_player.full_name


def test_search_with_short_term(client):
    """Test searching with a term that's too short"""
    response = client.get("/search?q=a")
    assert response.status_code == 400
    error = response.json()
    assert "minimum length" in error["detail"]


def test_search_no_results(client, test_team, test_player):
    """Test searching with a term that matches nothing"""
    response = client.get("/search?q=xyz")
    assert response.status_code == 200
    results = response.json()
    assert len(results["teams"]) == 0
    assert len(results["players"]) == 0


def test_search_partial_match(client, test_team):
    """Test searching with a partial match"""
    response = client.get("/search?q=Te")
    assert response.status_code == 200
    results = response.json()
    assert len(results["teams"]) == 1
    assert results["teams"][0]["team_id"] == test_team.team_id


def test_search_case_insensitive(client, test_team, test_player):
    """Test that search is case insensitive"""
    response = client.get("/search?q=test")
    assert response.status_code == 200
    results = response.json()
    assert len(results["teams"]) == 1
    assert results["teams"][0]["team_id"] == test_team.team_id
    assert len(results["players"]) == 1
    assert results["players"][0]["player_id"] == test_player.player_id


@pytest.mark.asyncio
async def test_search_traded_player(client, test_player, test_team, db):
    """Test searching for a traded player"""
    # Update player to be traded
    test_player.traded_date = datetime(2025, 5, 9, tzinfo=timezone.utc)
    await db.commit()

    response = client.get("/search?q=Test")
    assert response.status_code == 200
    results = response.json()
    assert len(results["players"]) == 1
    assert results["players"][0]["is_traded_flag"] is True
