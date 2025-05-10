from fastapi.testclient import TestClient
import pytest

def test_get_players(client, test_player):
    """Test getting all players"""
    response = client.get("/players")
    assert response.status_code == 200
    players = response.json()
    assert len(players) == 1
    assert players[0]["player_id"] == test_player.player_id
    assert players[0]["full_name"] == test_player.full_name
    assert players[0]["current_team_id"] == test_player.current_team_id

def test_get_players_by_team(client, test_player, test_team):
    """Test getting players filtered by team"""
    response = client.get(f"/players?team_id={test_team.team_id}")
    assert response.status_code == 200
    players = response.json()
    assert len(players) == 1
    assert players[0]["player_id"] == test_player.player_id
    assert players[0]["current_team_id"] == test_team.team_id

def test_get_player(client, test_player):
    """Test getting a specific player"""
    response = client.get(f"/players/{test_player.player_id}")
    assert response.status_code == 200
    player = response.json()
    assert player["player_id"] == test_player.player_id
    assert player["full_name"] == test_player.full_name
    assert player["first_name"] == test_player.first_name
    assert player["last_name"] == test_player.last_name
    assert player["position"] == test_player.position
    assert player["jersey_number"] == test_player.jersey_number

def test_get_nonexistent_player(client):
    """Test getting a player that doesn't exist"""
    response = client.get("/players/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Player not found"

def test_get_player_stats(client, test_player, test_player_stats):
    """Test getting player statistics"""
    response = client.get(f"/players/{test_player.player_id}/stats")
    assert response.status_code == 200
    stats = response.json()
    assert len(stats) == 1
    assert stats[0]["points"] == test_player_stats.points
    assert stats[0]["rebounds"] == test_player_stats.rebounds
    assert stats[0]["assists"] == test_player_stats.assists

def test_get_player_last_n_games(client, test_player, test_player_stats):
    """Test getting player's last N games statistics"""
    response = client.get(f"/players/{test_player.player_id}/last_x_games?count=5")
    assert response.status_code == 200
    stats = response.json()
    assert stats["games_analyzed"] == 1
    assert stats["stats"]["avg_points"] == test_player_stats.points
    assert stats["stats"]["avg_rebounds"] == test_player_stats.rebounds
    assert stats["stats"]["avg_assists"] == test_player_stats.assists

def test_get_player_high_low_games(client, test_player, test_player_stats):
    """Test getting player's highest and lowest scoring games"""
    response = client.get(f"/players/{test_player.player_id}/high_low_games")
    assert response.status_code == 200
    games = response.json()
    assert len(games["top_5"]) == 1
    assert games["top_5"][0]["points"] == test_player_stats.points
    assert len(games["bottom_5"]) == 1
    assert games["bottom_5"][0]["points"] == test_player_stats.points