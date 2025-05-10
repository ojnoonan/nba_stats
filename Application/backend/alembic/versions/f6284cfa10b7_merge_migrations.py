"""merge_migrations

Revision ID: f6284cfa10b7
Revises: 1f7d96f8d30e, 6b9af70bc726
Create Date: 2025-05-09 22:21:21.116902

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6284cfa10b7'
down_revision: Union[str, None] = ('1f7d96f8d30e', '6b9af70bc726')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
