from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from dotenv import load_dotenv
from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

if not os.getenv("VERCEL"):
    load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=True)

    APP_NAME: str = "ServantX API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "test", "staging", "production"] = "development"
    DEPLOYMENT_TARGET: Literal["default", "vercel"] = "default"
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    API_BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5000"
    CORS_ORIGINS: list[str] | str = Field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:5000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000",
        "https://www.servantx.ai",
        "https://servantx.ai",
        "https://servantx-frontend.vercel.app",
    ])

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    ADMIN_SECRET_KEY: str = ""
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "servantx@hirekosovo.com"
    SENDGRID_FROM_NAME: str = "ServantX Contact"
    SENDGRID_TO_EMAIL: str = ""
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    PHI_ENCRYPTION_KEY: str = ""

    DATABASE_URL: str = ""
    POSTGRES_URL: str = ""
    POSTGRES_URL_NON_POOLING: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "servantx"
    SQL_ECHO: bool = False
    SQL_POOL_SIZE: int = 10
    SQL_MAX_OVERFLOW: int = 20

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    ENABLE_CELERY_ASYNC: bool = False
    FORCE_INLINE_TASKS: bool = False

    STORAGE_BACKEND: Literal["local", "s3", "vercel_blob"] = "local"
    STORAGE_ROOT: str = "uploads"
    STORAGE_PUBLIC_BASE_URL: str = ""
    STORAGE_BUCKET: str = ""
    STORAGE_REGION: str = "us-east-1"
    STORAGE_ENDPOINT_URL: str = ""
    STORAGE_ACCESS_KEY_ID: str = ""
    STORAGE_SECRET_ACCESS_KEY: str = ""
    STORAGE_FORCE_PATH_STYLE: bool = False
    STORAGE_PRESIGN_SECRET: str = "dev-storage-secret"
    STORAGE_PRESIGN_TTL_SECONDS: int = 900
    DUCKDB_WORKSPACE_ROOT: str = "uploads/workspaces"
    BLOB_READ_WRITE_TOKEN: str = ""
    VERCEL_BLOB_ACCESS: Literal["private", "public"] = "private"
    VERCEL_BLOB_ADD_RANDOM_SUFFIX: bool = True

    AUTO_BOOTSTRAP_SQLITE: bool = True
    AUTO_SEED_RATE_DATA: bool = False

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def _normalize_environment(cls, value):
        if os.getenv("VERCEL") and (value is None or value == "development"):
            return "production"
        return value

    @field_validator("DEPLOYMENT_TARGET", mode="before")
    @classmethod
    def _normalize_deployment_target(cls, value):
        if os.getenv("VERCEL") and (value is None or value == "default"):
            return "vercel"
        return value

    @field_validator("STORAGE_BACKEND", mode="before")
    @classmethod
    def _normalize_storage_backend(cls, value):
        if os.getenv("VERCEL") and (value is None or value == "local"):
            return "vercel_blob"
        return value

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_vercel(self) -> bool:
        return self.DEPLOYMENT_TARGET == "vercel" or bool(os.getenv("VERCEL"))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_database_url(self) -> str:
        candidate = self.DATABASE_URL or self.POSTGRES_URL or self.POSTGRES_URL_NON_POOLING
        if candidate:
            if candidate.startswith("sqlite:///") and "+aiosqlite" not in candidate:
                return candidate.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
            if candidate.startswith("postgres") and "+asyncpg" not in candidate:
                # Ensure asyncpg driver prefix
                candidate = candidate.replace("postgresql://", "postgresql+asyncpg://", 1)
                candidate = candidate.replace("postgres://", "postgresql+asyncpg://", 1)
            # Strip sslmode query param — asyncpg uses connect_args ssl instead
            parsed = urlparse(candidate)
            qs = parse_qs(parsed.query, keep_blank_values=True)
            qs.pop("sslmode", None)
            candidate = urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))
            return candidate

        pg_host = os.getenv("PGHOST") or os.getenv("POSTGRES_HOST") or self.DB_HOST
        pg_port = os.getenv("PGPORT") or os.getenv("POSTGRES_PORT") or str(self.DB_PORT)
        pg_user = os.getenv("PGUSER") or os.getenv("POSTGRES_USER") or self.POSTGRES_USER
        pg_password = os.getenv("PGPASSWORD") or os.getenv("POSTGRES_PASSWORD") or self.POSTGRES_PASSWORD
        pg_db = os.getenv("PGDATABASE") or os.getenv("POSTGRES_DATABASE") or self.POSTGRES_DB
        if pg_host and pg_user and pg_db:
            return f"postgresql+asyncpg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"

        if self.ENVIRONMENT == "development":
            sqlite_path = Path("./servantx_local.db").resolve()
            return f"sqlite+aiosqlite:///{sqlite_path}"
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_sqlite(self) -> bool:
        return self.resolved_database_url.startswith("sqlite+aiosqlite://")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_storage_root(self) -> Path:
        root = Path(self.STORAGE_ROOT)
        if root.is_absolute():
            return root.expanduser().resolve()
        if self.is_vercel:
            return (Path("/tmp") / root).resolve()
        return root.expanduser().resolve()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_duckdb_workspace_root(self) -> Path:
        root = Path(self.DUCKDB_WORKSPACE_ROOT)
        if root.is_absolute():
            return root.expanduser().resolve()
        if self.is_vercel:
            return (Path("/tmp") / root).resolve()
        return (Path.cwd() / root).resolve()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_s3_storage(self) -> bool:
        return self.STORAGE_BACKEND == "s3"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_vercel_blob_storage(self) -> bool:
        return self.STORAGE_BACKEND == "vercel_blob"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def celery_async_enabled(self) -> bool:
        return self.ENABLE_CELERY_ASYNC and not self.FORCE_INLINE_TASKS and not self.is_vercel


def _validate_runtime_requirements(settings: Settings) -> None:
    requires_durable_database = settings.ENVIRONMENT != "development" or settings.is_vercel
    requires_durable_storage = settings.ENVIRONMENT != "development" or settings.is_vercel

    if requires_durable_database and settings.is_sqlite:
        raise RuntimeError(
            "SQLite is only allowed in local development. Configure DATABASE_URL/POSTGRES_URL for staging, production, or Vercel deployments."
        )

    if requires_durable_storage and settings.STORAGE_BACKEND == "local":
        raise RuntimeError(
            "Local filesystem storage is only allowed in local development. Configure STORAGE_BACKEND=s3 or STORAGE_BACKEND=vercel_blob for staging, production, or Vercel deployments."
        )

    if settings.is_vercel and settings.STORAGE_BACKEND == "vercel_blob" and not settings.BLOB_READ_WRITE_TOKEN:
        raise RuntimeError(
            "BLOB_READ_WRITE_TOKEN is required when deploying to Vercel with STORAGE_BACKEND=vercel_blob."
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    _validate_runtime_requirements(settings)
    settings.resolved_storage_root.mkdir(parents=True, exist_ok=True)
    settings.resolved_duckdb_workspace_root.mkdir(parents=True, exist_ok=True)
    if settings.is_sqlite:
        sqlite_path = settings.resolved_database_url.replace("sqlite+aiosqlite:///", "", 1)
        if sqlite_path and sqlite_path != ":memory:":
            Path(sqlite_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()
