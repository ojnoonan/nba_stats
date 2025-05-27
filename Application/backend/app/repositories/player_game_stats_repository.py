"""
Player game stats repository with optimized queries for statistics operations.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.models import Game, Player, PlayerGameStats, Team
from app.repositories.base import BaseRepository, PaginationResult


class PlayerGameStatsRepository(BaseRepository[PlayerGameStats]):
    """Repository for player game statistics operations."""

    def __init__(self, session: Session):
        super().__init__(session, PlayerGameStats)

    def get_player_game_stats(
        self, player_id: int, game_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[PlayerGameStats]:
        """
        Get player stats for specific games.
        Uses index: idx_player_games_player_id
        """
        query = (
            self.session.query(PlayerGameStats)
            .options(
                joinedload(PlayerGameStats.player),
                joinedload(PlayerGameStats.game),
                joinedload(PlayerGameStats.team),
            )
            .filter(PlayerGameStats.player_id == player_id)
        )

        if game_id:
            query = query.filter(PlayerGameStats.game_id == game_id)

        query = query.join(Game).order_by(desc(Game.game_date_utc))

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_game_stats(
        self, game_id: str, team_id: Optional[int] = None
    ) -> List[PlayerGameStats]:
        """
        Get all player stats for a specific game.
        Uses index: idx_player_games_game_id
        """
        query = (
            self.session.query(PlayerGameStats)
            .options(
                joinedload(PlayerGameStats.player), joinedload(PlayerGameStats.team)
            )
            .filter(PlayerGameStats.game_id == game_id)
        )

        if team_id:
            query = query.filter(PlayerGameStats.team_id == team_id)

        return query.order_by(desc(PlayerGameStats.points)).all()

    def get_team_game_stats(self, team_id: int, game_id: str) -> List[PlayerGameStats]:
        """Get all player stats for a team in a specific game."""
        return (
            self.session.query(PlayerGameStats)
            .options(joinedload(PlayerGameStats.player))
            .filter(
                and_(
                    PlayerGameStats.team_id == team_id,
                    PlayerGameStats.game_id == game_id,
                )
            )
            .order_by(desc(PlayerGameStats.points))
            .all()
        )

    def get_player_season_stats(
        self, player_id: int, season_year: str
    ) -> List[PlayerGameStats]:
        """Get player stats for entire season."""
        return (
            self.session.query(PlayerGameStats)
            .options(joinedload(PlayerGameStats.game), joinedload(PlayerGameStats.team))
            .join(Game)
            .filter(
                and_(
                    PlayerGameStats.player_id == player_id,
                    Game.season_year == season_year,
                )
            )
            .order_by(desc(Game.game_date_utc))
            .all()
        )

    def get_player_recent_stats(
        self, player_id: int, days: int = 30, limit: int = 10
    ) -> List[PlayerGameStats]:
        """Get player's recent game stats."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        return (
            self.session.query(PlayerGameStats)
            .options(joinedload(PlayerGameStats.game), joinedload(PlayerGameStats.team))
            .join(Game)
            .filter(
                and_(
                    PlayerGameStats.player_id == player_id,
                    Game.game_date_utc >= cutoff_date,
                )
            )
            .order_by(desc(Game.game_date_utc))
            .limit(limit)
            .all()
        )

    def get_top_performers(
        self,
        stat_type: str = "points",
        limit: int = 10,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[PlayerGameStats]:
        """Get top performers for a specific stat type."""
        query = self.session.query(PlayerGameStats).options(
            joinedload(PlayerGameStats.player),
            joinedload(PlayerGameStats.game),
            joinedload(PlayerGameStats.team),
        )

        # Date range filter if provided
        if date_from or date_to:
            query = query.join(Game)
            if date_from:
                query = query.filter(Game.game_date_utc >= date_from)
            if date_to:
                query = query.filter(Game.game_date_utc <= date_to)

        # Order by the specified stat
        stat_column = getattr(PlayerGameStats, stat_type, PlayerGameStats.points)
        query = query.filter(stat_column.isnot(None))
        query = query.order_by(desc(stat_column))

        return query.limit(limit).all()

    def get_player_averages(
        self,
        player_id: int,
        season_year: Optional[str] = None,
        last_n_games: Optional[int] = None,
    ) -> Dict[str, float]:
        """Calculate player averages for various stats."""
        query = self.session.query(
            func.avg(PlayerGameStats.points).label("avg_points"),
            func.avg(PlayerGameStats.rebounds).label("avg_rebounds"),
            func.avg(PlayerGameStats.assists).label("avg_assists"),
            func.avg(PlayerGameStats.steals).label("avg_steals"),
            func.avg(PlayerGameStats.blocks).label("avg_blocks"),
            func.avg(PlayerGameStats.fg_pct).label("avg_fg_pct"),
            func.avg(PlayerGameStats.tp_pct).label("avg_3p_pct"),
            func.avg(PlayerGameStats.ft_pct).label("avg_ft_pct"),
            func.count(PlayerGameStats.stat_id).label("games_played"),
        ).filter(PlayerGameStats.player_id == player_id)

        if season_year:
            query = query.join(Game).filter(Game.season_year == season_year)

        if last_n_games:
            # Get the latest games first, then calculate averages
            latest_stats = (
                self.session.query(PlayerGameStats)
                .join(Game)
                .filter(PlayerGameStats.player_id == player_id)
                .order_by(desc(Game.game_date_utc))
                .limit(last_n_games)
                .subquery()
            )

            query = self.session.query(
                func.avg(latest_stats.c.points).label("avg_points"),
                func.avg(latest_stats.c.rebounds).label("avg_rebounds"),
                func.avg(latest_stats.c.assists).label("avg_assists"),
                func.avg(latest_stats.c.steals).label("avg_steals"),
                func.avg(latest_stats.c.blocks).label("avg_blocks"),
                func.avg(latest_stats.c.fg_pct).label("avg_fg_pct"),
                func.avg(latest_stats.c.tp_pct).label("avg_3p_pct"),
                func.avg(latest_stats.c.ft_pct).label("avg_ft_pct"),
                func.count(latest_stats.c.stat_id).label("games_played"),
            )

        result = query.first()

        if not result or result.games_played == 0:
            return {}

        return {
            "points": round(float(result.avg_points or 0), 1),
            "rebounds": round(float(result.avg_rebounds or 0), 1),
            "assists": round(float(result.avg_assists or 0), 1),
            "steals": round(float(result.avg_steals or 0), 1),
            "blocks": round(float(result.avg_blocks or 0), 1),
            "field_goal_percentage": round(float(result.avg_fg_pct or 0), 3),
            "three_point_percentage": round(float(result.avg_3p_pct or 0), 3),
            "free_throw_percentage": round(float(result.avg_ft_pct or 0), 3),
            "games_played": result.games_played,
        }

    def get_team_game_totals(self, team_id: int, game_id: str) -> Dict[str, int]:
        """Get team totals for a specific game."""
        result = (
            self.session.query(
                func.sum(PlayerGameStats.points).label("total_points"),
                func.sum(PlayerGameStats.rebounds).label("total_rebounds"),
                func.sum(PlayerGameStats.assists).label("total_assists"),
                func.sum(PlayerGameStats.steals).label("total_steals"),
                func.sum(PlayerGameStats.blocks).label("total_blocks"),
                func.sum(PlayerGameStats.turnovers).label("total_turnovers"),
                func.count(PlayerGameStats.player_id).label("players_played"),
            )
            .filter(
                and_(
                    PlayerGameStats.team_id == team_id,
                    PlayerGameStats.game_id == game_id,
                )
            )
            .first()
        )

        if not result:
            return {}

        return {
            "points": result.total_points or 0,
            "rebounds": result.total_rebounds or 0,
            "assists": result.total_assists or 0,
            "steals": result.total_steals or 0,
            "blocks": result.total_blocks or 0,
            "turnovers": result.total_turnovers or 0,
            "players_played": result.players_played or 0,
        }

    def bulk_create_game_stats(
        self, game_stats_data: List[Dict]
    ) -> List[PlayerGameStats]:
        """Bulk create player game stats for improved performance."""
        # Add timestamp to all records
        for stats in game_stats_data:
            stats["last_updated"] = datetime.utcnow()

        return self.bulk_create(game_stats_data)

    def get_stats_needing_update(
        self, game_id: str, expected_player_count: Optional[int] = None
    ) -> bool:
        """Check if game stats need updating."""
        current_count = (
            self.session.query(func.count(PlayerGameStats.stat_id))
            .filter(PlayerGameStats.game_id == game_id)
            .scalar()
        )

        if expected_player_count:
            return current_count < expected_player_count

        return current_count == 0
