import asyncio
from celery_app import celery_app


@celery_app.task(name="tasks.summarize.task_summarize_batch")
def task_summarize_batch(batch_id: str):
    from services.audit_pipeline_service import run_stage4_summarize_batch

    return asyncio.run(run_stage4_summarize_batch(batch_id=batch_id))
