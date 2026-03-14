import asyncio
from celery_app import celery_app


@celery_app.task(name="tasks.ingest.task_ingest_835_file")
def task_ingest_835_file(file_document_id: str, batch_id: str):
    from services.audit_pipeline_service import run_stage1_ingest_835_file

    return asyncio.run(run_stage1_ingest_835_file(file_document_id=file_document_id, batch_id=batch_id))
