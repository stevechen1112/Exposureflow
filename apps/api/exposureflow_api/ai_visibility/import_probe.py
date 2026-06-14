"""Manual CSV / JSON import for AI probe runs."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

REQUIRED_CSV_FIELDS = frozenset(
    {"surface", "prompt", "answer_text", "cited_urls", "mentioned_brands", "sentiment", "run_at"}
)


def _parse_list_field(value: str | list | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except json.JSONDecodeError:
            pass
    return [part.strip() for part in text.split("|") if part.strip()]


def _parse_run_at(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def parse_csv_import(content: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValueError("CSV must include a header row")
    missing = REQUIRED_CSV_FIELDS - set(reader.fieldnames)
    if missing:
        raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")

    rows: list[dict] = []
    for row in reader:
        rows.append(
            {
                "surface": row["surface"].strip(),
                "prompt": row["prompt"].strip(),
                "answer_text": row["answer_text"].strip(),
                "cited_urls": _parse_list_field(row.get("cited_urls")),
                "mentioned_brands": _parse_list_field(row.get("mentioned_brands")),
                "competitor_mentions": _parse_list_field(row.get("competitor_mentions")),
                "sentiment": (row.get("sentiment") or "").strip() or None,
                "run_at": _parse_run_at(row.get("run_at")),
            }
        )
    return rows


def parse_json_import(data: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for item in data:
        for field in ("surface", "prompt", "answer_text"):
            if not item.get(field):
                raise ValueError(f"Each row must include {field}")
        rows.append(
            {
                "surface": str(item["surface"]).strip(),
                "prompt": str(item["prompt"]).strip(),
                "answer_text": str(item["answer_text"]).strip(),
                "cited_urls": _parse_list_field(item.get("cited_urls")),
                "mentioned_brands": _parse_list_field(item.get("mentioned_brands")),
                "competitor_mentions": _parse_list_field(item.get("competitor_mentions")),
                "sentiment": (item.get("sentiment") or None),
                "run_at": _parse_run_at(item.get("run_at")),
            }
        )
    return rows
