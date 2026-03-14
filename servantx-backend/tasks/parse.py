import asyncio
from celery_app import celery_app


@celery_app.task(name="tasks.parse.task_parse_claim_edi")
def task_parse_claim_edi(document_id: str):
    from services.audit_pipeline_service import run_stage2_parse_claim

    return asyncio.run(run_stage2_parse_claim(document_id=document_id))
