from fastapi import APIRouter, Depends, HTTPException, status
import os
from sqlalchemy import select

from core_services.db_service import AsyncSessionLocal
from models import BatchRun
from routes.auth import get_current_user
from schemas import AppealBuildRequest, AppealBuildResponse
from services.audit_pipeline_service import run_stage5_build_appeals
from tasks.appeals import task_build_appeals


router = APIRouter(prefix="/appeals", tags=["appeals"])


@router.post("/build", response_model=AppealBuildResponse)
async def build_appeal_packet(
    request: AppealBuildRequest,
    current_user: dict = Depends(get_current_user),
):
    async with AsyncSessionLocal() as db:
        batch_result = await db.execute(
            select(BatchRun).where(
                BatchRun.id == request.batchId,
                BatchRun.hospital_id == current_user["hospital_id"],
            )
        )
        batch = batch_result.scalar_one_or_none()
        if not batch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    if os.getenv("ENABLE_CELERY_ASYNC", "false").lower() == "true":
        try:
            task_result = task_build_appeals.delay(
                request.batchId,
                request.payerKey,
                request.minimumVariance,
            )
            return AppealBuildResponse(
                batchId=request.batchId,
                packet={
                    "queued": True,
                    "task_id": task_result.id,
                    "message": "Appeal packet build queued.",
                },
                message="Appeal packet build queued.",
            )
        except Exception:
            pass

    result = await run_stage5_build_appeals(
        batch_id=request.batchId,
        payer_key=request.payerKey,
        minimum_variance=request.minimumVariance,
    )
    if result.get("status") != "ok":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Failed to build appeal packet"),
        )
    return AppealBuildResponse(
        batchId=request.batchId,
        packet=result.get("packet", {}),
        message="Appeal packet built successfully.",
    )
