"""add medicare_drg_weights table

Revision ID: 005_drg_weights
Revises: 002_hospital_pricing
Create Date: 2026-04-15
"""

from alembic import op
import sqlalchemy as sa

revision = "005_drg_weights"
down_revision = "002_hospital_pricing"
branch_labels = "drg_weights"
depends_on = None


def upgrade() -> None:
    op.create_table(
        "medicare_drg_weights",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("drg_code", sa.String(10), nullable=False),
        sa.Column("drg_weight", sa.Numeric(10, 4), nullable=False),
        sa.Column("geometric_mean_los", sa.Numeric(6, 1), nullable=True),
        sa.Column("arithmetic_mean_los", sa.Numeric(6, 1), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index("ix_medicare_drg_weights_year", "medicare_drg_weights", ["year"])
    op.create_index("ix_medicare_drg_weights_drg_code", "medicare_drg_weights", ["drg_code"])


def downgrade() -> None:
    op.drop_index("ix_medicare_drg_weights_drg_code", table_name="medicare_drg_weights")
    op.drop_index("ix_medicare_drg_weights_year", table_name="medicare_drg_weights")
    op.drop_table("medicare_drg_weights")
