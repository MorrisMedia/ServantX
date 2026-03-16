from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import (
    MedicareConversionFactor,
    MedicareGpci,
    MedicareRvuRate,
    MedicareZipLocality,
    RateVersion,
    TxMedicaidFfsFeeSchedule,
)


@dataclass
class RateImportResult:
    payer_key: str
    version_label: str
    rows_imported: int
    row_count_total: int
    sha256: str
    skipped: bool = False


SUPPORTED_PAYER_KEYS = {
    "MEDICARE_MPFS",
    "MEDICARE_GPCI",
    "MEDICARE_ZIP_LOCALITY",
    "MEDICARE_CONVERSION_FACTOR",
    "TX_MEDICAID_FFS",
}


def parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        if len(value) == 8 and value.isdigit():
            return date(int(value[0:4]), int(value[4:6]), int(value[6:8]))
    return None


def parse_float(value: Optional[str], default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(str(value).strip())
    except ValueError:
        return default


def parse_int(value: Optional[str], default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return default


def load_csv_rows(file_content: bytes) -> tuple[list[dict[str, str]], str]:
    if not file_content:
        raise ValueError("File is empty")
    sha256 = hashlib.sha256(file_content).hexdigest()
    decoded = file_content.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(decoded))
    rows = list(reader)
    if not rows:
        raise ValueError("No rows found in CSV")
    return rows, sha256


async def import_rate_rows(
    db: AsyncSession,
    *,
    payer_key: str,
    version_label: str,
    source_url: str,
    rows: list[dict[str, str]],
    sha256: str,
) -> RateImportResult:
    if payer_key not in SUPPORTED_PAYER_KEYS:
        raise ValueError(f"Unsupported payerKey: {payer_key}")

    existing_version = await db.execute(
        select(RateVersion).where(
            RateVersion.payer_key == payer_key,
            RateVersion.sha256 == sha256,
        )
    )
    existing = existing_version.scalar_one_or_none()
    if existing:
        total = await _count_total(db, payer_key)
        return RateImportResult(
            payer_key=payer_key,
            version_label=existing.version_label,
            rows_imported=0,
            row_count_total=total,
            sha256=sha256,
            skipped=True,
        )

    imported_count = 0
    if payer_key == "MEDICARE_MPFS":
        for row in rows:
            db.add(
                MedicareRvuRate(
                    year=parse_int(row.get("year")),
                    cpt_hcpcs=(row.get("cpt_hcpcs") or row.get("cpt") or "").strip(),
                    work_rvu=parse_float(row.get("work_rvu")),
                    pe_rvu_facility=parse_float(row.get("pe_rvu_facility")),
                    pe_rvu_nonfacility=parse_float(row.get("pe_rvu_nonfacility")),
                    mp_rvu=parse_float(row.get("mp_rvu")),
                    status_indicator=(row.get("status_indicator") or None),
                    global_days=(row.get("global_days") or None),
                )
            )
            imported_count += 1
    elif payer_key == "MEDICARE_GPCI":
        for row in rows:
            db.add(
                MedicareGpci(
                    year=parse_int(row.get("year")),
                    locality_code=(row.get("locality_code") or "").strip(),
                    locality_name=(row.get("locality_name") or "").strip(),
                    work_gpci=parse_float(row.get("work_gpci")),
                    pe_gpci=parse_float(row.get("pe_gpci")),
                    mp_gpci=parse_float(row.get("mp_gpci")),
                )
            )
            imported_count += 1
    elif payer_key == "MEDICARE_ZIP_LOCALITY":
        for row in rows:
            db.add(
                MedicareZipLocality(
                    zip_code=(row.get("zip_code") or "").strip()[:5],
                    locality_code=(row.get("locality_code") or "").strip(),
                )
            )
            imported_count += 1
    elif payer_key == "MEDICARE_CONVERSION_FACTOR":
        for row in rows:
            db.add(
                MedicareConversionFactor(
                    year=parse_int(row.get("year")),
                    conversion_factor=parse_float(row.get("conversion_factor")),
                )
            )
            imported_count += 1
    elif payer_key == "TX_MEDICAID_FFS":
        for row in rows:
            db.add(
                TxMedicaidFfsFeeSchedule(
                    effective_start=parse_date(row.get("effective_start")) or date.today(),
                    effective_end=parse_date(row.get("effective_end")),
                    cpt_hcpcs=(row.get("cpt_hcpcs") or row.get("cpt") or "").strip(),
                    modifier=(row.get("modifier") or None),
                    allowed_amount=parse_float(row.get("allowed_amount")),
                )
            )
            imported_count += 1

    version = RateVersion(
        payer_key=payer_key,
        version_label=version_label,
        effective_start=None,
        effective_end=None,
        source_url=source_url,
        imported_at=datetime.utcnow(),
        row_count=imported_count,
        sha256=sha256,
    )
    db.add(version)
    await db.commit()

    total = await _count_total(db, payer_key)
    return RateImportResult(
        payer_key=payer_key,
        version_label=version_label,
        rows_imported=imported_count,
        row_count_total=total,
        sha256=sha256,
        skipped=False,
    )


async def _count_total(db: AsyncSession, payer_key: str) -> int:
    if payer_key == "MEDICARE_MPFS":
        query = select(func.count(MedicareRvuRate.id))
    elif payer_key == "MEDICARE_GPCI":
        query = select(func.count(MedicareGpci.id))
    elif payer_key == "MEDICARE_ZIP_LOCALITY":
        query = select(func.count(MedicareZipLocality.id))
    elif payer_key == "MEDICARE_CONVERSION_FACTOR":
        query = select(func.count(MedicareConversionFactor.id))
    elif payer_key == "TX_MEDICAID_FFS":
        query = select(func.count(TxMedicaidFfsFeeSchedule.id))
    else:
        raise ValueError(f"Unsupported payerKey: {payer_key}")
    result = await db.execute(query)
    return int(result.scalar() or 0)
