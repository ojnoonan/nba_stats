from fastapi.testclient import TestClient
import pytest

def test_search_team(client, test_team):
    """Test searching for a team"""
    response = client.get("/search?term=Test")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["team"]["team_id"] == test_team.team_id
    assert results[0]["team"]["name"] == test_team.name
    assert len(results[0]["players"]) == 0

def test_search_player(client, test_player, test_team):
    """Test searching for a player"""
    response = client.get("/search?term=Test")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["team"]["team_id"] == test_team.team_id
    assert len(results[0]["players"]) == 1
    assert results[0]["players"][0]["player_id"] == test_player.player_id
    assert results[0]["players"][0]["full_name"] == test_player.full_name

def test_search_with_short_term(client):
    """Test searching with a term that's too short"""
    response = client.get("/search?term=a")
    assert response.status_code == 422
    error = response.json()
    assert "min_length" in str(error["detail"])

def test_search_no_results(client, test_team, test_player):
    """Test searching with a term that matches nothing"""
    response = client.get("/search?term=xyz")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 0

def test_search_partial_match(client, test_team):
    """Test searching with a partial match"""
    response = client.get("/search?term=Te")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["team"]["team_id"] == test_team.team_id

def test_search_case_insensitive(client, test_team, test_player):
    """Test that search is case insensitive"""
    response = client.get("/search?term=test")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["team"]["team_id"] == test_team.team_id
    assert len(results[0]["players"]) == 1
    assert results[0]["players"][0]["player_id"] == test_player.player_id

def test_search_traded_player(client, test_player, test_team, db):
    """Test searching for a traded player"""
    # Update player to be traded
    test_player.traded_date = "2025-05-09T00:00:00"
    db.commit()

    response = client.get("/search?term=Test")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["players"][0]["is_traded_flag"] is True