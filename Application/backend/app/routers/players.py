import logging
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional
from app.models.models import Player as PlayerModel, PlayerGameStats, Game as GameModel
from app.database.database import get_db
from app.schemas.validation import PlayerIdSchema, PlayerQuerySchema, PaginationSchema, validate_nba_player_id, validate_nba_team_id

router = APIRouter(
    prefix="/players",
    tags=["players"]
)

logger = logging.getLogger(__name__)

@router.get("")
async def get_players(
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    active_only: bool = Query(True, description="Only return active players"),
    page: int = Query(1, ge=1, le=1000, description="Page number"),
    per_page: int = Query(20, ge=1, le=1000, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get all players, optionally filtered by team with pagination"""
    try:
        # Validate team_id if provided
        if team_id is not None:
            validate_nba_team_id(team_id)
        
        # Calculate pagination
        offset = (page - 1) * per_page
        
        query = db.query(PlayerModel)
        if team_id:
            query = query.filter(PlayerModel.current_team_id == team_id)
        if active_only:
            query = query.filter(PlayerModel.is_active == True)
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        players = query.offset(offset).limit(per_page).all()
        
        return {
            "players": players,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "pages": (total_count + per_page - 1) // per_page
            }
        }
    except ValueError as ve:
        logger.warning(f"Validation error in get_players: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error getting players: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{player_id}")
async def get_player(player_id: int, db: Session = Depends(get_db)):
    """Get a specific player"""
    try:
        # Validate player ID
        validate_nba_player_id(player_id)
        
        player = db.query(PlayerModel).filter(PlayerModel.player_id == player_id).first()
        if player is None:
            raise HTTPException(status_code=404, detail="Player not found")
        return player
    except ValueError as ve:
        logger.warning(f"Validation error in get_player: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting player {player_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{player_id}/stats")
async def get_player_stats(
    player_id: int,
    season: Optional[str] = Query(None, pattern=r'^\d{4}-\d{2}$', description="Season in YYYY-YY format"),
    page: int = Query(1, ge=1, le=1000, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get all game statistics for a player, optionally filtered by season with pagination"""
    try:
        # Validate player ID
        validate_nba_player_id(player_id)
        
        # Validate season if provided
        if season:
            from app.schemas.validation import sanitize_string
            season = sanitize_string(season)
            if not re.match(r'^\d{4}-\d{2}$', season):
                raise ValueError("Season must be in YYYY-YY format")
        
        # First verify player exists
        player = db.query(PlayerModel).filter(PlayerModel.player_id == player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Calculate pagination
        offset = (page - 1) * per_page
        
        # Get all stats with game info
        from app.models.models import Team
        query = (db.query(PlayerGameStats, GameModel)
                .join(GameModel, PlayerGameStats.game_id == GameModel.game_id)
                .filter(PlayerGameStats.player_id == player_id))
        
        if season:
            query = query.filter(GameModel.season_year == season)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        stats = (query.order_by(desc(GameModel.game_date))
                .offset(offset)
                .limit(per_page)
                .all())
        
        # Format response
        formatted_stats = []
        for stat, game in stats:
            formatted_stats.append({
                "game": {
                    "game_id": game.game_id,
                    "date": game.game_date,
                    "season": game.season_year,
                    "home_team_id": game.home_team_id,
                    "away_team_id": game.away_team_id
                },
                "stats": stat
            })
        
        return {
            "player_id": player_id,
            "stats": formatted_stats,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "pages": (total_count + per_page - 1) // per_page
            }
        }
    except ValueError as ve:
        logger.warning(f"Validation error in get_player_stats: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error getting player {player_id} stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
        if season:
            query = query.filter(GameModel.season_year == season)
            
        stats_with_games = query.order_by(GameModel.game_date_utc.desc()).all()
        
        # Get team names for opposition calculation
        team_query = db.query(Team).all()
        teams_dict = {team.team_id: team.name for team in team_query}
                
        # Return stats with game dates and opposition team
        result = []
        for stat, game in stats_with_games:
            stat_dict = stat.__dict__.copy()
            stat_dict['game_date_utc'] = game.game_date_utc
            
            # Determine opposition team
            if stat.team_id == game.home_team_id:
                # Player was on home team, opposition is away team
                stat_dict['opposition_team_id'] = game.away_team_id
                stat_dict['opposition_team_name'] = teams_dict.get(game.away_team_id, 'Unknown')
                stat_dict['is_home_game'] = True
            else:
                # Player was on away team, opposition is home team
                stat_dict['opposition_team_id'] = game.home_team_id
                stat_dict['opposition_team_name'] = teams_dict.get(game.home_team_id, 'Unknown')
                stat_dict['is_home_game'] = False
                
            # Remove SQLAlchemy internal attributes
            if '_sa_instance_state' in stat_dict:
                del stat_dict['_sa_instance_state']
                
            result.append(stat_dict)
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting stats for player {player_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{player_id}/last_x_games")
async def get_player_last_x_games(
    player_id: int,
    count: int = Query(5, ge=1, le=20),
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get aggregated stats for player's last N games, optionally filtered by season"""
    try:
        # First verify player exists
        player = db.query(PlayerModel).filter(PlayerModel.player_id == player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Get the last N games' stats
        query = (db.query(PlayerGameStats)
                       .join(GameModel, PlayerGameStats.game_id == GameModel.game_id)
                       .filter(PlayerGameStats.player_id == player_id))
        
        if season:
            query = query.filter(GameModel.season_year == season)
            
        recent_stats = (query.order_by(GameModel.game_date_utc.desc())
                       .limit(count)
                       .all())
        
        if not recent_stats:
            return {
                "games_analyzed": 0,
                "stats": {
                    "avg_points": 0,
                    "avg_rebounds": 0,
                    "avg_assists": 0
                }
            }
        
        # Calculate averages
        avg_stats = {
            "avg_points": sum(stat.points for stat in recent_stats) / len(recent_stats),
            "avg_rebounds": sum(stat.rebounds for stat in recent_stats) / len(recent_stats),
            "avg_assists": sum(stat.assists for stat in recent_stats) / len(recent_stats)
        }
        
        return {
            "games_analyzed": len(recent_stats),
            "stats": avg_stats
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting last {count} games for player {player_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{player_id}/high_low_games")
async def get_player_high_low_games(
    player_id: int,
    count: int = Query(5, ge=1, le=20),
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get player's highest and lowest scoring games, optionally filtered by season"""
    try:
        # First verify player exists
        player = db.query(PlayerModel).filter(PlayerModel.player_id == player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Base query
        base_query = (db.query(PlayerGameStats, GameModel)
                     .join(GameModel, PlayerGameStats.game_id == GameModel.game_id)
                     .filter(PlayerGameStats.player_id == player_id))
        
        if season:
            base_query = base_query.filter(GameModel.season_year == season)
        
        # Get highest scoring games
        high_games = (base_query
                     .order_by(desc(PlayerGameStats.points))
                     .limit(count)
                     .all())
                     
        # Get lowest scoring games
        low_games = (base_query
                    .order_by(PlayerGameStats.points)
                    .limit(count)
                    .all())
        
        # Format the results
        high_games_list = [{
            "game_id": stat.game_id,
            "date_utc": game.game_date_utc,
            "points": stat.points
        } for stat, game in high_games]
        
        low_games_list = [{
            "game_id": stat.game_id,
            "date_utc": game.game_date_utc,
            "points": stat.points
        } for stat, game in low_games]
        
        return {
            "top_5": high_games_list,
            "bottom_5": low_games_list
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting high/low games for player {player_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))