#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/infra/docker"

docker compose up -d
echo "PostgreSQL: localhost:5432 | Redis: localhost:6379"
