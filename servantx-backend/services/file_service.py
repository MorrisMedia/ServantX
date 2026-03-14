from pathlib import Path
from typing import Optional, Set, Tuple

from fastapi import HTTPException, UploadFile, status

from config import settings
from services.storage_service import (
    ALLOWED_835_EXTENSIONS,
    ALLOWED_835_TYPES,
    MAX_FILE_SIZE,
    storage_service,
)

BASE_STORAGE_DIR = settings.resolved_storage_root
CONTRACTS_DIR = BASE_STORAGE_DIR / "contracts"
RECEIPTS_DIR = BASE_STORAGE_DIR / "receipts"
ERAS_DIR = BASE_STORAGE_DIR / "eras"

CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
ERAS_DIR.mkdir(parents=True, exist_ok=True)

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


def _is_allowed_file(file: UploadFile, allowed_types: Set[str], allowed_extensions: Set[str]) -> bool:
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
    saved = await storage_service.save_upload(
        file,
        prefix="contracts",
        allowed_types=ALLOWED_CONTRACT_TYPES,
        allowed_extensions=ALLOWED_CONTRACT_EXTENSIONS,
        namespace=hospital_id,
    )
    return saved["storage_key"].split("/")[-1].split("_")[-1].split(".")[0], saved["storage_key"], saved["byte_size"]


async def save_receipt_file(file: UploadFile, hospital_id: str) -> Tuple[str, str, int]:
    saved = await storage_service.save_upload(
        file,
        prefix="receipts",
        allowed_types=ALLOWED_RECEIPT_TYPES,
        allowed_extensions=ALLOWED_RECEIPT_EXTENSIONS,
        namespace=hospital_id,
    )
    return saved["storage_key"].split("/")[-1].split("_")[-1].split(".")[0], saved["storage_key"], saved["byte_size"]


async def save_835_file(file: UploadFile, hospital_id: str, project_id: Optional[str] = None) -> Tuple[str, str, int]:
    file_ext = Path(file.filename or "remittance.835").suffix.lower() or ".835"
    if file_ext not in ALLOWED_835_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file extension. Allowed extensions: .835, .edi, .txt",
        )
    prefix = f"projects/{project_id}/eras" if project_id else "eras"
    saved = await storage_service.save_upload(
        file,
        prefix=prefix,
        allowed_types=ALLOWED_835_TYPES,
        allowed_extensions=ALLOWED_835_EXTENSIONS,
        namespace=hospital_id,
    )
    return saved["storage_key"].split("/")[-1].split("_")[-1].split(".")[0], saved["storage_key"], saved["byte_size"]


def delete_file(file_path: str) -> bool:
    if settings.STORAGE_BACKEND != "local":
        return False
    try:
        full_path = storage_service.resolve_local_path(file_path)
    except FileNotFoundError:
        return False
    if full_path.exists() and full_path.is_file():
        full_path.unlink()
        return True
    return False


def get_file_url(file_path: str, base_url: str = "") -> str:
    return storage_service.file_url(file_path, base_url=base_url)
