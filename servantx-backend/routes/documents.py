from fastapi import APIRouter, HTTPException, status, Depends, Query, Body
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import select
from schemas import Document, PaginatedDocumentsResponse
from core_services.db_service import AsyncSessionLocal
from models import AuditFinding, ParsedData
from services.document_service import get_document, get_all_documents, update_document, mark_documents_bulk_downloaded
from services.audit_service import log_event
from routes.auth import get_current_user


class DocumentUpdateRequest(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    receiptAmount: Optional[float] = None
    contractAmount: Optional[float] = None
    underpaymentAmount: Optional[float] = None
    status: Optional[str] = None

class BulkDownloadRequest(BaseModel):
    documentIds: List[str]

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("/stats")
async def get_document_statistics(
    project_id: Optional[str] = Query(None, alias="projectId"),
    current_user: dict = Depends(get_current_user)
):
    try:
        hospital_id = current_user["hospital_id"]
        documents, _ = await get_all_documents(hospital_id=hospital_id, project_id=project_id, limit=10000, offset=0)
        
        total = len(documents)
        not_submitted = sum(1 for doc in documents if doc.get("status") == "not_submitted")
        in_progress = sum(1 for doc in documents if doc.get("status") == "in_progress")
        succeeded = sum(1 for doc in documents if doc.get("status") == "succeeded")
        failed = sum(1 for doc in documents if doc.get("status") == "failed")
        total_revenue = sum(doc.get("amount", 0) for doc in documents if doc.get("status") == "succeeded")
        total_underpayment = sum(doc.get("amount", 0) for doc in documents)
        
        return {
            "total": total,
            "notSubmitted": not_submitted,
            "inProgress": in_progress,
            "succeeded": succeeded,
            "failed": failed,
            "totalRevenue": total_revenue,
            "totalUnderpayment": total_underpayment
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch document statistics: {str(e)}"
        )

@router.get("", response_model=PaginatedDocumentsResponse)
async def get_documents(
    current_user: dict = Depends(get_current_user),
    doc_status: Optional[List[str]] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    receipt_id: Optional[str] = Query(None, alias="receiptId"),
    date_from: Optional[str] = Query(None, alias="dateFrom"),
    date_to: Optional[str] = Query(None, alias="dateTo"),
    project_id: Optional[str] = Query(None, alias="projectId"),
    limit: int = Query(15, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    try:
        hospital_id = current_user["hospital_id"]
        
        parsed_date_from = None
        parsed_date_to = None
        if date_from:
            try:
                parsed_date_from = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            except ValueError:
                pass
        if date_to:
            try:
                parsed_date_to = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            except ValueError:
                pass
        
        documents, total = await get_all_documents(
            hospital_id=hospital_id,
            status=doc_status,
            search=search,
            receipt_id=receipt_id,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            project_id=project_id,
            limit=limit,
            offset=offset
        )
        
        return PaginatedDocumentsResponse(
            items=documents,
            total=total,
            limit=limit,
            offset=offset,
            hasMore=(offset + len(documents)) < total
        )
    
    except Exception as e:
        print(f"[DOCUMENTS] Error fetching documents: {e}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch documents: {str(e)}"
        )

@router.get("/{document_id}", response_model=Document)
async def get_document_by_id(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        doc_data = await get_document(document_id)
        
        if not doc_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        if doc_data.get("hospitalId") != current_user["hospital_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this document"
            )

        await log_event(
            "DOCUMENT_VIEW",
            hospital_id=doc_data.get("hospitalId"),
            user_id=current_user.get("id"),
            resource_type="document",
            resource_id=document_id,
        )

        # Claim-level documents include parsed payload, findings, and repricing summary.
        if doc_data.get("documentRole") == "CLAIM":
            async with AsyncSessionLocal() as db:
                parsed_result = await db.execute(
                    select(ParsedData).where(ParsedData.document_id == document_id)
                )
                parsed = parsed_result.scalar_one_or_none()
                finding_result = await db.execute(
                    select(AuditFinding).where(AuditFinding.document_id == document_id)
                )
                findings = finding_result.scalars().all()

            parsed_payload = parsed.payload if parsed else None
            doc_data["parsedData"] = parsed_payload
            doc_data["repricingSummary"] = (parsed_payload or {}).get("repricing") if parsed_payload else None
            doc_data["findings"] = [
                {
                    "id": finding.id,
                    "findingCode": finding.finding_code,
                    "severity": finding.severity,
                    "confidenceScore": finding.confidence_score,
                    "varianceAmount": float(finding.variance_amount) if finding.variance_amount is not None else None,
                    "metadata": finding.metadata_json,
                    "createdAt": finding.created_at,
                }
                for finding in findings
            ]
        
        return doc_data
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DOCUMENTS] Error fetching document {document_id}: {e}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch document: {str(e)}"
        )

@router.patch("/{document_id}", response_model=Document)
async def update_document_endpoint(
    document_id: str,
    update_data: DocumentUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        doc_data = await get_document(document_id)
        
        if not doc_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        if doc_data.get("hospitalId") != current_user["hospital_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this document"
            )
        
        update_dict = {}
        if update_data.name is not None:
            update_dict["name"] = update_data.name
        if update_data.notes is not None:
            update_dict["notes"] = update_data.notes
        if update_data.receiptAmount is not None:
            update_dict["receipt_amount"] = update_data.receiptAmount
        if update_data.contractAmount is not None:
            update_dict["contract_amount"] = update_data.contractAmount
        if update_data.underpaymentAmount is not None:
            update_dict["underpayment_amount"] = update_data.underpaymentAmount
            update_dict["amount"] = update_data.underpaymentAmount
        if update_data.status is not None:
            update_dict["status"] = update_data.status
        
        if not update_dict:
            return Document(**doc_data)
        
        updated_doc = await update_document(document_id, **update_dict)
        
        if not updated_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to update document"
            )
        
        return Document(**updated_doc)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DOCUMENTS] Error updating document {document_id}: {e}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}"
        )


@router.post("/{document_id}/submit", response_model=Document)
async def submit_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        doc_data = await get_document(document_id)
        
        if not doc_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        if doc_data.get("hospitalId") != current_user["hospital_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to submit this document"
            )
        
        updated_doc = await update_document(
            document_id,
            status="in_progress",
            submittedAt=datetime.utcnow()
        )
        
        if not updated_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to update document"
            )
        
        return Document(**updated_doc)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit document: {str(e)}"
        )

@router.post("/bulk-download")
async def mark_bulk_downloaded(
    request: BulkDownloadRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        hospital_id = current_user["hospital_id"]
        count = await mark_documents_bulk_downloaded(request.documentIds, hospital_id)
        
        return {
            "success": True,
            "count": count,
            "message": f"Marked {count} documents as bulk downloaded"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark documents as bulk downloaded: {str(e)}"
        )
