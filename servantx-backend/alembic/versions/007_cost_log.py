# servantx-backend/alembic/versions/007_cost_log.py
"""Add ai_cost_log table for per-call cost tracking

Revision ID: 007_cost_log
Revises: 006_document_appeal_fields
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa

revision = "007_cost_log"
down_revision = "006_document_appeal_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_cost_log",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("hospital_id", sa.String(), sa.ForeignKey("hospitals.id"), nullable=True, index=True),
        sa.Column("document_id", sa.String(), nullable=True, index=True),
        sa.Column("batch_run_id", sa.String(), nullable=True, index=True),
        sa.Column("service", sa.String(), nullable=False, index=True),   # "underpayment_analysis" | "contract_extraction" | "appeal_letter" | "contract_chat" | "benchmark"
        sa.Column("provider", sa.String(), nullable=False, index=True),  # "openai" | "anthropic"
        sa.Column("model", sa.String(), nullable=False),                  # "gpt-4.1" | "claude-sonnet-4-6"
        sa.Column("input_tokens", sa.Integer(), nullable=False, default=0),
        sa.Column("output_tokens", sa.Integer(), nullable=False, default=0),
        sa.Column("cache_read_tokens", sa.Integer(), nullable=False, default=0),   # Anthropic cache_read_input_tokens
        sa.Column("cache_write_tokens", sa.Integer(), nullable=False, default=0),  # Anthropic cache_creation_input_tokens
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, default=0),      # computed dollar cost
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, default=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_ai_cost_log_created_at", "ai_cost_log", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_cost_log_created_at", table_name="ai_cost_log")
    op.drop_table("ai_cost_log")
