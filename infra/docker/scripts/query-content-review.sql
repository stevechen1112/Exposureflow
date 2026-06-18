SELECT id, generation_mode, status, substring(output_markdown, 1, 120) AS preview, created_at
FROM content_generation_runs
WHERE site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
ORDER BY created_at DESC
LIMIT 5;

SELECT ac.action_type, eo.keyword, ac.decision_status, eo.priority
FROM action_candidates ac
JOIN exposure_opportunities eo ON ac.opportunity_id = eo.id
WHERE ac.site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
  AND ac.decision_status = 'approved'
ORDER BY ac.rank_score DESC
LIMIT 20;

SELECT ac.action_type, eo.keyword, ac.decision_status
FROM action_candidates ac
JOIN exposure_opportunities eo ON ac.opportunity_id = eo.id
WHERE ac.site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
  AND ac.decision_status = 'approved'
  AND ac.action_type IN ('create_page', 'enrich', 'add_faq', 'solution_page', 'schema_enhancement', 'comparison', 'case_study')
LIMIT 10;
