SELECT cgr.id, cgr.status, cgr.generation_mode,
       cgr2.gate_type, cgr2.status AS gate_status
FROM content_generation_runs cgr
LEFT JOIN content_gate_results cgr2 ON cgr2.content_generation_run_id = cgr.id
WHERE cgr.site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
  AND cgr.status = 'approved'
ORDER BY cgr.updated_at DESC;
