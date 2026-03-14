import uuid
from pathlib import Path
from typing import Optional, Set, Tuple
from fastapi import UploadFile, HTTPException, status

BASE_STORAGE_DIR = Path("uploads")
CONTRACTS_DIR = BASE_STORAGE_DIR / "contracts"
RECEIPTS_DIR = BASE_STORAGE_DIR / "receipts"
ERAS_DIR = BASE_STORAGE_DIR / "eras"

CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
ERAS_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB per file

ALLOWED_CONTRACT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/zip",
    "application/x-zip-compressed",
}
ALLOWED_CONTRACT_EXTENSIONS = {".pdf", ".doc", ".docx", ".zip"}

ALLOWED_RECEIPT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "application/json",
    "application/fhir+json",
    "text/plain",
    "application/octet-stream",
    "text/x-edi",
    "application/edi-x12",
    "text/x-hl7",
    "application/hl7-v2",
    "text/hl7",
    "text/x-hlz",
    "application/hlz",
    "text/hlz",
    "application/zip",
    "application/x-zip-compressed",
}
ALLOWED_RECEIPT_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".csv",
    ".edi",
    ".hl7",
    ".hlz",
    ".dat",
    ".json",
    ".zip",
    ".txt",
    ".835",
    ".837",
}

ALLOWED_835_TYPES = {
    "application/octet-stream",
    "text/plain",
    "text/x-edi",
}

def _is_allowed_file(
    file: UploadFile,
    allowed_types: Set[str],
    allowed_extensions: Set[str],
) -> bool:
    file_name = file.filename or ""
    file_ext = Path(file_name).suffix.lower()
    content_type = (file.content_type or "").lower()
    return (content_type in allowed_types) or (file_ext in allowed_extensions)


def validate_file(
    file: UploadFile,
    allowed_types: Set[str],
    allowed_extensions: Set[str],
    max_size: int = MAX_FILE_SIZE,
) -> Tuple[bool, Optional[str]]:
    if not _is_allowed_file(file, allowed_types, allowed_extensions):
        allowed_ext_display = ", ".join(sorted(allowed_extensions))
        return False, f"Invalid file type. Allowed extensions: {allowed_ext_display}"

    return True, None

async def save_contract_file(file: UploadFile, hospital_id: str) -> Tuple[str, str, int]:
    is_valid, error = validate_file(file, ALLOWED_CONTRACT_TYPES, ALLOWED_CONTRACT_EXTENSIONS)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    file_id = str(uuid.uuid4())
    
    original_filename = file.filename or "contract"
    file_ext = Path(original_filename).suffix or ".pdf"
    
    filename = f"{hospital_id}_{file_id}{file_ext}"
    file_path = CONTRACTS_DIR / filename
    
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.0f}MB"
        )
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    relative_path = f"contracts/{filename}"
    
    return file_id, relative_path, file_size

async def save_receipt_file(file: UploadFile, hospital_id: str) -> Tuple[str, str, int]:
    is_valid, error = validate_file(file, ALLOWED_RECEIPT_TYPES, ALLOWED_RECEIPT_EXTENSIONS)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    file_id = str(uuid.uuid4())
    
    original_filename = file.filename or "receipt"
    file_ext = Path(original_filename).suffix
    
    filename = f"{hospital_id}_{file_id}{file_ext}"
    file_path = RECEIPTS_DIR / filename
    
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.0f}MB"
        )
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    relative_path = f"receipts/{filename}"
    
    return file_id, relative_path, file_size


async def save_835_file(file: UploadFile, hospital_id: str) -> Tuple[str, str, int]:
    file_id = str(uuid.uuid4())

    original_filename = file.filename or "remittance.835"
    file_ext = Path(original_filename).suffix.lower() or ".835"
    if file_ext not in [".835", ".edi", ".txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file extension. Allowed extensions: .835, .edi, .txt",
        )

    if file.content_type and file.content_type not in ALLOWED_835_TYPES:
        # Many clients send generic content-types for EDI, so allow by extension fallback.
        if file_ext not in [".835", ".edi", ".txt"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_835_TYPES)}",
            )

    filename = f"{hospital_id}_{file_id}{file_ext}"
    file_path = ERAS_DIR / filename

    content = await file.read()
    file_size = len(content)

    if file_size > 500 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="835 file size exceeds maximum allowed size of 500MB",
        )

    with open(file_path, "wb") as f:
        f.write(content)

    relative_path = f"eras/{filename}"
    return file_id, relative_path, file_size

def delete_file(file_path: str) -> bool:
    full_path = BASE_STORAGE_DIR / file_path
    
    if full_path.exists() and full_path.is_file():
        full_path.unlink()
        return True
    
    return False

def get_file_url(file_path: str, base_url: str = "") -> str:
    if not file_path:
        return ""
    
    return f"{base_url}/files/{file_path}"
