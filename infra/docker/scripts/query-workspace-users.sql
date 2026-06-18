SELECT u.email, wm.role, w.id AS workspace_id
FROM workspace_memberships wm
JOIN users u ON u.id = wm.user_id
JOIN workspaces w ON w.id = wm.workspace_id
WHERE w.id = '67a1694d-fab1-4694-b05c-37790ef8ef87';
