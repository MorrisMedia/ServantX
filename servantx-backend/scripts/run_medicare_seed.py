"""
Run all Medicare/Medicaid rate seeds against production DB.

Usage:
    DATABASE_URL=... .venv/bin/python3 scripts/run_medicare_seed.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    # Patch DATABASE_URL to asyncpg format if needed
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url and not db_url.startswith("postgresql+asyncpg://"):
        if db_url.startswith("postgresql://"):
            os.environ["DATABASE_URL"] = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgres://"):
            os.environ["DATABASE_URL"] = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

    from core_services.db_service import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        print("=== Medicare/Medicaid Rate Seed ===", flush=True)

        from services.medicare_seed_service import (
            seed_conversion_factor,
            seed_gpci,
            seed_rvu_rates,
            seed_zip_locality,
            seed_drg_weights,
        )
        from services.tx_medicaid_seed_service import seed_tx_medicaid

        cf_count = await seed_conversion_factor(db)
        gpci_count = await seed_gpci(db)
        rvu_count = await seed_rvu_rates(db)
        zip_count = await seed_zip_locality(db)
        drg_count = await seed_drg_weights(db)
        tx_count = await seed_tx_medicaid(db)

        print("\n=== Seed Complete ===", flush=True)
        print(f"  Conversion factor rows: {cf_count}", flush=True)
        print(f"  GPCI rows:              {gpci_count}", flush=True)
        print(f"  RVU rate rows:          {rvu_count}", flush=True)
        print(f"  ZIP locality rows:      {zip_count}", flush=True)
        print(f"  DRG weight rows:        {drg_count}", flush=True)
        print(f"  TX Medicaid rows:       {tx_count}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
