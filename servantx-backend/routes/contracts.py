from datetime import datetime
import io
import uuid
import zipfile
from pathlib import Path as _Path
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, UploadFile, File, Depends
from config import settings
from typing import List
from schemas import (
    Contract,
    ContractChatRequest,
    ContractChatResponse,
    ContractChatSource,
    ContractUploadResponse,
)
from services.file_service import (
    save_contract_file,
    delete_file,
    get_file_url,
    ALLOWED_CONTRACT_EXTENSIONS,
    ALLOWED_CONTRACT_TYPES,
    MAX_FILE_SIZE,
)
from services.storage_service import storage_service
from services.contract_service import (
    create_contract,
    get_contract,
    get_all_contracts,
    delete_contract as delete_contract_storage,
    update_contract
)
from services.contract_chat_service import generate_contract_chat_response
from services.contract_processing_service import process_contract_with_rules_engine
from services.contract_rules_engine import get_contract_text_with_fallback
from routes.auth import get_current_user
from services.audit_service import log_event

router = APIRouter(prefix="/contracts", tags=["contracts"])


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_synthetic_contract_pdf(lines: List[str]) -> bytes:
    content_lines = ["BT", "/F1 11 Tf", "72 760 Td"]
    for index, line in enumerate(lines):
        escaped_line = _escape_pdf_text(line)
        if index == 0:
            content_lines.append(f"({escaped_line}) Tj")
        else:
            content_lines.append("T*")
            content_lines.append(f"({escaped_line}) Tj")
    content_lines.append("ET")
    content_stream = "\n".join(content_lines).encode("latin-1", errors="ignore")

    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>\nendobj\n",
        (
            f"4 0 obj\n<< /Length {len(content_stream)} >>\nstream\n".encode("latin-1")
            + content_stream
            + b"\nendstream\nendobj\n"
        ),
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF\n"
        ).encode("latin-1")
    )
    return bytes(pdf)


_VALID_CONTRACT_EXTS_IN_ZIP = {".pdf", ".doc", ".docx"}


def _is_zip_upload(file: UploadFile) -> bool:
    if file.content_type in ("application/zip", "application/x-zip-compressed"):
        return True
    return bool(file.filename and file.filename.lower().endswith(".zip"))


async def _process_contract_zip(
    zip_content: bytes,
    hospital_id: str,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Extract every PDF/DOC/DOCX from a ZIP and create a separate Contract for each.
    Returns {"contracts": [...], "errors": [...]}.
    """
    contracts: list = []
    errors: list = []

    try:
        with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_ref:
            for entry in zip_ref.namelist():
                try:
                    if entry.endswith("/"):
                        continue
                    # Skip macOS junk
                    if (entry.startswith("__MACOSX/") or entry.endswith(".DS_Store")
                            or entry.startswith("._") or "/._" in entry):
                        continue

                    ext = _Path(entry).suffix.lower()
                    if ext not in _VALID_CONTRACT_EXTS_IN_ZIP:
                        if not entry.startswith("."):
                            errors.append(f"Skipped {entry}: Not a PDF/DOC/DOCX")
                        continue

                    data = zip_ref.read(entry)
                    if len(data) > MAX_FILE_SIZE:
                        errors.append(f"Skipped {entry}: File too large (max {MAX_FILE_SIZE // (1024*1024)}MB)")
                        continue

                    original_name = _Path(entry).name
                    saved = storage_service.save_bytes(
                        content=data,
                        filename=original_name,
                        prefix="contracts",
                        content_type=None,
                        namespace=hospital_id,
                    )
                    relative_path = saved["storage_key"]
                    name = original_name.rsplit(".", 1)[0] if "." in original_name else original_name

                    contract_data = await create_contract(
                        hospital_id=hospital_id,
                        name=name,
                        file_name=original_name,
                        file_path=saved["storage_key"],
                        file_size=len(data),
                    )
                    contract_data["fileUrl"] = get_file_url(relative_path)
                    if settings.is_vercel:
                        await process_contract_with_rules_engine(contract_data["id"])
                    else:
                        background_tasks.add_task(process_contract_with_rules_engine, contract_data["id"])
                    contracts.append(Contract(**contract_data))

                except HTTPException as he:
                    errors.append(f"Skipped {entry}: {he.detail}")
                except Exception as exc:
                    errors.append(f"Error processing {entry}: {str(exc)}")

    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ZIP file format"
        )

    return {"contracts": contracts, "errors": errors}


@router.post("/upload", response_model=ContractUploadResponse)
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a contract file (PDF/DOC/DOCX) or a ZIP containing multiple contracts.
    ZIP files are auto-detected and extracted.
    """
    try:
        hospital_id = current_user["hospital_id"]

        # ── Auto-detect ZIP and extract ──
        if _is_zip_upload(file):
            zip_content = await file.read()
            if len(zip_content) > 1024 * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ZIP file size exceeds maximum allowed size of 1 GB"
                )
            result = await _process_contract_zip(zip_content, hospital_id, background_tasks)
            extracted = result.get("contracts", [])
            if not extracted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ZIP file contains no valid contract files (PDF/DOC/DOCX)."
                )
            return ContractUploadResponse(
                contract=extracted[0],
                message=f"ZIP processed: {len(extracted)} contract(s) created. Processing continues in the background."
            )

        # ── Normal single-file upload ──
        file_id, file_path, file_size = await save_contract_file(file, hospital_id)
        
        name = file.filename.rsplit('.', 1)[0] if '.' in (file.filename or '') else file.filename or "Contract"
        
        contract_data = await create_contract(
            hospital_id=hospital_id,
            name=name,
            file_name=file.filename or "contract.pdf",
            file_path=file_path,
            file_size=file_size
        )
        
        contract_data["fileUrl"] = get_file_url(file_path)
        if settings.is_vercel:
            await process_contract_with_rules_engine(contract_data["id"])
        else:
            background_tasks.add_task(process_contract_with_rules_engine, contract_data["id"])

        await log_event(
            "CONTRACT_UPLOAD",
            hospital_id=hospital_id,
            user_id=current_user.get("id"),
            resource_type="contract",
            resource_id=contract_data["id"],
        )

        contract = Contract(**contract_data)

        return ContractUploadResponse(
            contract=contract,
            message="Contract uploaded successfully. Processing continues in the background."
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload contract: {str(e)}"
        )


@router.post("/upload-bulk", response_model=dict)
async def upload_contracts_bulk(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload multiple contract files at once.
    ZIP files are auto-detected and extracted.
    """
    try:
        hospital_id = current_user["hospital_id"]
        uploaded_contracts = []
        failed_uploads = []
        
        for file in files:
            try:
                # Auto-detect ZIP
                if _is_zip_upload(file):
                    zip_content = await file.read()
                    if len(zip_content) > 1024 * 1024 * 1024:
                        failed_uploads.append({"fileName": file.filename, "error": "ZIP too large (max 1 GB)"})
                        continue
                    result = await _process_contract_zip(zip_content, hospital_id, background_tasks)
                    uploaded_contracts.extend(result.get("contracts", []))
                    for err in (result.get("errors") or []):
                        failed_uploads.append({"fileName": file.filename, "error": err})
                    continue

                file_id, file_path, file_size = await save_contract_file(file, hospital_id)
                
                name = file.filename.rsplit('.', 1)[0] if '.' in (file.filename or '') else file.filename or "Contract"
                
                contract_data = await create_contract(
                    hospital_id=hospital_id,
                    name=name,
                    file_name=file.filename or "contract.pdf",
                    file_path=file_path,
                    file_size=file_size
                )
                
                contract_data["fileUrl"] = get_file_url(file_path)
                contract = Contract(**contract_data)
                uploaded_contracts.append(contract)
                if settings.is_vercel:
                    await process_contract_with_rules_engine(contract_data["id"])
                else:
                    background_tasks.add_task(process_contract_with_rules_engine, contract_data["id"])
                
            except Exception as e:
                failed_uploads.append({
                    "fileName": file.filename,
                    "error": str(e)
                })
        
        return {
            "contracts": uploaded_contracts,
            "failedUploads": failed_uploads,
            "message": f"Successfully uploaded {len(uploaded_contracts)} contract(s). Background processing is running." + 
                      (f" {len(failed_uploads)} failed." if failed_uploads else "")
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload contracts: {str(e)}"
        )


@router.post("/seed", response_model=ContractUploadResponse)
async def seed_synthetic_contract(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Seed a synthetic contract for demo/testing without manual upload.
    """
    try:
        hospital_id = current_user["hospital_id"]

        contract_name = f"Synthetic Contract {datetime.utcnow().strftime('%Y-%m-%d')}"
        pdf_lines = [
            contract_name,
            "Hospital reimbursement baseline is 1200 USD per month.",
            "Any payment below baseline should be treated as underpayment.",
            "Payment terms are NET 30 from invoice date.",
            "After-hours services are reimbursed at 1.5x standard hourly rate.",
            "This file was generated as synthetic seed data for product demos.",
        ]
        pdf_bytes = _build_synthetic_contract_pdf(pdf_lines)

        saved = storage_service.save_bytes(
            content=pdf_bytes,
            filename="synthetic_contract.pdf",
            prefix="contracts",
            content_type="application/pdf",
            namespace=hospital_id,
        )

        contract_data = await create_contract(
            hospital_id=hospital_id,
            name=contract_name,
            file_name="synthetic_contract.pdf",
            file_path=saved["storage_key"],
            file_size=len(pdf_bytes)
        )

        updated_contract_data = await update_contract(
            contract_data["id"],
            status="processing",
            notes="Synthetic contract seeded for demo/testing."
        )
        if updated_contract_data:
            contract_data = updated_contract_data
        if settings.is_vercel:
            await process_contract_with_rules_engine(contract_data["id"])
        else:
            background_tasks.add_task(process_contract_with_rules_engine, contract_data["id"])

        contract_data["fileUrl"] = get_file_url(contract_data.get("filePath", saved["storage_key"]))
        contract = Contract(**contract_data)

        return ContractUploadResponse(
            contract=contract,
            message="Synthetic contract seeded successfully. Processing continues in the background."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed synthetic contract: {str(e)}"
        )


@router.post("/{contract_id}/reprocess", response_model=ContractUploadResponse)
async def reprocess_contract(
    contract_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """
    Re-run contract extraction engine in the background.
    """
    try:
        contract_data = await get_contract(contract_id)
        if not contract_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found",
            )

        if contract_data.get("hospitalId") != current_user["hospital_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to reprocess this contract",
            )

        updated = await update_contract(contract_id, status="processing")
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found",
            )

        if settings.is_vercel:
            await process_contract_with_rules_engine(contract_id)
        else:
            background_tasks.add_task(process_contract_with_rules_engine, contract_id)
        updated["fileUrl"] = get_file_url(updated.get("filePath", ""))
        return ContractUploadResponse(
            contract=Contract(**updated),
            message="Contract reprocessing started. Engine is running in the background.",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reprocess contract: {str(e)}",
        )


@router.post("/{contract_id}/chat", response_model=ContractChatResponse)
async def chat_with_contract_terms(
    contract_id: str,
    payload: ContractChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Ask AI questions against a specific contract.
    Optionally enrich with lightweight web context.
    """
    try:
        contract_data = await get_contract(contract_id)
        if not contract_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
        if contract_data.get("hospitalId") != current_user["hospital_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this contract",
            )

        contract_text = get_contract_text_with_fallback(contract_data)
        result = await generate_contract_chat_response(
            contract_name=contract_data.get("name", "Contract"),
            contract_text=contract_text,
            question=payload.question,
            include_web=payload.includeWeb,
            history=[{"role": item.role, "content": item.content} for item in (payload.history or [])],
        )

        return ContractChatResponse(
            contractId=contract_data["id"],
            contractName=contract_data.get("name", "Contract"),
            answer=result.get("answer", ""),
            usedWeb=bool(result.get("usedWeb", False)),
            sources=[
                ContractChatSource(
                    sourceType=source.get("sourceType", "contract"),
                    title=source.get("title", "Source"),
                    url=source.get("url"),
                    snippet=source.get("snippet", ""),
                )
                for source in (result.get("sources") or [])
            ],
            disclaimer=result.get("disclaimer", "For informational purposes only and not legal advice."),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process contract chat request: {str(e)}",
        )


@router.get("", response_model=List[Contract])
async def get_contracts(current_user: dict = Depends(get_current_user)):
    """
    Get all contracts for a hospital.
    """
    try:
        hospital_id = current_user["hospital_id"]
        contracts = await get_all_contracts(hospital_id=hospital_id)
        
        # Convert to Contract models and add file URLs
        result = []
        for contract_data in contracts:
            contract_data["fileUrl"] = get_file_url(contract_data.get("fileUrl", ""))
            contract = Contract(**contract_data)
            result.append(contract)
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch contracts: {str(e)}"
        )


@router.get("/{contract_id}", response_model=Contract)
async def get_contract_by_id(
    contract_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific contract by ID.
    """
    try:
        contract_data = await get_contract(contract_id)
        
        if not contract_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        if contract_data.get("hospitalId") != current_user["hospital_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this contract"
            )
        
        contract_data["fileUrl"] = get_file_url(contract_data.get("fileUrl", ""))
        contract = Contract(**contract_data)
        return contract
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch contract: {str(e)}"
        )


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a contract and its associated file.
    """
    try:
        contract_data = await get_contract(contract_id)
        
        if not contract_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        if contract_data.get("hospitalId") != current_user["hospital_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this contract"
            )
        
        file_path = contract_data.get("fileUrl", "")
        if file_path:
            if "/files/" in file_path:
                file_path = file_path.split("/files/")[-1]
            try:
                delete_file(file_path)
            except:
                pass
        
        deleted = await delete_contract_storage(contract_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        return {"message": "Contract deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete contract: {str(e)}"
        )

