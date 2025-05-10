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
from app.models.models import Team, Player, Game, PlayerGameStats, DataUpdateStatus
from requests.exceptions import Timeout, RequestException
import requests
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Configure NBA API
http.STATS_HEADERS['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
http.TIMEOUT = 60
requests.packages.urllib3.disable_warnings()
http.VERIFY = False

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
        self._request_timeout = 180  # 3 minutes
        self._read_timeout = 120    # 2 minutes
        self._connect_timeout = 60  # 1 minute
        self._last_request_time = 0
        self._base_delay = 2.0
        self._max_retries = 5
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
        raise last_error

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

    def _get_current_season(self):
        """Get the current NBA season string based on date"""
        today = datetime.now()
        # NBA regular season typically ends in April
        # Use previous season until the new season starts (typically October)
        if today.month >= 10:  # New season starts in October
            return f"{today.year}-{str(today.year+1)[2:]}"
        elif today.month < 10:  # Use previous season until new season starts
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
                return await self._make_nba_request(endpoint_class, **params)
            else:
                raise ValueError(f"Unknown endpoint: {endpoint}")
                
        except Exception as e:
            logger.error(f"Error in legacy _make_api_request: {str(e)}")
            raise

    async def update_games(self):
        """Update games and player statistics"""
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
                    await self._process_game(game.game_id, {
                        'GAME_ID': game.game_id,
                        'GAME_DATE': game.game_date_utc.strftime("%Y-%m-%d"),
                        'HOME_TEAM_ID': game.home_team_id,
                        'AWAY_TEAM_ID': game.away_team_id
                    }, current_season)
                except Exception as e:
                    logger.error(f"Error processing historical game {game.game_id}: {str(e)}")
                    continue
            
            # Then process today's games
            try:
                today = datetime.now() - timedelta(hours=4)
                date_str = today.strftime('%m/%d/%Y')
                logger.info(f"Fetching today's games for date: {date_str}")
                
                # Use NBA API's scoreboardv2 endpoint
                scoreboard = scoreboardv2.ScoreboardV2(
                    game_date=date_str,
                    league_id='00',
                    day_offset=0
                )
                
                games_dict = scoreboard.get_dict()
                
                if games_dict and 'resultSets' in games_dict:
                    game_header = next((rs for rs in games_dict['resultSets'] if rs['name'] == 'GameHeader'), None)
                    if game_header and game_header.get('rowSet'):
                        headers = {h: i for i, h in enumerate(game_header['headers'])}
                        
                        for game_row in game_header['rowSet']:
                            try:
                                game_id = str(game_row[headers['GAME_ID']])
                                # Parse the game date in EST
                                game_date_est = datetime.strptime(game_row[headers['GAME_DATE_EST']], '%Y-%m-%dT%H:%M:%S')
                                # Convert EST to UTC by adding 4 hours (EST is UTC-4)
                                game_date_utc = game_date_est + timedelta(hours=4)
                                
                                home_team_id = int(game_row[headers['HOME_TEAM_ID']])
                                away_team_id = int(game_row[headers['VISITOR_TEAM_ID']])
                                game_status_text = str(game_row[headers['GAME_STATUS_TEXT']])
                                
                                # Determine game status based on GAME_STATUS_TEXT
                                if game_status_text in ['Final', 'F/OT']:
                                    status = 'Completed'
                                elif game_status_text.endswith(' ET'):  # Time format like "8:30 pm ET"
                                    status = 'Upcoming'
                                else:
                                    status = 'Live'  # Game is in progress
                                
                                logger.info(f"Processing game {game_id} with status: {status}")
                                
                                # For upcoming games, scores will be None
                                # For completed or live games, we'll get scores from box score
                                home_score = None
                                away_score = None
                                
                                # Create or update game record
                                game = self.db.merge(Game(
                                    game_id=game_id,
                                    game_date_utc=game_date_utc,  # Now using properly converted UTC time
                                    home_team_id=home_team_id,
                                    away_team_id=away_team_id,
                                    home_score=home_score,
                                    away_score=away_score,
                                    status=status,
                                    season_year=current_season,
                                    last_updated=datetime.utcnow()
                                ))
                                self.db.commit()
                                
                                # For completed or live games, get scores from box score
                                if status in ['Completed', 'Live']:
                                    await self._process_game(game_id, {
                                        'GAME_ID': game_id,
                                        'GAME_DATE': game_date_utc.strftime("%Y-%m-%d"),
                                        'HOME_TEAM_ID': home_team_id,
                                        'AWAY_TEAM_ID': away_team_id
                                    }, current_season)
                                    
                            except Exception as e:
                                logger.error(f"Error processing game {game_id if 'game_id' in locals() else 'unknown'}: {str(e)}")
                                continue
                                
            except Exception as e:
                logger.error(f"Error fetching game schedule: {str(e)}")
                raise
                
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
                team.loading_progress = 0
                team.roster_loaded = False
                team.games_loaded = False  # Reset games loaded status
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
                    if existing_player and existing_player.current_team_id != team_id and existing_player.current_team_id is not None:
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
                            headshot_url=f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png",
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
                            headshot_url=f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png",
                            last_updated=datetime.utcnow()
                        ))
                    
                    self.db.commit()
                    
                    # Update progress
                    processed_players += 1
                    if team:
                        team.loading_progress = int((processed_players / total_players) * 100)
                        self.db.commit()
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    self.db.rollback()
                    logger.error(f"Error updating player data: {str(e)}")
                    continue
            
            # Mark team roster as loaded and update progress
            if team:
                team.roster_loaded = True
                team.loading_progress = 50  # Set to 50% when roster is loaded
                self.db.commit()

            # Update games for this team
            await self.update_team_games(team_id)
                    
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
                            team.loading_progress = 50 + games_progress  # Add to base 50% from roster loading
                            self.db.commit()

                        await asyncio.sleep(1)

                    except Exception as e:
                        logger.error(f"Error processing game {game_id if 'game_id' in locals() else 'unknown'}: {str(e)}")
                        continue

                # Mark games as loaded
                if team:
                    team.games_loaded = True
                    team.loading_progress = 100
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
            
            if status.is_updating:
                logger.warning("Update already in progress")
                return False

            # Reset status flags
            status.is_updating = True
            status.current_phase = 'cleanup'
            status.last_error = None
            status.last_error_time = None
            self.db.commit()
            
            try:
                # First clean up old season data
                await self.cleanup_old_seasons()
                
                # Check if teams need updating (every 6 hours)
                teams_need_update = not status.teams_updated or \
                    (status.last_successful_update and 
                     datetime.utcnow() - status.last_successful_update > timedelta(hours=6))
                
                if teams_need_update:
                    status.current_phase = 'teams'
                    status.teams_updated = False
                    self.db.commit()
                    await self.update_teams()
                    status.teams_updated = True
                    self.db.commit()
                else:
                    logger.info("Teams are up to date, skipping teams update")
                
                # Update players for each team that needs updating
                status.current_phase = 'players'
                status.players_updated = False
                self.db.commit()
                
                teams_query = self.db.query(Team)
                if status.last_successful_update:
                    teams_query = teams_query.filter(
                        (Team.last_updated == None) |
                        (Team.last_updated <= datetime.utcnow() - timedelta(hours=6))
                    )
                
                for team in teams_query.all():
                    await self.update_team_players(team.team_id)
                
                status.players_updated = True
                
                # Update games and stats (this should run each time to get latest scores)
                status.current_phase = 'games'
                status.games_updated = False
                self.db.commit()
                await self.update_games()
                status.games_updated = True
                status.current_phase = None
                
                # Update the final status
                status.last_successful_update = datetime.utcnow()
                status.next_scheduled_update = datetime.utcnow() + timedelta(hours=6)
                status.is_updating = False
                self.db.commit()
                return True
                
            except Exception as e:
                self.db.rollback()
                status = self.db.query(DataUpdateStatus).first()
                if status:
                    status.last_error = str(e)
                    status.last_error_time = datetime.utcnow()
                    status.is_updating = False
                    self.db.commit()
                raise e
                
        except Exception as e:
            # If anything fails during status update, try one last time to set is_updating to False
            try:
                status = self.db.query(DataUpdateStatus).first()
                if status:
                    status.is_updating = False
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
            if existing_game and existing_game.status == 'Completed':
                # Skip if game is already completed and has stats
                if self.db.query(PlayerGameStats).filter_by(game_id=game_id).count() > 0:
                    logger.info(f"Skipping game {game_id} - already completed with stats")
                    return
            
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
                    home_team_id = int(summary_row[summary_headers['HOME_TEAM_ID']])
                    away_team_id = int(summary_row[summary_headers['VISITOR_TEAM_ID']])
                elif team_stats_set and team_stats_set.get('rowSet'):
                    team_headers = {h: i for i, h in enumerate(team_stats_set['headers'])}
                    team1_id = int(team_stats_set['rowSet'][0][team_headers['TEAM_ID']])
                    team2_id = int(team_stats_set['rowSet'][1][team_headers['TEAM_ID']])
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
                    team1_id = int(team_stats[0][team_headers['TEAM_ID']])
                    team2_id = int(team_stats[1][team_headers['TEAM_ID']])
                    
                    # Look for points in different possible header names
                    pts_index = team_headers.get('PTS', team_headers.get('TEAM_PTS', team_headers.get('POINTS', -1)))
                    if pts_index != -1:
                        team1_score = int(team_stats[0][pts_index]) if team_stats[0][pts_index] is not None else None
                        team2_score = int(team_stats[1][pts_index]) if team_stats[1][pts_index] is not None else None
                        
                        logger.info(f"Processing scores for game {game_id}: Team1 ({team1_id}): {team1_score}, Team2 ({team2_id}): {team2_score}")
                        
                        # Update game scores based on home/away teams
                        if game.home_team_id == team1_id:
                            game.home_score = team1_score
                            game.away_score = team2_score
                        else:
                            game.home_score = team2_score
                            game.away_score = team1_score
                            
                        # Update game status based on score availability
                        if game.home_score is not None and game.away_score is not None:
                            game.status = 'Completed'
                            logger.info(f"Marked game {game_id} as Completed with final score: Home {game.home_score} - Away {game.away_score}")
                        elif game.status != 'Upcoming':
                            game.status = 'Live'
                            logger.info(f"Marked game {game_id} as Live with current score: Home {game.home_score} - Away {game.away_score}")
                            
                        game.last_updated = datetime.utcnow()
                        self.db.commit()
                        
                except Exception as e:
                    logger.error(f"Error processing team stats for game {game_id}: {str(e)}")
                    self.db.rollback()
                    return

            # Process player stats for completed games
            if game.status == 'Completed' and player_stats_set and player_stats_set.get('rowSet'):
                # Check if stats already exist
                existing_stats = self.db.query(PlayerGameStats).filter_by(game_id=game_id).count()
                if existing_stats > 0:
                    logger.info(f"Stats already exist for game {game_id}, skipping player stats processing")
                    return

                player_headers = {h: i for i, h in enumerate(player_stats_set['headers'])}
                for player_row in player_stats_set['rowSet']:
                    try:
                        player_data = {
                            'PLAYER_ID': int(player_row[player_headers['PLAYER_ID']]),
                            'TEAM_ID': int(player_row[player_headers['TEAM_ID']]),
                            'MIN': str(player_row[player_headers['MIN']]) if player_row[player_headers['MIN']] else '0',
                            'PTS': int(player_row[player_headers['PTS']]) if player_row[player_headers['PTS']] else 0,
                            'REB': int(player_row[player_headers['REB']]) if player_row[player_headers['REB']] else 0,
                            'AST': int(player_row[player_headers['AST']]) if player_row[player_headers['AST']] else 0,
                            'STL': int(player_row[player_headers['STL']]) if player_row[player_headers['STL']] else 0,
                            'BLK': int(player_row[player_headers['BLK']]) if player_row[player_headers['BLK']] else 0,
                            'FGM': int(player_row[player_headers['FGM']]) if player_row[player_headers['FGM']] else 0,
                            'FGA': int(player_row[player_headers['FGA']]) if player_row[player_headers['FGA']] else 0,
                            'FG_PCT': float(player_row[player_headers['FG_PCT']]) if player_row[player_headers['FG_PCT']] else 0.0,
                            'FG3M': int(player_row[player_headers['FG3M']]) if player_row[player_headers['FG3M']] else 0,
                            'FG3A': int(player_row[player_headers['FG3A']]) if player_row[player_headers['FG3A']] else 0,
                            'FG3_PCT': float(player_row[player_headers['FG3_PCT']]) if player_row[player_headers['FG3_PCT']] else 0.0,
                            'FTM': int(player_row[player_headers['FTM']]) if player_row[player_headers['FTM']] else 0,
                            'FTA': int(player_row[player_headers['FTA']]) if player_row[player_headers['FTA']] else 0,
                            'FT_PCT': float(player_row[player_headers['FT_PCT']]) if player_row[player_headers['FT_PCT']] else 0.0,
                            'TO': int(player_row[player_headers['TO']]) if player_row[player_headers['TO']] else 0,
                            'PF': int(player_row[player_headers['PF']]) if player_row[player_headers['PF']] else 0,
                            'PLUS_MINUS': float(player_row[player_headers['PLUS_MINUS']]) if player_row[player_headers['PLUS_MINUS']] else 0
                        }
                        await self._process_player_stats(player_data, game_id)
                    except Exception as e:
                        logger.error(f"Error processing player row in game {game_id}: {str(e)}")
                        continue
                        
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