SELECT issue_type, severity, status, url, description, source, last_seen_at
FROM technical_issues
WHERE site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
  AND status = 'open'
ORDER BY last_seen_at DESC
LIMIT 10;
