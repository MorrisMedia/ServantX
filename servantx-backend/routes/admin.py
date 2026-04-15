# servantx-backend/routes/admin.py
"""
Admin-only endpoints. Requires is_admin=True on the User record.
Routes:
  GET  /admin/stats          — system-wide counts, spend totals
  GET  /admin/costs          — paginated cost log with filters
  GET  /admin/costs/summary  — grouped spend by model/service/day
  GET  /admin/users          — all users with hospital info
  POST /admin/users/{id}/promote  — set is_admin=True (requires ADMIN_SECRET_KEY header)
  GET  /admin/api-keys       — which keys are configured (masked)
  POST /admin/benchmark      — run GPT-4.1 vs Claude on a document
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query
from sqlalchemy import func, select, desc

from config import settings
from core_services.db_service import AsyncSessionLocal
from models import AiCostLog, AppAuditLog, BatchRun, Document, Hospital, Receipt, User
from routes.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/stats")
async def get_admin_stats(admin: dict = Depends(require_admin)):
    """System-wide totals."""
    async with AsyncSessionLocal() as db:
        hospitals   = await db.scalar(select(func.count(Hospital.id)))
        users       = await db.scalar(select(func.count(User.id)))
        documents   = await db.scalar(select(func.count(Document.id)))
        receipts    = await db.scalar(select(func.count(Receipt.id)))
        batches     = await db.scalar(select(func.count(BatchRun.id)))
        total_cost  = await db.scalar(select(func.coalesce(func.sum(AiCostLog.cost_usd), 0)))
        total_calls = await db.scalar(select(func.count(AiCostLog.id)))
        cost_today  = await db.scalar(
            select(func.coalesce(func.sum(AiCostLog.cost_usd), 0))
            .where(AiCostLog.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0))
        )
        cost_7d = await db.scalar(
            select(func.coalesce(func.sum(AiCostLog.cost_usd), 0))
            .where(AiCostLog.created_at >= datetime.utcnow() - timedelta(days=7))
        )

    return {
        "hospitals": hospitals,
        "users": users,
        "documents": documents,
        "receipts": receipts,
        "batch_runs": batches,
        "ai_cost_total_usd": float(total_cost or 0),
        "ai_cost_today_usd": float(cost_today or 0),
        "ai_cost_7d_usd": float(cost_7d or 0),
        "ai_total_calls": total_calls,
    }


@router.get("/costs")
async def get_cost_log(
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    service: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    admin: dict = Depends(require_admin),
):
    async with AsyncSessionLocal() as db:
        q = select(AiCostLog).order_by(desc(AiCostLog.created_at))
        if service:
            q = q.where(AiCostLog.service == service)
        if model:
            q = q.where(AiCostLog.model == model)
        rows = (await db.execute(q.offset(offset).limit(limit))).scalars().all()
        total = await db.scalar(select(func.count(AiCostLog.id)))

    return {
        "total": total,
        "items": [
            {
                "id": r.id,
                "service": r.service,
                "provider": r.provider,
                "model": r.model,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "cache_read_tokens": r.cache_read_tokens,
                "cache_write_tokens": r.cache_write_tokens,
                "cost_usd": float(r.cost_usd),
                "latency_ms": r.latency_ms,
                "success": r.success,
                "hospital_id": r.hospital_id,
                "document_id": r.document_id,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
    }


@router.get("/costs/summary")
async def get_cost_summary(admin: dict = Depends(require_admin)):
    """Spend grouped by model and service."""
    async with AsyncSessionLocal() as db:
        by_model = (await db.execute(
            select(AiCostLog.model, AiCostLog.provider,
                   func.count(AiCostLog.id),
                   func.sum(AiCostLog.cost_usd),
                   func.sum(AiCostLog.input_tokens),
                   func.sum(AiCostLog.output_tokens),
                   func.sum(AiCostLog.cache_read_tokens))
            .group_by(AiCostLog.model, AiCostLog.provider)
            .order_by(func.sum(AiCostLog.cost_usd).desc())
        )).all()

        by_service = (await db.execute(
            select(AiCostLog.service,
                   func.count(AiCostLog.id),
                   func.sum(AiCostLog.cost_usd))
            .group_by(AiCostLog.service)
            .order_by(func.sum(AiCostLog.cost_usd).desc())
        )).all()

    return {
        "by_model": [
            {"model": r[0], "provider": r[1], "calls": r[2],
             "cost_usd": float(r[3] or 0), "input_tokens": r[4],
             "output_tokens": r[5], "cache_read_tokens": r[6]}
            for r in by_model
        ],
        "by_service": [
            {"service": r[0], "calls": r[1], "cost_usd": float(r[2] or 0)}
            for r in by_service
        ],
    }


@router.get("/users")
async def list_users(admin: dict = Depends(require_admin)):
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(User, Hospital.name)
            .join(Hospital, User.hospital_id == Hospital.id)
            .order_by(User.created_at.desc())
        )).all()
    return [
        {
            "id": u.id, "email": u.email, "name": u.name,
            "hospital_name": h_name, "hospital_id": u.hospital_id,
            "role": u.role, "is_admin": u.is_admin, "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
        }
        for u, h_name in rows
    ]


@router.post("/users/{user_id}/promote")
async def promote_to_admin(
    user_id: str,
    x_admin_secret: str = Header(..., alias="X-Admin-Secret"),
    admin: dict = Depends(require_admin),
):
    """Promote a user to admin. Requires X-Admin-Secret header matching ADMIN_SECRET_KEY env var."""
    if x_admin_secret != settings.ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_admin = True
        await db.commit()
    return {"success": True, "user_id": user_id, "is_admin": True}


@router.get("/api-keys")
async def get_api_key_status(admin: dict = Depends(require_admin)):
    """Returns which API keys are configured (masked — never returns actual values)."""
    def mask(val: str) -> str:
        if not val:
            return "NOT SET"
        return val[:8] + "..." + val[-4:] if len(val) > 12 else "SET"

    return {
        "openai": {
            "configured": bool(settings.OPENAI_API_KEY),
            "masked": mask(settings.OPENAI_API_KEY),
        },
        "anthropic": {
            "configured": bool(settings.ANTHROPIC_API_KEY),
            "masked": mask(settings.ANTHROPIC_API_KEY),
        },
        "sendgrid": {
            "configured": bool(settings.SENDGRID_API_KEY),
            "masked": mask(settings.SENDGRID_API_KEY),
        },
        "phi_encryption": {
            "configured": bool(settings.PHI_ENCRYPTION_KEY),
            "masked": mask(settings.PHI_ENCRYPTION_KEY),
        },
        "jwt_secret": {
            "configured": bool(settings.JWT_SECRET_KEY),
            "masked": mask(settings.JWT_SECRET_KEY),
        },
    }


@router.post("/benchmark")
async def run_benchmark(
    document_id: str = Body(..., embed=True),
    current_user: dict = Depends(require_admin),
):
    """Run underpayment analysis on the same claim with GPT-4.1 AND Claude Sonnet 4.6.
    Returns side-by-side cost, latency, confidence, and reasoning."""
    import asyncio, time
    from core_services.openai_service import chat_with_openai_async_tracked
    from core_services.anthropic_service import chat_with_claude_async
    from services.cost_service import compute_cost
    from services.ai_analysis_service import _build_analysis_prompt

    result = await _build_analysis_prompt(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Document not found or prompt build failed")
    system_prompt, user_prompt = result

    async def run_gpt():
        from schemas import UnderpaymentAnalysis
        t0 = time.monotonic()
        result, usage = await chat_with_openai_async_tracked(
            text=user_prompt, prompt=system_prompt, model="gpt-4.1", schema=UnderpaymentAnalysis
        )
        return result, usage, int((time.monotonic() - t0) * 1000)

    async def run_claude():
        from schemas import UnderpaymentAnalysis
        t0 = time.monotonic()
        result, usage = await chat_with_claude_async(
            text=user_prompt, prompt=system_prompt, model="claude-sonnet-4-6",
            cache_system=False, schema=UnderpaymentAnalysis
        )
        return result, usage, int((time.monotonic() - t0) * 1000)

    (gpt_result, gpt_usage, gpt_ms), (claude_result, claude_usage, claude_ms) = await asyncio.gather(
        run_gpt(), run_claude()
    )

    return {
        "document_id": document_id,
        "gpt_4_1": {
            "result": gpt_result,
            "latency_ms": gpt_ms,
            "input_tokens": gpt_usage.get("input_tokens", 0),
            "output_tokens": gpt_usage.get("output_tokens", 0),
            "cost_usd": compute_cost("gpt-4.1", gpt_usage.get("input_tokens", 0), gpt_usage.get("output_tokens", 0)),
        },
        "claude_sonnet_4_6": {
            "result": claude_result,
            "latency_ms": claude_ms,
            "input_tokens": claude_usage.get("input_tokens", 0),
            "output_tokens": claude_usage.get("output_tokens", 0),
            "cache_read_tokens": claude_usage.get("cache_read_tokens", 0),
            "cache_write_tokens": claude_usage.get("cache_write_tokens", 0),
            "cost_usd": compute_cost("claude-sonnet-4-6", claude_usage.get("input_tokens", 0), claude_usage.get("output_tokens", 0), claude_usage.get("cache_read_tokens", 0), claude_usage.get("cache_write_tokens", 0)),
        },
    }
