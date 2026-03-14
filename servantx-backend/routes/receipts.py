from fastapi import APIRouter, HTTPException, status, UploadFile, File, Query, Depends, BackgroundTasks
from config import settings
from typing import List, Optional
from datetime import datetime
import zipfile
import io
import uuid
from pathlib import Path
from schemas import Receipt, ReceiptUploadResponse, DocumentCreateResponse, Document, PaginatedReceiptsResponse
from services.file_service import (
    save_receipt_file,
    delete_file,
    get_file_url,
    ALLOWED_RECEIPT_TYPES,
    ALLOWED_RECEIPT_EXTENSIONS,
)
from services.storage_service import storage_service

from services.receipt_service import (
    create_receipt,
    get_receipt,
    get_all_receipts,
    delete_receipt as delete_receipt_storage,
    update_receipt
)
from services.contract_service import get_all_contracts
from services.document_service import create_document
from services.claim_adjudication_service import adjudicate_receipt
from services.contract_rules_engine import get_contract_text_with_fallback
from routes.auth import get_current_user

router = APIRouter(prefix="/receipts", tags=["receipts"])


def _is_metadata_only_contract_text(text: str) -> bool:
    normalized = (text or "").strip().lower()
    if not normalized:
        return True
    metadata_markers = (
        "processed by contract-rules-engine",
        "extraction warning:",
        "contract-rules-engine-v1 failed",
        "file not found:",
        "error extracting text",
        "warning:",
    )
    has_marker = any(marker in normalized for marker in metadata_markers)
    has_rule_like_content = any(token in normalized for token in ("must", "shall", "reimbursement", "payment", "rate", "underpayment"))
    return has_marker and not has_rule_like_content


async def _run_rules_scan_for_receipt(receipt_data: dict, hospital_id: str) -> DocumentCreateResponse:
    """
    Per-claim adjudication pipeline for a single receipt.

    1. Fetches contracts + rule libraries for the hospital.
    2. Calls adjudicate_receipt() which:
       - Detects file format (835, CSV, etc.)
       - Splits into individual claims
       - Detects claim type (Professional / Institutional IP / OP)
       - Routes to the correct repricing engine (MPFS, IPPS, OPPS, rule library)
       - Creates a Document per claim with per-line variance
    3. Aggregates results back to the Receipt.
    """
    contracts = await get_all_contracts(hospital_id=hospital_id)
    if not contracts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No contract found for your hospital. Please upload a contract first."
        )

    # Build contracts_with_text list (same shape expected by adjudicate_receipt)
    contracts_with_text = []
    for contract in contracts:
        contract_text = get_contract_text_with_fallback(contract)
        contracts_with_text.append({
            "id": contract["id"],
            "name": contract["name"],
            "text": contract_text,
            "rule_library": contract.get("ruleLibrary"),
        })

    usable_contracts = [
        c for c in contracts_with_text
        if (c.get("text", "").strip() and not _is_metadata_only_contract_text(c.get("text", "")))
        or (c.get("rule_library") and isinstance(c.get("rule_library"), dict) and c["rule_library"].get("rule_count", 0) > 0)
    ]
    if not usable_contracts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Contracts are missing source text or rule libraries for evaluation. "
                "Please re-upload your contracts, then upload billing records again."
            ),
        )

    # ── Run per-claim adjudication ──
    result = await adjudicate_receipt(
        receipt_data=receipt_data,
        hospital_id=hospital_id,
        contracts=usable_contracts,
    )

    # Handle adjudication errors
    if result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"],
        )

    documents_created = result.get("documents_created", [])
    has_underpayment = result.get("has_underpayment", False)
    total_variance = result.get("total_variance", 0.0)

    # Update the receipt with aggregated totals
    await update_receipt(
        receipt_data["id"],
        documentId=documents_created[0]["id"] if documents_created else None,
        hasDifference=has_underpayment,
        amount=total_variance,
        status="processed"
    )

    # Build response from the first document
    first_doc = documents_created[0] if documents_created else None
    if first_doc:
        document = Document(**first_doc)
    else:
        # Shouldn't happen, but be safe
        placeholder = await create_document(
            receipt_id=receipt_data["id"],
            hospital_id=hospital_id,
            contract_id=usable_contracts[0]["id"] if usable_contracts else None,
            amount=0.0,
            status="not_submitted",
            name=f"No Claims: {receipt_data.get('fileName', 'receipt')}",
            notes="No claims could be parsed from this billing record.",
            rules_applied=None,
        )
        document = Document(**placeholder)

    claims_processed = result.get("claims_processed", 0)
    file_format = result.get("file_format", "UNKNOWN")
    violations = len([d for d in documents_created if d.get("amount", 0) > 0])

    message = f"Per-claim adjudication complete ({file_format}). "
    message += f"Processed {claims_processed} claim(s). "
    if has_underpayment:
        message += f"Found {violations} underpayment(s). Total variance: ${total_variance:,.2f}"
    else:
        message += "No underpayment detected."

    return DocumentCreateResponse(
        document=document,
        message=message
    )


async def _run_rules_scan_for_receipt_background(receipt_id: str, hospital_id: str) -> None:
    try:
        receipt_data = await get_receipt(receipt_id)
        if not receipt_data:
            return
        if receipt_data.get("hospitalId") != hospital_id:
            return

        await _run_rules_scan_for_receipt(receipt_data, hospital_id)
    except Exception as exc:
        await update_receipt(receipt_id, status="error")
        print(f"[RECEIPT SCAN] Background rules scan failed for {receipt_id}: {exc}", flush=True)


async def _process_zip_contents(
    zip_content: bytes,
    hospital_id: str,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Extract and process all valid billing record files from a ZIP archive.
    Returns {"receipts": [...], "errors": [...], "message": "..."}.
    """
    receipts = []
    errors = []

    try:
        with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_ref:
            file_list = zip_ref.namelist()

            for file_name in file_list:
                try:
                    if file_name.endswith('/'):
                        continue

                    # Skip macOS system files silently
                    if (file_name.startswith('__MACOSX/') or
                            file_name.endswith('.DS_Store') or
                            file_name.startswith('._') or
                            '/._' in file_name):
                        continue

                    file_data = zip_ref.read(file_name)
                    file_ext = Path(file_name).suffix.lower()

                    if file_ext not in ALLOWED_RECEIPT_EXTENSIONS:
                        if not (file_name.startswith('.') or file_name.endswith('.DS_Store')):
                            errors.append(f"Skipped {file_name}: Invalid file type")
                        continue

                    # Per-file limit: 500 MB
                    file_size = len(file_data)
                    if file_size > 500 * 1024 * 1024:
                        errors.append(f"Skipped {file_name}: File too large (max 500MB)")
                        continue

                    content_type_map = {
                        '.pdf': 'application/pdf',
                        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                        '.png': 'image/png',
                        '.csv': 'text/csv',
                        '.edi': 'application/edi-x12',
                        '.hl7': 'text/x-hl7', '.hlz': 'text/x-hlz',
                        '.dat': 'text/plain',
                        '.json': 'application/json',
                        '.txt': 'text/plain',
                        '.835': 'application/edi-x12',
                        '.837': 'application/edi-x12',
                    }
                    content_type = content_type_map.get(file_ext, 'application/octet-stream')
                    if content_type not in ALLOWED_RECEIPT_TYPES:
                        errors.append(f"Skipped {file_name}: Unsupported content type ({content_type})")
                        continue

                    original_filename = Path(file_name).name
                    saved = storage_service.save_bytes(
                        content=file_data,
                        filename=original_filename,
                        prefix="receipts",
                        content_type=content_type,
                        namespace=hospital_id,
                    )
                    relative_path = saved["storage_key"]

                    receipt_data = await create_receipt(
                        hospital_id=hospital_id,
                        file_name=Path(file_name).name,
                        file_path=relative_path,
                        file_size=file_size,
                        amount=0.0,
                        has_difference=False,
                    )

                    queued_receipt = await update_receipt(receipt_data["id"], status="processing")
                    if queued_receipt:
                        receipt_data = queued_receipt
                    if settings.is_vercel:
                        await _run_rules_scan_for_receipt_background(receipt_data["id"], hospital_id)
                    else:
                        background_tasks.add_task(
                            _run_rules_scan_for_receipt_background, receipt_data["id"], hospital_id
                        )

                    receipt_data["fileUrl"] = get_file_url(relative_path)
                    receipt = Receipt(**receipt_data)
                    receipts.append(receipt)

                except HTTPException as e:
                    errors.append(f"Skipped {file_name}: {e.detail}")
                except Exception as e:
                    errors.append(f"Error processing {file_name}: {str(e)}")

    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ZIP file format"
        )

    message = f"Processed {len(receipts)} billing record(s) from ZIP"
    if errors:
        message += f". {len(errors)} file(s) skipped."

    return {
        "receipts": [r.dict() for r in receipts],
        "billingRecords": [r.dict() for r in receipts],
        "message": message,
        "errors": errors if errors else None,
    }


def _is_zip_file(file: UploadFile) -> bool:
    """Return True if the uploaded file looks like a ZIP."""
    if file.content_type in ("application/zip", "application/x-zip-compressed"):
        return True
    if file.filename and file.filename.lower().endswith(".zip"):
        return True
    return False


@router.post("/upload", response_model=ReceiptUploadResponse)
async def upload_receipt(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a billing record file (or a ZIP file -- auto-detected).
    If a ZIP is detected the contents are extracted and each valid billing
    record inside is created as its own receipt record.
    """
    try:
        hospital_id = current_user["hospital_id"]

        # ── Auto-detect ZIP and extract ──
        if _is_zip_file(file):
            zip_content = await file.read()
            # 1 GB limit for ZIP through any endpoint
            if len(zip_content) > 1024 * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ZIP file size exceeds maximum allowed size of 1 GB"
                )
            result = await _process_zip_contents(zip_content, hospital_id, background_tasks)
            extracted = result.get("receipts", [])
            if not extracted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ZIP file contains no valid billing record files."
                )
            # Return the first receipt in the normal single-file response shape
            first = extracted[0]
            receipt = Receipt(**first)
            return ReceiptUploadResponse(
                receipt=receipt,
                document=None,
            )

        # ── Normal single-file upload path ──
        file_id, file_path, file_size = await save_receipt_file(file, hospital_id)
        
        amount = 0.0
        has_difference = False
        
        receipt_data = await create_receipt(
            hospital_id=hospital_id,
            file_name=file.filename or "receipt.pdf",
            file_path=file_path,
            file_size=file_size,
            amount=amount,
            has_difference=has_difference
        )

        queued_receipt = await update_receipt(receipt_data["id"], status="processing")
        if queued_receipt:
            receipt_data = queued_receipt
        if settings.is_vercel:
            await _run_rules_scan_for_receipt_background(receipt_data["id"], hospital_id)
        else:
            background_tasks.add_task(_run_rules_scan_for_receipt_background, receipt_data["id"], hospital_id)
        
        receipt_data["fileUrl"] = get_file_url(file_path)
        
        document = None
        receipt = Receipt(**receipt_data)
        
        return ReceiptUploadResponse(
            receipt=receipt,
            document=document
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload billing record: {str(e)}"
        )


@router.post("/upload/bulk", response_model=List[ReceiptUploadResponse])
async def upload_receipts_bulk(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload multiple billing record files at once.
    ZIP files are auto-detected and extracted in-line.
    """
    try:
        hospital_id = current_user["hospital_id"]
        results = []
        
        for file in files:
            # Auto-detect ZIP and extract each file inside
            if _is_zip_file(file):
                zip_content = await file.read()
                if len(zip_content) > 1024 * 1024 * 1024:
                    # Skip this zip but continue with other files
                    continue
                zip_result = await _process_zip_contents(zip_content, hospital_id, background_tasks)
                for r_dict in zip_result.get("receipts", []):
                    receipt = Receipt(**r_dict)
                    results.append(ReceiptUploadResponse(receipt=receipt, document=None))
                continue

            # Normal file
            file_id, file_path, file_size = await save_receipt_file(file, hospital_id)
            
            amount = 0.0
            has_difference = False
            
            receipt_data = await create_receipt(
                hospital_id=hospital_id,
                file_name=file.filename or "receipt.pdf",
                file_path=file_path,
                file_size=file_size,
                amount=amount,
                has_difference=has_difference
            )

            queued_receipt = await update_receipt(receipt_data["id"], status="processing")
            if queued_receipt:
                receipt_data = queued_receipt
            if settings.is_vercel:
                await _run_rules_scan_for_receipt_background(receipt_data["id"], hospital_id)
            else:
                background_tasks.add_task(_run_rules_scan_for_receipt_background, receipt_data["id"], hospital_id)

            receipt_data["fileUrl"] = get_file_url(file_path)

            document = None
            receipt = Receipt(**receipt_data)
            results.append(ReceiptUploadResponse(receipt=receipt, document=document))
        
        return results
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload billing records: {str(e)}"
        )


@router.get("", response_model=PaginatedReceiptsResponse)
async def get_receipts(
    has_difference: Optional[bool] = Query(None, alias="hasDifference"),
    receipt_status: Optional[List[str]] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    limit: int = Query(15, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all billing records with optional filters and pagination.
    """
    try:
        hospital_id = current_user["hospital_id"]
        receipts_data, total = await get_all_receipts(
            hospital_id=hospital_id,
            has_difference=has_difference,
            status=receipt_status,
            search=search,
            limit=limit,
            offset=offset
        )
        
        result = []
        for receipt_data in receipts_data:
            receipt_data["fileUrl"] = get_file_url(receipt_data.get("fileUrl", ""))
            receipt = Receipt(**receipt_data)
            result.append(receipt)
        
        return PaginatedReceiptsResponse(
            items=result,
            total=total,
            limit=limit,
            offset=offset,
            hasMore=(offset + len(result)) < total
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch billing records: {str(e)}"
        )


@router.get("/{receipt_id}", response_model=Receipt)
async def get_receipt_by_id(receipt_id: str):
    """
    Get a specific billing record by ID.
    """
    try:
        receipt_data = await get_receipt(receipt_id)
        
        if not receipt_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Billing record not found"
            )
        
        receipt_data["fileUrl"] = get_file_url(receipt_data.get("fileUrl", ""))
        receipt = Receipt(**receipt_data)
        return receipt
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch billing record: {str(e)}"
        )


@router.post("/upload/zip", response_model=dict)
async def upload_receipts_zip(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a ZIP file containing billing record files.
    The ZIP will be extracted and each valid billing record file will be processed.
    """
    try:
        hospital_id = current_user["hospital_id"]
        # Validate it's a zip file
        if not _is_zip_file(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Please upload a ZIP file."
            )
        
        zip_content = await file.read()

        # 1 GB limit
        max_zip_size = 1024 * 1024 * 1024
        if len(zip_content) > max_zip_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ZIP file size exceeds maximum allowed size of {max_zip_size / (1024*1024):.0f}MB"
            )

        result = await _process_zip_contents(zip_content, hospital_id, background_tasks)

        if not result.get("receipts"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ZIP file contains no valid billing record files."
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process ZIP file: {str(e)}"
        )


@router.post("/{receipt_id}/scan", response_model=DocumentCreateResponse)
async def scan_receipt_for_issues(
    receipt_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Scan a billing record for underpayment issues using AI analysis.
    Compares the billing record against all hospital contracts in PARALLEL to detect discrepancies.
    Creates a document for each violation found.
    """
    scan_started = False
    try:
        hospital_id = current_user["hospital_id"]
        
        receipt_data = await get_receipt(receipt_id)
        if not receipt_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Billing record not found"
            )
        
        if receipt_data["hospitalId"] != hospital_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        await update_receipt(receipt_id, status="processing")
        scan_started = True
        return await _run_rules_scan_for_receipt(receipt_data, hospital_id)
    
    except HTTPException:
        if scan_started:
            await update_receipt(receipt_id, status="error")
        raise
    except Exception as e:
        if scan_started:
            await update_receipt(receipt_id, status="error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scan billing record: {str(e)}"
        )


@router.delete("/{receipt_id}")
async def delete_receipt(receipt_id: str):
    """
    Delete a billing record and its associated file.
    """
    try:
        receipt_data = await get_receipt(receipt_id)
        
        if not receipt_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Billing record not found"
            )
        
        # Delete file from storage
        file_path = receipt_data.get("fileUrl", "")
        if file_path:
            # Extract relative path from fileUrl if it's a full URL
            if "/files/" in file_path:
                file_path = file_path.split("/files/")[-1]
            delete_file(file_path)
        
        # Delete receipt record
        deleted = await delete_receipt_storage(receipt_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Billing record not found"
            )
        
        return {"message": "Billing record deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete billing record: {str(e)}"
        )

