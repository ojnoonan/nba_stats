import aiohttp
import asyncio
from datetime import datetime, timedelta
import time
import logging
import random
import os
from sqlalchemy.orm import Session
from nba_api.stats.endpoints import scoreboardv2, commonteamroster, teaminfocommon, boxscoretraditionalv2, leaguestandingsv3, teamgamelog
from nba_api.stats.static import teams
from nba_api.stats.library import http
from app.core.config import settings
from app.models.models import Team, Player, Game, PlayerGameStats, DataUpdateStatus
from requests.exceptions import Timeout, RequestException
import requests
import sys
import urllib3

# Configure logging
logger = logging.getLogger(__name__)

# Configure NBA API with settings
http.STATS_HEADERS['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
# Set timeout via environment variable or direct setting
os.environ['NBA_API_TIMEOUT'] = str(settings.request_timeout)
urllib3.disable_warnings()
# Set SSL verification to False
os.environ['PYTHONHTTPSVERIFY'] = '0'

# If running in a container, set SSL verification to False
os.environ['PYTHONHTTPSVERIFY'] = '0'

def parse_nba_date(date_str: str) -> datetime:
    """Parse date string from NBA API in various formats"""
    formats = [
        '%Y-%m-%d',  # Standard format
        '%b %d, %Y',  # Format like 'Feb 10, 2025'
        '%B %d, %Y',  # Format like 'February 10, 2025'
        '%Y-%m-%dT%H:%M:%S'  # ISO format
    ]
    
    # Convert month name to title case for consistent parsing
    if isinstance(date_str, str):
        for month in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']:
            date_str = date_str.replace(month, month.title())
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    raise ValueError(f"Could not parse date string: {date_str}")

class NBADataService:
    def __init__(self, db: Session):
        self.db = db
        self._request_timeout = settings.request_timeout
        self._read_timeout = settings.read_timeout
        self._connect_timeout = settings.connect_timeout
        self._last_request_time = 0
        self._base_delay = settings.nba_api_rate_limit
        self._max_retries = settings.max_retries
        self._max_backoff = 30
        
        # Configure proxy settings (use system proxy if available)
        self._proxies = {
            'http': os.environ.get('HTTP_PROXY'),
            'https': os.environ.get('HTTPS_PROXY')
        }
        
        # Define standard headers with varied User-Agents
        self._user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        
        self.headers = {
            'Host': 'stats.nba.com',
            'User-Agent': random.choice(self._user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nba.com/',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }

    async def _enforce_rate_limit(self):
        """Enforce rate limiting between API requests"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._base_delay:
            delay = self._base_delay - time_since_last + random.uniform(0.1, 0.5)  # Add jitter
            logger.info(f"Rate limiting: waiting {delay:.2f} seconds")
            await asyncio.sleep(delay)
            
        self._last_request_time = time.time()

    async def _make_nba_request(self, endpoint_class, **params):
        """Make request using nba_api endpoints with proper error handling and rate limiting"""
        retry_count = 0
        current_delay = self._base_delay
        last_error = None

        while retry_count <= self._max_retries:
            try:
                # Enforce rate limiting before making request
                await self._enforce_rate_limit()
                
                # Rotate User-Agent on each retry
                self.headers['User-Agent'] = random.choice(self._user_agents)
                
                # Configure endpoint with timeouts and proxy
                endpoint = endpoint_class(
                    timeout=(self._connect_timeout, self._read_timeout),
                    headers=self.headers,
                    proxy=self._proxies.get('https'),
                    **params
                )
                
                try:
                    # Get JSON string and parse it
                    json_str = endpoint.get_json()
                    if isinstance(json_str, str):
                        import json
                        data = json.loads(json_str)
                    else:
                        data = json_str
                    
                    # Reset delay on successful request
                    current_delay = self._base_delay
                    return data
                    
                except requests.exceptions.HTTPError as he:
                    last_error = he
                    if he.response.status_code == 429:  # Too Many Requests
                        retry_after = int(he.response.headers.get('Retry-After', current_delay))
                        logger.warning(f"Rate limit exceeded. Waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                    else:
                        logger.warning(f"HTTP error (attempt {retry_count + 1}/{self._max_retries}): {str(he)}")
                        await asyncio.sleep(current_delay)
                    current_delay = min(current_delay * 2, self._max_backoff)
                    retry_count += 1
                    continue
                    
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    last_error = e
                    logger.warning(f"Request failed (attempt {retry_count + 1}/{self._max_retries}): {str(e)}")
                    await asyncio.sleep(current_delay)
                    current_delay = min(current_delay * 2, self._max_backoff)
                    retry_count += 1
                    continue
                
            except Exception as e:
                last_error = e
                logger.warning(f"Request failed (attempt {retry_count + 1}/{self._max_retries}): {str(e)}")
                await asyncio.sleep(current_delay)
                current_delay = min(current_delay * 2, self._max_backoff)
                retry_count += 1
                continue

        logger.error(f"Max retries exceeded. Last error: {str(last_error)}")
        if last_error:
            raise last_error
        else:
            raise Exception("Max retries exceeded with no error captured")

    def _parse_int(self, value, default=0):
        """Safely parse an integer value"""
        try:
            if isinstance(value, str):
                # Remove any non-digit characters and convert
                clean_value = ''.join(filter(str.isdigit, value))
                return int(clean_value) if clean_value else default
            elif isinstance(value, (int, float)):
                return int(value)
            return default
        except (ValueError, TypeError):
            return default

    def _safe_int(self, value):
        """Safely convert a value to integer, handling float strings"""
        if value is None or value == '':
            return 0
        try:
            # First try direct int conversion
            return int(value)
        except ValueError:
            try:
                # If that fails, try converting through float first
                return int(float(value))
            except (ValueError, TypeError):
                return 0

    def _get_current_season(self):
        """Get the current NBA season string based on date"""
        today = datetime.now()
        # NBA regular season typically ends in April
        # Use previous season until the new season starts (typically October)
        if today.month >= 10:  # New season starts in October
            return f"{today.year}-{str(today.year+1)[2:]}"
        else:  # Use previous season until new season starts
            return f"{today.year-1}-{str(today.year)[2:]}"

    async def _make_api_request(self, endpoint, params=None):
        """Legacy method replaced by _make_nba_request"""
        try:
            # Map string endpoints to NBA API endpoint classes
            endpoint_mapping = {
                'leaguestandingsv3': leaguestandingsv3.LeagueStandingsV3,
                'boxscoretraditionalv2': boxscoretraditionalv2.BoxScoreTraditionalV2,
                'teamgamelog': teamgamelog.TeamGameLog,  # Fix incorrect mapping
                'commonteamroster': commonteamroster.CommonTeamRoster  # Add missing endpoint
            }
            
            endpoint_class = endpoint_mapping.get(endpoint)
            if endpoint_class:
                return await self._make_nba_request(endpoint_class, **(params or {}))
            else:
                raise ValueError(f"Unknown endpoint: {endpoint}")
                
        except Exception as e:
            logger.error(f"Error in legacy _make_api_request: {str(e)}")
            raise

    async def update_games(self):
        """Update games and player statistics by fetching complete season data for all teams"""
        try:
            current_season = self._get_current_season()
            logger.info(f"Updating games for season: {current_season}")
            
            # First update existing games in the database that need stats
            games_needing_stats = self.db.query(Game).filter(
                Game.status == 'Completed',
                ~Game.game_id.in_(
                    self.db.query(PlayerGameStats.game_id).distinct()
                )
            ).all()
            
            logger.info(f"Found {len(games_needing_stats)} completed games that need stats")
            
            for game in games_needing_stats:
                try:
                    logger.info(f"Processing historical game {game.game_id}")
                    await self._process_game(getattr(game, 'game_id'), {
                        'GAME_ID': getattr(game, 'game_id'),
                        'GAME_DATE': game.game_date_utc.strftime("%Y-%m-%d"),
                        'HOME_TEAM_ID': getattr(game, 'home_team_id'),
                        'AWAY_TEAM_ID': getattr(game, 'away_team_id')
                    }, current_season)
                except Exception as e:
                    game_id_str = getattr(game, 'game_id', 'unknown') if 'game' in locals() else 'unknown'
                    logger.error(f"Error processing historical game {game_id_str}: {str(e)}")
                    continue
            
            # Now fetch complete season data for all teams using TeamGameLog
            # Get all teams from the database
            teams = self.db.query(Team).all()
            logger.info(f"Fetching complete season games for {len(teams)} teams")
            
            processed_game_ids = set()  # Track processed games to avoid duplicates
            total_teams = len(teams)
            
            for team_index, team in enumerate(teams):
                try:
                    logger.info(f"Processing team {team.team_id} ({team.name}) - {team_index + 1}/{total_teams}")
                    
                    # Use the proper TeamGameLog endpoint to get all games for this team
                    schedule_data = await self._make_nba_request(
                        teamgamelog.TeamGameLog,
                        team_id=team.team_id,
                        season=current_season,
                        season_type_all_star="Regular Season"
                    )

                    if not schedule_data or 'resultSets' not in schedule_data:
                        logger.warning(f"No schedule data found for team {team.team_id}")
                        continue

                    games_set = schedule_data['resultSets'][0]
                    team_games = games_set.get('rowSet', [])
                    logger.info(f"Found {len(team_games)} games for team {team.name}")

                    for game_row in team_games:
                        game_id = 'unknown'  # Initialize for error handling
                        try:
                            game_id = str(game_row[games_set['headers'].index('Game_ID')])
                            
                            # Skip if we've already processed this game from another team
                            if game_id in processed_game_ids:
                                continue
                                
                            processed_game_ids.add(game_id)
                            game_date = game_row[games_set['headers'].index('GAME_DATE')]
                            
                            # Process game - this will create/update the game record and get full stats
                            await self._process_game(game_id, {
                                'GAME_ID': game_id,
                                'GAME_DATE': game_date,
                                'TEAM_ID': team.team_id
                            }, current_season)

                            # Small delay to avoid overwhelming the API
                            await asyncio.sleep(0.5)

                        except Exception as e:
                            logger.error(f"Error processing game {game_id} for team {team.team_id}: {str(e)}")
                            continue

                    # Delay between teams to be respectful to the API
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error fetching games for team {team.team_id}: {str(e)}")
                    continue
            
            logger.info(f"Completed processing {len(processed_game_ids)} unique games for season {current_season}")
            
            # Fix any past games that are still marked as 'Upcoming'
            await self.fix_upcoming_past_games()
                
        except Exception as e:
            logger.error(f"Error in update_games: {str(e)}")
            raise

    async def update_teams(self):
        """Update team information in the database"""
        try:
            # First reset all teams' loading flags
            self.db.query(Team).update({
                "roster_loaded": False,
                "games_loaded": False,
                "loading_progress": 0
            })
            self.db.commit()

            nba_teams = teams.get_teams()
            logger.info(f"Found {len(nba_teams)} teams to update")
            
            try:
                current_season = self._get_current_season()
                logger.info(f"Fetching standings for season: {current_season}")
                
                # Get team standings using leaguestandingsv3 endpoint
                standings = await self._make_nba_request(
                    leaguestandingsv3.LeagueStandingsV3,
                    season=current_season.split('-')[0]  # Use first year of season
                )
                
                if not standings or 'resultSets' not in standings:
                    logger.error("Invalid standings data format")
                    raise Exception("Invalid standings data format")

                standings_data = standings['resultSets'][0]
                headers = {h.lower(): i for i, h in enumerate(standings_data['headers'])}
                
                rows = standings_data['rowSet']
                if not rows:
                    logger.warning("No standings data found")
                    return
                    
                # Create a lookup table for team IDs to standings
                standings_lookup = {}
                
                for row in rows:
                    try:
                        team_id = str(row[headers['teamid']])
                        wins = self._parse_int(row[headers['wins']])
                        losses = self._parse_int(row[headers['losses']])
                        
                        standings_lookup[team_id] = {
                            'wins': wins,
                            'losses': losses,
                            'season': current_season
                        }
                        logger.info(f"Found standings for team {team_id}: {wins}W-{losses}L (Season: {current_season})")
                    except Exception as e:
                        logger.error(f"Error parsing standings row: {str(e)}. Row data: {row}")
                        continue

                # Update teams with standings data
                for team_info in nba_teams:
                    try:
                        team_id = str(team_info['id'])
                        team_standings = standings_lookup.get(team_id)
                        
                        if team_standings is None:
                            logger.warning(f"No standings found for team {team_info['full_name']} (ID: {team_id})")
                            continue

                        team = self.db.merge(Team(
                            team_id=team_info['id'],
                            name=team_info['full_name'],
                            abbreviation=team_info['abbreviation'],
                            conference=team_info.get('conference', ''),
                            division=team_info.get('division', ''),
                            wins=team_standings['wins'],
                            losses=team_standings['losses'],
                            logo_url=f"https://cdn.nba.com/logos/nba/{team_info['id']}/global/L/logo.svg",
                            last_updated=datetime.utcnow()
                        ))
                        
                        self.db.commit()
                        logger.info(f"Updated team: {team_info['full_name']} ({team_standings['wins']}W-{team_standings['losses']}L)")
                        
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        self.db.rollback()
                        logger.error(f"Error updating team {team_info['full_name']}: {str(e)}")
                        continue
                
            except Exception as e:
                logger.error(f"Error getting standings data: {str(e)}")
                raise
                    
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in update_teams: {str(e)}")
            raise

    async def update_team_players(self, team_id: int):
        """Update players for a specific team"""
        try:
            # Reset team's loading status
            team = self.db.query(Team).filter_by(team_id=team_id).first()
            if team:
                setattr(team, 'loading_progress', 0)
                setattr(team, 'roster_loaded', False)
                setattr(team, 'games_loaded', False)  # Reset games loaded status
                self.db.commit()

            # Use commonteamroster endpoint with proper NBA API class
            roster_data = await self._make_nba_request(
                commonteamroster.CommonTeamRoster,
                team_id=team_id,
                season=self._get_current_season()
            )
            
            if not roster_data or 'resultSets' not in roster_data or not roster_data['resultSets']:
                logger.error(f"Invalid roster data format for team {team_id}")
                return

            # Rest of the existing function...
            roster = roster_data['resultSets'][0]
            rows = roster.get('rowSet', [])
            if not rows:
                logger.warning(f"No roster data found for team {team_id}")
                return
            
            total_players = len(rows)
            processed_players = 0
            
            # Create header mapping and validate
            headers = {h.upper(): i for i, h in enumerate(roster.get('headers', []))}
            required_columns = {'PLAYER', 'NUM', 'POSITION', 'PLAYER_ID'}
            if not all(col in headers for col in required_columns):
                logger.error(f"Missing required columns in roster data for team {team_id}")
                return
                
            for player_data in rows:
                try:
                    if len(player_data) <= max(headers.values()):
                        logger.warning(f"Insufficient player data for team {team_id}: {player_data}")
                        continue

                    # Extract and validate player info
                    raw_player_id = player_data[headers['PLAYER_ID']]
                    if not raw_player_id:
                        logger.warning(f"Missing player ID in data: {player_data}")
                        continue
                        
                    player_id = self._parse_int(raw_player_id)
                    if not player_id:
                        logger.warning(f"Invalid player ID format: {raw_player_id}")
                        continue

                    # Process player data
                    player_name = str(player_data[headers['PLAYER']]).strip()
                    name_parts = player_name.split(maxsplit=1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ""

                    raw_jersey = str(player_data[headers['NUM']]).strip() if player_data[headers['NUM']] else None
                    jersey = ''.join(filter(str.isdigit, raw_jersey)) if raw_jersey else None

                    raw_position = str(player_data[headers['POSITION']]).strip() if player_data[headers['POSITION']] else None
                    valid_positions = {'G', 'F', 'C', 'G-F', 'F-G', 'F-C', 'C-F'}
                    position = raw_position if raw_position in valid_positions else None

                    # Update or create player
                    existing_player = self.db.query(Player).filter_by(player_id=player_id).first()
                    
                    # Generate new headshot URL
                    new_headshot_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"
                    
                    # Preserve existing headshot if new one doesn't work and existing one exists
                    headshot_url_to_use = new_headshot_url
                    if existing_player and getattr(existing_player, 'headshot_url', None):
                        # For now, always use the new URL structure but this preserves the logic for fallback
                        headshot_url_to_use = new_headshot_url
                    
                    if existing_player and getattr(existing_player, 'current_team_id', None) != team_id and getattr(existing_player, 'current_team_id', None) is not None:
                        player = self.db.merge(Player(
                            player_id=player_id,
                            full_name=player_name,
                            first_name=first_name,
                            last_name=last_name,
                            current_team_id=team_id,
                            previous_team_id=existing_player.current_team_id,
                            traded_date=datetime.utcnow(),
                            jersey_number=jersey,
                            position=position,
                            is_active=True,
                            headshot_url=headshot_url_to_use,
                            last_updated=datetime.utcnow()
                        ))
                    else:
                        player = self.db.merge(Player(
                            player_id=player_id,
                            full_name=player_name,
                            first_name=first_name,
                            last_name=last_name,
                            current_team_id=team_id,
                            jersey_number=jersey,
                            position=position,
                            is_active=True,
                            headshot_url=headshot_url_to_use,
                            last_updated=datetime.utcnow()
                        ))
                    
                    # Update progress (but don't commit on every player)
                    processed_players += 1
                    if team and processed_players % 5 == 0:  # Update progress every 5 players
                        setattr(team, 'loading_progress', int((processed_players / total_players) * 100))
                        self.db.commit()
                        
                    # Reduced sleep time to avoid excessive delays
                    await asyncio.sleep(0.2)
                        
                except Exception as e:
                    self.db.rollback()
                    logger.error(f"Error updating player data: {str(e)}")
                    continue
            
            # Final commit to ensure all player data is saved
            self.db.commit()
            
            # Mark team roster as loaded and update progress
            if team:
                setattr(team, 'roster_loaded', True)
                setattr(team, 'loading_progress', 100)  # Set to 100% when roster is loaded
                self.db.commit()

            # Note: Games are updated separately in the games phase
            # This prevents the players phase from getting stuck processing all games
                    
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating players for team {team_id}: {str(e)}")
            raise

    async def update_team_games(self, team_id: int):
        """Update games for a specific team"""
        try:
            team = self.db.query(Team).filter_by(team_id=team_id).first()
            if not team:
                return

            # Get today's date in EST (NBA's timezone)
            today = datetime.now() - timedelta(hours=4)
            season = self._get_current_season()
            
            try:
                # Use the proper TeamGameLog endpoint
                schedule_data = await self._make_nba_request(
                    teamgamelog.TeamGameLog,
                    team_id=team_id,
                    season=season,
                    season_type_all_star="Regular Season"
                )

                if not schedule_data or 'resultSets' not in schedule_data:
                    logger.warning(f"No schedule data found for team {team_id}")
                    return

                games_set = schedule_data['resultSets'][0]
                total_games = len(games_set.get('rowSet', []))
                processed_games = 0

                for game_row in games_set.get('rowSet', []):
                    game_id = 'unknown'  # Initialize for error handling
                    try:
                        game_id = str(game_row[games_set['headers'].index('Game_ID')])
                        game_date = game_row[games_set['headers'].index('GAME_DATE')]
                        
                        # Process game
                        await self._process_game(game_id, {
                            'GAME_ID': game_id,
                            'GAME_DATE': game_date,
                            'TEAM_ID': team_id
                        }, season)

                        # Update progress
                        processed_games += 1
                        if team:
                            # Calculate progress (50-100% range for games)
                            games_progress = int((processed_games / total_games) * 50)
                            setattr(team, 'loading_progress', 50 + games_progress)  # Add to base 50% from roster loading
                            self.db.commit()

                        await asyncio.sleep(1)

                    except Exception as e:
                        logger.error(f"Error processing game {game_id}: {str(e)}")
                        continue

                # Mark games as loaded
                if team:
                    setattr(team, 'games_loaded', True)
                    setattr(team, 'loading_progress', 100)
                    self.db.commit()

            except Exception as e:
                logger.error(f"Error fetching games for team {team_id}: {str(e)}")
                raise

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating games for team {team_id}: {str(e)}")
            raise

    async def update_all_data(self):
        """Update all NBA data in the database"""
        try:
            # Get existing status record or create new one
            status = self.db.query(DataUpdateStatus).first()
            if not status:
                status = DataUpdateStatus()
                self.db.add(status)
            
            # Prevent updates if initial load is in progress
            if getattr(status, 'is_updating', False) and getattr(status, 'current_phase', None) in ['teams', 'players', 'games']:
                logger.info("Initial data load in progress, skipping regular update")
                return False

            # Check if this is initial data load
            team_count = self.db.query(Team).count()
            is_initial_load = team_count == 0

            if getattr(status, 'is_updating', False) and not is_initial_load:
                logger.warning("Update already in progress")
                return False

            # Reset status flags
            setattr(status, 'is_updating', True)
            setattr(status, 'current_phase', 'cleanup')
            setattr(status, 'last_error', None)
            setattr(status, 'last_error_time', None)
            setattr(status, 'teams_updated', False)
            setattr(status, 'players_updated', False)
            setattr(status, 'games_updated', False)
            self.db.commit()
            
            try:
                # First clean up old season data
                if not is_initial_load:
                    await self.cleanup_old_seasons()
                
                # Update teams
                setattr(status, 'current_phase', 'teams')
                self.db.commit()
                await self.update_teams()
                setattr(status, 'teams_updated', True)
                self.db.commit()

                # Update players for each team
                setattr(status, 'current_phase', 'players')
                self.db.commit()
                
                teams = self.db.query(Team).all()
                for team in teams:
                    await self.update_team_players(getattr(team, 'team_id'))
                
                # Fix headshot URLs for free agents after processing all teams
                await self.fix_free_agent_headshots()
                
                setattr(status, 'players_updated', True)
                
                # Update games and stats
                setattr(status, 'current_phase', 'games')
                self.db.commit()
                await self.update_games()
                setattr(status, 'games_updated', True)
                
                # Fix free agent team assignments after processing all games
                await self.fix_free_agent_teams()
                
                # Update the final status
                setattr(status, 'current_phase', None)
                setattr(status, 'last_successful_update', datetime.utcnow())
                # Don't set next_scheduled_update here - let the scheduler handle it
                setattr(status, 'is_updating', False)
                self.db.commit()
                return True
                
            except Exception as e:
                self.db.rollback()
                status = self.db.query(DataUpdateStatus).first()
                if status:
                    setattr(status, 'last_error', str(e))
                    setattr(status, 'last_error_time', datetime.utcnow())
                    setattr(status, 'is_updating', False)
                    self.db.commit()
                raise e
                
        except Exception as e:
            try:
                status = self.db.query(DataUpdateStatus).first()
                if status:
                    setattr(status, 'is_updating', False)
                    self.db.commit()
            except:
                pass
            raise e

    async def _process_game(self, game_id: str, game_data: dict, season: str):
        """Process a single game and its player statistics"""
        try:
            # NBA API expects 10-digit game IDs, pad with zeros if needed
            padded_game_id = game_id.zfill(10)
            logger.info(f"Processing game {game_id} (padded: {padded_game_id})")
            
            # First check if the game exists and if it needs updating
            existing_game = self.db.query(Game).filter_by(game_id=game_id).first()
            if existing_game and getattr(existing_game, 'status', None) == 'Completed':
                # Skip if game is already completed and has complete stats (at least 20 players)
                existing_stats_count = self.db.query(PlayerGameStats).filter_by(game_id=game_id).count()
                if existing_stats_count >= 20:
                    logger.info(f"Skipping game {game_id} - already completed with complete stats ({existing_stats_count} players)")
                    return
                elif existing_stats_count > 0:
                    logger.info(f"Game {game_id} has incomplete stats ({existing_stats_count} players), will reprocess to get complete data")
            
            # Parse the game date using our flexible parser
            try:
                game_date_utc = parse_nba_date(game_data['GAME_DATE'])
            except ValueError as e:
                logger.error(f"Could not parse game date '{game_data['GAME_DATE']}' for game {game_id}: {str(e)}")
                return
            
            # Get box score data
            try:
                box_score = await self._make_nba_request(
                    boxscoretraditionalv2.BoxScoreTraditionalV2,
                    game_id=padded_game_id
                )
            except Exception as e:
                logger.error(f"Error fetching box score for game {game_id}: {str(e)}")
                return
                
            if not box_score:
                logger.warning(f"No box score data found for game {game_id}")
                return
                
            # Handle both resultSet and resultSets formats
            result_sets = box_score.get('resultSets', box_score.get('resultSet', []))
            if not result_sets:
                logger.warning(f"No result sets found in box score for game {game_id}")
                return

            # Find team stats first
            team_stats_set = next((rs for rs in result_sets if rs['name'] == 'TeamStats'), None)
            player_stats_set = next((rs for rs in result_sets if rs['name'] == 'PlayerStats'), None)
            
            # Create or update game record with available data
            home_team_id = game_data.get('HOME_TEAM_ID')
            away_team_id = game_data.get('AWAY_TEAM_ID')
            
            # If team IDs weren't provided, try to get them from box score
            if home_team_id is None or away_team_id is None:
                game_summary = next((rs for rs in result_sets if rs['name'] == 'GameSummary'), None)
                if game_summary and game_summary.get('rowSet'):
                    summary_headers = {h: i for i, h in enumerate(game_summary['headers'])}
                    summary_row = game_summary['rowSet'][0]
                    home_team_id = self._safe_int(summary_row[summary_headers['HOME_TEAM_ID']])
                    away_team_id = self._safe_int(summary_row[summary_headers['VISITOR_TEAM_ID']])
                elif team_stats_set and team_stats_set.get('rowSet'):
                    team_headers = {h: i for i, h in enumerate(team_stats_set['headers'])}
                    team1_id = self._safe_int(team_stats_set['rowSet'][0][team_headers['TEAM_ID']])
                    team2_id = self._safe_int(team_stats_set['rowSet'][1][team_headers['TEAM_ID']])
                    home_team_id = team1_id  # Assume first team is home team
                    away_team_id = team2_id
            
            if home_team_id is None or away_team_id is None:
                logger.error(f"Could not determine team IDs for game {game_id}")
                return

            # Determine if this is a playoff game and which round
            playoff_round = None
            if len(game_id) >= 2:
                game_type = game_id[0]  # First digit indicates game type
                if game_type == "4":  # Playoff game
                    round_num = int(game_id[1])  # Second digit indicates round
                    playoff_round = {
                        1: "First Round",
                        2: "Conference Semifinals",
                        3: "Conference Finals",
                        4: "NBA Finals"
                    }.get(round_num)

            game = self.db.merge(Game(
                game_id=game_id,
                game_date_utc=game_date_utc,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                status='Upcoming',  # Default to upcoming
                season_year=season,
                playoff_round=playoff_round,
                is_loaded=False,  # Initially set to False, will be updated when data is fully loaded
                last_updated=datetime.utcnow()
            ))
            
            try:
                self.db.commit()
            except Exception as e:
                if "unique_game_matchup" in str(e):
                    logger.info(f"Game {game_id} already exists, updating instead")
                    self.db.rollback()
                else:
                    raise

            # Process team stats if available
            if team_stats_set and team_stats_set.get('rowSet'):
                team_stats = team_stats_set['rowSet']
                team_headers = {h: i for i, h in enumerate(team_stats_set['headers'])}
                
                try:
                    team1_id = self._safe_int(team_stats[0][team_headers['TEAM_ID']])
                    team2_id = self._safe_int(team_stats[1][team_headers['TEAM_ID']])
                    
                    # Look for points in different possible header names
                    pts_index = team_headers.get('PTS', team_headers.get('TEAM_PTS', team_headers.get('POINTS', -1)))
                    if pts_index != -1:
                        team1_score = self._safe_int(team_stats[0][pts_index]) if team_stats[0][pts_index] is not None else None
                        team2_score = self._safe_int(team_stats[1][pts_index]) if team_stats[1][pts_index] is not None else None
                        
                        logger.info(f"Processing scores for game {game_id}: Team1 ({team1_id}): {team1_score}, Team2 ({team2_id}): {team2_score}")
                        
                        # Update game scores based on home/away teams
                        if getattr(game, 'home_team_id') == team1_id:
                            setattr(game, 'home_score', team1_score)
                            setattr(game, 'away_score', team2_score)
                        else:
                            setattr(game, 'home_score', team2_score)
                            setattr(game, 'away_score', team1_score)
                            
                        # Update game status based on score availability
                        if getattr(game, 'home_score') is not None and getattr(game, 'away_score') is not None:
                            setattr(game, 'status', 'Completed')
                            logger.info(f"Marked game {game_id} as Completed with final score: Home {getattr(game, 'home_score')} - Away {getattr(game, 'away_score')}")
                        elif getattr(game, 'status', None) != 'Upcoming':
                            setattr(game, 'status', 'Live')
                            logger.info(f"Marked game {game_id} as Live with current score: Home {getattr(game, 'home_score')} - Away {getattr(game, 'away_score')}")
                            
                        setattr(game, 'last_updated', datetime.utcnow())
                        self.db.commit()
                        
                except Exception as e:
                    logger.error(f"Error processing team stats for game {game_id}: {str(e)}")
                    self.db.rollback()
                    return

            # Process player stats for completed games
            if getattr(game, 'status', None) == 'Completed' and player_stats_set and player_stats_set.get('rowSet'):
                # Check if stats already exist and are complete (should have at least 20 players for a completed game)
                existing_stats = self.db.query(PlayerGameStats).filter_by(game_id=game_id).count()
                if existing_stats >= 20:
                    logger.info(f"Stats already exist for game {game_id} ({existing_stats} players), skipping player stats processing")
                    return
                elif existing_stats > 0:
                    logger.info(f"Game {game_id} has incomplete stats ({existing_stats} players), reprocessing to get complete data")
                    # Delete existing incomplete stats before reprocessing
                    self.db.query(PlayerGameStats).filter_by(game_id=game_id).delete()
                    self.db.commit()

                player_headers = {h: i for i, h in enumerate(player_stats_set['headers'])}
                for player_row in player_stats_set['rowSet']:
                    try:
                        player_data = {
                            'PLAYER_ID': self._safe_int(player_row[player_headers['PLAYER_ID']]),
                            'TEAM_ID': self._safe_int(player_row[player_headers['TEAM_ID']]),
                            'MIN': str(player_row[player_headers['MIN']]) if player_row[player_headers['MIN']] else '0',
                            'PTS': self._safe_int(player_row[player_headers['PTS']]),
                            'REB': self._safe_int(player_row[player_headers['REB']]),
                            'AST': self._safe_int(player_row[player_headers['AST']]),
                            'STL': self._safe_int(player_row[player_headers['STL']]),
                            'BLK': self._safe_int(player_row[player_headers['BLK']]),
                            'FGM': self._safe_int(player_row[player_headers['FGM']]),
                            'FGA': self._safe_int(player_row[player_headers['FGA']]),
                            'FG_PCT': float(player_row[player_headers['FG_PCT']]) if player_row[player_headers['FG_PCT']] else 0.0,
                            'FG3M': self._safe_int(player_row[player_headers['FG3M']]),
                            'FG3A': self._safe_int(player_row[player_headers['FG3A']]),
                            'FG3_PCT': float(player_row[player_headers['FG3_PCT']]) if player_row[player_headers['FG3_PCT']] else 0.0,
                            'FTM': self._safe_int(player_row[player_headers['FTM']]),
                            'FTA': self._safe_int(player_row[player_headers['FTA']]),
                            'FT_PCT': float(player_row[player_headers['FT_PCT']]) if player_row[player_headers['FT_PCT']] else 0.0,
                            'TO': self._safe_int(player_row[player_headers['TO']]),
                            'PF': self._safe_int(player_row[player_headers['PF']]),
                            'PLUS_MINUS': self._safe_int(player_row[player_headers['PLUS_MINUS']])
                        }
                        await self._process_player_stats(player_data, game_id)
                    except Exception as e:
                        logger.error(f"Error processing player row in game {game_id}: {str(e)}")
                        continue
                
                # Mark game as fully loaded after successfully processing all player stats
                setattr(game, 'is_loaded', True)
                self.db.commit()
                logger.info(f"Game {game_id} marked as fully loaded")
                        
        except Exception as e:
            logger.error(f"Error in _process_game for {game_id}: {str(e)}")
            self.db.rollback()
            raise

    async def cleanup_old_seasons(self):
        """Clean up data from old seasons"""
        try:
            current_season = self._get_current_season()
            logger.info(f"Cleaning up data for seasons before {current_season}")
            
            # Keep playoff games from the previous season
            previous_season = f"{int(current_season.split('-')[0])-1}-{int(current_season.split('-')[1])-1}"
            
            # Delete games from older seasons, keeping playoff games from previous season
            self.db.query(Game).filter(
                (Game.season_year < previous_season) |
                ((Game.season_year == previous_season) & (Game.playoff_round.is_(None)))
            ).delete(synchronize_session=False)
            
            self.db.commit()
            logger.info("Old seasons cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_seasons: {str(e)}")
            self.db.rollback()
            raise

    async def _process_player_stats(self, player_data: dict, game_id: str):
        """Process and store player statistics for a game"""
        try:
            # Convert minutes played to total minutes
            minutes_str = player_data.get('MIN', '0')
            if ':' in minutes_str:  # Format like "32:45"
                try:
                    minutes, seconds = minutes_str.split(':')
                    minutes = self._safe_int(minutes)
                    seconds = self._safe_int(seconds)
                    total_minutes = str(minutes) + ":" + str(seconds).zfill(2)  # Format as "MM:SS"
                except Exception as e:
                    logger.warning(f"Error parsing minutes format '{minutes_str}': {str(e)}, defaulting to 0:00")
                    total_minutes = "0:00"
            else:
                # Convert float minutes to MM:SS format
                try:
                    minutes_float = float(minutes_str) if minutes_str else 0.0
                    minutes = int(minutes_float)
                    seconds = int((minutes_float % 1) * 60)
                    total_minutes = str(minutes) + ":" + str(seconds).zfill(2)
                except Exception as e:
                    logger.warning(f"Error parsing minutes value '{minutes_str}': {str(e)}, defaulting to 0:00")
                    total_minutes = "0:00"

            # Create or update player game stats
            stats = PlayerGameStats(
                game_id=game_id,
                player_id=player_data['PLAYER_ID'],
                team_id=player_data['TEAM_ID'],
                minutes=total_minutes,
                points=player_data['PTS'],
                rebounds=player_data['REB'],
                assists=player_data['AST'],
                steals=player_data['STL'],
                blocks=player_data['BLK'],
                fgm=player_data['FGM'],  # Changed from field_goals_made
                fga=player_data['FGA'],  # Changed from field_goals_attempted
                fg_pct=player_data['FG_PCT'],  # Changed from field_goal_percentage
                tpm=player_data['FG3M'],  # Changed from three_pointers_made
                tpa=player_data['FG3A'],  # Changed from three_pointers_attempted
                tp_pct=player_data['FG3_PCT'],  # Changed from three_point_percentage
                ftm=player_data['FTM'],  # Changed from free_throws_made
                fta=player_data['FTA'],  # Changed from free_throws_attempted
                ft_pct=player_data['FT_PCT'],  # Changed from free_throw_percentage
                turnovers=player_data['TO'],
                fouls=player_data['PF'],
                plus_minus=player_data['PLUS_MINUS']
            )
            
            self.db.merge(stats)
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing player stats for game {game_id}: {str(e)}")
            raise

    async def fix_free_agent_headshots(self):
        """Fix headshot URLs for free agents who have NULL values"""
        try:
            logger.info("Starting free agent headshot URL fix...")
            
            # Get all free agents with NULL headshot URLs
            free_agents = self.db.query(Player).filter(
                Player.current_team_id.is_(None),
                Player.headshot_url.is_(None)
            ).all()
            
            if not free_agents:
                logger.info("No free agents with NULL headshot URLs found")
                return
            
            logger.info(f"Found {len(free_agents)} free agents with NULL headshot URLs")
            
            # Update each free agent with their headshot URL
            for player in free_agents:
                try:
                    # Generate headshot URL using the standard NBA CDN format
                    headshot_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player.player_id}.png"
                    
                    # Update the player record using merge
                    updated_player = self.db.merge(Player(
                        player_id=player.player_id,
                        full_name=player.full_name,
                        first_name=player.first_name,
                        last_name=player.last_name,
                        current_team_id=player.current_team_id,
                        previous_team_id=player.previous_team_id,
                        traded_date=player.traded_date,
                        position=player.position,
                        jersey_number=player.jersey_number,
                        is_active=player.is_active,
                        headshot_url=headshot_url,
                        last_updated=datetime.utcnow()
                    ))
                    
                    logger.info(f"Updated headshot URL for free agent: {player.full_name} (ID: {player.player_id})")
                    
                except Exception as e:
                    logger.error(f"Error updating headshot for player {player.player_id}: {str(e)}")
                    continue
            
            # Commit all changes
            self.db.commit()
            
            logger.info(f"Successfully updated headshot URLs for {len(free_agents)} free agents")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in fix_free_agent_headshots: {str(e)}")
            raise

    async def fix_free_agent_teams(self):
        """
        Fix players who are marked as free agents by assigning them to their last team
        based on their most recent game stats. Since we're going off players' last team
        for the season, no player should be a free agent.
        """
        try:
            logger.info("Starting free agent team assignment fix...")
            
            # Get all players without a current team
            free_agents = self.db.query(Player).filter(Player.current_team_id.is_(None)).all()
            
            if not free_agents:
                logger.info("No free agents found!")
                return
            
            logger.info(f"Found {len(free_agents)} players without team assignments")
            
            fixed_count = 0
            not_found_count = 0
            
            for player in free_agents:
                try:
                    # Find the player's most recent game stats
                    most_recent_game = (
                        self.db.query(PlayerGameStats, Game)
                        .join(Game, PlayerGameStats.game_id == Game.game_id)
                        .filter(PlayerGameStats.player_id == player.player_id)
                        .order_by(Game.game_date_utc.desc())
                        .first()
                    )
                    
                    if most_recent_game:
                        stats, game = most_recent_game
                        
                        # Update player's current team to their most recent team
                        player.current_team_id = stats.team_id
                        
                        logger.info(f"Assigned {player.full_name} to team {stats.team_id} based on most recent game")
                        fixed_count += 1
                    else:
                        logger.debug(f"No game stats found for {player.full_name} (ID: {player.player_id}) - likely inactive player")
                        not_found_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing player {player.full_name}: {str(e)}")
                    continue
            
            # Commit all changes
            self.db.commit()
            
            logger.info(f"Free agent team assignment fix completed!")
            logger.info(f"Players assigned to teams: {fixed_count}")
            logger.info(f"Players without game data (likely inactive): {not_found_count}")
            
            # Verify the fix
            remaining_free_agents = self.db.query(Player).filter(Player.current_team_id.is_(None)).count()
            logger.info(f"Remaining free agents: {remaining_free_agents}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in fix_free_agent_teams: {str(e)}")
            raise

    async def fix_upcoming_past_games(self):
        """Fix games that are in the past but still marked as 'Upcoming' or incomplete 'Completed' games"""
        try:
            from datetime import datetime, timezone
            import pytz
            
            logger.info("Starting fix for problematic past games...")
            
            # Get all games that need fixing:
            # 1. Games marked as 'Upcoming' that are actually in the past
            # 2. Games marked as 'Completed' but not fully loaded (is_loaded=False)
            current_time = datetime.now(timezone.utc)
            
            problematic_games = self.db.query(Game).filter(
                Game.game_date_utc < current_time,
                (
                    (Game.status == 'Upcoming') |
                    ((Game.status == 'Completed') & (Game.is_loaded == False))
                )
            ).all()
            
            if not problematic_games:
                logger.info("No problematic past games found")
                return
                
            logger.info(f"Found {len(problematic_games)} problematic past games (upcoming status or incomplete data)")
            
            fixed_count = 0
            fully_processed_count = 0
            
            for game in problematic_games:
                try:
                    game_id = game.game_id
                    logger.info(f"Fixing game {game_id} - {game.game_date_utc}")
                    
                    # Try to fully process the game using the existing _process_game method
                    # This will handle scores, player stats, and set is_loaded appropriately
                    try:
                        # Get the season for this game 
                        season = str(getattr(game, 'season_year', '')) if getattr(game, 'season_year', None) else self._get_current_season()
                        
                        # Create game data structure for _process_game
                        game_data = {
                            'GAME_ID': str(game_id),
                            'GAME_DATE': game.game_date_utc.strftime('%Y-%m-%dT%H:%M:%S'),
                            'HOME_TEAM_ID': getattr(game, 'home_team_id'),
                            'AWAY_TEAM_ID': getattr(game, 'away_team_id')
                        }
                        
                        # Use the existing _process_game method for complete processing
                        await self._process_game(str(game_id), game_data, season)
                        
                        # Check if the game was successfully processed
                        updated_game = self.db.query(Game).filter_by(game_id=str(game_id)).first()
                        if updated_game and str(updated_game.status) == 'Completed':
                            if bool(updated_game.is_loaded):
                                logger.info(f"Successfully fully processed past game {game_id} with complete data")
                                fully_processed_count += 1
                            else:
                                logger.info(f"Successfully updated past game {game_id} status and scores")
                            fixed_count += 1
                        else:
                            # Fallback: manually update using merge
                            updated_game_data = self.db.merge(Game(
                                game_id=str(game_id),
                                game_date_utc=game.game_date_utc,
                                home_team_id=getattr(game, 'home_team_id'),
                                away_team_id=getattr(game, 'away_team_id'),
                                status='Completed',
                                season_year=season,
                                playoff_round=getattr(game, 'playoff_round', None),
                                is_loaded=getattr(game, 'is_loaded', False),
                                last_updated=datetime.utcnow()
                            ))
                            self.db.commit()
                            logger.info(f"Fallback: Marked past game {game_id} as Completed")
                            fixed_count += 1
                        
                    except Exception as process_error:
                        logger.warning(f"_process_game failed for {game_id}: {str(process_error)}")
                        
                        # Fallback to original method: just update status and try to get scores
                        try:
                            padded_game_id = str(game_id).zfill(10)
                            box_score = await self._make_nba_request(
                                boxscoretraditionalv2.BoxScoreTraditionalV2,
                                game_id=padded_game_id
                            )
                            
                            # Initialize default values
                            home_score = None
                            away_score = None
                            
                            if box_score:
                                # Process the box score to get the final scores
                                result_sets = box_score.get('resultSets', box_score.get('resultSet', []))
                                team_stats_set = next((rs for rs in result_sets if rs['name'] == 'TeamStats'), None)
                                
                                if team_stats_set and team_stats_set.get('rowSet'):
                                    team_stats = team_stats_set['rowSet']
                                    team_headers = {h: i for i, h in enumerate(team_stats_set['headers'])}
                                    
                                    if len(team_stats) >= 2:
                                        # Get scores
                                        pts_index = team_headers.get('PTS', team_headers.get('TEAM_PTS', team_headers.get('POINTS', -1)))
                                        if pts_index != -1:
                                            team1_score = int(team_stats[0][pts_index]) if team_stats[0][pts_index] is not None else None
                                            team2_score = int(team_stats[1][pts_index]) if team_stats[1][pts_index] is not None else None
                                            
                                            if team1_score is not None and team2_score is not None:
                                                # Determine scores for home/away teams
                                                team1_id = int(team_stats[0][team_headers['TEAM_ID']])
                                                team2_id = int(team_stats[1][team_headers['TEAM_ID']])
                                                
                                                # Assign scores to home/away teams correctly
                                                if getattr(game, 'home_team_id') == team1_id:
                                                    home_score = team1_score
                                                    away_score = team2_score
                                                else:
                                                    home_score = team2_score
                                                    away_score = team1_score
                            
                            # Update game using merge method to avoid SQLAlchemy attribute assignment issues
                            updated_game = self.db.merge(Game(
                                game_id=str(game_id),
                                game_date_utc=game.game_date_utc,
                                home_team_id=getattr(game, 'home_team_id'),
                                away_team_id=getattr(game, 'away_team_id'),
                                home_score=home_score,
                                away_score=away_score,
                                status='Completed',
                                season_year=str(getattr(game, 'season_year', '')) if getattr(game, 'season_year', None) else self._get_current_season(),
                                playoff_round=getattr(game, 'playoff_round', None),
                                is_loaded=getattr(game, 'is_loaded', False),
                                last_updated=datetime.utcnow()
                            ))
                            self.db.commit()
                            
                            if home_score is not None and away_score is not None:
                                logger.info(f"Fallback: Fixed game {game_id} with scores Home {home_score} - Away {away_score}")
                            else:
                                logger.info(f"Fallback: Marked past game {game_id} as Completed")
                            fixed_count += 1
                        
                        except Exception as api_error:
                            # API call failed, but game is still in the past - mark as completed
                            logger.warning(f"Fallback API call failed for game {game_id}: {str(api_error)}")
                            
                            # Use merge to update game status
                            updated_game = self.db.merge(Game(
                                game_id=str(game_id),
                                game_date_utc=game.game_date_utc,
                                home_team_id=getattr(game, 'home_team_id'),
                                away_team_id=getattr(game, 'away_team_id'),
                                status='Completed',
                                season_year=str(getattr(game, 'season_year', '')) if getattr(game, 'season_year', None) else self._get_current_season(),
                                playoff_round=getattr(game, 'playoff_round', None),
                                is_loaded=getattr(game, 'is_loaded', False),
                                last_updated=datetime.utcnow()
                            ))
                            self.db.commit()
                            logger.info(f"Fallback: Marked past game {game_id} as Completed (API call failed)")
                            fixed_count += 1
                    
                    # Small delay between API calls
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing past game {game.game_id}: {str(e)}")
                    continue
            
            # Commit all changes
            self.db.commit()
            
            logger.info(f"Fixed {fixed_count} past games that were marked as 'Upcoming'")
            logger.info(f"Fully processed {fully_processed_count} games with complete player statistics")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in fix_upcoming_past_games: {str(e)}")
            raise