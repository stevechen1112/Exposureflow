-- Approve grounded_llm run (consultant ops)
UPDATE content_generation_runs
SET status = 'approved', updated_at = NOW()
WHERE id = '2355e8ef-82b1-4bc5-aea7-59b4efcc7268'
  AND site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e';

SELECT id, generation_mode, status FROM content_generation_runs
WHERE site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
ORDER BY updated_at DESC;
