"""add stat_id to player_game_stats

Revision ID: a61ad8e90a6e
Revises: efd93d7f13c5
Create Date: 2025-05-06 15:34:35.770809

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a61ad8e90a6e'
down_revision: Union[str, None] = 'efd93d7f13c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create new table with desired schema
    op.create_table(
        'player_game_stats_new',
        sa.Column('stat_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('player_id', sa.Integer(), sa.ForeignKey('players.player_id')),
        sa.Column('game_id', sa.Integer(), sa.ForeignKey('games.game_id')),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.team_id')),
        sa.Column('minutes', sa.String()),
        sa.Column('points', sa.Integer()),
        sa.Column('rebounds', sa.Integer()),
        sa.Column('assists', sa.Integer()),
        sa.Column('steals', sa.Integer()),
        sa.Column('blocks', sa.Integer()),
        sa.Column('fgm', sa.Integer()),
        sa.Column('fga', sa.Integer()),
        sa.Column('fg_pct', sa.Float()),
        sa.Column('tpm', sa.Integer()),
        sa.Column('tpa', sa.Integer()),
        sa.Column('tp_pct', sa.Float()),
        sa.Column('ftm', sa.Integer()),
        sa.Column('fta', sa.Integer()),
        sa.Column('ft_pct', sa.Float()),
        sa.Column('turnovers', sa.Integer()),
        sa.Column('fouls', sa.Integer()),
        sa.Column('plus_minus', sa.Integer()),
        sa.Column('last_updated', sa.DateTime()),
        sa.UniqueConstraint('player_id', 'game_id', 'team_id', name='unique_player_game_stats')
    )

    # Copy data from old table to new table
    op.execute(
        '''
        INSERT INTO player_game_stats_new (
            player_id, game_id, team_id, minutes, points, rebounds, assists,
            steals, blocks, fgm, fga, fg_pct, tpm, tpa, tp_pct, ftm, fta,
            ft_pct, turnovers, fouls, plus_minus, last_updated
        )
        SELECT 
            player_id, game_id, team_id, minutes, points, rebounds, assists,
            steals, blocks, fgm, fga, fg_pct, tpm, tpa, tp_pct, ftm, fta,
            ft_pct, turnovers, fouls, plus_minus, last_updated
        FROM player_game_stats
        '''
    )

    # Drop old table
    op.drop_table('player_game_stats')

    # Rename new table to original name
    op.rename_table('player_game_stats_new', 'player_game_stats')

def downgrade() -> None:
    # Create old table structure
    op.create_table(
        'player_game_stats_old',
        sa.Column('player_id', sa.Integer(), sa.ForeignKey('players.player_id'), primary_key=True),
        sa.Column('game_id', sa.Integer(), sa.ForeignKey('games.game_id'), primary_key=True),
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.team_id'), primary_key=True),
        sa.Column('minutes', sa.String()),
        sa.Column('points', sa.Integer()),
        sa.Column('rebounds', sa.Integer()),
        sa.Column('assists', sa.Integer()),
        sa.Column('steals', sa.Integer()),
        sa.Column('blocks', sa.Integer()),
        sa.Column('fgm', sa.Integer()),
        sa.Column('fga', sa.Integer()),
        sa.Column('fg_pct', sa.Float()),
        sa.Column('tpm', sa.Integer()),
        sa.Column('tpa', sa.Integer()),
        sa.Column('tp_pct', sa.Float()),
        sa.Column('ftm', sa.Integer()),
        sa.Column('fta', sa.Integer()),
        sa.Column('ft_pct', sa.Float()),
        sa.Column('turnovers', sa.Integer()),
        sa.Column('fouls', sa.Integer()),
        sa.Column('plus_minus', sa.Integer()),
        sa.Column('last_updated', sa.DateTime())
    )

    # Copy data back, excluding stat_id
    op.execute(
        '''
        INSERT INTO player_game_stats_old (
            player_id, game_id, team_id, minutes, points, rebounds, assists,
            steals, blocks, fgm, fga, fg_pct, tpm, tpa, tp_pct, ftm, fta,
            ft_pct, turnovers, fouls, plus_minus, last_updated
        )
        SELECT 
            player_id, game_id, team_id, minutes, points, rebounds, assists,
            steals, blocks, fgm, fga, fg_pct, tpm, tpa, tp_pct, ftm, fta,
            ft_pct, turnovers, fouls, plus_minus, last_updated
        FROM player_game_stats
        '''
    )

    # Drop new table
    op.drop_table('player_game_stats')

    # Rename old table to original name
    op.rename_table('player_game_stats_old', 'player_game_stats')
