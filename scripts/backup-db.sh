#!/usr/bin/env bash
# EF-H004: Daily PostgreSQL logical backup for ExposureFlow.
set -euo pipefail

PGHOST="${PGHOST:-localhost}"
PGUSER="${PGUSER:-exposureflow}"
PGDATABASE="${PGDATABASE:-exposureflow}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/exposureflow_${STAMP}.dump"

echo "Backing up $PGDATABASE on $PGHOST -> $OUT"
pg_dump -Fc -h "$PGHOST" -U "$PGUSER" "$PGDATABASE" > "$OUT"
echo "Backup complete: $OUT ($(du -h "$OUT" | cut -f1))"

find "$BACKUP_DIR" -name 'exposureflow_*.dump' -mtime +"$RETENTION_DAYS" -delete
echo "Pruned backups older than ${RETENTION_DAYS} days"
