from celery import Celery

from exposureflow_api.config import settings

celery_app = Celery(
    "exposureflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "exposureflow_api.jobs.tasks.*": {"queue": "default"},
    },
    task_default_queue="default",
)

celery_app.autodiscover_tasks(["exposureflow_api.jobs"])
