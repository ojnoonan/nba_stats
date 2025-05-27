"""
Player repository with optimized queries for player-related operations.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.models import Player, PlayerGameStats, Team
from app.repositories.base import BaseRepository, PaginationResult


class PlayerRepository(BaseRepository[Player]):
    """Repository for player-related database operations."""

    def __init__(self, session: Session):
        super().__init__(session, Player)

    def get_by_id(self, player_id: int) -> Optional[Player]:
        """Get player by ID with team relationship loaded."""
        return (
            self.session.query(Player)
            .options(joinedload(Player.team))
            .filter(Player.player_id == player_id)
            .first()
        )

    def search_players(
        self,
        search_term: str,
        team_id: Optional[int] = None,
        position: Optional[str] = None,
        is_active: bool = True,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginationResult:
        """
        Search players with filters and pagination.
        Uses indexes: idx_players_team_id
        """
        query = self.session.query(Player).options(joinedload(Player.team))

        # Apply search filter
        if search_term:
            search_filter = or_(
                Player.full_name.ilike(f"%{search_term}%"),
                Player.first_name.ilike(f"%{search_term}%"),
                Player.last_name.ilike(f"%{search_term}%"),
            )
            query = query.filter(search_filter)

        # Apply team filter (uses idx_players_team_id index)
        if team_id:
            query = query.filter(Player.current_team_id == team_id)

        # Apply position filter
        if position:
            query = query.filter(Player.position == position)

        # Apply active filter
        query = query.filter(Player.is_active == is_active)

        # Order by name for consistent results
        query = query.order_by(Player.full_name)

        return self.paginate(query, page, per_page)

    def get_team_roster(
        self, team_id: int, include_inactive: bool = False
    ) -> List[Player]:
        """
        Get all players for a specific team.
        Uses index: idx_players_team_id
        """
        query = self.session.query(Player).options(joinedload(Player.team))
        query = query.filter(Player.current_team_id == team_id)

        if not include_inactive:
            query = query.filter(Player.is_active == True)

        return query.order_by(Player.jersey_number, Player.full_name).all()

    def get_players_by_position(
        self, position: str, team_id: Optional[int] = None
    ) -> List[Player]:
        """Get players by position, optionally filtered by team."""
        query = self.session.query(Player).options(joinedload(Player.team))
        query = query.filter(Player.position == position, Player.is_active == True)

        if team_id:
            query = query.filter(Player.current_team_id == team_id)

        return query.order_by(Player.full_name).all()

    def get_recently_updated(self, limit: int = 50) -> List[Player]:
        """Get recently updated players."""
        return (
            self.session.query(Player)
            .options(joinedload(Player.team))
            .filter(Player.last_updated.isnot(None))
            .order_by(desc(Player.last_updated))
            .limit(limit)
            .all()
        )

    def get_players_needing_update(self, hours_threshold: int = 24) -> List[Player]:
        """Get players that haven't been updated within the threshold."""
        threshold_time = datetime.utcnow() - timedelta(hours=hours_threshold)

        return (
            self.session.query(Player)
            .filter(
                or_(
                    Player.last_updated.is_(None), Player.last_updated < threshold_time
                ),
                Player.is_active == True,
            )
            .all()
        )

    def get_player_stats_summary(self, player_id: int) -> dict:
        """Get aggregated stats for a player across all games."""
        stats = (
            self.session.query(
                func.count(PlayerGameStats.stat_id).label("games_played"),
                func.avg(PlayerGameStats.points).label("avg_points"),
                func.avg(PlayerGameStats.rebounds).label("avg_rebounds"),
                func.avg(PlayerGameStats.assists).label("avg_assists"),
                func.sum(PlayerGameStats.points).label("total_points"),
                func.max(PlayerGameStats.points).label("max_points"),
            )
            .filter(PlayerGameStats.player_id == player_id)
            .first()
        )

        if not stats or stats.games_played == 0:
            return {}

        return {
            "games_played": stats.games_played or 0,
            "avg_points": round(float(stats.avg_points or 0), 1),
            "avg_rebounds": round(float(stats.avg_rebounds or 0), 1),
            "avg_assists": round(float(stats.avg_assists or 0), 1),
            "total_points": stats.total_points or 0,
            "max_points": stats.max_points or 0,
        }

    def bulk_update_active_status(self, player_ids: List[int], is_active: bool) -> None:
        """Bulk update active status for multiple players."""
        updates = [
            {
                "player_id": pid,
                "is_active": is_active,
                "last_updated": datetime.utcnow(),
            }
            for pid in player_ids
        ]
        self.bulk_update(updates)
