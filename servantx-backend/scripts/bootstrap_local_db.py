from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from core_services.db_service import DATABASE_URL, IS_SQLITE, bootstrap_schema_if_needed


async def main() -> None:
    if not IS_SQLITE:
        raise SystemExit(
            f"bootstrap_local_db.py is intended for SQLite local dev only. DATABASE_URL={DATABASE_URL}"
        )
    await bootstrap_schema_if_needed()
    print(f"✅ SQLite schema ready at {DATABASE_URL}")


if __name__ == "__main__":
    asyncio.run(main())
