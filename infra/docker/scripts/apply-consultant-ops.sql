-- Step 1: Void old grounded_template approved article
UPDATE content_generation_runs
SET status = 'needs_changes',
    updated_at = NOW(),
    evidence_map_json = COALESCE(evidence_map_json, '{}'::jsonb) ||
      jsonb_build_object(
        'qa_report',
        COALESCE(evidence_map_json->'qa_report', '{}'::jsonb) ||
          jsonb_build_object(
            'human_review_notes',
            COALESCE(evidence_map_json->'qa_report'->'human_review_notes', '[]'::jsonb) ||
              '["作廢：grounded_template 低品質（英文模板、OG-004 外洩），由 grounded_llm 新版取代"]'::jsonb
          )
      )
WHERE id = 'b9b86ddf-bba4-45ea-95ac-9d49df58cc84'
  AND site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e';

-- Step 2: Insert create_page opportunity (OG-016 manual consultant seed)
WITH new_opp AS (
  INSERT INTO exposure_opportunities (
    id, workspace_id, site_id, opportunity_type, keyword,
    current_impressions, ranking_feasibility_score, serp_slot_score,
    ai_citation_score, topic_contribution_score, zero_click_value_score,
    total_opportunity_score, priority, status, reason, evidence_json,
    created_at, updated_at
  ) VALUES (
    gen_random_uuid(),
    '67a1694d-fab1-4694-b05c-37790ef8ef87',
    '02cb80a6-75ef-4a0a-b2b3-8911d650579e',
    'create_page',
    '紗窗破了怎麼辦',
    0,
    3.5, 2.5, 2.0, 3.0, 1.5,
    4.8,
    'high',
    'open',
    'OG-016: Approved pyramid topic without GSC coverage (consultant manual seed)',
    jsonb_build_object(
      'rule_id', 'OG-016',
      'pyramid_node_id', '3623c184-0c1c-4dd3-926b-2b5c4e71405e',
      'node_type', 'long_tail',
      'keyword', '紗窗破了怎麼辦',
      'seeded_by', 'consultant_ops'
    ),
    NOW(), NOW()
  )
  RETURNING id
),
new_candidate AS (
  INSERT INTO action_candidates (
    id, workspace_id, site_id, opportunity_id, action_type,
    action_payload_json, expected_exposure_impact, risk_level,
    required_inputs_json, evidence_json, created_by, decision_status,
    rank_score, created_at
  )
  SELECT
    gen_random_uuid(),
    '67a1694d-fab1-4694-b05c-37790ef8ef87',
    '02cb80a6-75ef-4a0a-b2b3-8911d650579e',
    new_opp.id,
    'create_page',
    jsonb_build_object(
      'opportunity_type', 'create_page',
      'keyword', '紗窗破了怎麼辦',
      'priority', 'high'
    ),
    4.8,
    'high',
    jsonb_build_array(jsonb_build_object('field', 'keyword', 'value', '紗窗破了怎麼辦')),
    jsonb_build_object(
      'opportunity_id', new_opp.id::text,
      'opportunity_type', 'create_page',
      'total_opportunity_score', 4.8,
      'reason', 'OG-016: Approved pyramid topic without GSC coverage (consultant manual seed)',
      'keyword', '紗窗破了怎麼辦',
      'rule_id', 'OG-016'
    ),
    'manual',
    'approved',
    4.8,
    NOW()
  FROM new_opp
  RETURNING id, opportunity_id
)
INSERT INTO action_decisions (
  id, workspace_id, candidate_id, decision, rationale, confidence, created_at
)
SELECT
  gen_random_uuid(),
  '67a1694d-fab1-4694-b05c-37790ef8ef87',
  new_candidate.id,
  'approve',
  'Consultant ops: seed create_page for content generation pipeline',
  0.95,
  NOW()
FROM new_candidate;

-- Verify
SELECT 'voided_run' AS step, id, status, generation_mode FROM content_generation_runs WHERE id = 'b9b86ddf-bba4-45ea-95ac-9d49df58cc84';
SELECT 'new_candidate' AS step, ac.id, ac.action_type, ac.decision_status, ac.rank_score, eo.keyword, eo.priority
FROM action_candidates ac
JOIN exposure_opportunities eo ON eo.id = ac.opportunity_id
WHERE ac.site_id = '02cb80a6-75ef-4a0a-b2b3-8911d650579e'
  AND ac.action_type = 'create_page'
ORDER BY ac.created_at DESC
LIMIT 1;
