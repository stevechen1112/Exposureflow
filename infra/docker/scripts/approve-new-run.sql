UPDATE content_generation_runs SET status = 'approved', updated_at = NOW()
WHERE id = '570c3fbd-b32c-4f2f-9f1a-228bde4e199a';

SELECT id, status, generation_mode FROM content_generation_runs
WHERE site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e' AND status IN ('approved','claim_verified')
ORDER BY updated_at DESC;
