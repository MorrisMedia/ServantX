import json
from pathlib import Path
from typing import Any, Dict, List

import duckdb
from sqlalchemy import select

from core_services.db_service import AsyncSessionLocal
from models import AuditFinding, BatchRun, Document, ParsedData, Project
from services.project_service import ensure_workspace_directory


def _connect(path: Path):
    return duckdb.connect(str(path))


async def sync_project_workspace(project: Project) -> Dict[str, Any]:
    workspace_path = ensure_workspace_directory(project.workspace_duckdb_path or f"workspaces/{project.slug}/project.duckdb")

    async with AsyncSessionLocal() as db:
        batch_rows = list(
            (await db.execute(select(BatchRun).where(BatchRun.project_id == project.id))).scalars().all()
        )
        doc_rows = list(
            (await db.execute(select(Document).where(Document.project_id == project.id))).scalars().all()
        )
        parsed_rows = list(
            (await db.execute(select(ParsedData).join(Document, ParsedData.document_id == Document.id).where(Document.project_id == project.id))).scalars().all()
        )
        finding_rows = list(
            (await db.execute(select(AuditFinding).join(Document, AuditFinding.document_id == Document.id).where(Document.project_id == project.id))).scalars().all()
        )

    conn = _connect(workspace_path)
    conn.execute("create schema if not exists servantx")
    conn.execute("create or replace table servantx.batch_runs (id varchar, status varchar, payer_scope varchar, source_file_count integer, claim_document_count integer, processed_claim_count integer, failed_claim_count integer, executive_summary varchar, created_at varchar, updated_at varchar)")
    conn.execute("delete from servantx.batch_runs")
    if batch_rows:
        conn.executemany(
            "insert into servantx.batch_runs values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row.id,
                    row.status,
                    row.payer_scope,
                    row.source_file_count,
                    row.claim_document_count,
                    row.processed_claim_count,
                    row.failed_claim_count,
                    row.executive_summary,
                    row.created_at.isoformat() if row.created_at else None,
                    row.updated_at.isoformat() if row.updated_at else None,
                )
                for row in batch_rows
            ],
        )

    conn.execute("create or replace table servantx.documents (id varchar, batch_run_id varchar, payer_key varchar, status varchar, amount double, receipt_amount double, contract_amount double, underpayment_amount double, billing_npi varchar, rendering_npi varchar, facility_npi varchar, dos_start varchar, dos_end varchar)")
    conn.execute("delete from servantx.documents")
    if doc_rows:
        conn.executemany(
            "insert into servantx.documents values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    row.id,
                    row.batch_run_id,
                    row.payer_key,
                    row.status,
                    row.amount,
                    row.receipt_amount,
                    row.contract_amount,
                    row.underpayment_amount,
                    row.billing_npi,
                    row.rendering_npi,
                    row.facility_npi,
                    row.dos_start.isoformat() if row.dos_start else None,
                    row.dos_end.isoformat() if row.dos_end else None,
                )
                for row in doc_rows
            ],
        )

    conn.execute("create or replace table servantx.parsed_claims (document_id varchar, schema_version varchar, payload_json varchar)")
    conn.execute("delete from servantx.parsed_claims")
    if parsed_rows:
        conn.executemany(
            "insert into servantx.parsed_claims values (?, ?, ?)",
            [(row.document_id, row.schema_version, json.dumps(row.payload or {})) for row in parsed_rows],
        )

    conn.execute("create or replace table servantx.audit_findings (document_id varchar, finding_code varchar, severity varchar, confidence_score double, variance_amount double, metadata_json varchar)")
    conn.execute("delete from servantx.audit_findings")
    if finding_rows:
        conn.executemany(
            "insert into servantx.audit_findings values (?, ?, ?, ?, ?, ?)",
            [
                (
                    row.document_id,
                    row.finding_code,
                    row.severity,
                    row.confidence_score,
                    float(row.variance_amount) if row.variance_amount is not None else None,
                    json.dumps(row.metadata_json or {}),
                )
                for row in finding_rows
            ],
        )

    summary = conn.execute(
        "select count(*) as documents, coalesce(sum(underpayment_amount), 0) as total_underpayment from servantx.documents"
    ).fetchone()
    conn.close()
    return {
        "duckdbPath": str(workspace_path),
        "documentCount": int(summary[0]),
        "totalUnderpayment": float(summary[1] or 0.0),
        "tables": ["servantx.batch_runs", "servantx.documents", "servantx.parsed_claims", "servantx.audit_findings"],
    }
