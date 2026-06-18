#!/usr/bin/env python3
"""Export publish_ready markdown for custom-site manual handoff."""
import asyncio
import re
import asyncpg

SITE = "02cb80a6-75ef-4a0a-b2b3-8911d650579e"
OUT_DIR = "/tmp/ezfix-handoff"

async def main():
    conn = await asyncpg.connect(
        host="postgres",
        port=5432,
        user="exposureflow",
        password="exposureflow",
        database="exposureflow",
    )
    rows = await conn.fetch(
        """
        SELECT cgr.id::text, cgr.status,
               cb.brief_json->>'title_hint' AS title_hint,
               cb.brief_json->>'keyword' AS keyword,
               cgr.output_markdown
        FROM content_generation_runs cgr
        JOIN content_briefs cb ON cb.id = cgr.content_brief_id
        WHERE cgr.site_id = $1::uuid AND cgr.status = 'publish_ready'
        ORDER BY cgr.updated_at DESC
        """,
        SITE,
    )
    await conn.close()
    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    manifest = []
    for r in rows:
        kw = r["keyword"] or r["title_hint"] or r["id"][:8]
        slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", kw).strip("-") or r["id"][:8]
        path = f"{OUT_DIR}/{slug}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(r["output_markdown"] or "")
        manifest.append({
            "run_id": r["id"],
            "keyword": kw,
            "file": path,
            "chars": len(r["output_markdown"] or ""),
        })
    import json
    with open(f"{OUT_DIR}/manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

asyncio.run(main())
