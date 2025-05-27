"""
Response formatting utilities.
This module provides standardized response formatting functions
to ensure consistent API responses.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def format_team_response(team_obj: Any) -> Dict[str, Any]:
    """
    Format a team object for API response.

    Args:
        team_obj: Team database model object

    Returns:
        Dictionary with formatted team data
    """
    return {
        "team_id": team_obj.team_id,
        "name": team_obj.name,
        "abbreviation": team_obj.abbreviation,
        "conference": team_obj.conference,
        "division": team_obj.division,
        "wins": team_obj.wins or 0,
        "losses": team_obj.losses or 0,
        "logo_url": team_obj.logo_url,
        "roster_loaded": (
            team_obj.roster_loaded if hasattr(team_obj, "roster_loaded") else False
        ),
        "games_loaded": (
            team_obj.games_loaded if hasattr(team_obj, "games_loaded") else False
        ),
    }


def format_player_response(
    player_obj: Any, include_team: bool = False
) -> Dict[str, Any]:
    """
    Format a player object for API response.

    Args:
        player_obj: Player database model object
        include_team: Whether to include team data

    Returns:
        Dictionary with formatted player data
    """
    is_traded = player_obj.traded_date is not None

    player_data = {
        "player_id": player_obj.player_id,
        "full_name": player_obj.full_name,
        "first_name": player_obj.first_name,
        "last_name": player_obj.last_name,
        "current_team_id": player_obj.current_team_id,
        "position": player_obj.position,
        "jersey_number": player_obj.jersey_number,
        "is_active": player_obj.is_active,
        "is_loaded": player_obj.is_loaded,
        "headshot_url": player_obj.headshot_url,
        "is_traded": is_traded,
        "is_traded_flag": is_traded,  # Add this for backward compatibility with existing tests
        "last_updated": player_obj.last_updated,  # Add last_updated timestamp
    }

    if include_team and player_obj.team:
        player_data["team"] = format_team_response(player_obj.team)

    return player_data


def format_game_response(game_obj: Any, include_teams: bool = True) -> Dict[str, Any]:
    """
    Format a game object for API response.

    Args:
        game_obj: Game database model object
        include_teams: Whether to include team data

    Returns:
        Dictionary with formatted game data
    """
    # Handle None season_year by providing a default value
    season_year = game_obj.season_year
    if season_year is None:
        # Generate a default season year based on the game date
        game_date = game_obj.game_date_utc
        if game_date:
            # NBA season spans calendar years, season starts in October
            # If month is Oct-Dec, it's the start of season (e.g., 2024-25)
            # If month is Jan-Sep, it's the end of season (e.g., 2024-25 for 2025 games)
            year = game_date.year
            if game_date.month >= 10:  # October or later
                season_year = f"{year}-{str(year + 1)[2:]}"
            else:  # January through September
                season_year = f"{year - 1}-{str(year)[2:]}"
        else:
            # Fallback to current season if no game date
            from datetime import datetime

            current_year = datetime.now().year
            season_year = f"{current_year}-{str(current_year + 1)[2:]}"

    game_data = {
        "game_id": game_obj.game_id,
        "game_date_utc": game_obj.game_date_utc,
        "home_team_id": game_obj.home_team_id,
        "away_team_id": game_obj.away_team_id,
        "home_score": game_obj.home_score,
        "away_score": game_obj.away_score,
        "status": game_obj.status,
        "season_year": season_year,
        "playoff_round": game_obj.playoff_round,
        "is_loaded": game_obj.is_loaded if hasattr(game_obj, "is_loaded") else False,
        "last_updated": (
            game_obj.last_updated if hasattr(game_obj, "last_updated") else None
        ),
    }

    if include_teams:
        if hasattr(game_obj, "home_team") and game_obj.home_team:
            game_data["home_team"] = format_team_response(game_obj.home_team)
        if hasattr(game_obj, "away_team") and game_obj.away_team:
            game_data["away_team"] = format_team_response(game_obj.away_team)

    return game_data


def format_player_stats_response(stats_obj: Any) -> Dict[str, Any]:
    """
    Format player game stats for API response.

    Args:
        stats_obj: PlayerGameStats database model object

    Returns:
        Dictionary with formatted stats data
    """
    # Make a base dict with all the stats data
    result = {
        "player_id": stats_obj.player_id,
        "game_id": stats_obj.game_id,
        "team_id": stats_obj.team_id,
        "minutes": stats_obj.minutes,
        "points": stats_obj.points,
        "rebounds": stats_obj.rebounds,
        "assists": stats_obj.assists,
        "steals": stats_obj.steals,
        "blocks": stats_obj.blocks,
        "fgm": stats_obj.fgm,
        "fga": stats_obj.fga,
        "fg_pct": stats_obj.fg_pct,
        "tpm": stats_obj.tpm,
        "tpa": stats_obj.tpa,
        "tp_pct": stats_obj.tp_pct,
        "ftm": stats_obj.ftm,
        "fta": stats_obj.fta,
        "ft_pct": stats_obj.ft_pct,
        "turnovers": stats_obj.turnovers,
        "fouls": stats_obj.fouls,
        "plus_minus": stats_obj.plus_minus,
        # Add additional fields that might be used in responses
        "player_name": getattr(stats_obj, "player_name", None),
        "game_date_utc": getattr(stats_obj, "game_date_utc", None),
    }

    # Add stat_id if it exists (it might not in older databases or tests)
    if hasattr(stats_obj, "stat_id"):
        result["stat_id"] = stats_obj.stat_id

    return result


def calculate_team_stats(team_obj: Any) -> Dict[str, Any]:
    """
    Calculate and format extended team statistics.

    Args:
        team_obj: Team database model object

    Returns:
        Dictionary with calculated team statistics
    """
    # Calculate winning percentage with null safety
    wins = team_obj.wins or 0
    losses = team_obj.losses or 0
    win_percentage = 0.0

    if wins + losses > 0:
        win_percentage = wins / (wins + losses)

    # Get extended stats
    return {
        "team_id": team_obj.team_id,
        "name": team_obj.name,
        "abbreviation": team_obj.abbreviation,
        "wins": wins,
        "losses": losses,
        "win_percentage": win_percentage,
        "conference": team_obj.conference,
        "division": team_obj.division,
    }
