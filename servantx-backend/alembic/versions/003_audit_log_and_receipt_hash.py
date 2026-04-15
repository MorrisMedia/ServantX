"""Add app_audit_log table and file_hash column to receipts

Revision ID: 003_audit_log_and_receipt_hash
Revises: 002_hospital_pricing
Create Date: 2026-04-15
"""

from alembic import op
import sqlalchemy as sa

revision = "003_audit_log_and_receipt_hash"
down_revision = "002_hospital_pricing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create app_audit_log table
    op.create_table(
        "app_audit_log",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("hospital_id", sa.String(), nullable=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=True),
        sa.Column("resource_id", sa.String(), nullable=True),
        sa.Column("ip_address", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_app_audit_log_hospital_id", "app_audit_log", ["hospital_id"])
    op.create_index("ix_app_audit_log_user_id", "app_audit_log", ["user_id"])
    op.create_index("ix_app_audit_log_event_type", "app_audit_log", ["event_type"])
    op.create_index("ix_app_audit_log_resource_id", "app_audit_log", ["resource_id"])
    op.create_index("ix_app_audit_log_created_at", "app_audit_log", ["created_at"])

    # Add file_hash to receipts
    op.add_column(
        "receipts",
        sa.Column("file_hash", sa.String(64), nullable=True),
    )
    op.create_index("ix_receipts_file_hash", "receipts", ["file_hash"])


def downgrade() -> None:
    op.drop_index("ix_receipts_file_hash", table_name="receipts")
    op.drop_column("receipts", "file_hash")

    op.drop_index("ix_app_audit_log_created_at", table_name="app_audit_log")
    op.drop_index("ix_app_audit_log_resource_id", table_name="app_audit_log")
    op.drop_index("ix_app_audit_log_event_type", table_name="app_audit_log")
    op.drop_index("ix_app_audit_log_user_id", table_name="app_audit_log")
    op.drop_index("ix_app_audit_log_hospital_id", table_name="app_audit_log")
    op.drop_table("app_audit_log")
