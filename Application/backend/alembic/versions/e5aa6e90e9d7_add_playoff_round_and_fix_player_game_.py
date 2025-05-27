"""add_playoff_round_and_fix_player_game_stats

Revision ID: e5aa6e90e9d7
Revises: 3dbae6769636
Create Date: 2025-05-22 13:19:33.838234

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5aa6e90e9d7'
down_revision: Union[str, None] = '3dbae6769636'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create a new player_game_stats table with a temporary name
    op.create_table('player_game_stats_new',
        sa.Column('stat_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.String(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('minutes', sa.String(), nullable=True),
        sa.Column('points', sa.Integer(), nullable=True),
        sa.Column('rebounds', sa.Integer(), nullable=True),
        sa.Column('assists', sa.Integer(), nullable=True),
        sa.Column('steals', sa.Integer(), nullable=True),
        sa.Column('blocks', sa.Integer(), nullable=True),
        sa.Column('fgm', sa.Integer(), nullable=True),
        sa.Column('fga', sa.Integer(), nullable=True),
        sa.Column('fg_pct', sa.Float(), nullable=True),
        sa.Column('tpm', sa.Integer(), nullable=True),
        sa.Column('tpa', sa.Integer(), nullable=True),
        sa.Column('tp_pct', sa.Float(), nullable=True),
        sa.Column('ftm', sa.Integer(), nullable=True),
        sa.Column('fta', sa.Integer(), nullable=True),
        sa.Column('ft_pct', sa.Float(), nullable=True),
        sa.Column('turnovers', sa.Integer(), nullable=True),
        sa.Column('fouls', sa.Integer(), nullable=True),
        sa.Column('plus_minus', sa.Integer(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.game_id'], name='fk_player_game_stats_game'),
        sa.ForeignKeyConstraint(['player_id'], ['players.player_id'], name='fk_player_game_stats_player'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.team_id'], name='fk_player_game_stats_team'),
        sa.UniqueConstraint('player_id', 'game_id', 'team_id', name='unique_player_game_stats')
    )

    # Copy data from the old table to the new one
    op.execute('''
        INSERT INTO player_game_stats_new (
            player_id, game_id, minutes, points, rebounds, assists,
            steals, blocks, turnovers, fouls, plus_minus, last_updated
        )
        SELECT player_id, game_id, minutes_played, points,
            offensive_rebounds + defensive_rebounds, assists,
            steals, blocks, turnovers, personal_fouls, plus_minus, last_updated
        FROM player_game_stats
    ''')

    # Drop the old table
    op.drop_table('player_game_stats')

    # Rename the new table to the original name
    op.rename_table('player_game_stats_new', 'player_game_stats')


def downgrade() -> None:
    # Create new table with old schema
    op.create_table('player_game_stats_old',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.String(), nullable=False),
        sa.Column('minutes_played', sa.Float(), nullable=True),
        sa.Column('points', sa.Integer(), nullable=True),
        sa.Column('offensive_rebounds', sa.Integer(), nullable=True),
        sa.Column('defensive_rebounds', sa.Integer(), nullable=True),
        sa.Column('assists', sa.Integer(), nullable=True),
        sa.Column('steals', sa.Integer(), nullable=True),
        sa.Column('blocks', sa.Integer(), nullable=True),
        sa.Column('field_goals_made', sa.Integer(), nullable=True),
        sa.Column('field_goals_attempted', sa.Integer(), nullable=True),
        sa.Column('three_pointers_made', sa.Integer(), nullable=True),
        sa.Column('three_pointers_attempted', sa.Integer(), nullable=True),
        sa.Column('free_throws_made', sa.Integer(), nullable=True),
        sa.Column('free_throws_attempted', sa.Integer(), nullable=True),
        sa.Column('turnovers', sa.Integer(), nullable=True),
        sa.Column('personal_fouls', sa.Integer(), nullable=True),
        sa.Column('plus_minus', sa.Integer(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['game_id'], ['games.game_id']),
        sa.ForeignKeyConstraint(['player_id'], ['players.player_id'])
    )

    # Copy data from the new table to the old one
    op.execute('''
        INSERT INTO player_game_stats_old (
            player_id, game_id, minutes_played, points,
            offensive_rebounds, defensive_rebounds, assists,
            steals, blocks, field_goals_made, field_goals_attempted,
            three_pointers_made, three_pointers_attempted,
            free_throws_made, free_throws_attempted,
            turnovers, personal_fouls, plus_minus, last_updated
        )
        SELECT player_id, game_id,
            CAST(SUBSTR(minutes, 1, INSTR(minutes, ':') - 1) AS FLOAT) +
            CAST(SUBSTR(minutes, INSTR(minutes, ':') + 1) AS FLOAT) / 60,
            points,
            CAST(rebounds/2 AS INTEGER), CAST((rebounds+1)/2 AS INTEGER),
            assists, steals, blocks,
            fgm, fga, tpm, tpa, ftm, fta,
            turnovers, fouls, plus_minus, last_updated
        FROM player_game_stats
    ''')

    # Drop the new table
    op.drop_table('player_game_stats')

    # Rename the old table to the original name
    op.rename_table('player_game_stats_old', 'player_game_stats')
