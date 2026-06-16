FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY packages/connectors packages/connectors
COPY packages/execution-adapters packages/execution-adapters
COPY apps/api apps/api
COPY docs docs
COPY scripts scripts
COPY apps/web apps/web

WORKDIR /app/apps/api

RUN pip install --no-cache-dir /app/packages/connectors /app/packages/execution-adapters \
    && sed -i \
      -e 's|exposureflow-connectors @ file:../../packages/connectors|exposureflow-connectors|' \
      -e 's|exposureflow-execution-adapters @ file:../../packages/execution-adapters|exposureflow-execution-adapters|' \
      pyproject.toml \
    && pip install --no-cache-dir .

COPY infra/docker/scripts/api-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
