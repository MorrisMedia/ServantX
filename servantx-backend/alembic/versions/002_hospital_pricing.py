"""add pricing_mode and state columns to hospitals table

Revision ID: 002_hospital_pricing
Revises: 001_phi_token_map
Create Date: 2026-04-15
"""

from alembic import op
import sqlalchemy as sa

revision = "002_hospital_pricing"
down_revision = "001_phi_token_map"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "hospitals",
        sa.Column(
            "pricing_mode",
            sa.String(),
            nullable=False,
            server_default="AUTO",
        ),
    )
    op.add_column(
        "hospitals",
        sa.Column(
            "state",
            sa.String(2),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("hospitals", "state")
    op.drop_column("hospitals", "pricing_mode")
