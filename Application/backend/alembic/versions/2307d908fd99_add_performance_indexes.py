"""add_performance_indexes

Revision ID: 2307d908fd99
Revises: 8fa212fe9902
Create Date: 2025-05-25 23:02:02.483382

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2307d908fd99'
down_revision: Union[str, None] = '8fa212fe9902'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create performance indexes for frequently queried columns

    # Index for player_game_stats lookups by player_id (most common query pattern)
    op.create_index('idx_player_games_player_id', 'player_game_stats', ['player_id'])

    # Index for games lookups by date (timeline queries, recent games)
    op.create_index('idx_games_date', 'games', ['game_date_utc'])

    # Index for players lookups by team_id (roster queries)
    op.create_index('idx_players_team_id', 'players', ['current_team_id'])

    # Index for games lookups by status (filter completed vs in-progress games)
    op.create_index('idx_games_status', 'games', ['status'])

    # Composite index for player_game_stats lookups by game_id (game stats queries)
    op.create_index('idx_player_games_game_id', 'player_game_stats', ['game_id'])

    # Composite index for efficient date range and team queries
    op.create_index('idx_games_team_date', 'games', ['home_team_id', 'game_date_utc'])
    op.create_index('idx_games_away_team_date', 'games', ['away_team_id', 'game_date_utc'])


def downgrade() -> None:
    # Drop the performance indexes
    op.drop_index('idx_player_games_player_id', 'player_game_stats')
    op.drop_index('idx_games_date', 'games')
    op.drop_index('idx_players_team_id', 'players')
    op.drop_index('idx_games_status', 'games')
    op.drop_index('idx_player_games_game_id', 'player_game_stats')
    op.drop_index('idx_games_team_date', 'games')
    op.drop_index('idx_games_away_team_date', 'games')
