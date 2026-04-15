from fastapi import APIRouter, Depends
from routes.auth import get_current_user
from core_services.db_service import AsyncSessionLocal
from models import Document, DocumentRole
from sqlalchemy import select, func, and_

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/roi")
async def get_roi_summary(current_user: dict = Depends(get_current_user)):
    """
    Returns revenue recovery ROI metrics for the hospital's dashboard.
    """
    hospital_id = current_user["hospital_id"]

    async with AsyncSessionLocal() as db:
        # Base filter: claim-level documents (CLAIM from batch pipeline, LEGACY from receipt scan)
        base = and_(
            Document.hospital_id == hospital_id,
            Document.document_role.in_([DocumentRole.CLAIM, DocumentRole.LEGACY]),
        )

        # Total underpayment identified
        total_identified = await db.scalar(
            select(func.coalesce(func.sum(Document.underpayment_amount), 0)).where(
                base, Document.underpayment_amount > 0
            )
        )

        # Total recovered
        total_recovered = await db.scalar(
            select(func.coalesce(func.sum(Document.recovered_amount), 0)).where(
                base, Document.recovered_amount.isnot(None)
            )
        )

        # Count by appeal_status
        status_rows = await db.execute(
            select(
                Document.appeal_status,
                func.count(Document.id),
                func.coalesce(func.sum(Document.underpayment_amount), 0),
            )
            .where(base)
            .group_by(Document.appeal_status)
        )
        by_status = {
            row[0]: {"count": row[1], "amount": float(row[2])}
            for row in status_rows
        }

        # By payer (top 10 by underpayment)
        payer_rows = await db.execute(
            select(
                Document.payer_key,
                func.count(Document.id),
                func.coalesce(func.sum(Document.underpayment_amount), 0),
                func.coalesce(func.sum(Document.recovered_amount), 0),
            )
            .where(base, Document.underpayment_amount > 0)
            .group_by(Document.payer_key)
            .order_by(func.sum(Document.underpayment_amount).desc())
            .limit(10)
        )
        by_payer = [
            {
                "payer": r[0] or "UNKNOWN",
                "count": r[1],
                "identified": float(r[2]),
                "recovered": float(r[3] or 0),
            }
            for r in payer_rows
        ]

        # Totals
        total_claims = await db.scalar(select(func.count(Document.id)).where(base))
        total_flagged = await db.scalar(
            select(func.count(Document.id)).where(base, Document.underpayment_amount > 0)
        )

    identified_f = float(total_identified or 0)
    recovered_f = float(total_recovered or 0)
    recovery_rate = (recovered_f / identified_f) if identified_f > 0 else 0.0
    claims_count = total_claims or 0
    flagged_count = total_flagged or 0

    return {
        "identified_total": identified_f,
        "recovered_total": recovered_f,
        "recovery_rate": round(recovery_rate, 4),
        "total_claims_processed": claims_count,
        "total_flagged": flagged_count,
        "flag_rate": round((flagged_count / claims_count) if claims_count else 0, 4),
        "by_status": by_status,
        "by_payer": by_payer,
    }
