from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from config import settings

Base = declarative_base()

DATABASE_URL = settings.resolved_database_url
IS_SQLITE = settings.is_sqlite

engine_kwargs = {
    "echo": settings.SQL_ECHO,
}
if not IS_SQLITE:
    engine_kwargs.update(
        {
            "pool_pre_ping": True,
            "pool_size": settings.SQL_POOL_SIZE,
            "max_overflow": settings.SQL_MAX_OVERFLOW,
        }
    )

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

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


async def bootstrap_schema_if_needed(force: bool = False) -> None:
    if not IS_SQLITE and not force:
        return

    from models import Base as ModelsBase

    async with engine.begin() as conn:
        await conn.run_sync(ModelsBase.metadata.create_all)
