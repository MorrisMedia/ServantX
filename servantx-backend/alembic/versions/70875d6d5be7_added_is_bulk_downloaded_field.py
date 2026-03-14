"""Added is_bulk_downloaded field

Revision ID: 70875d6d5be7
Revises: bac1d1dc91c0
Create Date: 2026-02-02 11:02:12.050138

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70875d6d5be7'
down_revision: Union[str, None] = 'bac1d1dc91c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.add_column('documents', sa.Column('is_bulk_downloaded', sa.Boolean(), nullable=False, server_default='false'))
    op.alter_column('documents', 'is_bulk_downloaded', server_default=None)


def downgrade() -> None:
    op.drop_column('documents', 'is_bulk_downloaded')
