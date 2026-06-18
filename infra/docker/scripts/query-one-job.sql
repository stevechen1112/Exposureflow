SELECT id, job_type, status, output_json, completed_at
FROM job_runs
WHERE job_type = 'indexability.sitemap_health'
ORDER BY created_at DESC
LIMIT 3;
