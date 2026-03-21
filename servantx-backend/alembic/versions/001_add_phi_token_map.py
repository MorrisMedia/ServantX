"""add phi_token_map table for HIPAA PHI de-identification

Revision ID: 001_phi_token_map
Revises:
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa

revision = "001_phi_token_map"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "phi_token_map",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("hospital_id", sa.String(), nullable=False),
        sa.Column("document_id", sa.String(), nullable=True),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("phi_field", sa.String(), nullable=False),
        sa.Column("phi_value", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hospital_id", "token", name="uq_phi_token_map_hospital_token"),
    )
    op.create_index("ix_phi_token_map_hospital_id", "phi_token_map", ["hospital_id"])
    op.create_index("ix_phi_token_map_document_id", "phi_token_map", ["document_id"])
    op.create_index("ix_phi_token_map_token", "phi_token_map", ["token"])


def downgrade() -> None:
    op.drop_index("ix_phi_token_map_token", table_name="phi_token_map")
    op.drop_index("ix_phi_token_map_document_id", table_name="phi_token_map")
    op.drop_index("ix_phi_token_map_hospital_id", table_name="phi_token_map")
    op.drop_table("phi_token_map")
