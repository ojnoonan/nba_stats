from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
import logging
from typing import Optional

from app.models.models import Team, Player, PlayerGameStats, Game
from app.database.database import get_db

router = APIRouter(
    prefix="/search",
    tags=["search"]
)

logger = logging.getLogger(__name__)

@router.get("")
async def search(
    term: str = Query(..., min_length=2),
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Search for teams and players matching the query term, optionally filtered by season"""
    try:
        # Get all teams that match the search term
        teams = db.query(Team).filter(
            or_(
                Team.name.ilike(f"%{term}%"),
                Team.abbreviation.ilike(f"%{term}%")
            )
        ).all()

        # Get all players that match the search term
        player_query = db.query(Player).filter(
            or_(
                Player.full_name.ilike(f"%{term}%"),
                Player.first_name.ilike(f"%{term}%"),
                Player.last_name.ilike(f"%{term}%")
            )
        )
        
        # If season is specified, filter players who played in that season
        if season:
            # Get player IDs who have game stats in the specified season
            player_ids_in_season = db.query(PlayerGameStats.player_id).join(
                Game, PlayerGameStats.game_id == Game.game_id
            ).filter(Game.season_year == season).distinct()
            
            player_query = player_query.filter(Player.player_id.in_(player_ids_in_season))
        
        players = player_query.all()

        # Group players by team
        results = []
        team_dict = {}

        # First add teams with direct matches
        for team in teams:
            team_dict[team.team_id] = {
                "team": {
                    "team_id": team.team_id,
                    "name": team.name,
                    "logo_url": team.logo_url
                },
                "players": []
            }
            results.append(team_dict[team.team_id])

        # Then add players under their teams
        for player in players:
            # If player's team wasn't a direct match, add it
            if player.current_team_id not in team_dict:
                team = db.query(Team).filter(Team.team_id == player.current_team_id).first()
                if team:
                    team_dict[team.team_id] = {
                        "team": {
                            "team_id": team.team_id,
                            "name": team.name,
                            "logo_url": team.logo_url
                        },
                        "players": []
                    }
                    results.append(team_dict[team.team_id])
            
            # Add player to their team's group
            if player.current_team_id in team_dict:
                team_dict[player.current_team_id]["players"].append({
                    "player_id": player.player_id,
                    "full_name": player.full_name,
                    "is_traded_flag": player.traded_date is not None
                })

        return results

    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))