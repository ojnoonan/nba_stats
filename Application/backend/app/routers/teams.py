import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db, get_session_factory
from app.models.models import DataUpdateStatus, Game, Player
from app.models.models import Team as TeamModel
from app.services.nba_data_service import NBADataService
from app.utils.query_utils import apply_filters, paginate_query
from app.utils.response_utils import (
    calculate_team_stats,
    format_game_response,
    format_player_response,
    format_team_response,
)
from app.utils.router_utils import RouterUtils
from app.utils.status_utils import get_or_create_status

router = APIRouter(prefix="/teams", tags=["teams"])

logger = logging.getLogger(__name__)


@router.get("")
async def get_teams(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000),
    conference: Optional[str] = Query(default=None, pattern="^(East|West)$"),
    db: AsyncSession = Depends(get_db),
):
    """Get all teams with optional pagination and filtering"""
    try:
        # Build the query
        stmt = select(TeamModel)

        # Apply filters
        filters = {}
        if conference:
            filters["conference"] = conference

        stmt = apply_filters(stmt, TeamModel, filters)

        # Apply pagination
        stmt = paginate_query(stmt, skip, limit)

        # Execute query
        result = await db.execute(stmt)
        teams = result.scalars().all()

        # Format team responses using utility function
        formatted_teams = [format_team_response(team) for team in teams]
        return formatted_teams
    except Exception as e:
        logger.error(f"Error fetching teams: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{team_id}")
async def get_team(team_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific team by ID"""
    team = await RouterUtils.get_entity_or_404(db, TeamModel, team_id, "team_id")
    return format_team_response(team)


@router.post("/{team_id}/update")
async def update_team(
    team_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    """Trigger an update for a specific team's data"""
    try:
        # First check if the team exists
        team = await RouterUtils.get_entity_or_404(db, TeamModel, team_id, "team_id")

        # Check there's no in-progress update
        await RouterUtils.check_update_status(db)

        # Initialize nested and flat status for 'players'
        from app.utils.status_utils import (  # noqa
            get_or_create_status,
            initialize_status,
        )

        await initialize_status("players", db)
        # Add a detail message
        status = await get_or_create_status(db)
        status.current_detail = f"Updating team: {team.name}"
        await db.commit()

        # Define the team update task
        async def update_team_task(session: AsyncSession, team_id: int) -> None:
            try:
                service = NBADataService(session)
                await service.update_team_players(team_id)
                # Status is already handled by the service via finalize_component
            except Exception as e:
                # Log the error - status is already handled by the service via handle_component_error
                logger.error(f"Error in team update task for team {team_id}: {str(e)}")
                raise

        # Start the background task
        background_tasks.add_task(
            RouterUtils.create_async_session_task, update_team_task, team_id
        )

        return {"message": f"Team {team_id} update initiated"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{team_id}/update/games")
async def update_team_games(
    team_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    """Trigger an update for a specific team's game data"""
    try:
        # Check if team exists
        team = await RouterUtils.get_entity_or_404(db, TeamModel, team_id, "team_id")

        # Set update status
        status = await get_or_create_status(db)
        status.is_updating = True
        status.current_phase = "games"
        status.current_detail = f"Updating games for team {team.name}"
        await db.commit()

        # Define the team games update task
        async def update_team_games_task(session: AsyncSession, team_id: int) -> None:
            try:
                service = NBADataService(session)
                await service.update_team_games(team_id)

                # Update status after completion
                session_factory = get_session_factory()
                async with session_factory() as status_session:
                    status = await get_or_create_status(status_session)
                    status.is_updating = False
                    status.current_phase = None
                    status.last_successful_update = datetime.now(timezone.utc)
                    status.next_scheduled_update = datetime.now(
                        timezone.utc
                    ) + timedelta(hours=6)
                    status.current_detail = "Team games update completed"

                    # Update games completion status
                    status.games_updated = True
                    status.games_percent_complete = 100

                    if (
                        isinstance(status.components, dict)
                        and "games" in status.components
                    ):
                        status.components["games"].update(
                            {
                                "updated": True,
                                "percent_complete": 100,
                                "last_update": datetime.now(timezone.utc).isoformat(),
                            }
                        )

                    await status_session.commit()
            except Exception as e:
                # Update error status
                session_factory = get_session_factory()
                async with session_factory() as error_session:
                    status = await get_or_create_status(error_session)
                    status.is_updating = False
                    status.current_phase = None
                    status.last_error = str(e)
                    status.last_error_time = datetime.now(timezone.utc)

                    if (
                        isinstance(status.components, dict)
                        and "games" in status.components
                    ):
                        status.components["games"]["last_error"] = str(e)

                    await error_session.commit()
                raise

        # Start the background task
        background_tasks.add_task(
            RouterUtils.create_async_session_task, update_team_games_task, team_id
        )

        return {"message": f"Team {team_id} games update initiated"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating team {team_id} games: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{team_id}/roster")
async def get_team_roster(
    team_id: int,
    active_only: bool = True,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get a team's roster of players"""
    return await _get_team_players(team_id, active_only, skip, limit, db)


@router.get("/{team_id}/players")
async def get_team_players(
    team_id: int,
    active_only: bool = True,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get a team's players (alias for roster)"""
    return await _get_team_players(team_id, active_only, skip, limit, db)


async def _get_team_players(
    team_id: int, active_only: bool, skip: int, limit: int, db: AsyncSession
):
    """Internal function to get team players"""
    try:
        # First check if the team exists
        team = await RouterUtils.get_entity_or_404(db, TeamModel, team_id, "team_id")

        # Check if roster data is loaded
        if not team.roster_loaded:
            logger.warning(f"Roster for team {team_id} is not loaded yet")
            return []

        # Get players for the team
        player_stmt = select(Player).filter(Player.current_team_id == team_id)

        # Filter by active status if requested
        filters = {"current_team_id": team_id}
        if active_only:
            filters["is_active"] = True

        player_stmt = apply_filters(player_stmt, Player, filters)
        player_stmt = paginate_query(player_stmt, skip, limit)

        player_result = await db.execute(player_stmt)
        players = player_result.scalars().all()

        # Format player responses using utility function
        formatted_players = [format_player_response(player) for player in players]
        return formatted_players
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error fetching roster for team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{team_id}/stats")
async def get_team_stats(team_id: int, db: AsyncSession = Depends(get_db)):
    """Get statistics for a specific team"""
    try:
        # Get team or raise 404
        team = await RouterUtils.get_entity_or_404(db, TeamModel, team_id, "team_id")

        # Calculate and return stats using the utility function
        return calculate_team_stats(team)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stats for team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def load_team_for_game(db: AsyncSession, team_id: int):
    """Helper function to load team data for a game"""
    try:
        return await RouterUtils.get_entity_or_404(db, TeamModel, team_id, "team_id")
    except HTTPException:
        # We don't want to fail the entire request if one team can't be loaded
        logger.warning(f"Team {team_id} not found when loading for game")
        return None


@router.get("/{team_id}/schedule")
async def get_team_schedule(
    team_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get a team's game schedule"""
    try:
        # Get team or raise 404
        team = await RouterUtils.get_entity_or_404(db, TeamModel, team_id, "team_id")

        # Check if game data is loaded
        if not team.games_loaded:
            logger.warning(f"Games for team {team_id} are not loaded yet")
            return []

        # Get games for the team
        game_stmt = (
            select(Game)
            .filter(or_(Game.home_team_id == team_id, Game.away_team_id == team_id))
            .order_by(Game.game_date_utc)
        )

        # Apply pagination
        game_stmt = paginate_query(game_stmt, skip, limit)

        game_result = await db.execute(game_stmt)
        games = game_result.scalars().all()

        # Format games with related team data
        game_list = []
        for game in games:
            try:
                # Load related team data explicitly
                setattr(
                    game, "home_team", await load_team_for_game(db, game.home_team_id)
                )
                setattr(
                    game, "away_team", await load_team_for_game(db, game.away_team_id)
                )

                # Format the game using the utility function
                game_data = format_game_response(game)
                game_list.append(game_data)
            except Exception as e:
                logger.warning(f"Error formatting game {game.game_id}: {str(e)}")
                # Fallback to basic formatting if there's an issue
                game_data = format_game_response(game, include_teams=False)
                game_list.append(game_data)

        return game_list
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching schedule for team {team_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
