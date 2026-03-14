import asyncio
from typing import Optional
from celery_app import celery_app


@celery_app.task(name="tasks.appeals.task_build_appeals")
def task_build_appeals(batch_id: str, payer_key: Optional[str] = None, minimum_variance: Optional[float] = None):
    from services.audit_pipeline_service import run_stage5_build_appeals

    return asyncio.run(
        run_stage5_build_appeals(
            batch_id=batch_id,
            payer_key=payer_key,
            minimum_variance=minimum_variance,
        )
    )
