SELECT cgr.id,
       cgr.status,
       cb.brief_json->>'title_hint' AS title_hint,
       cb.brief_json->>'target_url' AS target_url,
       cb.brief_json->>'keyword' AS keyword,
       length(cgr.output_markdown) AS chars,
       cgr.output_markdown
FROM content_generation_runs cgr
JOIN content_briefs cb ON cb.id = cgr.content_brief_id
WHERE cgr.site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
  AND cgr.status = 'publish_ready'
ORDER BY cgr.updated_at DESC;
