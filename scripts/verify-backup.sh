#!/usr/bin/env bash
# Verify latest backup artifact exists and is non-empty.
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
LATEST="$(ls -t "$BACKUP_DIR"/exposureflow_*.dump 2>/dev/null | head -1 || true)"

if [[ -z "$LATEST" ]]; then
  echo "FAIL: No backup files in $BACKUP_DIR"
  exit 1
fi

SIZE="$(stat -f%z "$LATEST" 2>/dev/null || stat -c%s "$LATEST")"
if [[ "$SIZE" -lt 1024 ]]; then
  echo "FAIL: Backup too small ($SIZE bytes): $LATEST"
  exit 1
fi

echo "PASS: Latest backup $LATEST ($SIZE bytes)"
