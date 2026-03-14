import asyncio
from celery_app import celery_app


@celery_app.task(name="tasks.reprice.task_reprice_claim")
def task_reprice_claim(document_id: str):
    from services.audit_pipeline_service import run_stage3_reprice_claim

    return asyncio.run(run_stage3_reprice_claim(document_id=document_id))
