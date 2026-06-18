#!/bin/bash
set -e
OUT=/tmp/ezfix-handoff
mkdir -p "$OUT"
COMPOSE="docker compose -f /opt/exposureflow/infra/docker/docker-compose.prod.yml"

export_one() {
  local id="$1"
  local name="$2"
  $COMPOSE exec -T postgres psql -U exposureflow -d exposureflow -t -A -c \
    "SELECT output_markdown FROM content_generation_runs WHERE id = '$id';" > "$OUT/${name}.md"
  echo "exported $name.md"
}

export_one "2355e8ef-82b1-4bc5-aea7-59b4efcc7268" "換紗窗價格"
export_one "570c3fbd-b32c-4f2f-9f1a-228bde4e199a" "紗窗破了怎麼辦"
ls -la "$OUT"
