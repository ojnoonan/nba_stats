"""
Team repository with optimized queries for team-related operations.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.models import Game, Player, Team
from app.repositories.base import BaseRepository, PaginationResult


class TeamRepository(BaseRepository[Team]):
    """Repository for team-related database operations."""

    def __init__(self, session: Session):
        super().__init__(session, Team)

    def get_by_id(self, team_id: int) -> Optional[Team]:
        """Get team by ID with optimized loading."""
        return self.session.query(Team).filter(Team.team_id == team_id).first()

    def get_all_active(self) -> List[Team]:
        """Get all active teams ordered by name."""
        return (
            self.session.query(Team)
            .filter(Team.is_active == True)
            .order_by(Team.name)
            .all()
        )

    def search_teams(
        self,
        search_term: str,
        conference: Optional[str] = None,
        division: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginationResult:
        """Search teams with filters and pagination."""
        query = self.session.query(Team)

        # Apply search filter
        if search_term:
            query = query.filter(
                or_(
                    Team.name.ilike(f"%{search_term}%"),
                    Team.abbreviation.ilike(f"%{search_term}%"),
                )
            )

        # Apply conference filter
        if conference:
            query = query.filter(Team.conference == conference)

        # Apply division filter
        if division:
            query = query.filter(Team.division == division)

        # Only active teams
        query = query.filter(Team.is_active == True)

        # Order by name
        query = query.order_by(Team.name)

        return self.paginate(query, page, per_page)

    def get_by_conference(self, conference: str) -> List[Team]:
        """Get teams by conference."""
        return (
            self.session.query(Team)
            .filter(Team.conference == conference, Team.is_active == True)
            .order_by(Team.name)
            .all()
        )

    def get_by_division(self, division: str) -> List[Team]:
        """Get teams by division."""
        return (
            self.session.query(Team)
            .filter(Team.division == division, Team.is_active == True)
            .order_by(Team.name)
            .all()
        )

    def get_team_with_roster(self, team_id: int) -> Optional[Team]:
        """Get team with full roster loaded."""
        return (
            self.session.query(Team)
            .options(joinedload(Team.players).joinedload(Player.game_stats))
            .filter(Team.team_id == team_id)
            .first()
        )

    def get_teams_by_record(self, limit: int = 30) -> List[Team]:
        """Get teams ordered by win-loss record."""
        return (
            self.session.query(Team)
            .filter(Team.is_active == True)
            .order_by(desc(Team.wins), Team.losses)
            .limit(limit)
            .all()
        )

    def get_team_roster_count(self, team_id: int) -> int:
        """Get active player count for a team."""
        return (
            self.session.query(func.count(Player.player_id))
            .filter(Player.current_team_id == team_id, Player.is_active == True)
            .scalar()
        )

    def get_team_recent_games(self, team_id: int, limit: int = 10) -> List[Game]:
        """Get recent games for a team."""
        return (
            self.session.query(Game)
            .options(joinedload(Game.home_team), joinedload(Game.away_team))
            .filter(or_(Game.home_team_id == team_id, Game.away_team_id == team_id))
            .order_by(desc(Game.game_date_utc))
            .limit(limit)
            .all()
        )

    def get_team_standings_data(self) -> List[dict]:
        """Get teams with calculated standings data."""
        teams = self.session.query(Team).filter(Team.is_active == True).all()

        standings_data = []
        for team in teams:
            # Calculate win percentage
            total_games = (team.wins or 0) + (team.losses or 0)
            win_pct = (team.wins / total_games) if total_games > 0 else 0.0

            standings_data.append(
                {
                    "team_id": team.team_id,
                    "name": team.name,
                    "abbreviation": team.abbreviation,
                    "conference": team.conference,
                    "division": team.division,
                    "wins": team.wins or 0,
                    "losses": team.losses or 0,
                    "win_percentage": round(win_pct, 3),
                    "games_played": total_games,
                }
            )

        # Sort by conference, then by win percentage
        standings_data.sort(key=lambda x: (x["conference"], -x["win_percentage"]))

        return standings_data

    def get_teams_needing_update(self, hours_threshold: int = 24) -> List[Team]:
        """Get teams that haven't been updated within the threshold."""
        from datetime import timedelta

        threshold_time = datetime.utcnow() - timedelta(hours=hours_threshold)

        return (
            self.session.query(Team)
            .filter(
                or_(Team.last_updated.is_(None), Team.last_updated < threshold_time),
                Team.is_active == True,
            )
            .all()
        )

    def update_team_record(
        self, team_id: int, wins: int, losses: int
    ) -> Optional[Team]:
        """Update team win-loss record."""
        team = self.get_by_id(team_id)
        if team:
            team.wins = wins
            team.losses = losses
            team.last_updated = datetime.utcnow()
            self.session.commit()
            self.session.refresh(team)
        return team

    def mark_roster_loaded(self, team_id: int, progress: int = 100) -> None:
        """Mark team roster as loaded with progress."""
        team = self.get_by_id(team_id)
        if team:
            team.roster_loaded = True
            team.loading_progress = progress
            team.last_updated = datetime.utcnow()
            self.session.commit()
