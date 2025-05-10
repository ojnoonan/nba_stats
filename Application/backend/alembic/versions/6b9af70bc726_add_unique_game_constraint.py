"""add unique game constraint

Revision ID: 6b9af70bc726
Revises: efd93d7f13c5
Create Date: 2025-05-09 12:34:56.789012

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '6b9af70bc726'
down_revision: Union[str, None] = 'efd93d7f13c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # First, remove duplicate games by keeping only the most recently updated version
    conn = op.get_bind()
    conn.execute(text("""
        DELETE FROM games
        WHERE game_id IN (
            SELECT game_id
            FROM (
                SELECT game_id,
                       ROW_NUMBER() OVER (
                           PARTITION BY home_team_id, away_team_id, game_date_utc, season_year
                           ORDER BY last_updated DESC
                       ) as rn
                FROM games
            ) t
            WHERE t.rn > 1
        )
    """))

    # Create new table with constraint
    with op.batch_alter_table('games') as batch_op:
        batch_op.create_unique_constraint(
            'unique_game_matchup',
            ['home_team_id', 'away_team_id', 'game_date_utc', 'season_year']
        )

def downgrade() -> None:
    with op.batch_alter_table('games') as batch_op:
        batch_op.drop_constraint('unique_game_matchup')
