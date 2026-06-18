SELECT id, generation_mode, status, length(output_markdown) AS chars,
       substring(output_markdown, 1, 120) AS head
FROM content_generation_runs
WHERE site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
ORDER BY updated_at DESC;
