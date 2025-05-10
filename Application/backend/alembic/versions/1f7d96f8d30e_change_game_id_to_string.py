"""change_game_id_to_string

Revision ID: 1f7d96f8d30e
Revises: a61ad8e90a6e
Create Date: 2025-05-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1f7d96f8d30e'
down_revision = 'a61ad8e90a6e'
branch_labels = None
depends_on = None

def upgrade():
    # Create new games table with string game_id
    op.create_table(
        'games_new',
        sa.Column('game_id', sa.String(), nullable=False),
        sa.Column('game_date_utc', sa.DateTime(), nullable=False),
        sa.Column('home_team_id', sa.Integer(), nullable=False),
        sa.Column('away_team_id', sa.Integer(), nullable=False),
        sa.Column('home_score', sa.Integer()),
        sa.Column('away_score', sa.Integer()),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('season_year', sa.String(), nullable=False),
        sa.Column('last_updated', sa.DateTime()),
        sa.ForeignKeyConstraint(['away_team_id'], ['teams.team_id'], ),
        sa.ForeignKeyConstraint(['home_team_id'], ['teams.team_id'], ),
        sa.PrimaryKeyConstraint('game_id')
    )
    
    # Copy data, converting game_id to string
    op.execute(
        'INSERT INTO games_new SELECT CAST(game_id AS VARCHAR), game_date_utc, home_team_id, '
        'away_team_id, home_score, away_score, status, season_year, last_updated FROM games'
    )
    
    # Drop old table and rename new one
    op.drop_table('games')
    op.rename_table('games_new', 'games')
    
    # Do the same for player_game_stats
    op.create_table(
        'player_game_stats_new',
        sa.Column('stat_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('player_id', sa.Integer()),
        sa.Column('game_id', sa.String()),
        sa.Column('team_id', sa.Integer()),
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
        sa.ForeignKeyConstraint(['game_id'], ['games.game_id'], ),
        sa.ForeignKeyConstraint(['player_id'], ['players.player_id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.team_id'], ),
        sa.PrimaryKeyConstraint('stat_id'),
        sa.UniqueConstraint('player_id', 'game_id', 'team_id', name='unique_player_game_stats')
    )
    
    # Copy data, converting game_id to string
    op.execute(
        'INSERT INTO player_game_stats_new SELECT stat_id, player_id, CAST(game_id AS VARCHAR), '
        'team_id, minutes, points, rebounds, assists, steals, blocks, fgm, fga, fg_pct, '
        'tpm, tpa, tp_pct, ftm, fta, ft_pct, turnovers, fouls, plus_minus, last_updated '
        'FROM player_game_stats'
    )
    
    # Drop old table and rename new one
    op.drop_table('player_game_stats')
    op.rename_table('player_game_stats_new', 'player_game_stats')

def downgrade():
    # Create new games table with integer game_id
    op.create_table(
        'games_new',
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('game_date_utc', sa.DateTime(), nullable=False),
        sa.Column('home_team_id', sa.Integer(), nullable=False),
        sa.Column('away_team_id', sa.Integer(), nullable=False),
        sa.Column('home_score', sa.Integer()),
        sa.Column('away_score', sa.Integer()),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('season_year', sa.String(), nullable=False),
        sa.Column('last_updated', sa.DateTime()),
        sa.ForeignKeyConstraint(['away_team_id'], ['teams.team_id'], ),
        sa.ForeignKeyConstraint(['home_team_id'], ['teams.team_id'], ),
        sa.PrimaryKeyConstraint('game_id')
    )
    
    # Copy data, converting game_id to integer
    op.execute(
        'INSERT INTO games_new SELECT CAST(game_id AS INTEGER), game_date_utc, home_team_id, '
        'away_team_id, home_score, away_score, status, season_year, last_updated FROM games'
    )
    
    # Drop old table and rename new one
    op.drop_table('games')
    op.rename_table('games_new', 'games')
    
    # Do the same for player_game_stats
    op.create_table(
        'player_game_stats_new',
        sa.Column('stat_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('player_id', sa.Integer()),
        sa.Column('game_id', sa.Integer()),
        sa.Column('team_id', sa.Integer()),
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
        sa.ForeignKeyConstraint(['game_id'], ['games.game_id'], ),
        sa.ForeignKeyConstraint(['player_id'], ['players.player_id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.team_id'], ),
        sa.PrimaryKeyConstraint('stat_id'),
        sa.UniqueConstraint('player_id', 'game_id', 'team_id', name='unique_player_game_stats')
    )
    
    # Copy data, converting game_id to integer
    op.execute(
        'INSERT INTO player_game_stats_new SELECT stat_id, player_id, CAST(game_id AS INTEGER), '
        'team_id, minutes, points, rebounds, assists, steals, blocks, fgm, fga, fg_pct, '
        'tpm, tpa, tp_pct, ftm, fta, ft_pct, turnovers, fouls, plus_minus, last_updated '
        'FROM player_game_stats'
    )
    
    # Drop old table and rename new one
    op.drop_table('player_game_stats')
    op.rename_table('player_game_stats_new', 'player_game_stats')
