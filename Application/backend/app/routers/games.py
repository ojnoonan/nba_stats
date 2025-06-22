from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import distinct
from typing import Optional, List
import logging

from app.models.models import Game as GameModel, PlayerGameStats, Player as PlayerModel
from app.schemas.schemas import GameBase, PlayerGameStatsBase
from app.database.database import get_db
from app.core.exceptions import ErrorHandler, NotFoundError, DatabaseError

router = APIRouter(
    prefix="/games",
    tags=["games"]
)

logger = logging.getLogger(__name__)

@router.get("/seasons")
async def get_available_seasons(db: Session = Depends(get_db)):
    """Get all available seasons in the database"""
    try:
        seasons = db.query(distinct(GameModel.season_year)).order_by(GameModel.season_year.desc()).all()
        return [season[0] for season in seasons if season[0]]
    except Exception as e:
        raise ErrorHandler.handle_error(e, "get available seasons")

@router.get("", response_model=List[GameBase])
async def get_games(
    team_id: Optional[int] = None,
    status: Optional[str] = None,
    player_id: Optional[int] = None,
    season: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all games, optionally filtered by team, status, player, or season"""
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
        
        if season:
            query = query.filter(GameModel.season_year == season)
        
        # If no status filter, use default descending order
        if not status:
            query = query.order_by(GameModel.game_date_utc.desc())
            
        games = query.all()
        return games
        
    except Exception as e:
        raise ErrorHandler.handle_error(e, "get games")

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
            raise NotFoundError("Game", game_id)
        return game
    except Exception as e:
        raise ErrorHandler.handle_error(e, f"get game {game_id}")

@router.get("/{game_id}/stats", response_model=List[PlayerGameStatsBase])
async def get_game_stats(game_id: str, db: Session = Depends(get_db)):
    """Get player statistics for a specific game"""
    try:
        # First verify the game exists
        game = db.query(GameModel).filter(GameModel.game_id == game_id).first()
        if not game:
            raise NotFoundError("Game", game_id)
        
        # For upcoming games, return empty stats list
        if getattr(game, 'status') == 'Upcoming':
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
        
    except Exception as e:
        raise ErrorHandler.handle_error(e, f"get game stats for {game_id}")