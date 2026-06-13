from exposureflow_api.jobs.celery_app import celery_app
from exposureflow_api.jobs.service import execute_job_run_sync


@celery_app.task(name="exposureflow_api.jobs.tasks.execute_job_run", bind=True, max_retries=3)
def execute_job_run(self, job_run_id: str) -> None:
    try:
        execute_job_run_sync(job_run_id)
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc, countdown=60) from exc
