from __future__ import annotations

from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession


async def auto_seed_rate_data(db: AsyncSession) -> list[dict]:
    """
    Seed all CMS 2026 Medicare/Medicaid rate tables.

    Each seeder is idempotent — safe to call on every startup.
    Returns a list of dicts describing what was seeded.
    """
    seeded: list[dict] = []

    # Seed OPPS APC rates
    from services.opps_seed_service import seed_opps_rates
    opps_inserted = await seed_opps_rates(db)
    if opps_inserted > 0:
        seeded.append({
            "payer_key": "CMS_OPPS_2026",
            "rows_imported": opps_inserted,
            "sha256": "static_seed",
        })

    # Seed CMS Medicare tables
    from services.medicare_seed_service import (
        seed_conversion_factor,
        seed_gpci,
        seed_rvu_rates,
        seed_zip_locality,
        seed_drg_weights,
    )

    cf_rows = await seed_conversion_factor(db)
    if cf_rows > 0:
        seeded.append({"payer_key": "MEDICARE_CONVERSION_FACTOR", "rows_imported": cf_rows, "sha256": "hardcoded"})

    gpci_rows = await seed_gpci(db)
    if gpci_rows > 0:
        seeded.append({"payer_key": "MEDICARE_GPCI", "rows_imported": gpci_rows, "sha256": "hardcoded"})

    rvu_rows = await seed_rvu_rates(db)
    if rvu_rows > 0:
        seeded.append({"payer_key": "MEDICARE_MPFS_RVU", "rows_imported": rvu_rows, "sha256": "cms_download"})

    zip_rows = await seed_zip_locality(db)
    if zip_rows > 0:
        seeded.append({"payer_key": "MEDICARE_ZIP_LOCALITY", "rows_imported": zip_rows, "sha256": "cms_download"})

    drg_rows = await seed_drg_weights(db)
    if drg_rows > 0:
        seeded.append({"payer_key": "MEDICARE_DRG_WEIGHTS", "rows_imported": drg_rows, "sha256": "hardcoded"})

    # Seed TX Medicaid FFS
    from services.tx_medicaid_seed_service import seed_tx_medicaid
    tx_rows = await seed_tx_medicaid(db)
    if tx_rows > 0:
        seeded.append({"payer_key": "TX_MEDICAID_FFS", "rows_imported": tx_rows, "sha256": "hardcoded"})

    return seeded
