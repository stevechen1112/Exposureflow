SELECT provider, site_id, status, credential_name
FROM integration_credentials
WHERE site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
ORDER BY provider;

SELECT id, status, generation_mode,
       (output_json::text IS NOT NULL) AS has_job_output
FROM content_generation_runs
WHERE site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
ORDER BY updated_at DESC
LIMIT 5;
