from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List
import logging

from app.models.models import Game as GameModel, PlayerGameStats, Player as PlayerModel
from app.schemas.schemas import GameBase, PlayerGameStatsBase
from app.database.database import get_db

router = APIRouter(
    prefix="/games",
    tags=["games"]
)

logger = logging.getLogger(__name__)

@router.get("", response_model=List[GameBase])
async def get_games(
    team_id: Optional[int] = None,
    status: Optional[str] = None,
    player_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all games, optionally filtered by team, status, or player"""
    try:
        query = (db.query(GameModel)
                .options(
                    joinedload(GameModel.home_team),
                    joinedload(GameModel.away_team)
                ))
        
        if team_id:
            query = query.filter(
                (GameModel.home_team_id == team_id) | 
                (GameModel.away_team_id == team_id)
            )
            
        if status:
            query = query.filter(GameModel.status == status)
            # For upcoming games, sort by ascending date
            if status == 'Upcoming':
                query = query.order_by(GameModel.game_date_utc.asc())
            else:
                query = query.order_by(GameModel.game_date_utc.desc())
            
        if player_id:
            # Get all games where player has stats
            game_ids = db.query(PlayerGameStats.game_id).filter(
                PlayerGameStats.player_id == player_id
            ).distinct()
            query = query.filter(GameModel.game_id.in_(game_ids))
        
        # If no status filter, use default descending order
        if not status:
            query = query.order_by(GameModel.game_date_utc.desc())
            
        games = query.all()
        return games
        
    except SQLAlchemyError as e:
        logger.error(f"Database error getting games: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.error(f"Error getting games: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{game_id}", response_model=GameBase)
async def get_game(game_id: str, db: Session = Depends(get_db)):
    """Get a specific game by ID"""
    try:
        game = (db.query(GameModel)
                .options(
                    joinedload(GameModel.home_team),
                    joinedload(GameModel.away_team)
                )
                .filter(GameModel.game_id == game_id)
                .first())
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        return game
    except SQLAlchemyError as e:
        logger.error(f"Database error getting game {game_id}: {str(e)}")
        # Rollback session if needed
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting game {game_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{game_id}/stats", response_model=List[PlayerGameStatsBase])
async def get_game_stats(game_id: str, db: Session = Depends(get_db)):
    """Get player statistics for a specific game"""
    try:
        # First verify the game exists
        game = db.query(GameModel).filter(GameModel.game_id == game_id).first()
        if not game:
            raise HTTPException(
                status_code=404, 
                detail=f"Game {game_id} not found"
            )
        
        # For upcoming games, return empty stats list
        if game.status == 'Upcoming':
            return []
            
        # Get all player stats for this game with player names
        stats = (db.query(PlayerGameStats, PlayerModel)
                .join(PlayerModel, PlayerGameStats.player_id == PlayerModel.player_id)
                .filter(PlayerGameStats.game_id == game_id)
                .all())
                
        # Format stats with player names
        result = []
        for stat, player in stats:
            stat_dict = {
                "stat_id": stat.stat_id,
                "player_id": stat.player_id,
                "player_name": player.full_name,  # Include player name from joined Player model
                "game_id": stat.game_id,
                "team_id": stat.team_id,
                "minutes": stat.minutes or "0:00",
                "points": stat.points or 0,
                "rebounds": stat.rebounds or 0,
                "assists": stat.assists or 0,
                "steals": stat.steals or 0,
                "blocks": stat.blocks or 0,
                "fgm": stat.fgm or 0,
                "fga": stat.fga or 0,
                "fg_pct": float(stat.fg_pct or 0),  # Convert to float in case it's None
                "tpm": stat.tpm or 0,
                "tpa": stat.tpa or 0,
                "tp_pct": float(stat.tp_pct or 0),
                "ftm": stat.ftm or 0,
                "fta": stat.fta or 0,
                "ft_pct": float(stat.ft_pct or 0),
                "turnovers": stat.turnovers or 0,
                "fouls": stat.fouls or 0,
                "plus_minus": stat.plus_minus or 0
            }
            result.append(stat_dict)
                
        return result
        
    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        logger.error(f"Database error getting game stats for {game_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting game stats for {game_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )