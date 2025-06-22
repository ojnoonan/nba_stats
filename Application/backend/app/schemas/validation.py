"""
Input validation schemas for API endpoints.
Provides security through input validation and sanitization.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union
from datetime import datetime
import re
import html
import logging

logger = logging.getLogger(__name__)

def sanitize_string(value: str) -> str:
    """Sanitize string input to prevent XSS and injection attacks."""
    if not isinstance(value, str):
        return value
    
    # HTML escape
    value = html.escape(value)
    
    # Remove null bytes and control characters
    value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
    
    # Limit length to prevent DoS
    if len(value) > 1000:
        logger.warning(f"String truncated from {len(value)} to 1000 characters")
        value = value[:1000]
    
    return value.strip()

def validate_nba_team_id(team_id: int) -> int:
    """Validate NBA team ID range."""
    if not isinstance(team_id, int):
        raise ValueError("Team ID must be an integer")
    if team_id < 1 or team_id > 1611661399:  # NBA team ID range
        raise ValueError(f"Invalid NBA team ID: {team_id}")
    return team_id

def validate_nba_player_id(player_id: int) -> int:
    """Validate NBA player ID range."""
    if not isinstance(player_id, int):
        raise ValueError("Player ID must be an integer")
    if player_id < 1 or player_id > 999999999:  # NBA player ID range
        raise ValueError(f"Invalid NBA player ID: {player_id}")
    return player_id

def validate_nba_game_id(game_id: str) -> str:
    """Validate NBA game ID format."""
    if not isinstance(game_id, str):
        raise ValueError("Game ID must be a string")
    if not re.match(r'^\d{10}$', game_id):
        raise ValueError(f"Invalid NBA game ID format: {game_id}")
    return game_id

class UpdateRequestSchema(BaseModel):
    """Schema for data update requests."""
    update_types: Optional[List[str]] = Field(None, description="Types of data to update")
    force: Optional[bool] = Field(False, description="Force update even if recently updated")
    
    @field_validator('update_types')
    @classmethod
    def validate_update_types(cls, v):
        if v is not None:
            valid_types = ['teams', 'players', 'games', 'all']
            for update_type in v:
                if update_type not in valid_types:
                    raise ValueError(f"Invalid update type: {update_type}. Must be one of {valid_types}")
        return v

class TeamIdSchema(BaseModel):
    """Schema for team ID validation."""
    team_id: int = Field(..., description="NBA team ID")
    
    @field_validator('team_id')
    @classmethod
    def validate_team_id(cls, v):
        return validate_nba_team_id(v)

class PlayerIdSchema(BaseModel):
    """Schema for player ID validation."""
    player_id: int = Field(..., description="NBA player ID")
    
    @field_validator('player_id')
    @classmethod
    def validate_player_id(cls, v):
        return validate_nba_player_id(v)

class GameIdSchema(BaseModel):
    """Schema for game ID validation."""
    game_id: str = Field(..., description="NBA game ID (10 digits)")
    
    @field_validator('game_id')
    @classmethod
    def validate_game_id(cls, v):
        return validate_nba_game_id(v)

class SearchQuerySchema(BaseModel):
    """Schema for search queries."""
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Maximum number of results")
    
    @field_validator('query')
    @classmethod
    def sanitize_query(cls, v):
        # Sanitize the query string
        sanitized = sanitize_string(v)
        # Allow only alphanumeric, spaces, hyphens, apostrophes, periods
        sanitized = re.sub(r'[^a-zA-Z0-9\s\-\'\.]', '', sanitized)
        if len(sanitized.strip()) == 0:
            raise ValueError("Query cannot be empty after sanitization")
        return sanitized.strip()

class SeasonSchema(BaseModel):
    """Schema for season validation."""
    season: Optional[str] = Field(None, description="Season in YYYY-YY format")
    
    @field_validator('season')
    @classmethod
    def validate_season(cls, v):
        if v is not None:
            v = sanitize_string(v)
            if not re.match(r'^\d{4}-\d{2}$', v):
                raise ValueError("Season must be in YYYY-YY format")
            year = int(v[:4])
            if year < 1946 or year > datetime.now().year + 1:
                raise ValueError("Invalid season year")
        return v

class PlayerQuerySchema(BaseModel):
    """Schema for player query parameters."""
    team_id: Optional[int] = Field(None, description="Filter by team ID")
    active_only: bool = Field(True, description="Only return active players")
    limit: Optional[int] = Field(50, ge=1, le=500, description="Maximum number of results")
    offset: Optional[int] = Field(0, ge=0, description="Number of results to skip")
    
    @field_validator('team_id')
    @classmethod
    def validate_team_id(cls, v):
        if v is not None:
            return validate_nba_team_id(v)
        return v

class AdminUpdateSchema(BaseModel):
    """Schema for admin update requests."""
    update_type: str = Field(..., description="Type of update to perform")
    force: Optional[bool] = Field(False, description="Force update even if recently updated")
    
    @field_validator('update_type')
    @classmethod
    def validate_update_type(cls, v):
        v = sanitize_string(v)
        valid_types = ['teams', 'players', 'games', 'all']
        if v not in valid_types:
            raise ValueError(f"Invalid update type: {v}. Must be one of {valid_types}")
        return v

class PaginationSchema(BaseModel):
    """Schema for pagination parameters."""
    page: int = Field(1, ge=1, le=1000, description="Page number")
    per_page: int = Field(20, ge=1, le=1000, description="Items per page")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        return self.per_page
