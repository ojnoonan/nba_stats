from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True

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
    home_team: Optional[TeamBase] = None
    away_team: Optional[TeamBase] = None

    class Config:
        from_attributes = True

class PlayerGameStatsBase(BaseModel):
    stat_id: Optional[int] = None
    player_id: int
    game_id: str
    team_id: int
    minutes: str
    points: int
    rebounds: int
    assists: int
    steals: int
    blocks: int
    fgm: int
    fga: int
    fg_pct: float
    tpm: int
    tpa: int
    tp_pct: float
    ftm: int
    fta: int
    ft_pct: float
    turnovers: int
    fouls: int
    plus_minus: int
    player_name: Optional[str] = None  # Added for stats response
    game_date_utc: Optional[datetime] = None

    class Config:
        from_attributes = True

class DataUpdateStatusBase(BaseModel):
    id: int
    last_successful_update: Optional[datetime] = None
    next_scheduled_update: Optional[datetime] = None
    is_updating: bool = False
    teams_updated: bool = False
    players_updated: bool = False
    games_updated: bool = False
    current_phase: Optional[str] = None
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    class Config:
        from_attributes = True