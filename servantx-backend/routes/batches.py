from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select

from config import settings
from core_services.db_service import AsyncSessionLocal
from models import AuditFinding, BatchRun as BatchRunModel
from models import Document, DocumentRole, ParsedData, Project
from routes.auth import get_current_user
from schemas import BatchRun, BatchUploadResponse, Document as DocumentSchema, PaginatedDocumentsResponse
from services.audit_pipeline_service import run_stage1_ingest_835_file
from services.file_service import save_835_file
from services.project_service import ensure_default_project
from tasks.ingest import task_ingest_835_file

router = APIRouter(prefix="/batches", tags=["batches"])


def _serialize_batch(batch: BatchRunModel) -> dict:
    return {
        "id": batch.id,
        "hospitalId": batch.hospital_id,
        "projectId": batch.project_id,
        "status": batch.status,
        "payerScope": batch.payer_scope,
        "sourceFileCount": batch.source_file_count,
        "claimDocumentCount": batch.claim_document_count,
        "processedClaimCount": batch.processed_claim_count,
        "failedClaimCount": batch.failed_claim_count,
        "executiveSummary": batch.executive_summary,
        "reconciliationJson": batch.reconciliation_json,
        "startedAt": batch.started_at,
        "finishedAt": batch.finished_at,
        "createdAt": batch.created_at,
        "updatedAt": batch.updated_at,
    }


def _serialize_document(doc: Document) -> dict:
    return {
        "id": doc.id,
        "receiptId": doc.receipt_id,
        "hospitalId": doc.hospital_id,
        "projectId": doc.project_id,
        "contractId": doc.contract_id,
        "batchRunId": doc.batch_run_id,
        "documentRole": doc.document_role.value if doc.document_role else None,
        "parentDocumentId": doc.parent_document_id,
        "payerKey": doc.payer_key,
        "dosStart": doc.dos_start,
        "dosEnd": doc.dos_end,
        "billingNpi": doc.billing_npi,
        "renderingNpi": doc.rendering_npi,
        "facilityNpi": doc.facility_npi,
        "sourceFileName": doc.source_file_name,
        "sourceFilePath": doc.source_file_path,
        "name": doc.name,
        "status": doc.status,
        "amount": doc.amount,
        "receiptAmount": doc.receipt_amount,
        "contractAmount": doc.contract_amount,
        "underpaymentAmount": doc.underpayment_amount,
        "createdAt": doc.created_at,
        "updatedAt": doc.updated_at,
        "submittedAt": doc.submitted_at,
        "notes": doc.notes,
        "rulesApplied": doc.rules_applied.split(",") if doc.rules_applied else None,
        "isBulkDownloaded": doc.is_bulk_downloaded,
    }


@router.post("/upload-835", response_model=BatchUploadResponse)
async def upload_835_files(
    files: List[UploadFile] = File(...),
    project_id: Optional[str] = Form(default=None),
    current_user: dict = Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one 835 file is required.")

    hospital_id = current_user["hospital_id"]
    file_document_ids: List[str] = []

    async with AsyncSessionLocal() as db:
        project = None
        if project_id:
            project = (
                await db.execute(
                    select(Project).where(Project.id == project_id, Project.hospital_id == hospital_id)
                )
            ).scalar_one_or_none()
            if not project:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        else:
            project = await ensure_default_project(hospital_id, current_user.get("id"))

        batch = BatchRunModel(
            hospital_id=hospital_id,
            project_id=project.id if project else None,
            status="queued",
            payer_scope=project.payer_scope if project and project.payer_scope else "MEDICARE_TX_MEDICAID_FFS",
            source_file_count=len(files),
            claim_document_count=0,
            processed_claim_count=0,
            failed_claim_count=0,
            started_at=datetime.utcnow(),
        )
        db.add(batch)
        await db.flush()

        for file in files:
            _, file_path, file_size = await save_835_file(file=file, hospital_id=hospital_id, project_id=batch.project_id)
            file_document = Document(
                receipt_id=None,
                hospital_id=hospital_id,
                project_id=batch.project_id,
                batch_run_id=batch.id,
                contract_id=None,
                document_role=DocumentRole.FILE,
                parent_document_id=None,
                payer_key=None,
                source_file_name=file.filename or "era.835",
                source_file_path=file_path,
                name=file.filename or "835 ERA File",
                status="queued_ingest",
                amount=0.0,
                receipt_amount=0.0,
                contract_amount=0.0,
                underpayment_amount=0.0,
                notes=f"size_bytes={file_size}",
                rules_applied=None,
            )
            db.add(file_document)
            await db.flush()
            file_document_ids.append(file_document.id)

        batch.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(batch)

    for document_id in file_document_ids:
        if settings.celery_async_enabled:
            try:
                task_ingest_835_file.delay(document_id, batch.id)
                continue
            except Exception:
                pass
        await run_stage1_ingest_835_file(file_document_id=document_id, batch_id=batch.id)

    return BatchUploadResponse(
        batch=BatchRun(**_serialize_batch(batch)),
        filesQueued=len(file_document_ids),
        message=f"Queued {len(file_document_ids)} file(s) for 835 ingest.",
    )


@router.get("/{batch_id}/status", response_model=BatchRun)
async def get_batch_status(batch_id: str, current_user: dict = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(BatchRunModel).where(BatchRunModel.id == batch_id, BatchRunModel.hospital_id == current_user["hospital_id"])
        )
        batch = result.scalar_one_or_none()
        if not batch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
        return BatchRun(**_serialize_batch(batch))


@router.get("/{batch_id}/documents", response_model=PaginatedDocumentsResponse)
async def get_batch_documents(batch_id: str, current_user: dict = Depends(get_current_user)):
    async with AsyncSessionLocal() as db:
        batch_result = await db.execute(
            select(BatchRunModel).where(BatchRunModel.id == batch_id, BatchRunModel.hospital_id == current_user["hospital_id"])
        )
        batch = batch_result.scalar_one_or_none()
        if not batch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

        docs_result = await db.execute(
            select(Document).where(Document.batch_run_id == batch_id, Document.hospital_id == current_user["hospital_id"])
        )
        docs = docs_result.scalars().all()
        doc_ids = [doc.id for doc in docs]

        parsed_map = {}
        findings_map = {}
        if doc_ids:
            parsed_result = await db.execute(select(ParsedData).where(ParsedData.document_id.in_(doc_ids)))
            for parsed in parsed_result.scalars().all():
                parsed_map[parsed.document_id] = parsed.payload

            finding_result = await db.execute(select(AuditFinding).where(AuditFinding.document_id.in_(doc_ids)))
            for finding in finding_result.scalars().all():
                findings_map.setdefault(finding.document_id, []).append(
                    {
                        "id": finding.id,
                        "findingCode": finding.finding_code,
                        "severity": finding.severity,
                        "confidenceScore": finding.confidence_score,
                        "varianceAmount": float(finding.variance_amount) if finding.variance_amount is not None else None,
                        "metadata": finding.metadata_json,
                        "createdAt": finding.created_at,
                    }
                )

        items = []
        for doc in docs:
            serialized = _serialize_document(doc)
            payload = parsed_map.get(doc.id)
            serialized["parsedData"] = payload
            serialized["repricingSummary"] = (payload or {}).get("repricing") if payload else None
            serialized["findings"] = findings_map.get(doc.id, [])
            items.append(DocumentSchema(**serialized))

        return PaginatedDocumentsResponse(items=items, total=len(items), limit=len(items) if items else 0, offset=0, hasMore=False)
