"""
Tests for utility functions.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Player, Team
from app.utils.query_utils import apply_date_filter, apply_filters, paginate_query
from app.utils.router_utils import RouterUtils

pytestmark = pytest.mark.asyncio


async def test_get_entity_or_404_success(db: AsyncSession, test_team):
    """Test getting an entity successfully using RouterUtils"""
    entity = await RouterUtils.get_entity_or_404(db, Team, test_team.team_id, "team_id")
    assert entity.team_id == test_team.team_id
    assert entity.name == test_team.name


async def test_get_entity_or_404_not_found(db: AsyncSession):
    """Test 404 error when entity doesn't exist"""
    with pytest.raises(HTTPException) as excinfo:
        await RouterUtils.get_entity_or_404(db, Team, 999, "team_id")
    assert excinfo.value.status_code == 404
    assert "Team not found" in str(excinfo.value.detail)


async def test_check_update_status(db: AsyncSession):
    """Test checking update status"""
    status = await RouterUtils.check_update_status(db)
    # Should not raise an exception if status.is_updating is False
    assert status is not None
    assert hasattr(status, "is_updating")


async def test_paginate_query(db: AsyncSession, test_team, test_player):
    """Test applying pagination to a query"""
    # Create 5 more test players
    for i in range(5):
        player = Player(
            player_id=i + 10,
            full_name=f"Test Player {i}",
            current_team_id=test_team.team_id,
            is_active=True,
        )
        db.add(player)
    await db.commit()

    # Query with pagination
    stmt = paginate_query(
        select(Player).filter(Player.current_team_id == test_team.team_id),
        skip=1,
        limit=2,
    )
    result = await db.execute(stmt)
    players = result.scalars().all()

    # Should return exactly 2 players (limit=2)
    assert len(players) == 2


async def test_apply_filters(db: AsyncSession, test_team, test_player):
    """Test applying filters to a query"""
    # Create a second player with different attributes
    player2 = Player(
        player_id=200,
        full_name="Inactive Player",
        current_team_id=test_team.team_id,
        is_active=False,
    )
    db.add(player2)
    await db.commit()

    # Apply filters
    filters = {"is_active": True}
    stmt = apply_filters(
        select(Player).filter(Player.current_team_id == test_team.team_id),
        Player,
        filters,
    )
    result = await db.execute(stmt)
    players = result.scalars().all()

    # Should only return active players
    assert all(p.is_active for p in players)
    assert len(players) == 1


async def test_apply_date_filter(db: AsyncSession, test_game):
    """Test applying date filters to a query"""
    # Get the date string for the test game
    date_str = test_game.game_date_utc.strftime("%Y-%m-%d")

    # Apply date filter
    stmt, success = apply_date_filter(
        select(type(test_game)), type(test_game), "game_date_utc", date_str
    )

    # Filter should be applied successfully
    assert success is True

    # Execute query
    result = await db.execute(stmt)
    games = result.scalars().all()

    # Should find the test game
    assert len(games) == 1
    assert games[0].game_id == test_game.game_id
