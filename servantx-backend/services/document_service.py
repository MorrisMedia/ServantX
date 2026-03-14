from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from models import Document, DocumentRole
from core_services.db_service import AsyncSessionLocal
from sqlalchemy import func, or_

async def create_document(
    receipt_id: str,
    hospital_id: str,
    contract_id: Optional[str],
    amount: float,
    status: str = "not_submitted",
    name: Optional[str] = None,
    notes: Optional[str] = None,
    rules_applied: Optional[str] = None,
    receipt_amount: float = 0.0,
    contract_amount: float = 0.0,
    underpayment_amount: float = 0.0
) -> dict:
    async with AsyncSessionLocal() as db:
        document = Document(
            receipt_id=receipt_id,
            hospital_id=hospital_id,
            contract_id=contract_id,
            amount=amount,
            status=status,
            name=name,
            notes=notes,
            rules_applied=rules_applied,
            receipt_amount=receipt_amount,
            contract_amount=contract_amount,
            underpayment_amount=underpayment_amount
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        return {
            "id": document.id,
            "receiptId": document.receipt_id,
            "hospitalId": document.hospital_id,
            "contractId": document.contract_id,
            "name": document.name,
            "status": document.status,
            "amount": document.amount,
            "receiptAmount": document.receipt_amount,
            "contractAmount": document.contract_amount,
            "underpaymentAmount": document.underpayment_amount,
            "createdAt": document.created_at,
            "updatedAt": document.updated_at,
            "submittedAt": document.submitted_at,
            "notes": document.notes,
            "rulesApplied": document.rules_applied.split(",") if document.rules_applied else None,
            "isBulkDownloaded": document.is_bulk_downloaded
        }

async def get_document(document_id: str) -> Optional[dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).filter(Document.id == document_id))
        document = result.scalar_one_or_none()
        if not document:
            return None
        
        return {
            "id": document.id,
            "receiptId": document.receipt_id,
            "hospitalId": document.hospital_id,
            "contractId": document.contract_id,
            "batchRunId": document.batch_run_id,
            "documentRole": document.document_role.value if document.document_role else None,
            "parentDocumentId": document.parent_document_id,
            "payerKey": document.payer_key,
            "dosStart": document.dos_start,
            "dosEnd": document.dos_end,
            "billingNpi": document.billing_npi,
            "renderingNpi": document.rendering_npi,
            "facilityNpi": document.facility_npi,
            "sourceFileName": document.source_file_name,
            "sourceFilePath": document.source_file_path,
            "name": document.name,
            "status": document.status,
            "amount": document.amount,
            "receiptAmount": document.receipt_amount,
            "contractAmount": document.contract_amount,
            "underpaymentAmount": document.underpayment_amount,
            "createdAt": document.created_at,
            "updatedAt": document.updated_at,
            "submittedAt": document.submitted_at,
            "notes": document.notes,
            "rulesApplied": document.rules_applied.split(",") if document.rules_applied else None,
            "isBulkDownloaded": document.is_bulk_downloaded
        }

async def get_documents_by_receipt(receipt_id: str) -> List[dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).filter(Document.receipt_id == receipt_id))
        documents = result.scalars().all()
        
        return [
            {
                "id": doc.id,
                "receiptId": doc.receipt_id,
                "hospitalId": doc.hospital_id,
                "contractId": doc.contract_id,
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
                "isBulkDownloaded": doc.is_bulk_downloaded
            }
            for doc in documents
        ]

async def get_document_by_receipt(receipt_id: str) -> Optional[dict]:
    docs = await get_documents_by_receipt(receipt_id)
    return docs[0] if docs else None

async def get_all_documents(
    hospital_id: Optional[str] = None,
    status: Optional[List[str]] = None,
    search: Optional[str] = None,
    receipt_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 15,
    offset: int = 0,
    document_roles: Optional[List[str]] = None
) -> tuple[List[dict], int]:
    async with AsyncSessionLocal() as db:        
        query = select(Document)
        count_query = select(func.count(Document.id))

        # Documents tab should only surface records generated from billing records.
        # Legacy orphan rows (receipt_id is null) can exist from prior flows/migrations.
        query = query.filter(Document.receipt_id.is_not(None))
        count_query = count_query.filter(Document.receipt_id.is_not(None))

        if document_roles:
            query = query.filter(Document.document_role.in_(document_roles))
            count_query = count_query.filter(Document.document_role.in_(document_roles))
        else:
            query = query.filter(Document.document_role == DocumentRole.LEGACY)
            count_query = count_query.filter(Document.document_role == DocumentRole.LEGACY)
        
        if hospital_id:
            query = query.filter(Document.hospital_id == hospital_id)
            count_query = count_query.filter(Document.hospital_id == hospital_id)
        
        if status:
            query = query.filter(Document.status.in_(status))
            count_query = count_query.filter(Document.status.in_(status))
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Document.name.ilike(search_pattern),
                    Document.receipt_id.ilike(search_pattern)
                )
            )
            count_query = count_query.filter(
                or_(
                    Document.name.ilike(search_pattern),
                    Document.receipt_id.ilike(search_pattern)
                )
            )
        
        if receipt_id:
            query = query.filter(Document.receipt_id == receipt_id)
            count_query = count_query.filter(Document.receipt_id == receipt_id)
        
        if date_from:
            query = query.filter(Document.created_at >= date_from)
            count_query = count_query.filter(Document.created_at >= date_from)
        
        if date_to:
            query = query.filter(Document.created_at <= date_to)
            count_query = count_query.filter(Document.created_at <= date_to)
        
        query = query.order_by(Document.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        items = [
            {
                "id": doc.id,
                "receiptId": doc.receipt_id,
                "hospitalId": doc.hospital_id,
                "contractId": doc.contract_id,
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
                "isBulkDownloaded": doc.is_bulk_downloaded
            }
            for doc in documents
        ]
        
        return items, total

async def update_document(document_id: str, **kwargs) -> Optional[dict]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).filter(Document.id == document_id))
        document = result.scalar_one_or_none()
        if not document:
            return None
        
        for key, value in kwargs.items():
            snake_key = key
            if key == "receiptId":
                snake_key = "receipt_id"
            elif key == "hospitalId":
                snake_key = "hospital_id"
            elif key == "contractId":
                snake_key = "contract_id"
            elif key == "createdAt":
                snake_key = "created_at"
            elif key == "updatedAt":
                snake_key = "updated_at"
            elif key == "submittedAt":
                snake_key = "submitted_at"
            elif key == "rulesApplied" and isinstance(value, list):
                snake_key = "rules_applied"
                value = ",".join(value)
            elif key == "isBulkDownloaded":
                snake_key = "is_bulk_downloaded"
            
            if hasattr(document, snake_key):
                setattr(document, snake_key, value)
        
        await db.commit()
        await db.refresh(document)
        
        return {
            "id": document.id,
            "receiptId": document.receipt_id,
            "hospitalId": document.hospital_id,
            "contractId": document.contract_id,
            "name": document.name,
            "status": document.status,
            "amount": document.amount,
            "receiptAmount": document.receipt_amount,
            "contractAmount": document.contract_amount,
            "underpaymentAmount": document.underpayment_amount,
            "createdAt": document.created_at,
            "updatedAt": document.updated_at,
            "submittedAt": document.submitted_at,
            "notes": document.notes,
            "rulesApplied": document.rules_applied.split(",") if document.rules_applied else None,
            "isBulkDownloaded": document.is_bulk_downloaded
        }

async def delete_documents_by_receipt(receipt_id: str) -> int:
    """Delete all documents linked to a receipt. Used before re-scanning."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document).filter(Document.receipt_id == receipt_id)
        )
        documents = result.scalars().all()
        count = len(documents)
        for doc in documents:
            await db.delete(doc)
        if count:
            await db.commit()
        return count


async def mark_documents_bulk_downloaded(document_ids: List[str], hospital_id: str) -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document).filter(
                Document.id.in_(document_ids),
                Document.hospital_id == hospital_id
            )
        )
        documents = result.scalars().all()
        
        count = 0
        for document in documents:
            document.is_bulk_downloaded = True
            count += 1
        
        await db.commit()
        return count
