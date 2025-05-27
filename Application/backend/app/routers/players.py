import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.models.models import Game as GameModel
from app.models.models import Player as PlayerModel
from app.models.models import PlayerGameStats
from app.services.nba_data_service import NBADataService  # Import the service
from app.utils.query_utils import apply_filters, paginate_query
from app.utils.response_utils import (
    format_player_response,
    format_player_stats_response,
)
from app.utils.router_utils import RouterUtils

router = APIRouter(prefix="/players", tags=["players"])

# Get logger for this module
logger = logging.getLogger(__name__)


@router.get("")  # Changed from "/"
async def get_players(
    db: AsyncSession = Depends(get_db),
    team_id: Optional[int] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000),
):
    """Get all players, optionally filtered by team"""
    # Validate team_id if provided
    if team_id is not None and team_id < 0:
        raise HTTPException(
            status_code=422, detail="team_id must be a positive integer"
        )

    try:
        stmt = select(PlayerModel)

        # Apply filters if team_id is provided
        filters = {"current_team_id": team_id} if team_id is not None else {}
        stmt = apply_filters(stmt, PlayerModel, filters)

        # Apply pagination
        stmt = paginate_query(stmt, skip, limit)

        result = await db.execute(stmt)
        players = result.scalars().all()

        # Format response
        return [format_player_response(player) for player in players]
    except Exception as e:
        logger.error(f"Error fetching players: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active")
async def get_active_players(
    db: AsyncSession = Depends(get_db),
    team_id: Optional[int] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000),
):
    """Get active players, optionally filtered by team"""
    try:
        stmt = select(PlayerModel).filter(PlayerModel.is_active == True)

        # Apply filters if team_id is provided
        filters = {"current_team_id": team_id} if team_id is not None else {}
        stmt = apply_filters(stmt, PlayerModel, filters)

        # Apply pagination
        stmt = paginate_query(stmt, skip, limit)

        result = await db.execute(stmt)
        players = result.scalars().all()

        # Format response
        return [format_player_response(player) for player in players]
    except Exception as e:
        logger.error(f"Error fetching active players: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{player_id}")
async def get_player(player_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific player by ID"""
    try:
        # Use RouterUtils to get player or raise 404
        player = await RouterUtils.get_entity_or_404(
            db, PlayerModel, player_id, "player_id"
        )

        # Format and return response
        return format_player_response(player, include_team=True)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching player {player_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{player_id}/stats")
async def get_player_stats(
    player_id: int,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=10, le=100),
    skip: int = Query(default=0, ge=0),
):
    """Get game statistics for a specific player"""
    try:
        # Check if player exists using RouterUtils
        await RouterUtils.get_entity_or_404(db, PlayerModel, player_id, "player_id")

        # Get player's game stats
        stmt = (
            select(PlayerGameStats)
            .join(GameModel)
            .filter(PlayerGameStats.player_id == player_id)
            .order_by(desc(GameModel.game_date_utc))
        )

        # Apply pagination
        stmt = paginate_query(stmt, skip, limit)

        result = await db.execute(stmt)
        stats = result.scalars().all()

        # Format the response
        return [format_player_stats_response(stat) for stat in stats]
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching stats for player {player_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{player_id}/last_x_games")
async def get_player_last_x_games(
    player_id: int,
    count: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated stats for player's last N games"""
    try:
        # First verify player exists using RouterUtils
        await RouterUtils.get_entity_or_404(db, PlayerModel, player_id, "player_id")

        # Get the last N games' stats
        result = await db.execute(
            select(PlayerGameStats)
            .join(GameModel, PlayerGameStats.game_id == GameModel.game_id)
            .filter(PlayerGameStats.player_id == player_id)
            .order_by(GameModel.game_date_utc.desc())
            .limit(count)
        )
        recent_stats = result.scalars().all()

        if not recent_stats:
            return {
                "games_analyzed": 0,
                "stats": {"avg_points": 0, "avg_rebounds": 0, "avg_assists": 0},
            }

        # Calculate averages
        avg_stats = {
            "avg_points": sum(stat.points or 0 for stat in recent_stats)
            / len(recent_stats),
            "avg_rebounds": sum(stat.rebounds or 0 for stat in recent_stats)
            / len(recent_stats),
            "avg_assists": sum(stat.assists or 0 for stat in recent_stats)
            / len(recent_stats),
        }

        return {"games_analyzed": len(recent_stats), "stats": avg_stats}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(
            f"Error getting last {count} games for player {player_id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{player_id}/high_low_games")
async def get_player_high_low_games(
    player_id: int,
    count: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Get player's highest and lowest scoring games"""
    try:
        # First verify player exists using RouterUtils
        await RouterUtils.get_entity_or_404(db, PlayerModel, player_id, "player_id")

        # Async path - Get highest scoring games
        result = await db.execute(
            select(PlayerGameStats, GameModel)
            .join(GameModel, PlayerGameStats.game_id == GameModel.game_id)
            .filter(PlayerGameStats.player_id == player_id)
            .order_by(desc(PlayerGameStats.points))
            .limit(count)
        )
        high_games = result.all()

        # Get lowest scoring games
        result = await db.execute(
            select(PlayerGameStats, GameModel)
            .join(GameModel, PlayerGameStats.game_id == GameModel.game_id)
            .filter(PlayerGameStats.player_id == player_id)
            .order_by(PlayerGameStats.points)
            .limit(count)
        )
        low_games = result.all()

        # Format the results
        high_games_list = [
            {
                "game_id": stat.game_id,
                "date_utc": game.game_date_utc,
                "points": stat.points,
            }
            for stat, game in high_games
        ]

        low_games_list = [
            {
                "game_id": stat.game_id,
                "date_utc": game.game_date_utc,
                "points": stat.points,
            }
            for stat, game in low_games
        ]

        return {"top_5": high_games_list, "bottom_5": low_games_list}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting high/low games for player {player_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{player_id}/update")
async def update_player(
    player_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger an update for a specific player's data"""
    try:
        # First check if the player exists
        player = await RouterUtils.get_entity_or_404(
            db, PlayerModel, player_id, "player_id"
        )

        # Then check if an update is already in progress
        await RouterUtils.check_update_status(db)

        # Define the player update task
        async def update_player_task(session: AsyncSession, player_id: int) -> None:
            service = NBADataService(session)
            # Get the player's team_id to update team players
            result = await session.execute(
                select(PlayerModel.current_team_id).filter(
                    PlayerModel.player_id == player_id
                )
            )
            team_id = result.scalar_one_or_none()
            if team_id:
                await service.update_team_players(team_id)

        # Start the background task
        background_tasks.add_task(
            RouterUtils.create_async_session_task, update_player_task, player_id
        )

        return {"message": f"Player {player_id} update initiated"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating player {player_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
