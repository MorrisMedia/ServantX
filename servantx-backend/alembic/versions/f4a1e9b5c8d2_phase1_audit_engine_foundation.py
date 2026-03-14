"""phase1 audit engine foundation

Revision ID: f4a1e9b5c8d2
Revises: 70875d6d5be7
Create Date: 2026-02-12 14:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f4a1e9b5c8d2"
down_revision: Union[str, None] = "70875d6d5be7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    document_role_enum = postgresql.ENUM(
        "LEGACY",
        "FILE",
        "CLAIM",
        name="document_role_enum",
        create_type=False,
    )
    entity_type_enum = postgresql.ENUM(
        "BILLING_NPI",
        "RENDERING_NPI",
        "FACILITY_NPI",
        "TAX_ID",
        name="entity_type_enum",
        create_type=False,
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'document_role_enum') THEN
                CREATE TYPE document_role_enum AS ENUM ('LEGACY', 'FILE', 'CLAIM');
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'entity_type_enum') THEN
                CREATE TYPE entity_type_enum AS ENUM ('BILLING_NPI', 'RENDERING_NPI', 'FACILITY_NPI', 'TAX_ID');
            END IF;
        END
        $$;
        """
    )

    op.create_table(
        "batch_runs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("hospital_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("payer_scope", sa.String(), nullable=False),
        sa.Column("source_file_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("claim_document_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_claim_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_claim_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("executive_summary", sa.Text(), nullable=True),
        sa.Column("reconciliation_json", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_batch_runs_hospital_id"), "batch_runs", ["hospital_id"], unique=False)

    op.add_column("documents", sa.Column("batch_run_id", sa.String(), nullable=True))
    op.add_column(
        "documents",
        sa.Column("document_role", document_role_enum, nullable=False, server_default="LEGACY"),
    )
    op.add_column("documents", sa.Column("parent_document_id", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("payer_key", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("dos_start", sa.Date(), nullable=True))
    op.add_column("documents", sa.Column("dos_end", sa.Date(), nullable=True))
    op.add_column("documents", sa.Column("billing_npi", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("rendering_npi", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("facility_npi", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("source_file_name", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("source_file_path", sa.String(), nullable=True))

    op.alter_column("documents", "document_role", server_default=None)
    op.alter_column("documents", "receipt_id", existing_type=sa.String(), nullable=True)

    op.create_foreign_key(
        "fk_documents_batch_run_id_batch_runs",
        "documents",
        "batch_runs",
        ["batch_run_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_documents_parent_document_id_documents",
        "documents",
        "documents",
        ["parent_document_id"],
        ["id"],
    )
    op.create_index(op.f("ix_documents_batch_run_id"), "documents", ["batch_run_id"], unique=False)
    op.create_index(op.f("ix_documents_document_role"), "documents", ["document_role"], unique=False)
    op.create_index(op.f("ix_documents_parent_document_id"), "documents", ["parent_document_id"], unique=False)
    op.create_index(op.f("ix_documents_payer_key"), "documents", ["payer_key"], unique=False)

    op.create_table(
        "parsed_data",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("document_id", sa.String(), nullable=False),
        sa.Column("schema_version", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["batch_runs.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
    )
    op.create_index(op.f("ix_parsed_data_batch_id"), "parsed_data", ["batch_id"], unique=False)
    op.create_index(op.f("ix_parsed_data_document_id"), "parsed_data", ["document_id"], unique=False)

    op.create_table(
        "audit_findings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("document_id", sa.String(), nullable=False),
        sa.Column("finding_code", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("variance_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["batch_runs.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_findings_batch_id"), "audit_findings", ["batch_id"], unique=False)
    op.create_index(op.f("ix_audit_findings_document_id"), "audit_findings", ["document_id"], unique=False)
    op.create_index(op.f("ix_audit_findings_finding_code"), "audit_findings", ["finding_code"], unique=False)
    op.create_index(op.f("ix_audit_findings_severity"), "audit_findings", ["severity"], unique=False)

    op.create_table(
        "audit_notes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=True),
        sa.Column("document_id", sa.String(), nullable=True),
        sa.Column("note_type", sa.String(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["batch_runs.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_notes_batch_id"), "audit_notes", ["batch_id"], unique=False)
    op.create_index(op.f("ix_audit_notes_document_id"), "audit_notes", ["document_id"], unique=False)

    op.create_table(
        "rate_versions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("payer_key", sa.String(), nullable=False),
        sa.Column("version_label", sa.String(), nullable=False),
        sa.Column("effective_start", sa.Date(), nullable=True),
        sa.Column("effective_end", sa.Date(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sha256", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rate_versions_payer_key"), "rate_versions", ["payer_key"], unique=False)

    op.create_table(
        "medicare_rvu_rates",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("cpt_hcpcs", sa.String(), nullable=False),
        sa.Column("work_rvu", sa.Numeric(12, 4), nullable=False),
        sa.Column("pe_rvu_facility", sa.Numeric(12, 4), nullable=False),
        sa.Column("pe_rvu_nonfacility", sa.Numeric(12, 4), nullable=False),
        sa.Column("mp_rvu", sa.Numeric(12, 4), nullable=False),
        sa.Column("status_indicator", sa.String(), nullable=True),
        sa.Column("global_days", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_medicare_rvu_rates_cpt_hcpcs"), "medicare_rvu_rates", ["cpt_hcpcs"], unique=False)
    op.create_index(op.f("ix_medicare_rvu_rates_year"), "medicare_rvu_rates", ["year"], unique=False)

    op.create_table(
        "medicare_gpci",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("locality_code", sa.String(), nullable=False),
        sa.Column("locality_name", sa.String(), nullable=False),
        sa.Column("work_gpci", sa.Numeric(12, 4), nullable=False),
        sa.Column("pe_gpci", sa.Numeric(12, 4), nullable=False),
        sa.Column("mp_gpci", sa.Numeric(12, 4), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_medicare_gpci_locality_code"), "medicare_gpci", ["locality_code"], unique=False)
    op.create_index(op.f("ix_medicare_gpci_year"), "medicare_gpci", ["year"], unique=False)

    op.create_table(
        "medicare_conversion_factor",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("conversion_factor", sa.Numeric(12, 4), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_medicare_conversion_factor_year"), "medicare_conversion_factor", ["year"], unique=True)

    op.create_table(
        "medicare_zip_locality",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("zip_code", sa.String(), nullable=False),
        sa.Column("locality_code", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_medicare_zip_locality_locality_code"), "medicare_zip_locality", ["locality_code"], unique=False)
    op.create_index(op.f("ix_medicare_zip_locality_zip_code"), "medicare_zip_locality", ["zip_code"], unique=False)

    op.create_table(
        "locality_overrides",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("entity_type", entity_type_enum, nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("zip_code", sa.String(), nullable=True),
        sa.Column("locality_code", sa.String(), nullable=False),
        sa.Column("effective_start", sa.Date(), nullable=True),
        sa.Column("effective_end", sa.Date(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_locality_overrides_entity_id"), "locality_overrides", ["entity_id"], unique=False)
    op.create_index(op.f("ix_locality_overrides_entity_type"), "locality_overrides", ["entity_type"], unique=False)

    op.create_table(
        "tx_medicaid_ffs_fee_schedule",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("effective_start", sa.Date(), nullable=False),
        sa.Column("effective_end", sa.Date(), nullable=True),
        sa.Column("cpt_hcpcs", sa.String(), nullable=False),
        sa.Column("modifier", sa.String(), nullable=True),
        sa.Column("allowed_amount", sa.Numeric(12, 2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tx_medicaid_ffs_fee_schedule_cpt_hcpcs"), "tx_medicaid_ffs_fee_schedule", ["cpt_hcpcs"], unique=False)
    op.create_index(op.f("ix_tx_medicaid_ffs_fee_schedule_effective_end"), "tx_medicaid_ffs_fee_schedule", ["effective_end"], unique=False)
    op.create_index(op.f("ix_tx_medicaid_ffs_fee_schedule_effective_start"), "tx_medicaid_ffs_fee_schedule", ["effective_start"], unique=False)
    op.create_index(op.f("ix_tx_medicaid_ffs_fee_schedule_modifier"), "tx_medicaid_ffs_fee_schedule", ["modifier"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tx_medicaid_ffs_fee_schedule_modifier"), table_name="tx_medicaid_ffs_fee_schedule")
    op.drop_index(op.f("ix_tx_medicaid_ffs_fee_schedule_effective_start"), table_name="tx_medicaid_ffs_fee_schedule")
    op.drop_index(op.f("ix_tx_medicaid_ffs_fee_schedule_effective_end"), table_name="tx_medicaid_ffs_fee_schedule")
    op.drop_index(op.f("ix_tx_medicaid_ffs_fee_schedule_cpt_hcpcs"), table_name="tx_medicaid_ffs_fee_schedule")
    op.drop_table("tx_medicaid_ffs_fee_schedule")

    op.drop_index(op.f("ix_locality_overrides_entity_type"), table_name="locality_overrides")
    op.drop_index(op.f("ix_locality_overrides_entity_id"), table_name="locality_overrides")
    op.drop_table("locality_overrides")

    op.drop_index(op.f("ix_medicare_zip_locality_zip_code"), table_name="medicare_zip_locality")
    op.drop_index(op.f("ix_medicare_zip_locality_locality_code"), table_name="medicare_zip_locality")
    op.drop_table("medicare_zip_locality")

    op.drop_index(op.f("ix_medicare_conversion_factor_year"), table_name="medicare_conversion_factor")
    op.drop_table("medicare_conversion_factor")

    op.drop_index(op.f("ix_medicare_gpci_year"), table_name="medicare_gpci")
    op.drop_index(op.f("ix_medicare_gpci_locality_code"), table_name="medicare_gpci")
    op.drop_table("medicare_gpci")

    op.drop_index(op.f("ix_medicare_rvu_rates_year"), table_name="medicare_rvu_rates")
    op.drop_index(op.f("ix_medicare_rvu_rates_cpt_hcpcs"), table_name="medicare_rvu_rates")
    op.drop_table("medicare_rvu_rates")

    op.drop_index(op.f("ix_rate_versions_payer_key"), table_name="rate_versions")
    op.drop_table("rate_versions")

    op.drop_index(op.f("ix_audit_notes_document_id"), table_name="audit_notes")
    op.drop_index(op.f("ix_audit_notes_batch_id"), table_name="audit_notes")
    op.drop_table("audit_notes")

    op.drop_index(op.f("ix_audit_findings_severity"), table_name="audit_findings")
    op.drop_index(op.f("ix_audit_findings_finding_code"), table_name="audit_findings")
    op.drop_index(op.f("ix_audit_findings_document_id"), table_name="audit_findings")
    op.drop_index(op.f("ix_audit_findings_batch_id"), table_name="audit_findings")
    op.drop_table("audit_findings")

    op.drop_index(op.f("ix_parsed_data_document_id"), table_name="parsed_data")
    op.drop_index(op.f("ix_parsed_data_batch_id"), table_name="parsed_data")
    op.drop_table("parsed_data")

    op.drop_index(op.f("ix_documents_payer_key"), table_name="documents")
    op.drop_index(op.f("ix_documents_parent_document_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_document_role"), table_name="documents")
    op.drop_index(op.f("ix_documents_batch_run_id"), table_name="documents")
    op.drop_constraint("fk_documents_parent_document_id_documents", "documents", type_="foreignkey")
    op.drop_constraint("fk_documents_batch_run_id_batch_runs", "documents", type_="foreignkey")
    op.drop_column("documents", "source_file_path")
    op.drop_column("documents", "source_file_name")
    op.drop_column("documents", "facility_npi")
    op.drop_column("documents", "rendering_npi")
    op.drop_column("documents", "billing_npi")
    op.drop_column("documents", "dos_end")
    op.drop_column("documents", "dos_start")
    op.drop_column("documents", "payer_key")
    op.drop_column("documents", "parent_document_id")
    op.drop_column("documents", "document_role")
    op.drop_column("documents", "batch_run_id")
    op.alter_column("documents", "receipt_id", existing_type=sa.String(), nullable=False)

    op.drop_index(op.f("ix_batch_runs_hospital_id"), table_name="batch_runs")
    op.drop_table("batch_runs")

    op.execute("DROP TYPE IF EXISTS entity_type_enum")
    op.execute("DROP TYPE IF EXISTS document_role_enum")
