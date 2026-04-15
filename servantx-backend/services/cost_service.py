# servantx-backend/services/cost_service.py
"""
Records AI API call costs to ai_cost_log.
Call log_ai_cost() after every AI call — fire-and-forget (never raises).
"""
import time
from datetime import datetime
from typing import Optional

from core_services.db_service import AsyncSessionLocal
from models import AiCostLog
from core_services.logger_service import error_log

# ── Pricing table (per 1M tokens, USD) ───────────────────────────────────────
_PRICING = {
    "gpt-4.1":            {"input": 2.00,  "output": 8.00,  "cache_read": 0.0, "cache_write": 0.0},
    "gpt-4o-mini":        {"input": 0.15,  "output": 0.60,  "cache_read": 0.0, "cache_write": 0.0},
    "claude-sonnet-4-6":  {"input": 3.00,  "output": 15.00, "cache_read": 0.30, "cache_write": 3.75},
    "claude-opus-4-6":    {"input": 15.00, "output": 75.00, "cache_read": 1.50, "cache_write": 18.75},
    "claude-haiku-4-5":   {"input": 0.80,  "output": 4.00,  "cache_read": 0.08, "cache_write": 1.00},
}

def compute_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    """Return cost in USD for a single API call."""
    p = _PRICING.get(model, {"input": 0.0, "output": 0.0, "cache_read": 0.0, "cache_write": 0.0})
    return (
        input_tokens      * p["input"]       / 1_000_000 +
        output_tokens     * p["output"]      / 1_000_000 +
        cache_read_tokens * p["cache_read"]  / 1_000_000 +
        cache_write_tokens* p["cache_write"] / 1_000_000
    )


async def log_ai_cost(
    service: str,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    hospital_id: Optional[str] = None,
    document_id: Optional[str] = None,
    batch_run_id: Optional[str] = None,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
    latency_ms: Optional[int] = None,
    success: bool = True,
    error_message: Optional[str] = None,
) -> None:
    """
    Fire-and-forget: write one row to ai_cost_log.
    Never raises — cost logging must never break the main pipeline.
    """
    try:
        cost = compute_cost(model, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens)
        async with AsyncSessionLocal() as db:
            row = AiCostLog(
                hospital_id=hospital_id,
                document_id=document_id,
                batch_run_id=batch_run_id,
                service=service,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cache_read_tokens,
                cache_write_tokens=cache_write_tokens,
                cost_usd=cost,
                latency_ms=latency_ms,
                success=success,
                error_message=error_message,
                created_at=datetime.utcnow(),
            )
            db.add(row)
            await db.commit()
    except Exception as e:
        error_log(action="log_ai_cost", error=str(e))
