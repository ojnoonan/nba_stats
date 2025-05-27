import asyncio
import functools
import logging
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, TypedDict, Union, cast

import aiohttp
import requests
import urllib3
from nba_api.stats.endpoints import (
    boxscoretraditionalv2,
    commonallplayers,
    commonteamroster,
    leaguestandingsv3,
    scoreboardv2,
    teamgamelog,
    teaminfocommon,
)
from nba_api.stats.library import http
from nba_api.stats.static import teams
from requests.exceptions import RequestException, Timeout
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.exceptions import TaskCancelledError
from app.models.models import (
    Components,
    ComponentStatus,
    DataUpdateStatus,
    Game,
    Player,
    PlayerGameStats,
    Team,
)
from app.utils.date_utils import parse_nba_date
from app.utils.status_utils import (
    finalize_component,
    handle_component_error,
    initialize_status,
    update_progress,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Configure NBA API
http.STATS_HEADERS["User-Agent"] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

# Turn off SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants for API headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}


class NBADataService:
    """Service for handling NBA data updates"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.headers = DEFAULT_HEADERS.copy()
        self.verify_ssl = not os.environ.get("RUNNING_IN_CONTAINER", False)
        self._status: Optional[DataUpdateStatus] = None
        self._status_lock = asyncio.Lock()

    def _get_current_season(self) -> str:
        """Get the current NBA season string"""
        today = datetime.now()
        if today.month >= 10:  # NBA season starts in October
            return f"{today.year}-{str(today.year + 1)[-2:]}"
        return f"{today.year - 1}-{str(today.year)[-2:]}"

    async def _safe_commit(self) -> None:
        """Safely commit database changes"""
        try:
            await self.db.commit()
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            await self._safe_rollback()
            raise

    async def _safe_rollback(self) -> None:
        """Safely rollback database changes"""
        try:
            await self.db.rollback()
        except Exception as e:
            logger.error(f"Error rolling back changes: {e}")

    def _parse_int(self, value: Any) -> Optional[int]:
        """Safely parse an integer value with improved validation"""
        if value is None or value == "":
            return None

        try:
            # Handle bool explicitly since it's a subclass of int
            if isinstance(value, bool):
                return 1 if value else 0

            # Handle numeric types
            if isinstance(value, (int, float)):
                # Validate range and convert NaN/Inf
                if not (float("-inf") < float(value) < float("inf")):
                    return None
                return int(value)

            if isinstance(value, str):
                # Remove whitespace and validate
                cleaned = value.strip()
                if not cleaned or cleaned.lower() in ("na", "n/a", "null", "none"):
                    return None

                # Try integer first
                try:
                    return int(cleaned)
                except ValueError:
                    # Try float then convert to int, but validate first
                    try:
                        float_val = float(cleaned)
                        if not (float("-inf") < float_val < float("inf")):
                            return None
                        return int(float_val)
                    except ValueError:
                        return None

        except (ValueError, TypeError, OverflowError) as e:
            logger.warning(
                f"Failed to parse integer from value: {repr(value)}, error: {str(e)}"
            )
            return None

    async def _check_cancellation(self) -> None:
        """Check if the current operation should be cancelled by querying the flag directly"""
        from sqlalchemy import select

        from app.models.models import DataUpdateStatus

        # Query only the cancellation flag to avoid lazy-loading
        stmt = select(DataUpdateStatus.cancellation_requested).filter_by(id=1)
        result = await self.db.execute(stmt)
        cancelled = result.scalar_one_or_none()
        if cancelled:
            logger.info("Operation cancelled by user request")
            raise TaskCancelledError("Operation cancelled by user request")

    async def _make_nba_request(self, endpoint_class: Any, **kwargs) -> Dict:
        """Make a request to the NBA API with proper error handling"""
        max_retries = 3
        base_delay = 2.0  # Increased from 1.0 to reduce rate limiting

        for attempt in range(max_retries):
            try:
                # Add a delay before each request to respect rate limits
                if attempt > 0:
                    await asyncio.sleep(base_delay * (2**attempt))
                else:
                    await asyncio.sleep(1.0)  # Always wait at least 1 second

                # Run sync endpoint call in thread
                endpoint = await asyncio.to_thread(endpoint_class, **kwargs)
                return await asyncio.to_thread(endpoint.get_dict)
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Too Many Requests" in error_str:
                    # Special handling for rate limit errors
                    delay = base_delay * (3**attempt) + random.uniform(
                        1, 3
                    )  # Longer delays for rate limits
                    logger.warning(
                        f"Rate limit hit (attempt {attempt + 1}/{max_retries}), waiting {delay:.1f}s: {e}"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)
                        continue

                if attempt == max_retries - 1:
                    raise

                delay = base_delay * (2**attempt) + random.uniform(0, 1)
                logger.warning(
                    f"NBA API request failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                await asyncio.sleep(delay)

        raise Exception("NBA API request failed after all retries")

    async def _get_status(self) -> Optional[DataUpdateStatus]:
        """Get or create status object with proper initialization"""
        async with self._status_lock:
            if self._status:
                return self._status

            # Try to get existing status
            stmt = sa_select(DataUpdateStatus)
            result = await self.db.execute(stmt)
            self._status = result.scalar_one_or_none()

            if not self._status:
                # Create new status if none exists
                self._status = DataUpdateStatus(
                    id=1,
                    is_updating=False,
                    cancellation_requested=False,
                    teams_updated=False,
                    players_updated=False,
                    games_updated=False,
                    teams_percent_complete=0,
                    players_percent_complete=0,
                    games_percent_complete=0,
                    current_phase=None,
                    current_detail=None,
                    components={},
                )
                self.db.add(self._status)
                await self._safe_commit()
                await self.db.refresh(self._status)

            return self._status

    async def _init_component(self, status: DataUpdateStatus, component: str) -> None:
        """Initialize component status"""
        if not isinstance(status.components, dict):
            status.components = {}

        if component not in status.components:
            status.components[component] = {}

        status.components[component].update(
            {
                "updated": False,
                "percent_complete": 0,
                "last_error": None,
                "start_time": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def update_team_players(self, team_id: Optional[int] = None) -> None:
        """Update player information for a specific team or all teams"""
        try:
            # Initialize update state using utility
            await initialize_status("players", self.db)

            # If no team_id provided, update all teams
            if team_id is None:
                team_ids = await self._get_all_team_ids()
                total_teams = len(team_ids)
                if total_teams == 0:
                    error_msg = "No teams found to update players"
                    logger.error(error_msg)
                    await handle_component_error("players", error_msg, self.db)
                    raise ValueError(error_msg)

                processed_teams = 0
                for current_team_id in team_ids:
                    await self._check_cancellation()
                    try:
                        await self._update_single_team_players(current_team_id)
                        processed_teams += 1
                        await update_progress(
                            "players", processed_teams, total_teams, self.db
                        )
                    except Exception as e:
                        error_msg = (
                            f"Error updating team {current_team_id} players: {str(e)}"
                        )
                        logger.error(error_msg)
                        await handle_component_error("players", error_msg, self.db)
                        raise
            else:
                # Update single team
                try:
                    await self._update_single_team_players(team_id)
                    await update_progress("players", 1, 1, self.db)
                except Exception as e:
                    error_msg = f"Error updating team {team_id} players: {str(e)}"
                    logger.error(error_msg)
                    await handle_component_error("players", error_msg, self.db)
                    raise

            # Finalize component on success
            await finalize_component("players", self.db)

        except TaskCancelledError:
            # Let cancellation propagate up
            raise
        except Exception as e:
            error_msg = f"Error updating players: {str(e)}"
            logger.error(error_msg)
            await handle_component_error("players", error_msg, self.db)
            raise

    async def _update_single_team_players(self, team_id: int) -> None:
        """Update players for a single team."""
        try:
            # Get team roster
            await self._check_cancellation()

            # Add a delay before making the roster request to respect rate limits
            await asyncio.sleep(2.0)  # 2 second delay between team roster requests

            try:
                # Fetch roster in thread to avoid blocking event loop
                roster = await asyncio.to_thread(
                    commonteamroster.CommonTeamRoster, team_id=str(team_id)
                )
                roster_dict = await asyncio.to_thread(roster.get_dict)

                if not roster_dict or "resultSets" not in roster_dict:
                    error_msg = f"Invalid roster response for team {team_id}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                player_data = roster_dict["resultSets"][0]["rowSet"]
            except Exception as e:
                error_msg = f"Failed to fetch roster for team {team_id}: {str(e)}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            total_players = len(player_data)
            processed_players = 0

            for player_row in player_data:
                await self._check_cancellation()
                current_player_id = None
                try:
                    current_player_id = int(
                        player_row[14]
                    )  # PLAYER_ID column (index 14)
                    player = await self._get_or_create_player(current_player_id)

                    if player:
                        # Update player info
                        await self._update_player_info(player, player_row)
                        processed_players += 1
                        await update_progress(
                            "players", processed_players, total_players, self.db
                        )

                except Exception as e:
                    error_msg = f"Error updating player {current_player_id}: {str(e)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            # Update team info
            team = (
                await self.db.execute(sa_select(Team).filter(Team.team_id == team_id))
            ).scalar_one_or_none()
            now = datetime.now(timezone.utc)
            if team:
                team.roster_loaded = True
                team.loading_progress = 100
                team.last_updated = now
                await self._safe_commit()

        except TaskCancelledError:
            raise
        except Exception as e:
            error_msg = f"Error updating team {team_id} players: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def update_games(self) -> None:
        """Update game information from NBA API"""
        try:
            # Initialize update state
            await initialize_status("games", self.db)

            await self._check_cancellation()

            # TODO: Implement game updates here
            # Placeholder for now - just complete successfully
            await update_progress("games", 1, 1, self.db)

            # Finalize on success
            await finalize_component("games", self.db)

        except TaskCancelledError:
            # Let cancellation propagate up
            raise
        except Exception as e:
            error_msg = f"Error in games update process: {str(e)}"
            logger.error(error_msg)
            await handle_component_error("games", error_msg, self.db)
            raise

    async def update_team_games(self, team_id: int) -> None:
        """Update game information for a specific team"""
        try:
            # Initialize update state
            await initialize_status("games", self.db)

            await self._check_cancellation()

            # Get games for this team
            stmt = select(Game).filter(
                (Game.home_team_id == team_id) | (Game.away_team_id == team_id)
            )
            result = await self.db.execute(stmt)
            team_games = result.scalars().all()

            if not team_games:
                logger.warning(f"No games found for team {team_id}")
                await update_progress("games", 1, 1, self.db)
                await finalize_component("games", self.db)
                return

            total_games = len(team_games)
            processed_games = 0

            for game in team_games:
                await self._check_cancellation()

                # Mark game as loaded and update timestamp
                game.is_loaded = True
                game.last_updated = datetime.now(timezone.utc)

                processed_games += 1
                await update_progress("games", processed_games, total_games, self.db)
                await self._safe_commit()

            # Update team games_loaded status
            team_stmt = select(Team).filter(Team.team_id == team_id)
            team_result = await self.db.execute(team_stmt)
            team = team_result.scalar_one_or_none()
            if team:
                team.games_loaded = True
                team.last_updated = datetime.now(timezone.utc)
                await self._safe_commit()

            # Finalize on success
            await finalize_component("games", self.db)

        except TaskCancelledError:
            # Let cancellation propagate up
            raise
        except Exception as e:
            error_msg = f"Error updating team {team_id} games: {str(e)}"
            logger.error(error_msg)
            await handle_component_error("games", error_msg, self.db)
            raise

    async def update_teams(self) -> None:
        """Update team information from NBA API"""
        try:
            # Initialize update state using utility
            await initialize_status("teams", self.db)

            await self._check_cancellation()

            # Get list of teams from NBA API with retries
            team_data = await self._fetch_team_data()
            team_ids = self._extract_team_ids(team_data)

            if not team_ids:
                error_msg = "No valid team IDs found in API response"
                logger.error(error_msg)
                await handle_component_error("teams", error_msg, self.db)
                raise ValueError(error_msg)

            total_teams = len(team_ids)
            processed_teams = 0

            # Process each team
            for team_id in team_ids:
                await self._check_cancellation()
                try:
                    await self._update_single_team(team_id)
                    processed_teams += 1
                    await update_progress(
                        "teams", processed_teams, total_teams, self.db
                    )
                except Exception as e:
                    error_msg = f"Error updating team {team_id}: {str(e)}"
                    logger.error(error_msg)
                    await handle_component_error("teams", error_msg, self.db)
                    raise ValueError(error_msg)

            # Finalize component on success
            await finalize_component("teams", self.db)

        except TaskCancelledError:
            # Let cancellation propagate up
            raise
        except Exception as e:
            error_msg = f"Error in team update process: {str(e)}"
            logger.error(error_msg)
            await handle_component_error("teams", error_msg, self.db)
            raise

    async def _get_or_create_player(self, player_id: int) -> Player:
        """Get or create a player record"""
        stmt = select(Player).filter_by(player_id=player_id)
        result = await self.db.execute(stmt)
        player = result.scalar_one_or_none()

        if not player:
            player = Player(player_id=player_id)
            self.db.add(player)
            await self._safe_commit()

        return player

    async def _get_or_create_team(
        self, team_id: int, name: str = None, abbreviation: str = None
    ) -> Team:
        """Get or create a team record"""
        stmt = select(Team).filter_by(team_id=team_id)
        result = await self.db.execute(stmt)
        team = result.scalar_one_or_none()

        if not team:
            # Create team with required fields
            team_name = name or f"Team {team_id}"  # Fallback name if none provided
            team_abbreviation = abbreviation or ""

            team = Team(team_id=team_id, name=team_name, abbreviation=team_abbreviation)
            self.db.add(team)
            await self._safe_commit()

        return team

    async def _update_player_info(self, player: Player, player_row: list) -> None:
        """Update player information"""
        player.full_name = str(player_row[3] or "")  # PLAYER column (index 3)
        player.first_name = str(player_row[3].split()[0] if player_row[3] else "")
        player.last_name = str(player_row[3].split()[-1] if player_row[3] else "")
        player.position = str(player_row[7] or "")  # POSITION column (index 7)
        player.jersey_number = str(player_row[6] or "")  # NUM column (index 6)
        player.is_active = True
        player.last_updated = datetime.now(timezone.utc)
        await self._safe_commit()

    async def _fetch_team_data(self) -> Any:
        """Fetch team data from NBA API"""
        # Use static teams data which is more reliable
        from nba_api.stats.static import teams as static_teams

        return static_teams.get_teams()

    def _extract_team_ids(self, team_data: Any) -> List[int]:
        """Extract team IDs from NBA API response"""
        if team_data and isinstance(team_data, list):
            # Using static teams data
            return [team["id"] for team in team_data if team.get("id")]
        return []

    async def _update_single_team(self, team_id: int) -> None:
        """Update information for a single team"""
        try:
            # Use static teams data which is more reliable and doesn't cause rate limiting
            from nba_api.stats.static import teams as static_teams

            # Get static teams data - this is a simple function call, no need for asyncio.to_thread
            static_team_data = static_teams.get_teams()

            # Find the team by ID
            team_info = None
            for static_team in static_team_data:
                if static_team["id"] == team_id:
                    team_info = static_team
                    break

            if not team_info:
                logger.warning(f"No static data found for team {team_id}")
                return

            # Pre-calculate name and abbreviation for team creation
            city = team_info.get("city", "") or ""
            nickname = team_info.get("nickname", "") or ""
            full_name = team_info.get("full_name", "") or ""

            # Use full_name if available, otherwise construct from city + nickname
            if full_name:
                team_name = full_name
            elif city and nickname:
                team_name = f"{city} {nickname}".strip()
            elif nickname:
                team_name = nickname
            elif city:
                team_name = city
            else:
                # Fallback to abbreviation or team ID if nothing else is available
                team_name = team_info.get("abbreviation", f"Team {team_id}")

            team_abbreviation = team_info.get("abbreviation", "") or ""

            # Get or create team with the required data
            team = await self._get_or_create_team(team_id, team_name, team_abbreviation)

            if team:
                # Update team data
                team.name = team_name
                team.abbreviation = team_abbreviation
                # Set default values for fields that aren't in static data
                # Don't check existing values to avoid lazy loading - just set defaults
                team.conference = ""
                team.division = ""
                team.is_active = True
                team.last_updated = datetime.now(timezone.utc)
                await self._safe_commit()

        except Exception as e:
            error_msg = f"Error updating team {team_id}: {str(e)}"
            logger.error(error_msg)
            raise

    async def update_game(self, game_id: str) -> None:
        """Update information for a single game"""
        try:
            # Initialize status
            await initialize_status("games", self.db)
            await update_progress("games", 0, 1, self.db)

            # Get game info with retries and timeout
            try:
                game_info = await asyncio.wait_for(
                    self._make_nba_request(
                        boxscoretraditionalv2.BoxScoreTraditionalV2, game_id=game_id
                    ),
                    timeout=settings.nba_api.timeout,
                )

                if not game_info.get("resultSets", [{}])[0].get("rowSet"):
                    logger.warning(f"No data returned for game {game_id}")
                    return

                # Update game with stats
                await self._update_game_stats(game_id, game_info)
                await update_progress("games", 1, 1, self.db)
                await finalize_component("games", self.db)

            except (asyncio.TimeoutError, Exception) as e:
                error_msg = f"Error updating game {game_id}: {str(e)}"
                logger.error(error_msg)
                await handle_component_error("games", error_msg, self.db)
                raise ValueError(error_msg)

        except Exception as e:
            error_msg = f"Error updating game {game_id}: {str(e)}"
            logger.error(error_msg)
            await handle_component_error("games", error_msg, self.db)
            raise ValueError(error_msg)

    async def _initialize_component_status(self, component: str) -> None:
        """Initialize component status - internal helper method"""
        await initialize_status(component, self.db)

    async def _finalize_component_update(self, component: str) -> None:
        """Finalize component update - internal helper method"""
        await finalize_component(component, self.db)

    async def _handle_component_error(self, component: str, error_msg: str) -> None:
        """Handle component error - internal helper method"""
        await handle_component_error(component, error_msg, self.db)

    async def _update_game_stats(self, game_id: str, game_info: dict) -> None:
        """Update game stats"""
        # Get game record
        stmt = select(Game).filter_by(game_id=game_id)
        result = await self.db.execute(stmt)
        game = result.scalar_one_or_none()
        if not game:
            return

        # Update game
        try:
            # Update game stats
            game.is_loaded = True
            game.last_updated = datetime.now(timezone.utc)

            player_stats = game_info["resultSets"][0]["rowSet"]
            for row in player_stats:
                player_id = row[4]  # PLAYER_ID

                stmt = select(PlayerGameStats).filter_by(
                    game_id=game_id, player_id=player_id
                )
                result = await self.db.execute(stmt)
                stats = result.scalar_one_or_none()

                if not stats:
                    stats = PlayerGameStats(
                        game_id=game_id, player_id=player_id, team_id=row[1]  # TEAM_ID
                    )
                    self.db.add(stats)

                # Update stats using correct field names from the model
                stats.minutes = str(row[8] or "")  # MIN
                stats.fgm = int(row[9] or 0)  # FGM
                stats.fga = int(row[10] or 0)  # FGA
                stats.fg_pct = float(row[11] or 0)  # FG_PCT
                stats.tpm = int(row[12] or 0)  # FG3M
                stats.tpa = int(row[13] or 0)  # FG3A
                stats.tp_pct = float(row[14] or 0)  # FG3_PCT
                stats.ftm = int(row[15] or 0)  # FTM
                stats.fta = int(row[16] or 0)  # FTA
                stats.ft_pct = float(row[17] or 0)  # FT_PCT
                stats.rebounds = int(row[18] or 0)  # REB
                stats.assists = int(row[19] or 0)  # AST
                stats.steals = int(row[20] or 0)  # STL
                stats.blocks = int(row[21] or 0)  # BLK
                stats.turnovers = int(row[22] or 0)  # TO
                stats.points = int(row[24] or 0)  # PTS

            await self._safe_commit()

        except Exception as e:
            error_msg = f"Error updating game stats for {game_id}: {str(e)}"
            logger.error(error_msg)
            await handle_component_error("games", error_msg, self.db)
            raise

    async def update_all_data(self) -> None:
        """Update all NBA data (teams, players, and games)"""
        try:
            await self._check_cancellation()
            await self.update_teams()

            await self._check_cancellation()
            await self.update_team_players()

            await self._check_cancellation()
            await self.update_games()

        except TaskCancelledError:
            raise  # Let the router handle cancellation cleanup
        except Exception as e:
            error_msg = f"Error in full update process: {str(e)}"
            logger.error(error_msg)
            raise

    async def _get_all_team_ids(self) -> List[int]:
        """Get all team IDs from the database"""
        stmt = select(Team.team_id)
        result = await self.db.execute(stmt)
        return [r[0] for r in result.fetchall()]
