SELECT action_type, priority, status, count(*) 
FROM opportunity_candidates 
WHERE site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
GROUP BY action_type, priority, status
ORDER BY status, action_type;
