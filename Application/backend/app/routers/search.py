from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
import logging
from typing import Optional

from app.models.models import Team, Player, PlayerGameStats, Game
from app.database.database import get_db
from app.schemas.validation import SearchQuerySchema, SeasonSchema, sanitize_string
from app.core.exceptions import ErrorHandler, ValidationException

router = APIRouter(
    prefix="/search",
    tags=["search"]
)

logger = logging.getLogger(__name__)

@router.get("")
async def search(
    term: str = Query(..., min_length=2, max_length=100, description="Search term"),
    season: Optional[str] = Query(None, pattern=r'^\d{4}-\d{2}$', description="Season in YYYY-YY format"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """Search for teams and players matching the query term, optionally filtered by season"""
    try:
        # Sanitize and validate search term
        term = sanitize_string(term)
        if len(term.strip()) < 2:
            raise ValidationException("Search term must be at least 2 characters after sanitization")
        
        # Validate season if provided
        if season:
            season = sanitize_string(season)
            import re
            if not re.match(r'^\d{4}-\d{2}$', season):
                raise ValidationException("Season must be in YYYY-YY format")
        
        # Limit term length to prevent performance issues
        if len(term) > 100:
            term = term[:100]
            logger.warning(f"Search term truncated to 100 characters")
        
        # Escape SQL wildcards in user input to prevent SQL injection
        escaped_term = term.replace('%', '\\%').replace('_', '\\_')
        search_pattern = f"%{escaped_term}%"
        
        # Get all teams that match the search term
        teams_query = db.query(Team).filter(
            or_(
                Team.name.ilike(search_pattern),
                Team.abbreviation.ilike(search_pattern)
            )
        ).limit(limit // 2)  # Reserve half the results for teams
        
        teams = teams_query.all()

        # Get all players that match the search term
        players_query = db.query(Player).filter(
            or_(
                Player.full_name.ilike(search_pattern),
                Player.first_name.ilike(search_pattern),
                Player.last_name.ilike(search_pattern)
            )
        )
        
        # If season is specified, filter players who played in that season
        if season:
            # Get player IDs who have game stats in the specified season
            player_ids_in_season = db.query(PlayerGameStats.player_id).join(
                Game, PlayerGameStats.game_id == Game.game_id
            ).filter(Game.season_year == season).distinct()
            
            players_query = players_query.filter(Player.player_id.in_(player_ids_in_season))
        
        # Limit players to remaining slots
        remaining_limit = limit - len(teams)
        players = players_query.limit(remaining_limit).all()
        
        return {
            "query": term,
            "season": season,
            "results": {
                "teams": teams,
                "players": players
            },
            "total": len(teams) + len(players)
        }
        
    except Exception as e:
        raise ErrorHandler.handle_error(e, f"search with term '{term}'")