import csv
import hashlib
import io
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select

from core_services.db_service import AsyncSessionLocal
from models import (
    MedicareConversionFactor,
    MedicareGpci,
    MedicareRvuRate,
    MedicareZipLocality,
    RateVersion,
    TxMedicaidFfsFeeSchedule,
)
from routes.auth import get_current_user
from schemas import RateImportResponse, RateStatusResponse


router = APIRouter(prefix="/admin/rates", tags=["admin-rates"])


def _parse_date(value: Optional[str]) -> Optional[date]:
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


def _parse_float(value: Optional[str], default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(str(value).strip())
    except ValueError:
        return default


def _parse_int(value: Optional[str], default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return default


@router.post("/import", response_model=RateImportResponse)
async def import_rates(
    payer_key: str = Form(..., alias="payerKey"),
    version_label: str = Form(..., alias="versionLabel"),
    source_url: str = Form(..., alias="sourceUrl"),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    file_content = await file.read()
    if not file_content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

    sha256 = hashlib.sha256(file_content).hexdigest()
    decoded = file_content.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(decoded))
    rows = list(reader)
    if not rows:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No rows found in CSV")

    async with AsyncSessionLocal() as db:
        imported_count = 0

        if payer_key == "MEDICARE_MPFS":
            for row in rows:
                db.add(
                    MedicareRvuRate(
                        year=_parse_int(row.get("year")),
                        cpt_hcpcs=(row.get("cpt_hcpcs") or row.get("cpt") or "").strip(),
                        work_rvu=_parse_float(row.get("work_rvu")),
                        pe_rvu_facility=_parse_float(row.get("pe_rvu_facility")),
                        pe_rvu_nonfacility=_parse_float(row.get("pe_rvu_nonfacility")),
                        mp_rvu=_parse_float(row.get("mp_rvu")),
                        status_indicator=(row.get("status_indicator") or None),
                        global_days=(row.get("global_days") or None),
                    )
                )
                imported_count += 1
            count_query = select(func.count(MedicareRvuRate.id))
        elif payer_key == "MEDICARE_GPCI":
            for row in rows:
                db.add(
                    MedicareGpci(
                        year=_parse_int(row.get("year")),
                        locality_code=(row.get("locality_code") or "").strip(),
                        locality_name=(row.get("locality_name") or "").strip(),
                        work_gpci=_parse_float(row.get("work_gpci")),
                        pe_gpci=_parse_float(row.get("pe_gpci")),
                        mp_gpci=_parse_float(row.get("mp_gpci")),
                    )
                )
                imported_count += 1
            count_query = select(func.count(MedicareGpci.id))
        elif payer_key == "MEDICARE_ZIP_LOCALITY":
            for row in rows:
                db.add(
                    MedicareZipLocality(
                        zip_code=(row.get("zip_code") or "").strip()[:5],
                        locality_code=(row.get("locality_code") or "").strip(),
                    )
                )
                imported_count += 1
            count_query = select(func.count(MedicareZipLocality.id))
        elif payer_key == "MEDICARE_CONVERSION_FACTOR":
            for row in rows:
                db.add(
                    MedicareConversionFactor(
                        year=_parse_int(row.get("year")),
                        conversion_factor=_parse_float(row.get("conversion_factor")),
                    )
                )
                imported_count += 1
            count_query = select(func.count(MedicareConversionFactor.id))
        elif payer_key == "TX_MEDICAID_FFS":
            for row in rows:
                db.add(
                    TxMedicaidFfsFeeSchedule(
                        effective_start=_parse_date(row.get("effective_start")) or date.today(),
                        effective_end=_parse_date(row.get("effective_end")),
                        cpt_hcpcs=(row.get("cpt_hcpcs") or row.get("cpt") or "").strip(),
                        modifier=(row.get("modifier") or None),
                        allowed_amount=_parse_float(row.get("allowed_amount")),
                    )
                )
                imported_count += 1
            count_query = select(func.count(TxMedicaidFfsFeeSchedule.id))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported payerKey: {payer_key}")

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

        count_result = await db.execute(count_query)
        row_count_total = int(count_result.scalar() or 0)

    return RateImportResponse(
        payerKey=payer_key,
        versionLabel=version_label,
        rowsImported=imported_count,
        rowCountTotal=row_count_total,
        sha256=sha256,
        message=f"Imported {imported_count} rows for {payer_key}.",
    )


@router.get("/status", response_model=RateStatusResponse)
async def get_rates_status(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    async with AsyncSessionLocal() as db:
        versions_result = await db.execute(
            select(RateVersion).order_by(RateVersion.imported_at.desc())
        )
        versions = versions_result.scalars().all()

        medicare_rvu_count = int((await db.execute(select(func.count(MedicareRvuRate.id)))).scalar() or 0)
        gpci_count = int((await db.execute(select(func.count(MedicareGpci.id)))).scalar() or 0)
        cf_count = int((await db.execute(select(func.count(MedicareConversionFactor.id)))).scalar() or 0)
        zip_count = int((await db.execute(select(func.count(MedicareZipLocality.id)))).scalar() or 0)
        tx_count = int((await db.execute(select(func.count(TxMedicaidFfsFeeSchedule.id)))).scalar() or 0)

    serialized_versions = [
        {
            "id": version.id,
            "payerKey": version.payer_key,
            "versionLabel": version.version_label,
            "effectiveStart": version.effective_start.isoformat() if version.effective_start else None,
            "effectiveEnd": version.effective_end.isoformat() if version.effective_end else None,
            "sourceUrl": version.source_url,
            "importedAt": version.imported_at.isoformat(),
            "rowCount": version.row_count,
            "sha256": version.sha256,
        }
        for version in versions
    ]

    coverage = {
        "medicare_rvu_rows": medicare_rvu_count,
        "medicare_gpci_rows": gpci_count,
        "medicare_conversion_factor_rows": cf_count,
        "medicare_zip_locality_rows": zip_count,
        "tx_medicaid_ffs_rows": tx_count,
    }
    return RateStatusResponse(versions=serialized_versions, coverage=coverage)
