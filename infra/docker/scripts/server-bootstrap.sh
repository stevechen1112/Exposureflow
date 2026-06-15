#!/bin/bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/exposureflow}"
COMPOSE_FILE="$APP_DIR/infra/docker/docker-compose.prod.yml"
ENV_FILE="$APP_DIR/infra/docker/.env"
PUBLIC_URL="${PUBLIC_URL:-https://app.kakusinn.com}"

if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
fi

if ! swapon --show | grep -q '/swapfile'; then
  if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
  fi
  swapon /swapfile || true
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

mkdir -p "$APP_DIR/infra/docker"

if [ ! -f "$ENV_FILE" ]; then
  POSTGRES_PASSWORD="$(openssl rand -hex 16)"
  JWT_SECRET="$(openssl rand -hex 32)"
  ENCRYPTION_KEY="$(openssl rand -hex 16)"

  cat > "$ENV_FILE" <<EOF
APP_ENV=staging
APP_BASE_URL=${PUBLIC_URL}
API_BASE_URL=${PUBLIC_URL}

POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=postgresql+asyncpg://exposureflow:${POSTGRES_PASSWORD}@postgres:5432/exposureflow
REDIS_URL=redis://redis:6379/0

JWT_SECRET=${JWT_SECRET}
ENCRYPTION_KEY=${ENCRYPTION_KEY}

NEXT_PUBLIC_API_BASE_URL=${PUBLIC_URL}
NEXT_PUBLIC_ENABLE_DEV_AUTH=true
EOF
  chmod 600 "$ENV_FILE"
  echo "Created $ENV_FILE"
fi

cd "$APP_DIR/infra/docker"
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

echo "Waiting for API health..."
for i in $(seq 1 60); do
  if curl -fsS "${PUBLIC_URL}/health" >/dev/null 2>&1; then
    echo "OK: ${PUBLIC_URL}/health"
    exit 0
  fi
  sleep 5
done

echo "Health check timed out — inspect: docker compose -f $COMPOSE_FILE logs"
exit 1
