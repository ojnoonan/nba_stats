from fastapi.testclient import TestClient
import pytest
from datetime import datetime

def test_get_teams(client, test_team):
    """Test getting all teams"""
    response = client.get("/teams")
    assert response.status_code == 200
    teams = response.json()
    assert len(teams) == 1
    assert teams[0]["team_id"] == test_team.team_id
    assert teams[0]["name"] == test_team.name
    assert teams[0]["abbreviation"] == test_team.abbreviation

def test_get_team(client, test_team):
    """Test getting a specific team"""
    response = client.get(f"/teams/{test_team.team_id}")
    assert response.status_code == 200
    team = response.json()
    assert team["team_id"] == test_team.team_id
    assert team["name"] == test_team.name
    assert team["abbreviation"] == test_team.abbreviation
    assert team["conference"] == test_team.conference
    assert team["division"] == test_team.division
    assert team["wins"] == test_team.wins
    assert team["losses"] == test_team.losses

def test_get_nonexistent_team(client):
    """Test getting a team that doesn't exist"""
    response = client.get("/teams/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Team not found"

def test_update_team(client, test_team):
    """Test triggering a team update"""
    response = client.post(f"/teams/{test_team.team_id}/update")
    assert response.status_code == 200
    assert response.json()["message"] == f"Update initiated for team {test_team.team_id}"

def test_update_nonexistent_team(client):
    """Test triggering an update for a nonexistent team"""
    response = client.post("/teams/999/update")
    assert response.status_code == 404
    assert response.json()["detail"] == "Team not found"