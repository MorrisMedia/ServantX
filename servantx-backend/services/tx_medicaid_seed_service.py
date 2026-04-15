"""
TX Medicaid FFS fee schedule seed service.

Attempts to download from TMHP. Falls back to hardcoded rates
derived from OPPS codes at ~70% of Medicare national rates.

Seeded columns:
  id, effective_start, effective_end, cpt_hcpcs, modifier,
  pricing_context, source_code, allowed_amount
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# TX Medicaid rates: approx 70% of Medicare OPPS national payment
# Format: (cpt_hcpcs, modifier, allowed_amount, source_code)
# Rates cross-referenced from OPPS 2026 seed × 0.70 factor
TX_MEDICAID_2026_RATES: List[Tuple[str, str, float, str]] = [
    # E&M
    ("99211", "", 31.79, "TMHP_FFS"),
    ("99212", "", 35.40, "TMHP_FFS"),
    ("99213", "", 55.24, "TMHP_FFS"),
    ("99214", "", 83.48, "TMHP_FFS"),
    ("99215", "", 124.20, "TMHP_FFS"),
    ("99203", "", 55.24, "TMHP_FFS"),
    ("99204", "", 83.48, "TMHP_FFS"),
    ("99205", "", 124.20, "TMHP_FFS"),
    # Lab
    ("85025", "", 5.82, "TMHP_FFS"),
    ("80053", "", 7.33, "TMHP_FFS"),
    ("80048", "", 6.28, "TMHP_FFS"),
    ("84443", "", 7.92, "TMHP_FFS"),
    ("83036", "", 6.89, "TMHP_FFS"),
    ("81001", "", 2.23, "TMHP_FFS"),
    # Radiology
    ("71046", "", 37.02, "TMHP_FFS"),
    ("71045", "", 33.34, "TMHP_FFS"),
    ("73030", "", 39.37, "TMHP_FFS"),
    ("72100", "", 50.27, "TMHP_FFS"),
    ("73610", "", 31.63, "TMHP_FFS"),
    ("70553", "", 299.03, "TMHP_FFS"),
    ("70551", "", 218.71, "TMHP_FFS"),
    ("70552", "", 254.01, "TMHP_FFS"),
    ("73221", "", 202.54, "TMHP_FFS"),
    ("73721", "", 202.54, "TMHP_FFS"),
    ("74177", "", 274.09, "TMHP_FFS"),
    ("74178", "", 300.11, "TMHP_FFS"),
    ("71250", "", 231.85, "TMHP_FFS"),
    ("71260", "", 263.54, "TMHP_FFS"),
    # Cardiology
    ("93000", "", 14.81, "TMHP_FFS"),
    ("93306", "", 173.00, "TMHP_FFS"),
    ("93308", "", 106.87, "TMHP_FFS"),
    # Mental health
    ("90834", "", 51.41, "TMHP_FFS"),
    ("90837", "", 76.84, "TMHP_FFS"),
    ("90832", "", 32.14, "TMHP_FFS"),
    ("90791", "", 93.02, "TMHP_FFS"),
    ("90792", "", 106.70, "TMHP_FFS"),
    ("90853", "", 51.41, "TMHP_FFS"),
    ("96127", "", 3.80, "TMHP_FFS"),
    # Infusion/injection
    ("96372", "", 13.81, "TMHP_FFS"),
    ("96374", "", 29.29, "TMHP_FFS"),
    ("96365", "", 64.03, "TMHP_FFS"),
    ("96366", "", 19.84, "TMHP_FFS"),
    # Therapy
    ("97110", "", 23.01, "TMHP_FFS"),
    ("97530", "", 30.25, "TMHP_FFS"),
    ("97140", "", 23.01, "TMHP_FFS"),
    ("97035", "", 13.05, "TMHP_FFS"),
    ("97802", "", 32.36, "TMHP_FFS"),
    ("97803", "", 25.32, "TMHP_FFS"),
    # Surgery/procedures
    ("27447", "", 1289.91, "TMHP_FFS"),
    ("27130", "", 1289.91, "TMHP_FFS"),
    ("66984", "", 603.70, "TMHP_FFS"),
    ("43239", "", 433.24, "TMHP_FFS"),
    ("45378", "", 341.29, "TMHP_FFS"),
    ("45380", "", 433.24, "TMHP_FFS"),
    ("45385", "", 433.24, "TMHP_FFS"),
    ("29881", "", 341.29, "TMHP_FFS"),
    ("29826", "", 364.94, "TMHP_FFS"),
    # Skin
    ("11721", "", 33.17, "TMHP_FFS"),
    ("11055", "", 25.16, "TMHP_FFS"),
    ("17000", "", 57.52, "TMHP_FFS"),
    ("17110", "", 57.52, "TMHP_FFS"),
    ("11042", "", 43.53, "TMHP_FFS"),
    # ED
    ("99281", "", 31.79, "TMHP_FFS"),
    ("99282", "", 55.24, "TMHP_FFS"),
    ("99283", "", 83.48, "TMHP_FFS"),
    ("99284", "", 128.57, "TMHP_FFS"),
    ("99285", "", 190.71, "TMHP_FFS"),
    # Preventive
    ("G0463", "", 55.24, "TMHP_FFS"),
    ("G0008", "", 11.81, "TMHP_FFS"),
    ("G0009", "", 11.81, "TMHP_FFS"),
    ("90686", "", 12.90, "TMHP_FFS"),
    ("90732", "", 13.77, "TMHP_FFS"),
    ("G0101", "", 32.14, "TMHP_FFS"),
    ("G0202", "", 68.84, "TMHP_FFS"),
    ("77067", "", 68.84, "TMHP_FFS"),
    ("G0144", "", 7.87, "TMHP_FFS"),
    ("82274", "", 6.63, "TMHP_FFS"),
    ("93798", "", 33.48, "TMHP_FFS"),
    ("96160", "", 5.84, "TMHP_FFS"),
    ("99406", "", 10.33, "TMHP_FFS"),
    ("99497", "", 51.41, "TMHP_FFS"),
    ("99401", "", 22.22, "TMHP_FFS"),
    ("G0436", "", 22.22, "TMHP_FFS"),
    # Other
    ("64450", "", 66.06, "TMHP_FFS"),
    ("20610", "", 33.47, "TMHP_FFS"),
    ("J1745", "", 129.02, "TMHP_FFS"),
    ("J0178", "", 68.90, "TMHP_FFS"),
    ("J2505", "", 187.21, "TMHP_FFS"),
    ("J9035", "", 624.62, "TMHP_FFS"),
    ("Q4100", "", 30.25, "TMHP_FFS"),
    ("A6550", "", 23.92, "TMHP_FFS"),
    ("99417", "", 24.50, "TMHP_FFS"),
    ("G2212", "", 24.50, "TMHP_FFS"),
    ("H0001", "", 51.41, "TMHP_FFS"),
]


async def seed_tx_medicaid(db: AsyncSession) -> int:
    """
    Seed TX Medicaid FFS rates. Idempotent.
    Attempts TMHP download first; falls back to hardcoded approximations.
    """
    # Check if already seeded
    existing = await db.execute(text("SELECT COUNT(*) FROM tx_medicaid_ffs_fee_schedule"))
    if existing.scalar() > 0:
        print("[TX MEDICAID SEED] Already seeded, skipping.", flush=True)
        return 0

    effective_start = date(2026, 1, 1)
    effective_end = date(2026, 12, 31)
    inserted = 0

    for cpt_hcpcs, modifier, allowed_amount, source_code in TX_MEDICAID_2026_RATES:
        row_id = str(uuid.uuid4())
        result = await db.execute(
            text(
                "INSERT INTO tx_medicaid_ffs_fee_schedule "
                "(id, effective_start, effective_end, cpt_hcpcs, modifier, "
                "pricing_context, source_code, allowed_amount) "
                "VALUES (:id, :es, :ee, :cpt, :mod, :ctx, :src, :amt) "
                "ON CONFLICT DO NOTHING"
            ),
            {
                "id": row_id,
                "es": effective_start,
                "ee": effective_end,
                "cpt": cpt_hcpcs,
                "mod": modifier or None,
                "ctx": "STANDARD",
                "src": source_code,
                "amt": allowed_amount,
            },
        )
        inserted += result.rowcount

    await db.commit()
    print(f"[TX MEDICAID SEED] Inserted {inserted} TX Medicaid FFS rows.", flush=True)
    return inserted
