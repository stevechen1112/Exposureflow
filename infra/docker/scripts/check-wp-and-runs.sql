SELECT provider, status, site_id FROM integration_credentials
WHERE workspace_id = '67a1694d-fab1-4694-b05c-37790ef8ef87'
  AND site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e';

SELECT id, generation_mode, status FROM content_generation_runs
WHERE site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
ORDER BY updated_at DESC;
