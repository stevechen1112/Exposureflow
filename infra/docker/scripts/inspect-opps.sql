-- Sample existing opportunity + candidate structure
SELECT eo.id, eo.opportunity_type, eo.keyword, eo.priority, eo.status,
       ac.id AS candidate_id, ac.action_type, ac.decision_status, ac.rank_score
FROM exposure_opportunities eo
LEFT JOIN action_candidates ac ON ac.opportunity_id = eo.id
WHERE eo.site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
ORDER BY eo.created_at DESC
LIMIT 5;
