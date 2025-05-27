"""add_previous_team_and_traded_date

Revision ID: 285029f4cca0
Revises: e5aa6e90e9d7
Create Date: 2025-05-22 13:47:56.551421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '285029f4cca0'
down_revision: Union[str, None] = 'e5aa6e90e9d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add foreign key constraint
    with op.batch_alter_table("players", recreate="always") as batch_op:
        batch_op.create_foreign_key(
            constraint_name='fk_players_previous_team',
            local_cols=['previous_team_id'],
            referent_table='teams',
            remote_cols=['team_id']
        )


def downgrade() -> None:
    # Remove the foreign key constraint
    with op.batch_alter_table("players", recreate="always") as batch_op:
        batch_op.drop_constraint('fk_players_previous_team', type_='foreignkey')
