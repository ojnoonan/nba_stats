from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict, Union, cast

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO format string, or None if input is None."""
    if not dt:
        return None
    return dt.isoformat() if dt.tzinfo else dt.replace(tzinfo=timezone.utc).isoformat()


def serialize_value(value: Any) -> Any:
    """Serialize any value, handling datetime objects specially."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return serialize_datetime(value)
    if isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize_value(item) for item in value]
    return value


def normalize_components(
    components: Union[Dict[str, Any], None],
) -> Dict[str, Dict[str, Any]]:
    """Ensure component dictionary has consistent structure and all values are properly serialized"""
    if not isinstance(components, dict):
        components = {}

    for component in ["teams", "players", "games"]:
        if component not in components:
            components[component] = {}

        current = components[component]
        if not isinstance(current, dict):
            current = {}

        # Ensure required fields exist
        defaults = {
            "updated": False,
            "percent_complete": 0,
            "last_update": None,
            "last_error": None,
        }

        # Create normalized component dict with defaults and serialized values
        normalized = {}
        for key, default in defaults.items():
            value = current.get(key, default)
            normalized[key] = serialize_value(value)

        components[component] = normalized

    return components


class ComponentStatus(TypedDict, total=False):
    updated: bool
    percent_complete: int
    last_error: Optional[str]
    last_update: Optional[datetime]


class Components(TypedDict, total=False):
    players: ComponentStatus
    teams: ComponentStatus
    games: ComponentStatus


class DataUpdateStatus(Base):
    __tablename__ = "data_update_status"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=False
    )  # Ensure id=1 is explicitly managed
    last_successful_update: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    next_scheduled_update: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    is_updating: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancellation_requested: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Store component details in a JSON column
    components: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Overall status for each component
    teams_updated: Mapped[bool] = mapped_column(Boolean, default=False)
    players_updated: Mapped[bool] = mapped_column(Boolean, default=False)
    games_updated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Progress tracking for each component
    teams_percent_complete: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    players_percent_complete: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    games_percent_complete: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Last update time for each component
    teams_last_update: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    players_last_update: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    games_last_update: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Current phase and error info
    current_phase: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    current_detail: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_error_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __init__(self, **kwargs):
        # Ensure 'id' is explicitly set, defaulting to 1 if not provided.
        # This is crucial for the singleton nature of this table.
        if "id" not in kwargs:
            kwargs["id"] = 1

        if "components" not in kwargs:
            kwargs["components"] = {}
        else:
            if isinstance(kwargs["components"], dict):
                # Normalize and serialize the components
                kwargs["components"] = normalize_components(kwargs["components"])
        super().__init__(**kwargs)

    def __setattr__(self, key, value):
        if key == "components" and isinstance(value, dict):
            # Normalize and serialize any datetime values in components when set
            value = normalize_components(value)
        super().__setattr__(key, value)


class Team(Base):
    __tablename__ = "teams"

    team_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    abbreviation: Mapped[str] = mapped_column(String, nullable=False)
    conference: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    division: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    wins: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    losses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    logo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    roster_loaded: Mapped[bool] = mapped_column(Boolean, default=False)
    loading_progress: Mapped[int] = mapped_column(Integer, default=0)
    games_loaded: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    players: Mapped[List["Player"]] = relationship(
        "Player", back_populates="team", foreign_keys="[Player.current_team_id]"
    )
    home_games: Mapped[List["Game"]] = relationship(
        "Game", foreign_keys="[Game.home_team_id]", backref="home_team"
    )
    away_games: Mapped[List["Game"]] = relationship(
        "Game", foreign_keys="[Game.away_team_id]", backref="away_team"
    )


class Player(Base):
    __tablename__ = "players"

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    jersey_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    current_team_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("teams.team_id"), nullable=True
    )
    previous_team_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("teams.team_id"), nullable=True
    )
    traded_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    headshot_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_loaded: Mapped[bool] = mapped_column(Boolean, default=False)
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    team: Mapped[Optional["Team"]] = relationship(
        "Team", back_populates="players", foreign_keys=[current_team_id]
    )
    game_stats: Mapped[List["PlayerGameStats"]] = relationship(
        "PlayerGameStats", back_populates="player"
    )


class Game(Base):
    __tablename__ = "games"

    game_id: Mapped[str] = mapped_column(String, primary_key=True)
    home_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.team_id"), nullable=False
    )
    away_team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.team_id"), nullable=False
    )
    game_date_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    home_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    season_year: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    playoff_round: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    is_loaded: Mapped[bool] = mapped_column(Boolean, default=False)
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    player_stats: Mapped[List["PlayerGameStats"]] = relationship(
        "PlayerGameStats", back_populates="game"
    )


class PlayerGameStats(Base):
    __tablename__ = "player_game_stats"

    stat_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.player_id"), nullable=False
    )
    game_id: Mapped[str] = mapped_column(ForeignKey("games.game_id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.team_id"), nullable=False)
    minutes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rebounds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    assists: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    steals: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    blocks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fgm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fga: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fg_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tpm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tpa: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tp_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ftm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fta: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ft_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    turnovers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fouls: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    plus_minus: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "player_id", "game_id", "team_id", name="unique_player_game_stats"
        ),
    )

    # Relationships
    player: Mapped["Player"] = relationship("Player", back_populates="game_stats")
    game: Mapped["Game"] = relationship("Game", back_populates="player_stats")
    team: Mapped["Team"] = relationship("Team")
