from celery import Celery
from kombu import Queue

from config import settings

celery_app = Celery(
    "servantx_audit_engine",
    broker=settings.resolved_celery_broker_url,
    backend=settings.resolved_celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_publish_retry=False,
    broker_connection_retry=False,
    broker_connection_retry_on_startup=False,
    broker_connection_max_retries=0,
    task_queues=(
        Queue("ingest"),
        Queue("parse"),
        Queue("review"),
        Queue("synthesize"),
        Queue("reconcile"),
    ),
    task_routes={
        "tasks.ingest.*": {"queue": "ingest"},
        "tasks.parse.*": {"queue": "parse"},
        "tasks.reprice.*": {"queue": "review"},
        "tasks.summarize.*": {"queue": "synthesize"},
        "tasks.appeals.*": {"queue": "reconcile"},
    },
    task_default_queue="ingest",
)

celery_app.autodiscover_tasks(["tasks"])
