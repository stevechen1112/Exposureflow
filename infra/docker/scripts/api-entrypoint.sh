#!/bin/sh
set -e

cd /app/apps/api
alembic upgrade head

# docker-compose passes `celery ...` as CMD; default is API server.
if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec uvicorn exposureflow_api.main:app --host 0.0.0.0 --port 8000
