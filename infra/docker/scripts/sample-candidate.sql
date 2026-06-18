SELECT action_type, action_payload_json, evidence_json, rank_score, risk_level
FROM action_candidates
WHERE site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
LIMIT 1;
