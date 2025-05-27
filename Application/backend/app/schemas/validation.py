"""
Request and response validation schemas.
Enhanced Pydantic models with comprehensive input validation.
"""

import re
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class PaginationParams(BaseModel):
    """Standard pagination parameters with validation."""

    skip: int = Field(default=0, ge=0, le=10000, description="Number of items to skip")
    limit: int = Field(
        default=100, ge=1, le=1000, description="Maximum number of items to return"
    )


class TeamQueryParams(PaginationParams):
    """Query parameters for team endpoints."""

    conference: Optional[Literal["East", "West"]] = Field(
        default=None, description="Filter by conference"
    )


class PlayerQueryParams(PaginationParams):
    """Query parameters for player endpoints."""

    team_id: Optional[int] = Field(
        default=None, ge=1, le=9999, description="Filter by team ID"
    )
    active_only: bool = Field(
        default=True, description="Filter for active players only"
    )


class GameQueryParams(PaginationParams):
    """Query parameters for game endpoints."""

    team_id: Optional[int] = Field(
        default=None, ge=1, le=9999, description="Filter by team ID"
    )
    status: Optional[
        Literal["Scheduled", "Live", "Final", "Postponed", "Cancelled"]
    ] = Field(default=None, description="Filter by game status")
    player_id: Optional[int] = Field(
        default=None, ge=1, description="Filter by player ID"
    )
    date: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Filter by date (YYYY-MM-DD format)",
    )

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v):
        """Validate date format and ensure it's a valid date."""
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class SearchQueryParams(BaseModel):
    """Query parameters for search endpoints."""

    q: str = Field(..., min_length=1, max_length=100, description="Search query string")
    skip: int = Field(default=0, ge=0, le=1000)
    limit: int = Field(default=10, ge=1, le=100)
    include_inactive: bool = Field(
        default=False, description="Include inactive players/teams"
    )

    @field_validator("q")
    @classmethod
    def validate_search_query(cls, v):
        """Sanitize search query."""
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>&"\'%;]', "", v.strip())
        if not sanitized:
            raise ValueError("Search query cannot be empty after sanitization")
        return sanitized


class PlayerStatsQueryParams(PaginationParams):
    """Query parameters for player stats endpoints."""

    player_id: int = Field(ge=1, description="Player ID")
    season: Optional[str] = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}$",
        description="Season in YYYY-YY format (e.g., 2023-24)",
    )


class UpdateRequest(BaseModel):
    """Request body for data updates."""

    components: Optional[List[Literal["teams", "players", "games"]]] = Field(
        default=None, description="Specific components to update"
    )
    force: bool = Field(
        default=False, description="Force update even if recently updated"
    )


class AdminKeyValidation(BaseModel):
    """Validation for admin API key."""

    api_key: Optional[str] = Field(
        default=None, min_length=1, max_length=255, description="Admin API key"
    )


# Enhanced response models with additional validation
class TeamResponse(BaseModel):
    """Enhanced team response model."""

    model_config = ConfigDict(from_attributes=True)

    team_id: int = Field(ge=1, description="Unique team identifier")
    name: str = Field(min_length=1, max_length=100, description="Team name")
    abbreviation: str = Field(
        min_length=2, max_length=5, description="Team abbreviation"
    )
    conference: Optional[Literal["East", "West"]] = None
    division: Optional[str] = Field(default=None, max_length=50)
    wins: int = Field(ge=0, default=0)
    losses: int = Field(ge=0, default=0)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    loading_progress: int = Field(ge=0, le=100, default=0)
    roster_loaded: bool = False
    games_loaded: bool = False


class PlayerResponse(BaseModel):
    """Enhanced player response model."""

    model_config = ConfigDict(from_attributes=True)

    player_id: int = Field(ge=1, description="Unique player identifier")
    full_name: str = Field(min_length=1, max_length=100)
    first_name: Optional[str] = Field(default=None, max_length=50)
    last_name: Optional[str] = Field(default=None, max_length=50)
    current_team_id: Optional[int] = Field(default=None, ge=1)
    previous_team_id: Optional[int] = Field(default=None, ge=1)
    traded_date: Optional[datetime] = None
    position: Optional[str] = Field(default=None, max_length=10)
    jersey_number: Optional[str] = Field(default=None, max_length=3)
    is_active: bool = True
    headshot_url: Optional[str] = Field(default=None, max_length=500)


class GameResponse(BaseModel):
    """Enhanced game response model."""

    model_config = ConfigDict(from_attributes=True)

    game_id: str = Field(min_length=1, max_length=50)
    game_date_utc: datetime
    home_team_id: int = Field(ge=1)
    away_team_id: int = Field(ge=1)
    home_score: Optional[int] = Field(default=None, ge=0, le=300)
    away_score: Optional[int] = Field(default=None, ge=0, le=300)
    status: str = Field(min_length=1, max_length=20)
    season_year: str = Field(pattern=r"^\d{4}-\d{2}$")
    playoff_round: Optional[str] = Field(default=None, max_length=50)
    home_team: Optional[TeamResponse] = None
    away_team: Optional[TeamResponse] = None


class PlayerStatsResponse(BaseModel):
    """Enhanced player statistics response model."""

    model_config = ConfigDict(from_attributes=True)

    stat_id: Optional[int] = None
    player_id: int = Field(ge=1)
    game_id: str = Field(min_length=1, max_length=50)
    team_id: int = Field(ge=1)
    minutes: Optional[str] = Field(default=None, max_length=10)
    points: Optional[int] = Field(default=None, ge=0, le=100)
    rebounds: Optional[int] = Field(default=None, ge=0, le=50)
    assists: Optional[int] = Field(default=None, ge=0, le=50)
    steals: Optional[int] = Field(default=None, ge=0, le=20)
    blocks: Optional[int] = Field(default=None, ge=0, le=20)
    fgm: Optional[int] = Field(default=None, ge=0, le=50)
    fga: Optional[int] = Field(default=None, ge=0, le=100)
    fg_pct: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tpm: Optional[int] = Field(default=None, ge=0, le=30)
    tpa: Optional[int] = Field(default=None, ge=0, le=50)
    tp_pct: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    ftm: Optional[int] = Field(default=None, ge=0, le=50)
    fta: Optional[int] = Field(default=None, ge=0, le=50)
    ft_pct: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    turnovers: Optional[int] = Field(default=None, ge=0, le=20)
    fouls: Optional[int] = Field(default=None, ge=0, le=10)
    plus_minus: Optional[int] = Field(default=None, ge=-100, le=100)
    player_name: Optional[str] = Field(default=None, max_length=100)
    game_date_utc: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[dict] = Field(
        default=None, description="Additional error details"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StatusResponse(BaseModel):
    """API status response model."""

    status: str = Field(description="API status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(description="API version")
    database_connected: bool = Field(description="Database connection status")
