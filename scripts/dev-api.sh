#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/apps/api"

exec uvicorn exposureflow_api.main:app --reload --host 0.0.0.0 --port 8000
