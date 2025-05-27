from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class TeamBase(BaseModel):
    team_id: int
    name: str
    abbreviation: str
    conference: Optional[str] = None
    division: Optional[str] = None
    wins: int = 0
    losses: int = 0
    logo_url: Optional[str] = None
    loading_progress: int = 0
    roster_loaded: bool = False
    games_loaded: bool = False

    model_config = ConfigDict(from_attributes=True)


class PlayerBase(BaseModel):
    player_id: int
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    current_team_id: Optional[int] = None
    previous_team_id: Optional[int] = None
    traded_date: Optional[datetime] = None
    position: Optional[str] = None
    jersey_number: Optional[str] = None
    is_active: bool = True
    headshot_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GameBase(BaseModel):
    game_id: str
    game_date_utc: datetime
    home_team_id: int
    away_team_id: int
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: str
    season_year: str
    playoff_round: Optional[str] = None
    is_loaded: bool = False
    last_updated: Optional[datetime] = None
    home_team: Optional[TeamBase] = None
    away_team: Optional[TeamBase] = None

    model_config = ConfigDict(from_attributes=True)


class PlayerGameStatsBase(BaseModel):
    stat_id: Optional[int] = None
    player_id: int
    game_id: str
    team_id: int
    minutes: Optional[str] = None
    points: Optional[int] = None
    rebounds: Optional[int] = None
    assists: Optional[int] = None
    steals: Optional[int] = None
    blocks: Optional[int] = None
    fgm: Optional[int] = None
    fga: Optional[int] = None
    fg_pct: Optional[float] = None
    tpm: Optional[int] = None
    tpa: Optional[int] = None
    tp_pct: Optional[float] = None
    ftm: Optional[int] = None
    fta: Optional[int] = None
    ft_pct: Optional[float] = None
    turnovers: Optional[int] = None
    fouls: Optional[int] = None
    plus_minus: Optional[int] = None
    player_name: Optional[str] = None  # Added for stats response
    game_date_utc: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DataUpdateStatusBase(BaseModel):
    id: int
    last_successful_update: Optional[datetime] = None
    next_scheduled_update: Optional[datetime] = None
    is_updating: bool = False
    cancellation_requested: bool = False
    # Overall status for each component
    teams_updated: bool = False
    players_updated: bool = False
    games_updated: bool = False
    # Last update time for each component
    teams_last_update: Optional[datetime] = None
    players_last_update: Optional[datetime] = None
    games_last_update: Optional[datetime] = None
    # Current phase and error info
    current_phase: Optional[str] = None
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
