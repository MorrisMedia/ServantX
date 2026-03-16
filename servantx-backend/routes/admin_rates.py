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
from services.rate_import_service import import_rate_rows, load_csv_rows
from routes.auth import get_current_user
from schemas import RateImportResponse, RateStatusResponse


router = APIRouter(prefix="/admin/rates", tags=["admin-rates"])





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
    try:
        rows, sha256 = load_csv_rows(file_content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    async with AsyncSessionLocal() as db:
        try:
            result = await import_rate_rows(
                db,
                payer_key=payer_key,
                version_label=version_label,
                source_url=source_url,
                rows=rows,
                sha256=sha256,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return RateImportResponse(
        payerKey=result.payer_key,
        versionLabel=result.version_label,
        rowsImported=result.rows_imported,
        rowCountTotal=result.row_count_total,
        sha256=result.sha256,
        message=(
            f"Skipped import for {result.payer_key}; identical file already loaded."
            if result.skipped
            else f"Imported {result.rows_imported} rows for {result.payer_key}."
        ),
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
