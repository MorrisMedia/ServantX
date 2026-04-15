"""add opps_apc_rates table

Revision ID: 004_opps_apc_rates
Revises: 002_hospital_pricing
Create Date: 2026-04-15
"""

from alembic import op
import sqlalchemy as sa

revision = "004_opps_apc_rates"
down_revision = "002_hospital_pricing"
branch_labels = "opps_apc"
depends_on = None


def upgrade() -> None:
    op.create_table(
        "opps_apc_rates",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("hcpcs_code", sa.String(10), nullable=False),
        sa.Column("apc_code", sa.String(10), nullable=False),
        sa.Column("payment_rate", sa.Numeric(12, 2), nullable=False),
        sa.Column("status_indicator", sa.String(5), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_opps_apc_rates_year", "opps_apc_rates", ["year"])
    op.create_index("ix_opps_apc_rates_hcpcs_code", "opps_apc_rates", ["hcpcs_code"])
    op.create_index("ix_opps_apc_rates_apc_code", "opps_apc_rates", ["apc_code"])


def downgrade() -> None:
    op.drop_index("ix_opps_apc_rates_apc_code", table_name="opps_apc_rates")
    op.drop_index("ix_opps_apc_rates_hcpcs_code", table_name="opps_apc_rates")
    op.drop_index("ix_opps_apc_rates_year", table_name="opps_apc_rates")
    op.drop_table("opps_apc_rates")
