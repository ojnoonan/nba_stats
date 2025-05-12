import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional
from app.models.models import Player as PlayerModel, PlayerGameStats, Game as GameModel
from app.database.database import get_db

router = APIRouter(
    prefix="/players",
    tags=["players"]
)

logger = logging.getLogger(__name__)

@router.get("")
async def get_players(
    team_id: Optional[int] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all players, optionally filtered by team"""
    try:
        query = db.query(PlayerModel)
        if team_id:
            query = query.filter(PlayerModel.current_team_id == team_id)
        if active_only:
            query = query.filter(PlayerModel.is_active == True)
        players = query.all()
        return players
    except Exception as e:
        logger.error(f"Error getting players: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{player_id}")
async def get_player(player_id: int, db: Session = Depends(get_db)):
    """Get a specific player"""
    try:
        player = db.query(PlayerModel).filter(PlayerModel.player_id == player_id).first()
        if player is None:
            raise HTTPException(status_code=404, detail="Player not found")
        return player
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting player {player_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{player_id}/stats")
async def get_player_stats(
    player_id: int,
    db: Session = Depends(get_db)
):
    """Get all game statistics for a player"""
    try:
        # First verify player exists
        player = db.query(PlayerModel).filter(PlayerModel.player_id == player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
            
        # Get all stats with game info
        stats = (db.query(PlayerGameStats, GameModel)
                .join(GameModel, PlayerGameStats.game_id == GameModel.game_id)
                .filter(PlayerGameStats.player_id == player_id)
                .order_by(GameModel.game_date_utc.desc())
                .all())
                
        # Return stats with game dates
        result = []
        for stat, game in stats:
            stat_dict = stat.__dict__
            stat_dict['game_date_utc'] = game.game_date_utc
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
    db: Session = Depends(get_db)
):
    """Get aggregated stats for player's last N games"""
    try:
        # First verify player exists
        player = db.query(PlayerModel).filter(PlayerModel.player_id == player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Get the last N games' stats
        recent_stats = (db.query(PlayerGameStats)
                       .join(GameModel, PlayerGameStats.game_id == GameModel.game_id)
                       .filter(PlayerGameStats.player_id == player_id)
                       .order_by(GameModel.game_date_utc.desc())
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
    db: Session = Depends(get_db)
):
    """Get player's highest and lowest scoring games"""
    try:
        # First verify player exists
        player = db.query(PlayerModel).filter(PlayerModel.player_id == player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Get highest scoring games
        high_games = (db.query(PlayerGameStats, GameModel)
                     .join(GameModel, PlayerGameStats.game_id == GameModel.game_id)
                     .filter(PlayerGameStats.player_id == player_id)
                     .order_by(desc(PlayerGameStats.points))
                     .limit(count)
                     .all())
                     
        # Get lowest scoring games
        low_games = (db.query(PlayerGameStats, GameModel)
                    .join(GameModel, PlayerGameStats.game_id == GameModel.game_id)
                    .filter(PlayerGameStats.player_id == player_id)
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