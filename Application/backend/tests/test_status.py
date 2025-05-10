from fastapi.testclient import TestClient
import pytest
from datetime import datetime, timedelta

def test_get_status_new(client):
    """Test getting status when no status exists"""
    response = client.get("/status")
    assert response.status_code == 200
    status = response.json()
    assert status["is_updating"] is True
    assert status["current_phase"] == "initializing"
    assert status["last_update"] is not None
    assert status["next_update"] is not None

def test_get_status_existing(client, db):
    """Test getting status when status exists"""
    from app.models.models import DataUpdateStatus
    
    status = DataUpdateStatus(
        is_updating=False,
        current_phase=None,
        last_successful_update=datetime.utcnow(),
        next_scheduled_update=datetime.utcnow() + timedelta(hours=6),
        teams_updated=True,
        players_updated=True,
        games_updated=True
    )
    db.add(status)
    db.commit()

    response = client.get("/status")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["is_updating"] is False
    assert status_data["current_phase"] is None
    assert status_data["teams_updated"] is True
    assert status_data["players_updated"] is True
    assert status_data["games_updated"] is True

def test_trigger_update(client):
    """Test triggering a full data update"""
    response = client.post("/update")
    assert response.status_code == 200
    assert response.json()["message"] == "Update initiated"

def test_trigger_games_update(client):
    """Test triggering a games-only update"""
    response = client.post("/update/games")
    assert response.status_code == 200
    assert response.json()["message"] == "Games update initiated"

def test_reset_update_status(client):
    """Test resetting a stuck update status"""
    response = client.post("/reset-update-status")
    assert response.status_code == 200
    assert response.json()["message"] == "Update status reset successfully"

def test_prevent_concurrent_updates(client, db):
    """Test that concurrent updates are prevented"""
    from app.models.models import DataUpdateStatus
    
    # Set status to updating
    status = DataUpdateStatus(
        is_updating=True,
        current_phase="teams",
        last_successful_update=datetime.utcnow(),
        next_scheduled_update=datetime.utcnow() + timedelta(hours=6)
    )
    db.add(status)
    db.commit()

    # Try to trigger another update
    response = client.post("/update")
    assert response.status_code == 400
    assert response.json()["detail"] == "Update already in progress"

    # Same for games update
    response = client.post("/update/games")
    assert response.status_code == 400
    assert response.json()["detail"] == "Update already in progress"