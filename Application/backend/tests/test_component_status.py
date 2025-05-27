import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import DataUpdateStatus


@pytest.mark.asyncio
async def test_initialize_status(client: TestClient, db: AsyncSession, test_team):
    """Test that the component status is correctly initialized"""
    # Get initial status
    stmt = select(DataUpdateStatus).filter_by(id=1)
    result = await db.execute(stmt)
    status = result.scalar_one_or_none()
    assert status, "Status object not found"

    # Initialize values
    status.is_updating = False
    status.players_updated = True
    status.players_percent_complete = 100
    status.components = {}
    await db.commit()

    # Trigger an update
    response = client.post("/teams/1/update")
    assert response.status_code == 200

    # Verify status was initialized properly
    stmt = select(DataUpdateStatus).filter_by(id=1)
    result = await db.execute(stmt)
    status = result.scalar_one_or_none()
    assert status is not None, "Status object not found after update"
    print(f"DEBUG: Test sees is_updating: {status.is_updating}")
    print(f"DEBUG: Test sees last_error: {status.last_error}")
    print(f"DEBUG: Test sees current_phase: {status.current_phase}")

    # The update might complete immediately if no players exist for the team
    # So we check for either the in-progress state OR the completed state
    assert isinstance(status.components, dict)
    assert "players" in status.components
    assert status.components["players"]["last_error"] is None

    if status.is_updating:
        # If still updating, verify initial state
        assert status.players_updated is False  # Should be reset
        assert status.players_percent_complete == 0  # Should be reset
        assert status.components["players"]["updated"] is False
        assert status.components["players"]["percent_complete"] == 0
    else:
        # If already completed, verify completion state
        assert status.players_updated is True  # Should be completed
        assert status.players_percent_complete == 100  # Should be completed
        assert status.components["players"]["updated"] is True
        assert status.components["players"]["percent_complete"] == 100


@pytest.mark.asyncio
async def test_update_progress(client: TestClient, db: AsyncSession, test_team):
    """Test that component progress is properly updated"""
    # Get initial status
    stmt = select(DataUpdateStatus).filter_by(id=1)
    result = await db.execute(stmt)
    status = result.scalar_one_or_none()
    assert status, "Status object not found"

    # Initialize values
    status.is_updating = False
    status.players_updated = True
    status.players_percent_complete = 100
    status.components = {"players": {"updated": True, "percent_complete": 100}}
    await db.commit()

    # Trigger an update
    response = client.post("/teams/1/update")
    assert response.status_code == 200

    # Wait for some progress updates
    await asyncio.sleep(1)  # Give time for update to start

    # Check status
    stmt = select(DataUpdateStatus).filter_by(id=1)
    result = await db.execute(stmt)
    status = result.scalar_one_or_none()
    assert status is not None, "Status object not found during update"
    assert status.players_percent_complete < 100  # Should show some progress
    assert (
        status.components["players"]["percent_complete"]
        == status.players_percent_complete
    )  # Should match
    assert status.components["players"]["updated"] is False  # Not finished yet


@pytest.mark.asyncio
async def test_finalize_status(client: TestClient, db: AsyncSession, test_team):
    """Test that the component status is correctly finalized"""
    # Get initial status
    stmt = select(DataUpdateStatus).filter_by(id=1)
    result = await db.execute(stmt)
    status = result.scalar_one_or_none()
    assert status, "Status object not found"

    # Initialize values
    status.is_updating = True
    status.current_phase = "players"  # Set current phase for single component test
    status.players_updated = False
    status.players_percent_complete = 50
    status.components = {"players": {"updated": False, "percent_complete": 50}}
    await db.commit()

    # Manually mark the update as complete
    from app.services.nba_data_service import NBADataService

    service = NBADataService(db)
    await service._finalize_component_update("players")

    # Verify status was finalized properly
    stmt = select(DataUpdateStatus).filter_by(id=1)
    result = await db.execute(stmt)
    status = result.scalar_one_or_none()
    assert status is not None, "Status object not found after finalization"
    assert status.is_updating is False
    assert status.players_updated is True
    assert status.players_percent_complete == 100
    assert status.components["players"]["updated"] is True
    assert status.components["players"]["percent_complete"] == 100
    assert status.components["players"]["last_error"] is None
    assert status.components["players"]["last_update"] is not None
