SELECT id, keyword, priority, node_type, business_fit_status, approved_at IS NOT NULL AS approved
FROM keyword_pyramid_nodes
WHERE site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
  AND business_fit_status = 'in_scope'
ORDER BY priority DESC, keyword
LIMIT 15;
