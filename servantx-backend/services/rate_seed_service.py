from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import RateVersion
from services.rate_import_service import import_rate_rows, load_csv_rows

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEMO_DATA_DIR = BACKEND_ROOT / "demo_data"
RATE_FILES: List[Dict[str, str]] = [
    {
        "payer_key": "MEDICARE_MPFS",
        "version_label": "CMS MPFS 2026",
        "source_url": "https://www.cms.gov/files/zip/rvu26a-updated-12-29-2025.zip",
        "path": str(DEMO_DATA_DIR / "medicare_mpfs_2026.csv"),
    },
    {
        "payer_key": "MEDICARE_GPCI",
        "version_label": "CMS GPCI 2026",
        "source_url": "https://www.cms.gov/files/zip/rvu26a-updated-12-29-2025.zip",
        "path": str(DEMO_DATA_DIR / "medicare_gpci_2026.csv"),
    },
    {
        "payer_key": "MEDICARE_CONVERSION_FACTOR",
        "version_label": "CMS Conversion Factor 2026",
        "source_url": "https://www.cms.gov/files/zip/rvu26a-updated-12-29-2025.zip",
        "path": str(DEMO_DATA_DIR / "medicare_conversion_factor_2026.csv"),
    },
    {
        "payer_key": "MEDICARE_ZIP_LOCALITY",
        "version_label": "CMS ZIP Locality 2026",
        "source_url": "https://www.cms.gov/files/zip/zip-code-carrier-locality-file-revised-02-18-2026.zip",
        "path": str(DEMO_DATA_DIR / "medicare_zip_locality_2026.csv"),
    },
    {
        "payer_key": "TX_MEDICAID_FFS",
        "version_label": "TMHP expanded fee schedule 2026",
        "source_url": "https://public.tmhp.com/FeeSchedules/StaticFeeSchedule/FeeSchedules.aspx?fn=%5c%5ctmhp.net%5cFeeSchedule%5cPROD%5cStatic%5cTexas_Medicaid_Fee_Schedule_PRCR405C.xls",
        "path": str(DEMO_DATA_DIR / "tx_medicaid_ffs_expanded_2026.csv"),
    },
]


async def auto_seed_rate_data(db: AsyncSession) -> list[dict]:
    seeded = []
    for item in RATE_FILES:
        existing = await db.execute(select(RateVersion).where(RateVersion.payer_key == item["payer_key"]))
        if existing.scalars().first():
            continue
        payload = Path(item["path"]).read_bytes()
        rows, sha256 = load_csv_rows(payload)
        result = await import_rate_rows(
            db,
            payer_key=item["payer_key"],
            version_label=item["version_label"],
            source_url=item["source_url"],
            rows=rows,
            sha256=sha256,
        )
        seeded.append({
            "payer_key": result.payer_key,
            "rows_imported": result.rows_imported,
            "sha256": result.sha256,
        })

    # Seed OPPS APC rates (idempotent — ON CONFLICT DO NOTHING)
    from services.opps_seed_service import seed_opps_rates
    opps_inserted = await seed_opps_rates(db)
    if opps_inserted > 0:
        seeded.append({
            "payer_key": "CMS_OPPS_2026",
            "rows_imported": opps_inserted,
            "sha256": "static_seed",
        })

    return seeded
