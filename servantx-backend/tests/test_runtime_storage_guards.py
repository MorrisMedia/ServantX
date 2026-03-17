import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

MODULE_NAME = "config"


@pytest.fixture(autouse=True)
def clear_vercel_env(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)


@pytest.fixture
def config_module():
    sys.modules.pop(MODULE_NAME, None)
    module = importlib.import_module(MODULE_NAME)
    yield module
    sys.modules.pop(MODULE_NAME, None)


def test_development_allows_sqlite_and_local_storage(monkeypatch, config_module):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test-dev.db")
    monkeypatch.setenv("STORAGE_BACKEND", "local")

    settings = config_module.Settings()
    config_module._validate_runtime_requirements(settings)

    assert settings.is_sqlite is True
    assert settings.STORAGE_BACKEND == "local"


def test_production_rejects_sqlite(monkeypatch, config_module):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./prod.db")
    monkeypatch.setenv("STORAGE_BACKEND", "s3")

    settings = config_module.Settings()

    with pytest.raises(RuntimeError, match="SQLite is only allowed"):
        config_module._validate_runtime_requirements(settings)


def test_production_rejects_local_storage(monkeypatch, config_module):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/servantx")
    monkeypatch.setenv("STORAGE_BACKEND", "local")

    settings = config_module.Settings()

    with pytest.raises(RuntimeError, match="Local filesystem storage is only allowed"):
        config_module._validate_runtime_requirements(settings)


def test_vercel_blob_requires_token(monkeypatch, config_module):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/servantx")
    monkeypatch.setenv("STORAGE_BACKEND", "vercel_blob")
    monkeypatch.delenv("BLOB_READ_WRITE_TOKEN", raising=False)

    settings = config_module.Settings()

    with pytest.raises(RuntimeError, match="BLOB_READ_WRITE_TOKEN is required"):
        config_module._validate_runtime_requirements(settings)
