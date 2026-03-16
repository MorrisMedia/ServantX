"""add tx medicaid pricing context columns

Revision ID: 20260316_02_tx_medicaid_context_columns
Revises: 20260314_01_project_spine
Create Date: 2026-03-16 04:50:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = '20260316_02_tx_medicaid_context_columns'
down_revision = '20260314_01_project_spine'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('tx_medicaid_ffs_fee_schedule') as batch_op:
        batch_op.add_column(sa.Column('pricing_context', sa.String(), nullable=False, server_default='STANDARD'))
        batch_op.add_column(sa.Column('source_code', sa.String(), nullable=True))
        batch_op.create_index('ix_tx_medicaid_ffs_fee_schedule_pricing_context', ['pricing_context'], unique=False)
        batch_op.create_index('ix_tx_medicaid_ffs_fee_schedule_source_code', ['source_code'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('tx_medicaid_ffs_fee_schedule') as batch_op:
        batch_op.drop_index('ix_tx_medicaid_ffs_fee_schedule_source_code')
        batch_op.drop_index('ix_tx_medicaid_ffs_fee_schedule_pricing_context')
        batch_op.drop_column('source_code')
        batch_op.drop_column('pricing_context')
