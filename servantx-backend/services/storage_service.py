from __future__ import annotations

import hashlib
import hmac
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Set
from urllib.parse import urlencode

import boto3
from botocore.client import Config as BotoConfig
from fastapi import HTTPException, UploadFile, status

from config import settings

MAX_FILE_SIZE = 500 * 1024 * 1024
ALLOWED_835_TYPES = {"application/octet-stream", "text/plain", "text/x-edi"}
ALLOWED_835_EXTENSIONS = {".835", ".edi", ".txt"}


class BaseStorageService:
    backend = "base"

    def build_key(self, prefix: str, filename: str, namespace: Optional[str] = None) -> str:
        extension = Path(filename or "upload.bin").suffix or ".bin"
        ns = f"{namespace}_" if namespace else ""
        clean_prefix = prefix.rstrip("/")
        return f"{clean_prefix}/{ns}{uuid.uuid4()}{extension}" if clean_prefix else f"{ns}{uuid.uuid4()}{extension}"

    async def save_upload(self, file: UploadFile, *, prefix: str, allowed_types: Set[str], allowed_extensions: Set[str], max_size: int = MAX_FILE_SIZE, namespace: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError

    def read_text(self, storage_key: str) -> str:
        raise NotImplementedError

    def file_url(self, storage_key: str, base_url: str = "") -> str:
        raise NotImplementedError

    def presign(self, storage_key: str, operation: str = "download", expires_in: int = settings.STORAGE_PRESIGN_TTL_SECONDS) -> Dict[str, Any]:
        raise NotImplementedError

    def healthcheck(self) -> Dict[str, Any]:
        return {"backend": self.backend, "ok": True}

    async def _read_and_validate_upload(self, file: UploadFile, *, allowed_types: Set[str], allowed_extensions: Set[str], max_size: int) -> tuple[str, str, bytes]:
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
        return file_name, content_type, content


class LocalStorageService(BaseStorageService):
    backend = "local"

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, file: UploadFile, *, prefix: str, allowed_types: Set[str], allowed_extensions: Set[str], max_size: int = MAX_FILE_SIZE, namespace: Optional[str] = None) -> Dict[str, Any]:
        file_name, content_type, content = await self._read_and_validate_upload(
            file,
            allowed_types=allowed_types,
            allowed_extensions=allowed_extensions,
            max_size=max_size,
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
        if settings.STORAGE_PUBLIC_BASE_URL:
            return f"{settings.STORAGE_PUBLIC_BASE_URL.rstrip('/')}/{storage_key}"
        return f"{base_url.rstrip('/')}/files/{storage_key}" if base_url else f"/files/{storage_key}"

    def presign(self, storage_key: str, operation: str = "download", expires_in: int = settings.STORAGE_PRESIGN_TTL_SECONDS) -> Dict[str, Any]:
        expires_at = int(time.time()) + expires_in
        payload = f"{operation}:{storage_key}:{expires_at}"
        signature = hmac.new(settings.STORAGE_PRESIGN_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        query = urlencode({"op": operation, "exp": expires_at, "sig": signature})
        return {
            "storageKey": storage_key,
            "operation": operation,
            "expiresAt": expires_at,
            "token": signature,
            "url": f"/files/{storage_key}?{query}",
            "backend": self.backend,
        }

    def healthcheck(self) -> Dict[str, Any]:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            probe = self.root / ".healthcheck"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return {"backend": self.backend, "ok": True, "root": str(self.root)}
        except Exception as exc:
            return {"backend": self.backend, "ok": False, "error": str(exc)}


class S3StorageService(BaseStorageService):
    backend = "s3"

    def __init__(self):
        session = boto3.session.Session()
        self.bucket = settings.STORAGE_BUCKET
        self.region = settings.STORAGE_REGION
        self.client = session.client(
            "s3",
            region_name=self.region,
            endpoint_url=settings.STORAGE_ENDPOINT_URL or None,
            aws_access_key_id=settings.STORAGE_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.STORAGE_SECRET_ACCESS_KEY or None,
            config=BotoConfig(signature_version="s3v4", s3={"addressing_style": "path" if settings.STORAGE_FORCE_PATH_STYLE else "auto"}),
        )

    async def save_upload(self, file: UploadFile, *, prefix: str, allowed_types: Set[str], allowed_extensions: Set[str], max_size: int = MAX_FILE_SIZE, namespace: Optional[str] = None) -> Dict[str, Any]:
        file_name, content_type, content = await self._read_and_validate_upload(
            file,
            allowed_types=allowed_types,
            allowed_extensions=allowed_extensions,
            max_size=max_size,
        )
        storage_key = self.build_key(prefix=prefix, filename=file_name, namespace=namespace)
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        self.client.put_object(Bucket=self.bucket, Key=storage_key, Body=content, **extra_args)
        return {
            "storage_key": storage_key,
            "byte_size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "content_type": content_type or None,
            "original_file_name": file_name,
        }

    def read_text(self, storage_key: str) -> str:
        response = self.client.get_object(Bucket=self.bucket, Key=storage_key)
        return response["Body"].read().decode("utf-8", errors="ignore")

    def file_url(self, storage_key: str, base_url: str = "") -> str:
        if not storage_key:
            return ""
        if settings.STORAGE_PUBLIC_BASE_URL:
            return f"{settings.STORAGE_PUBLIC_BASE_URL.rstrip('/')}/{storage_key}"
        signed = self.presign(storage_key=storage_key, operation="download")
        return signed["url"]

    def presign(self, storage_key: str, operation: str = "download", expires_in: int = settings.STORAGE_PRESIGN_TTL_SECONDS) -> Dict[str, Any]:
        client_method = "put_object" if operation == "upload" else "get_object"
        url = self.client.generate_presigned_url(
            client_method,
            Params={"Bucket": self.bucket, "Key": storage_key},
            ExpiresIn=expires_in,
        )
        return {
            "storageKey": storage_key,
            "operation": operation,
            "expiresAt": int(time.time()) + expires_in,
            "token": None,
            "url": url,
            "backend": self.backend,
            "bucket": self.bucket,
        }

    def healthcheck(self) -> Dict[str, Any]:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return {"backend": self.backend, "ok": True, "bucket": self.bucket, "region": self.region}
        except Exception as exc:
            return {"backend": self.backend, "ok": False, "bucket": self.bucket, "error": str(exc)}


storage_service: BaseStorageService
if settings.has_s3_storage:
    storage_service = S3StorageService()
else:
    storage_service = LocalStorageService(settings.resolved_storage_root)
