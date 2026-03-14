import hashlib
import hmac
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple
from urllib.parse import urlencode

from fastapi import HTTPException, UploadFile, status

STORAGE_ROOT = Path(os.getenv("STORAGE_ROOT", "uploads"))
STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
PRESIGN_SECRET = os.getenv("STORAGE_PRESIGN_SECRET", os.getenv("JWT_SECRET_KEY", "dev-storage-secret"))
PRESIGN_TTL_SECONDS = int(os.getenv("STORAGE_PRESIGN_TTL_SECONDS", "900"))
MAX_FILE_SIZE = 500 * 1024 * 1024

ALLOWED_835_TYPES = {"application/octet-stream", "text/plain", "text/x-edi"}
ALLOWED_835_EXTENSIONS = {".835", ".edi", ".txt"}


class LocalStorageService:
    def __init__(self, root: Path = STORAGE_ROOT):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def ensure_prefix(self, prefix: str) -> Path:
        path = self.root / prefix
        path.mkdir(parents=True, exist_ok=True)
        return path

    def build_key(self, prefix: str, filename: str, namespace: Optional[str] = None) -> str:
        extension = Path(filename or "upload.bin").suffix or ".bin"
        ns = f"{namespace}_" if namespace else ""
        return f"{prefix.rstrip('/')}/{ns}{uuid.uuid4()}{extension}"

    async def save_upload(
        self,
        file: UploadFile,
        *,
        prefix: str,
        allowed_types: Set[str],
        allowed_extensions: Set[str],
        max_size: int = MAX_FILE_SIZE,
        namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        file_name = file.filename or "upload.bin"
        extension = Path(file_name).suffix.lower()
        content_type = (file.content_type or "").lower()
        if extension not in allowed_extensions and content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed extensions: {', '.join(sorted(allowed_extensions))}",
            )

        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {max_size // (1024 * 1024)}MB",
            )

        storage_key = self.build_key(prefix=prefix, filename=file_name, namespace=namespace)
        full_path = self.root / storage_key
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return {
            "storage_key": storage_key,
            "byte_size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "content_type": content_type or None,
            "original_file_name": file_name,
        }

    def read_text(self, storage_key: str) -> str:
        path = self.root / storage_key
        if not path.exists():
            raise FileNotFoundError(f"Storage file not found: {storage_key}")
        return path.read_text(encoding="utf-8", errors="ignore")

    def file_url(self, storage_key: str, base_url: str = "") -> str:
        if not storage_key:
            return ""
        return f"{base_url}/files/{storage_key}"

    def presign(self, storage_key: str, operation: str = "download", expires_in: int = PRESIGN_TTL_SECONDS) -> Dict[str, Any]:
        expires_at = int(time.time()) + expires_in
        payload = f"{operation}:{storage_key}:{expires_at}"
        signature = hmac.new(PRESIGN_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        query = urlencode({"op": operation, "exp": expires_at, "sig": signature})
        return {
            "storageKey": storage_key,
            "operation": operation,
            "expiresAt": expires_at,
            "token": signature,
            "url": f"/files/{storage_key}?{query}",
        }


storage_service = LocalStorageService()
