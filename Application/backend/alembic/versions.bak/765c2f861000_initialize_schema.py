"""initialize_schema

Revision ID: 765c2f861000
Revises: None
Create Date: 2025-05-22 11:59:14.654843

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '765c2f861000'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create data_update_status table
    op.create_table('data_update_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('last_successful_update', sa.DateTime(), nullable=True),
        sa.Column('next_scheduled_update', sa.DateTime(), nullable=True),
        sa.Column('is_updating', sa.Boolean(), nullable=False, default=False),
        sa.Column('cancellation_requested', sa.Boolean(), nullable=False, default=False),
        sa.Column('components', sa.JSON(), nullable=False, default=dict),
        sa.Column('teams_updated', sa.Boolean(), nullable=False, default=False),
        sa.Column('players_updated', sa.Boolean(), nullable=False, default=False),
        sa.Column('games_updated', sa.Boolean(), nullable=False, default=False),
        sa.Column('teams_percent_complete', sa.Integer(), nullable=False, default=0),
        sa.Column('players_percent_complete', sa.Integer(), nullable=False, default=0),
        sa.Column('games_percent_complete', sa.Integer(), nullable=False, default=0),
        sa.Column('teams_last_update', sa.DateTime(), nullable=True),
        sa.Column('players_last_update', sa.DateTime(), nullable=True),
        sa.Column('games_last_update', sa.DateTime(), nullable=True),
        sa.Column('current_phase', sa.String(), nullable=True),
        sa.Column('current_detail', sa.String(), nullable=True),
        sa.Column('last_error', sa.String(), nullable=True),
        sa.Column('last_error_time', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create teams table
    op.create_table('teams',
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('abbreviation', sa.String(), nullable=False),
        sa.Column('conference', sa.String(), nullable=True),
        sa.Column('division', sa.String(), nullable=True),
        sa.Column('wins', sa.Integer(), nullable=True, default=0),
        sa.Column('losses', sa.Integer(), nullable=True, default=0),
        sa.Column('logo_url', sa.String(), nullable=True),
        sa.Column('roster_loaded', sa.Boolean(), default=False),
        sa.Column('loading_progress', sa.Integer(), default=0),
        sa.Column('games_loaded', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('team_id')
    )

    # Create players table
    op.create_table('players',
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('position', sa.String(), nullable=True),
        sa.Column('jersey_number', sa.String(), nullable=True),
        sa.Column('current_team_id', sa.Integer(), sa.ForeignKey('teams.team_id'), nullable=True),
        sa.Column('headshot_url', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_loaded', sa.Boolean(), default=False),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('player_id')
    )

    # Create games table
    op.create_table('games',
        sa.Column('game_id', sa.String(), nullable=False),
        sa.Column('home_team_id', sa.Integer(), sa.ForeignKey('teams.team_id'), nullable=False),
        sa.Column('away_team_id', sa.Integer(), sa.ForeignKey('teams.team_id'), nullable=False),
        sa.Column('game_date_utc', sa.DateTime(), nullable=False),
        sa.Column('home_score', sa.Integer(), nullable=True),
        sa.Column('away_score', sa.Integer(), nullable=True),
        sa.Column('season_year', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('is_loaded', sa.Boolean(), default=False),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('game_id')
    )

    # Create player_game_stats table
    op.create_table('player_game_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), sa.ForeignKey('players.player_id'), nullable=False),
        sa.Column('game_id', sa.String(), sa.ForeignKey('games.game_id'), nullable=False),
        sa.Column('minutes_played', sa.Float(), nullable=True),
        sa.Column('field_goals_made', sa.Integer(), nullable=True),
        sa.Column('field_goals_attempted', sa.Integer(), nullable=True),
        sa.Column('three_pointers_made', sa.Integer(), nullable=True),
        sa.Column('three_pointers_attempted', sa.Integer(), nullable=True),
        sa.Column('free_throws_made', sa.Integer(), nullable=True),
        sa.Column('free_throws_attempted', sa.Integer(), nullable=True),
        sa.Column('offensive_rebounds', sa.Integer(), nullable=True),
        sa.Column('defensive_rebounds', sa.Integer(), nullable=True),
        sa.Column('assists', sa.Integer(), nullable=True),
        sa.Column('steals', sa.Integer(), nullable=True),
        sa.Column('blocks', sa.Integer(), nullable=True),
        sa.Column('turnovers', sa.Integer(), nullable=True),
        sa.Column('personal_fouls', sa.Integer(), nullable=True),
        sa.Column('points', sa.Integer(), nullable=True),
        sa.Column('plus_minus', sa.Integer(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('player_game_stats')
    op.drop_table('games')
    op.drop_table('players')
    op.drop_table('teams')
    op.drop_table('data_update_status')
