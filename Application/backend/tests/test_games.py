import pytest
from fastapi.testclient import TestClient


def test_get_games(client, test_game):
    """Test getting all games"""
    response = client.get("/games")
    assert response.status_code == 200
    games = response.json()
    assert len(games) == 1
    assert games[0]["game_id"] == test_game.game_id
    assert games[0]["home_team_id"] == test_game.home_team_id
    assert games[0]["away_team_id"] == test_game.away_team_id


def test_get_games_by_team(client, test_game, test_team):
    """Test getting games filtered by team"""
    response = client.get(f"/games?team_id={test_team.team_id}")
    assert response.status_code == 200
    games = response.json()
    assert len(games) == 1
    assert games[0]["game_id"] == test_game.game_id
    assert games[0]["home_team_id"] == test_team.team_id


def test_get_games_by_status(client, test_game):
    """Test getting games filtered by status"""
    response = client.get("/games?status=Completed")
    assert response.status_code == 200
    games = response.json()
    assert len(games) == 1
    assert games[0]["game_id"] == test_game.game_id
    assert games[0]["status"] == "Completed"


def test_get_games_by_player(client, test_game, test_player, test_player_stats):
    """Test getting games filtered by player"""
    response = client.get(f"/games?player_id={test_player.player_id}")
    assert response.status_code == 200
    games = response.json()
    assert len(games) == 1
    assert games[0]["game_id"] == test_game.game_id


def test_get_game(client, test_game):
    """Test getting a specific game"""
    response = client.get(f"/games/{test_game.game_id}")
    assert response.status_code == 200
    game = response.json()
    assert game["game_id"] == test_game.game_id
    assert game["home_team_id"] == test_game.home_team_id
    assert game["away_team_id"] == test_game.away_team_id
    assert game["home_score"] == test_game.home_score
    assert game["away_score"] == test_game.away_score
    assert game["status"] == test_game.status


def test_get_nonexistent_game(client):
    """Test getting a game that doesn't exist"""
    response = client.get("/games/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Game not found"


def test_get_game_stats(client, test_game, test_player_stats):
    """Test getting game statistics"""
    response = client.get(f"/games/{test_game.game_id}/stats")
    assert response.status_code == 200
    stats = response.json()
    assert len(stats) == 1
    assert stats[0]["game_id"] == test_game.game_id
    assert stats[0]["points"] == test_player_stats.points
    assert stats[0]["rebounds"] == test_player_stats.rebounds
    assert stats[0]["assists"] == test_player_stats.assists
    assert stats[0]["minutes"] == test_player_stats.minutes


def test_get_game_stats_nonexistent_game(client):
    """Test getting statistics for a nonexistent game"""
    response = client.get("/games/999/stats")
    assert response.status_code == 404
    assert response.json()["detail"] == "Game not found"
