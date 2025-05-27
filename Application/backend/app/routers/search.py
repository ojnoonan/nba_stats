import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.models.models import Player, Team
from app.utils.query_utils import paginate_query
from app.utils.response_utils import format_player_response, format_team_response
from app.utils.router_utils import RouterUtils

router = APIRouter(prefix="/search", tags=["search"])

logger = logging.getLogger(__name__)


@router.get("")
async def search(
    q: str = Query(...),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, le=100),
    include_inactive: bool = Query(default=False),
):
    """Search for teams or players by name"""

    if not q or q.strip() == "":
        raise HTTPException(status_code=422, detail="Search query cannot be empty")

    if len(q) < 2:
        raise HTTPException(
            status_code=422,
            detail="Search query must have a minimum length of 2 characters",
        )

    term = q
    try:
        # Search for teams
        team_stmt = select(Team).filter(
            or_(Team.name.ilike(f"%{term}%"), Team.abbreviation.ilike(f"%{term}%"))
        )
        # Apply pagination
        team_stmt = paginate_query(team_stmt, skip, limit)

        team_result = await db.execute(team_stmt)
        teams = team_result.scalars().all()

        # Search for players
        player_stmt = select(Player).filter(
            or_(
                Player.full_name.ilike(f"%{term}%"),
                Player.first_name.ilike(f"%{term}%"),
                Player.last_name.ilike(f"%{term}%"),
            )
        )

        # Filter for active players only if not including inactive
        if not include_inactive:
            player_stmt = player_stmt.filter(Player.is_active == True)

        # Apply pagination
        player_stmt = paginate_query(player_stmt, skip, limit)

        player_result = await db.execute(player_stmt)
        players = player_result.scalars().all()

        # Return a dictionary with separate lists for teams and players using format functions
        results = {
            "teams": [format_team_response(team) for team in teams],
            "players": [format_player_response(player) for player in players],
        }

        return results

    except Exception as e:
        logger.error(f"Error performing search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
