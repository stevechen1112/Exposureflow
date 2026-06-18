from celery import Celery
from celery.schedules import crontab

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
    beat_schedule={
        "content-scheduled-batch": {
            "task": "exposureflow_api.jobs.tasks.execute_scheduled_batch",
            "schedule": 43200.0,  # every 12 hours
        },
        "indexability-sitemap-health": {
            "task": "exposureflow_api.jobs.tasks.enqueue_sitemap_health_checks",
            "schedule": crontab(minute=45, hour=4, day_of_week=1),
        },
        "indexability-published-noindex": {
            "task": "exposureflow_api.jobs.tasks.enqueue_published_noindex_checks",
            "schedule": crontab(minute=10, hour=4),
        },
        "indexability-coverage-check": {
            "task": "exposureflow_api.jobs.tasks.enqueue_indexability_coverage_checks",
            "schedule": crontab(minute=0, hour=5, day_of_week=5),
        },
        "ops-daily-health": {
            "task": "exposureflow_api.jobs.tasks.run_ops_daily_health",
            "schedule": crontab(minute=0, hour=0),
        },
    },
)

celery_app.autodiscover_tasks(["exposureflow_api.jobs"])
