from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import DataUpdateStatus


def test_get_status_new(client: TestClient):
    """Test getting status when no status exists"""
    response = client.get("/status")
    assert response.status_code == 200
    status = response.json()
    assert status["is_updating"] is False
    assert status["current_phase"] is None
    assert not status["teams_updated"]
    assert not status["players_updated"]
    assert not status["games_updated"]


async def test_get_status_existing(client: TestClient, db: AsyncSession):
    """Test getting status when status exists"""
    # Get existing status row
    status = (await db.execute(select(DataUpdateStatus).filter_by(id=1))).scalar_one()

    # Update its fields
    status.is_updating = False
    status.current_phase = None
    status.last_successful_update = datetime.now(timezone.utc)
    status.next_scheduled_update = datetime.now(timezone.utc) + timedelta(hours=6)
    status.teams_updated = True
    status.players_updated = True
    status.games_updated = True

    await db.commit()

    response = client.get("/status")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["is_updating"] is False
    assert status_data["teams_updated"] is True
    assert status_data["players_updated"] is True
    assert status_data["games_updated"] is True


def test_trigger_update(client: TestClient):
    """Test triggering a full data update"""
    response = client.post("/update", json={"update_types": None})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["types"] == "all"


def test_trigger_games_update(client: TestClient):
    """Test triggering a games-only update"""
    response = client.post("/update/games")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "started" in data["message"].lower()


def test_reset_update_status(client: TestClient):
    """Test resetting a stuck update status"""
    response = client.post("/reset-update-status")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "reset" in data["message"].lower()


async def test_prevent_concurrent_updates(client: TestClient, db: AsyncSession):
    """Test that concurrent updates are prevented"""
    # Set status to updating
    status = (await db.execute(select(DataUpdateStatus).filter_by(id=1))).scalar_one()
    status.is_updating = True
    status.current_phase = "teams"
    status.last_successful_update = datetime.now(timezone.utc)
    status.next_scheduled_update = datetime.now(timezone.utc) + timedelta(hours=6)
    await db.commit()

    # Try to trigger another update
    response = client.post("/update", json={"update_types": None})
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "in progress" in data["detail"].lower()
