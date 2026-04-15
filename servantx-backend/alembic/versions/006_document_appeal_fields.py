"""Add appeal and recovery fields to documents table

Revision ID: 006_document_appeal_fields
Revises: 003_audit_log_and_receipt_hash
Create Date: 2026-04-15
"""

from alembic import op
import sqlalchemy as sa

revision = "006_document_appeal_fields"
down_revision = "003_audit_log_and_receipt_hash"
branch_labels = "appeal_fields"
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("appeal_status", sa.String(), nullable=False, server_default="none"),
    )
    op.create_index("ix_documents_appeal_status", "documents", ["appeal_status"])

    op.add_column(
        "documents",
        sa.Column("appeal_letter", sa.Text(), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("recovered_amount", sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("appeal_filed_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("appeal_updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_index("ix_documents_appeal_status", table_name="documents")
    op.drop_column("documents", "appeal_status")
    op.drop_column("documents", "appeal_letter")
    op.drop_column("documents", "recovered_amount")
    op.drop_column("documents", "appeal_filed_at")
    op.drop_column("documents", "appeal_updated_at")
