"""add_missing_columns

Revision ID: 4f0aa53aa9c5
Revises: 7812903378f3
Create Date: 2025-05-22 11:49:14.416678

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f0aa53aa9c5'
down_revision: Union[str, None] = '285029f4cca0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns
    op.add_column('players', sa.Column('headshot_url', sa.String(), nullable=True))
    op.add_column('games', sa.Column('season_year', sa.String(), nullable=True))

    # Drop old score columns
    op.drop_column('games', 'home_team_score')
    op.drop_column('games', 'away_team_score')

    # Add new score columns with correct names
    op.add_column('games', sa.Column('home_score', sa.Integer(), nullable=True))
    op.add_column('games', sa.Column('away_score', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Revert score column changes
    op.drop_column('games', 'home_score')
    op.drop_column('games', 'away_score')
    op.add_column('games', sa.Column('home_team_score', sa.Integer(), nullable=True))
    op.add_column('games', sa.Column('away_team_score', sa.Integer(), nullable=True))

    # Drop other columns
    op.drop_column('games', 'season_year')
    op.drop_column('players', 'headshot_url')
