from __future__ import annotations

import hashlib
import hmac
import io
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Set
from urllib.parse import urlencode

import boto3
import requests
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

    def save_bytes(self, *, content: bytes, filename: str, prefix: str, content_type: str | None = None, namespace: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError

    def read_bytes(self, storage_key: str) -> bytes:
        raise NotImplementedError

    def read_text(self, storage_key: str) -> str:
        return self.read_bytes(storage_key).decode("utf-8", errors="ignore")

    def file_url(self, storage_key: str, base_url: str = "") -> str:
        raise NotImplementedError

    def presign(self, storage_key: str, operation: str = "download", expires_in: int = settings.STORAGE_PRESIGN_TTL_SECONDS) -> Dict[str, Any]:
        raise NotImplementedError

    def resolve_local_path(self, storage_key: str) -> Path:
        raise FileNotFoundError("Local filesystem access is not available for this storage backend.")

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
        return self.save_bytes(content=content, filename=file_name, prefix=prefix, content_type=content_type or None, namespace=namespace)

    def save_bytes(self, *, content: bytes, filename: str, prefix: str, content_type: str | None = None, namespace: Optional[str] = None) -> Dict[str, Any]:
        storage_key = self.build_key(prefix=prefix, filename=filename, namespace=namespace)
        full_path = self.root / storage_key
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return {
            "storage_key": storage_key,
            "byte_size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "content_type": content_type,
            "original_file_name": filename,
        }

    def read_bytes(self, storage_key: str) -> bytes:
        path = self.resolve_local_path(storage_key)
        return path.read_bytes()

    def resolve_local_path(self, storage_key: str) -> Path:
        path = self.root / storage_key
        if not path.exists():
            raise FileNotFoundError(f"Storage file not found: {storage_key}")
        return path

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
        return self.save_bytes(content=content, filename=file_name, prefix=prefix, content_type=content_type or None, namespace=namespace)

    def save_bytes(self, *, content: bytes, filename: str, prefix: str, content_type: str | None = None, namespace: Optional[str] = None) -> Dict[str, Any]:
        storage_key = self.build_key(prefix=prefix, filename=filename, namespace=namespace)
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        self.client.put_object(Bucket=self.bucket, Key=storage_key, Body=content, **extra_args)
        return {
            "storage_key": storage_key,
            "byte_size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "content_type": content_type,
            "original_file_name": filename,
        }

    def read_bytes(self, storage_key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=storage_key)
        return response["Body"].read()

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


class VercelBlobStorageService(BaseStorageService):
    backend = "vercel_blob"

    def __init__(self):
        self.token = settings.BLOB_READ_WRITE_TOKEN
        self.access = settings.VERCEL_BLOB_ACCESS
        self.add_random_suffix = settings.VERCEL_BLOB_ADD_RANDOM_SUFFIX
        if not self.token:
            raise RuntimeError("BLOB_READ_WRITE_TOKEN is required when STORAGE_BACKEND=vercel_blob")
        try:
            from vercel.blob import BlobClient  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on env package install
            raise RuntimeError(
                "Missing Python Vercel Blob client. Install the `vercel` package to use STORAGE_BACKEND=vercel_blob."
            ) from exc
        self.client = BlobClient(token=self.token)

    async def save_upload(self, file: UploadFile, *, prefix: str, allowed_types: Set[str], allowed_extensions: Set[str], max_size: int = MAX_FILE_SIZE, namespace: Optional[str] = None) -> Dict[str, Any]:
        file_name, content_type, content = await self._read_and_validate_upload(
            file,
            allowed_types=allowed_types,
            allowed_extensions=allowed_extensions,
            max_size=max_size,
        )
        return self.save_bytes(content=content, filename=file_name, prefix=prefix, content_type=content_type or None, namespace=namespace)

    def save_bytes(self, *, content: bytes, filename: str, prefix: str, content_type: str | None = None, namespace: Optional[str] = None) -> Dict[str, Any]:
        pathname = self.build_key(prefix=prefix, filename=filename, namespace=namespace)
        blob = self.client.put(
            pathname,
            content,
            access=self.access,
            add_random_suffix=self.add_random_suffix,
            content_type=content_type,
        )
        blob_path = getattr(blob, "pathname", pathname)
        return {
            "storage_key": blob_path,
            "byte_size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "content_type": content_type,
            "original_file_name": filename,
            "url": getattr(blob, "url", None),
            "download_url": getattr(blob, "download_url", None),
            "etag": getattr(blob, "etag", None),
        }

    def _get_blob(self, storage_key: str):
        return self.client.get(storage_key, access=self.access)

    def read_bytes(self, storage_key: str) -> bytes:
        blob = self._get_blob(storage_key)
        if blob is None:
            raise FileNotFoundError(f"Storage file not found: {storage_key}")
        if hasattr(blob, "read"):
            return blob.read()
        stream = getattr(blob, "stream", None)
        if stream is None:
            raise RuntimeError(f"Unable to read blob content for {storage_key}")
        if hasattr(stream, "read"):
            return stream.read()
        return io.BytesIO(b"".join(stream)).read()

    def file_url(self, storage_key: str, base_url: str = "") -> str:
        if not storage_key:
            return ""
        blob = self.client.head(storage_key)
        if blob is None:
            return ""
        return getattr(blob, "url", "") or ""

    def presign(self, storage_key: str, operation: str = "download", expires_in: int = settings.STORAGE_PRESIGN_TTL_SECONDS) -> Dict[str, Any]:
        if operation == "download":
            blob = self.client.head(storage_key)
            url = getattr(blob, "download_url", None) or getattr(blob, "url", None)
            return {
                "storageKey": storage_key,
                "operation": operation,
                "expiresAt": int(time.time()) + expires_in,
                "token": None,
                "url": url,
                "backend": self.backend,
            }
        return {
            "storageKey": storage_key,
            "operation": operation,
            "expiresAt": int(time.time()) + expires_in,
            "token": None,
            "url": None,
            "backend": self.backend,
            "note": "Server-side uploads only. Upload through the backend when using vercel_blob.",
        }

    def healthcheck(self) -> Dict[str, Any]:
        try:
            listing = self.client.list_objects(limit=1)
            return {"backend": self.backend, "ok": True, "sampleCount": len(getattr(listing, "blobs", []) or [])}
        except Exception as exc:
            return {"backend": self.backend, "ok": False, "error": str(exc)}


storage_service: BaseStorageService
if settings.has_s3_storage:
    storage_service = S3StorageService()
elif settings.has_vercel_blob_storage:
    try:
        storage_service = VercelBlobStorageService()
    except Exception as exc:
        print(f"Warning: Vercel Blob unavailable, falling back to local storage: {exc}")
        storage_service = LocalStorageService(settings.resolved_storage_root)
else:
    storage_service = LocalStorageService(settings.resolved_storage_root)
