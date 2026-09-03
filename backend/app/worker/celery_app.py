from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "agent_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60,       # hard timeout 60s
    task_soft_time_limit=45,  # soft timeout 45s
    broker_connection_retry_on_startup=True,
)
