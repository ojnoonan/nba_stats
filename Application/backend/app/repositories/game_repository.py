"""
Game repository with optimized queries for game-related operations.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.models import Game, PlayerGameStats, Team
from app.repositories.base import BaseRepository, PaginationResult


class GameRepository(BaseRepository[Game]):
    """Repository for game-related database operations."""

    def __init__(self, session: Session):
        super().__init__(session, Game)

    def get_by_id(self, game_id: str) -> Optional[Game]:
        """Get game by ID with team relationships loaded."""
        return (
            self.session.query(Game)
            .options(joinedload(Game.home_team), joinedload(Game.away_team))
            .filter(Game.game_id == game_id)
            .first()
        )

    def get_games_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        team_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginationResult:
        """
        Get games within date range with filters.
        Uses indexes: idx_games_date, idx_games_team_date, idx_games_status
        """
        query = self.session.query(Game).options(
            joinedload(Game.home_team), joinedload(Game.away_team)
        )

        # Date range filter (uses idx_games_date index)
        query = query.filter(
            and_(Game.game_date_utc >= start_date, Game.game_date_utc <= end_date)
        )

        # Team filter (uses idx_games_team_date composite index)
        if team_id:
            query = query.filter(
                or_(Game.home_team_id == team_id, Game.away_team_id == team_id)
            )

        # Status filter (uses idx_games_status index)
        if status:
            query = query.filter(Game.status == status)

        # Order by date descending
        query = query.order_by(desc(Game.game_date_utc))

        return self.paginate(query, page, per_page)

    def get_team_games(
        self,
        team_id: int,
        limit: Optional[int] = None,
        home_only: bool = False,
        away_only: bool = False,
    ) -> List[Game]:
        """
        Get games for a specific team.
        Uses indexes: idx_games_team_date, idx_games_away_team_date
        """
        query = self.session.query(Game).options(
            joinedload(Game.home_team), joinedload(Game.away_team)
        )

        if home_only:
            query = query.filter(Game.home_team_id == team_id)
        elif away_only:
            query = query.filter(Game.away_team_id == team_id)
        else:
            query = query.filter(
                or_(Game.home_team_id == team_id, Game.away_team_id == team_id)
            )

        query = query.order_by(desc(Game.game_date_utc))

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_recent_games(
        self, days: int = 7, status: Optional[str] = None, limit: int = 50
    ) -> List[Game]:
        """
        Get recent games within specified days.
        Uses index: idx_games_date
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = (
            self.session.query(Game)
            .options(joinedload(Game.home_team), joinedload(Game.away_team))
            .filter(Game.game_date_utc >= cutoff_date)
        )

        if status:
            query = query.filter(Game.status == status)

        return query.order_by(desc(Game.game_date_utc)).limit(limit).all()

    def get_games_by_status(
        self, status: str, limit: Optional[int] = None
    ) -> List[Game]:
        """
        Get games by status.
        Uses index: idx_games_status
        """
        query = (
            self.session.query(Game)
            .options(joinedload(Game.home_team), joinedload(Game.away_team))
            .filter(Game.status == status)
        )

        query = query.order_by(desc(Game.game_date_utc))

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_upcoming_games(
        self, team_id: Optional[int] = None, days_ahead: int = 7, limit: int = 20
    ) -> List[Game]:
        """Get upcoming games within specified days."""
        now = datetime.utcnow()
        end_date = now + timedelta(days=days_ahead)

        query = (
            self.session.query(Game)
            .options(joinedload(Game.home_team), joinedload(Game.away_team))
            .filter(and_(Game.game_date_utc >= now, Game.game_date_utc <= end_date))
        )

        if team_id:
            query = query.filter(
                or_(Game.home_team_id == team_id, Game.away_team_id == team_id)
            )

        return query.order_by(Game.game_date_utc).limit(limit).all()

    def get_season_games(
        self,
        season_year: str,
        team_id: Optional[int] = None,
        playoff_only: bool = False,
    ) -> List[Game]:
        """Get games for a specific season."""
        query = (
            self.session.query(Game)
            .options(joinedload(Game.home_team), joinedload(Game.away_team))
            .filter(Game.season_year == season_year)
        )

        if team_id:
            query = query.filter(
                or_(Game.home_team_id == team_id, Game.away_team_id == team_id)
            )

        if playoff_only:
            query = query.filter(Game.playoff_round.isnot(None))

        return query.order_by(Game.game_date_utc).all()

    def get_head_to_head(
        self, team1_id: int, team2_id: int, limit: Optional[int] = None
    ) -> List[Game]:
        """Get head-to-head games between two teams."""
        query = (
            self.session.query(Game)
            .options(joinedload(Game.home_team), joinedload(Game.away_team))
            .filter(
                or_(
                    and_(Game.home_team_id == team1_id, Game.away_team_id == team2_id),
                    and_(Game.home_team_id == team2_id, Game.away_team_id == team1_id),
                )
            )
        )

        query = query.order_by(desc(Game.game_date_utc))

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_games_needing_update(self, hours_threshold: int = 2) -> List[Game]:
        """Get games that need stats updates (recent games without full data)."""
        threshold_time = datetime.utcnow() - timedelta(hours=hours_threshold)

        return (
            self.session.query(Game)
            .filter(
                and_(
                    Game.game_date_utc >= threshold_time,
                    Game.status == "Final",
                    Game.is_loaded == False,
                )
            )
            .order_by(desc(Game.game_date_utc))
            .all()
        )

    def get_game_stats_summary(self, game_id: str) -> dict:
        """Get aggregated stats summary for a game."""
        home_stats = (
            self.session.query(
                func.sum(PlayerGameStats.points).label("total_points"),
                func.count(PlayerGameStats.player_id).label("players_count"),
            )
            .join(Game)
            .filter(
                and_(
                    PlayerGameStats.game_id == game_id,
                    PlayerGameStats.team_id == Game.home_team_id,
                )
            )
            .first()
        )

        away_stats = (
            self.session.query(
                func.sum(PlayerGameStats.points).label("total_points"),
                func.count(PlayerGameStats.player_id).label("players_count"),
            )
            .join(Game)
            .filter(
                and_(
                    PlayerGameStats.game_id == game_id,
                    PlayerGameStats.team_id == Game.away_team_id,
                )
            )
            .first()
        )

        return {
            "home_total_points": home_stats.total_points or 0 if home_stats else 0,
            "away_total_points": away_stats.total_points or 0 if away_stats else 0,
            "home_players": home_stats.players_count or 0 if home_stats else 0,
            "away_players": away_stats.players_count or 0 if away_stats else 0,
        }
