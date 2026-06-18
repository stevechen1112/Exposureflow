SELECT id, status, generation_mode, updated_at
FROM content_generation_runs
WHERE site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
ORDER BY updated_at DESC
LIMIT 5;

SELECT ej.output_json
FROM execution_jobs ej
JOIN content_generation_runs cgr ON cgr.execution_job_id = ej.id
WHERE cgr.site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
  AND cgr.status = 'published';
