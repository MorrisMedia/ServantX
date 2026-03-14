from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

load_dotenv()

Base = declarative_base()


def _normalize_database_url(raw_url: str | None) -> str:
    if raw_url:
        if raw_url.startswith("sqlite:///") and "+aiosqlite" not in raw_url:
            return raw_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return raw_url

    default_path = Path("./servantx_local.db").resolve()
    return f"sqlite+aiosqlite:///{default_path}"


DATABASE_URL = _normalize_database_url(os.getenv("DATABASE_URL"))
IS_SQLITE = DATABASE_URL.startswith("sqlite+aiosqlite://")

if IS_SQLITE:
    sqlite_path = DATABASE_URL.replace("sqlite+aiosqlite:///", "", 1)
    if sqlite_path and sqlite_path != ":memory:":
        Path(sqlite_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=not IS_SQLITE,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def bootstrap_schema_if_needed() -> None:
    if not IS_SQLITE:
        return

    from models import Base as ModelsBase

    async with engine.begin() as conn:
        await conn.run_sync(ModelsBase.metadata.create_all)
