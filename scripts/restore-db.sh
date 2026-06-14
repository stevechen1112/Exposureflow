#!/usr/bin/env bash
# EF-H004: Restore PostgreSQL backup (maintenance window only).
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <backup.dump>"
  exit 1
fi

PGHOST="${PGHOST:-localhost}"
PGUSER="${PGUSER:-exposureflow}"
PGDATABASE="${PGDATABASE:-exposureflow}"
BACKUP_FILE="$1"

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

echo "WARNING: This will restore $PGDATABASE from $BACKUP_FILE"
echo "Ensure API and Celery workers are stopped."
read -r -p "Continue? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
  echo "Aborted."
  exit 0
fi

pg_restore -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" --clean --if-exists "$BACKUP_FILE"
echo "Restore complete. Run: cd apps/api && alembic upgrade head"
echo "Then verify: curl http://localhost:8000/health && pytest tests/test_tenant_isolation.py"
