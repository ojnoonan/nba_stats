"""Add performance indexes

Revision ID: 001_add_indexes
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_add_indexes'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Add indexes for performance optimization."""
    
    # Teams table indexes
    op.create_index('idx_teams_conference', 'teams', ['conference'])
    op.create_index('idx_teams_division', 'teams', ['division'])
    op.create_index('idx_teams_last_updated', 'teams', ['last_updated'])
    
    # Players table indexes
    op.create_index('idx_players_current_team_id', 'players', ['current_team_id'])
    op.create_index('idx_players_full_name', 'players', ['full_name'])
    op.create_index('idx_players_last_name', 'players', ['last_name'])
    op.create_index('idx_players_position', 'players', ['position'])
    op.create_index('idx_players_is_active', 'players', ['is_active'])
    op.create_index('idx_players_last_updated', 'players', ['last_updated'])
    
    # Games table indexes
    op.create_index('idx_games_game_date_utc', 'games', ['game_date_utc'])
    op.create_index('idx_games_home_team_id', 'games', ['home_team_id'])
    op.create_index('idx_games_away_team_id', 'games', ['away_team_id'])
    op.create_index('idx_games_status', 'games', ['status'])
    op.create_index('idx_games_season_year', 'games', ['season_year'])
    op.create_index('idx_games_is_loaded', 'games', ['is_loaded'])
    op.create_index('idx_games_last_updated', 'games', ['last_updated'])
    # Composite index for team schedules
    op.create_index('idx_games_team_date', 'games', ['home_team_id', 'game_date_utc'])
    op.create_index('idx_games_away_team_date', 'games', ['away_team_id', 'game_date_utc'])
    
    # PlayerGameStats table indexes
    op.create_index('idx_player_game_stats_player_id', 'player_game_stats', ['player_id'])
    op.create_index('idx_player_game_stats_game_id', 'player_game_stats', ['game_id'])
    op.create_index('idx_player_game_stats_team_id', 'player_game_stats', ['team_id'])
    op.create_index('idx_player_game_stats_points', 'player_game_stats', ['points'])
    op.create_index('idx_player_game_stats_last_updated', 'player_game_stats', ['last_updated'])
    # Composite index for player season stats
    op.create_index('idx_player_stats_player_season', 'player_game_stats', ['player_id', 'team_id'])

def downgrade():
    """Remove performance indexes."""
    
    # Teams table indexes
    op.drop_index('idx_teams_conference')
    op.drop_index('idx_teams_division')
    op.drop_index('idx_teams_last_updated')
    
    # Players table indexes
    op.drop_index('idx_players_current_team_id')
    op.drop_index('idx_players_full_name')
    op.drop_index('idx_players_last_name')
    op.drop_index('idx_players_position')
    op.drop_index('idx_players_is_active')
    op.drop_index('idx_players_last_updated')
    
    # Games table indexes
    op.drop_index('idx_games_game_date_utc')
    op.drop_index('idx_games_home_team_id')
    op.drop_index('idx_games_away_team_id')
    op.drop_index('idx_games_status')
    op.drop_index('idx_games_season_year')
    op.drop_index('idx_games_is_loaded')
    op.drop_index('idx_games_last_updated')
    op.drop_index('idx_games_team_date')
    op.drop_index('idx_games_away_team_date')
    
    # PlayerGameStats table indexes
    op.drop_index('idx_player_game_stats_player_id')
    op.drop_index('idx_player_game_stats_game_id')
    op.drop_index('idx_player_game_stats_team_id')
    op.drop_index('idx_player_game_stats_points')
    op.drop_index('idx_player_game_stats_last_updated')
    op.drop_index('idx_player_stats_player_season')
