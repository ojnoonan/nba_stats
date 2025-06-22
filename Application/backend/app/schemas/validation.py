"""
Input validation schemas for API endpoints.
Provides security through input validation and sanitization.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class UpdateRequestSchema(BaseModel):
    """Schema for data update requests."""
    update_types: Optional[List[str]] = Field(None, description="Types of data to update")
    force: Optional[bool] = Field(False, description="Force update even if recently updated")
    
    @validator('update_types')
    def validate_update_types(cls, v):
        if v is not None:
            valid_types = ['teams', 'players', 'games', 'all']
            for update_type in v:
                if update_type not in valid_types:
                    raise ValueError(f"Invalid update type: {update_type}. Must be one of {valid_types}")
        return v

class TeamIdSchema(BaseModel):
    """Schema for team ID validation."""
    team_id: int = Field(..., ge=1, le=9999, description="NBA team ID")

class PlayerIdSchema(BaseModel):
    """Schema for player ID validation."""
    player_id: int = Field(..., ge=1, le=999999, description="NBA player ID")

class GameIdSchema(BaseModel):
    """Schema for game ID validation."""
    game_id: str = Field(..., pattern=r'^\d{10}$', description="NBA game ID (10 digits)")

class SearchQuerySchema(BaseModel):
    """Schema for search queries."""
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Maximum number of results")
    
    @validator('query')
    def sanitize_query(cls, v):
        # Basic sanitization - remove potentially harmful characters
        import re
        # Allow only alphanumeric, spaces, hyphens, apostrophes
        sanitized = re.sub(r'[^a-zA-Z0-9\s\-\']', '', v)
        if len(sanitized.strip()) == 0:
            raise ValueError("Query cannot be empty after sanitization")
        return sanitized.strip()

class SeasonSchema(BaseModel):
    """Schema for season validation."""
    season: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}$', description="Season in YYYY-YY format")
    
    @validator('season')
    def validate_season(cls, v):
        if v is not None:
            year = int(v[:4])
            if year < 1946 or year > datetime.now().year + 1:
                raise ValueError("Invalid season year")
        return v
