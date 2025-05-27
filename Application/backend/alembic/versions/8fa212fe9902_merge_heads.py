"""merge_heads

Revision ID: 8fa212fe9902
Revises: 4f0aa53aa9c5, 765c2f861000, f94cc0915d18
Create Date: 2025-05-25 23:00:53.234393

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8fa212fe9902'
down_revision: Union[str, None] = ('4f0aa53aa9c5', '765c2f861000', 'f94cc0915d18')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
