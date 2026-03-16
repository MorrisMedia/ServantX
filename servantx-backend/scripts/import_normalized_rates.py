from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from core_services.db_service import AsyncSessionLocal, bootstrap_schema_if_needed
from services.rate_import_service import import_rate_rows, load_csv_rows


RATE_FILES = [
    {
        "payer_key": "MEDICARE_MPFS",
        "version_label": "CMS MPFS 2026",
        "source_url": "https://www.cms.gov/files/zip/rvu26a-updated-12-29-2025.zip",
        "path": REPO_ROOT / "data" / "normalized_rate_imports" / "medicare_mpfs_2026.csv",
    },
    {
        "payer_key": "MEDICARE_GPCI",
        "version_label": "CMS GPCI 2026",
        "source_url": "https://www.cms.gov/files/zip/rvu26a-updated-12-29-2025.zip",
        "path": REPO_ROOT / "data" / "normalized_rate_imports" / "medicare_gpci_2026.csv",
    },
    {
        "payer_key": "MEDICARE_CONVERSION_FACTOR",
        "version_label": "CMS Conversion Factor 2026",
        "source_url": "https://www.cms.gov/files/zip/rvu26a-updated-12-29-2025.zip",
        "path": REPO_ROOT / "data" / "normalized_rate_imports" / "medicare_conversion_factor_2026.csv",
    },
    {
        "payer_key": "MEDICARE_ZIP_LOCALITY",
        "version_label": "CMS ZIP Locality 2026",
        "source_url": "https://www.cms.gov/files/zip/zip-code-carrier-locality-file-revised-02-18-2026.zip",
        "path": REPO_ROOT / "data" / "normalized_rate_imports" / "medicare_zip_locality_2026.csv",
    },
    {
        "payer_key": "TX_MEDICAID_FFS",
        "version_label": "TMHP PRCR405C / import-ready 2026",
        "source_url": "https://public.tmhp.com/FeeSchedules/StaticFeeSchedule/FeeSchedules.aspx?fn=%5c%5ctmhp.net%5cFeeSchedule%5cPROD%5cStatic%5cTexas_Medicaid_Fee_Schedule_PRCR405C.xls",
        "path": REPO_ROOT / "data" / "normalized_rate_imports" / "tx_medicaid_ffs_2026.csv",
    },
]


async def main(selected: set[str] | None = None) -> None:
    await bootstrap_schema_if_needed()
    targets = [item for item in RATE_FILES if not selected or item["payer_key"] in selected]
    if not targets:
        raise SystemExit("No matching payer keys selected.")

    async with AsyncSessionLocal() as db:
        for item in targets:
            payload = item["path"].read_bytes()
            rows, sha256 = load_csv_rows(payload)
            result = await import_rate_rows(
                db,
                payer_key=item["payer_key"],
                version_label=item["version_label"],
                source_url=item["source_url"],
                rows=rows,
                sha256=sha256,
            )
            verb = "SKIPPED" if result.skipped else "IMPORTED"
            print(
                f"{verb} {result.payer_key}: rowsImported={result.rows_imported} "
                f"rowCountTotal={result.row_count_total} sha256={result.sha256[:12]}"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import normalized ServantX rate CSVs into the configured database")
    parser.add_argument("--payer", action="append", dest="payers", help="Optional payer key to import (repeatable)")
    args = parser.parse_args()
    asyncio.run(main(set(args.payers or [])))
