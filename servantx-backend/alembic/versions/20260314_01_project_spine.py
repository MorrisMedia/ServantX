"""project centered audit spine

Revision ID: 20260314_01
Revises: f4a1e9b5c8d2
Create Date: 2026-03-14 14:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260314_01"
down_revision = "f4a1e9b5c8d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("hospital_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("payer_scope", sa.String(), nullable=True),
        sa.Column("workspace_duckdb_path", sa.String(), nullable=True),
        sa.Column("storage_prefix", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hospital_id", "slug", name="uq_projects_hospital_slug"),
    )
    op.create_index(op.f("ix_projects_hospital_id"), "projects", ["hospital_id"], unique=False)
    op.create_index(op.f("ix_projects_slug"), "projects", ["slug"], unique=False)

    for table in ("contracts", "receipts", "batch_runs", "documents"):
        op.add_column(table, sa.Column("project_id", sa.String(), nullable=True))
        op.create_index(op.f(f"ix_{table}_project_id"), table, ["project_id"], unique=False)
        op.create_foreign_key(f"fk_{table}_project_id_projects", table, "projects", ["project_id"], ["id"])

    op.create_table(
        "project_artifacts",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("hospital_id", sa.String(), nullable=False),
        sa.Column("document_id", sa.String(), nullable=True),
        sa.Column("artifact_type", sa.String(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("original_file_name", sa.String(), nullable=True),
        sa.Column("content_type", sa.String(), nullable=True),
        sa.Column("byte_size", sa.Integer(), nullable=True),
        sa.Column("sha256", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_project_artifacts_project_id"), "project_artifacts", ["project_id"], unique=False)
    op.create_index(op.f("ix_project_artifacts_hospital_id"), "project_artifacts", ["hospital_id"], unique=False)
    op.create_index(op.f("ix_project_artifacts_document_id"), "project_artifacts", ["document_id"], unique=False)
    op.create_index(op.f("ix_project_artifacts_artifact_type"), "project_artifacts", ["artifact_type"], unique=False)
    op.create_index(op.f("ix_project_artifacts_sha256"), "project_artifacts", ["sha256"], unique=False)

    op.create_table(
        "truth_verification_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("hospital_id", sa.String(), nullable=False),
        sa.Column("batch_run_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("verification_summary", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["batch_run_id"], ["batch_runs.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_truth_verification_runs_project_id"), "truth_verification_runs", ["project_id"], unique=False)
    op.create_index(op.f("ix_truth_verification_runs_hospital_id"), "truth_verification_runs", ["hospital_id"], unique=False)
    op.create_index(op.f("ix_truth_verification_runs_batch_run_id"), "truth_verification_runs", ["batch_run_id"], unique=False)

    op.create_table(
        "formal_audit_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("hospital_id", sa.String(), nullable=False),
        sa.Column("batch_run_id", sa.String(), nullable=True),
        sa.Column("verification_run_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("audit_standard", sa.String(), nullable=False, server_default="MEDICAL_AUDIT_V1"),
        sa.Column("report_json", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["batch_run_id"], ["batch_runs.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["verification_run_id"], ["truth_verification_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_formal_audit_runs_project_id"), "formal_audit_runs", ["project_id"], unique=False)
    op.create_index(op.f("ix_formal_audit_runs_hospital_id"), "formal_audit_runs", ["hospital_id"], unique=False)
    op.create_index(op.f("ix_formal_audit_runs_batch_run_id"), "formal_audit_runs", ["batch_run_id"], unique=False)
    op.create_index(op.f("ix_formal_audit_runs_verification_run_id"), "formal_audit_runs", ["verification_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_formal_audit_runs_verification_run_id"), table_name="formal_audit_runs")
    op.drop_index(op.f("ix_formal_audit_runs_batch_run_id"), table_name="formal_audit_runs")
    op.drop_index(op.f("ix_formal_audit_runs_hospital_id"), table_name="formal_audit_runs")
    op.drop_index(op.f("ix_formal_audit_runs_project_id"), table_name="formal_audit_runs")
    op.drop_table("formal_audit_runs")

    op.drop_index(op.f("ix_truth_verification_runs_batch_run_id"), table_name="truth_verification_runs")
    op.drop_index(op.f("ix_truth_verification_runs_hospital_id"), table_name="truth_verification_runs")
    op.drop_index(op.f("ix_truth_verification_runs_project_id"), table_name="truth_verification_runs")
    op.drop_table("truth_verification_runs")

    op.drop_index(op.f("ix_project_artifacts_sha256"), table_name="project_artifacts")
    op.drop_index(op.f("ix_project_artifacts_artifact_type"), table_name="project_artifacts")
    op.drop_index(op.f("ix_project_artifacts_document_id"), table_name="project_artifacts")
    op.drop_index(op.f("ix_project_artifacts_hospital_id"), table_name="project_artifacts")
    op.drop_index(op.f("ix_project_artifacts_project_id"), table_name="project_artifacts")
    op.drop_table("project_artifacts")

    for table in ("documents", "batch_runs", "receipts", "contracts"):
        op.drop_constraint(f"fk_{table}_project_id_projects", table, type_="foreignkey")
        op.drop_index(op.f(f"ix_{table}_project_id"), table_name=table)
        op.drop_column(table, "project_id")

    op.drop_index(op.f("ix_projects_slug"), table_name="projects")
    op.drop_index(op.f("ix_projects_hospital_id"), table_name="projects")
    op.drop_table("projects")
