SELECT id, job_type, status, error_code, output_json, error_message, completed_at
FROM job_runs
WHERE id IN (
  '69422008-51a2-42c4-b83e-f26b74c00c73',
  'a5cb611b-9890-4a3c-9f93-fbaae36d317e',
  '94d8c6ef-c10b-457e-973d-8b10c4b02038',
  '5d9466ba-364f-49ce-b6b6-188fe50fd671',
  '69fee792-1be9-41aa-adc0-e1a58e495c90'
)
ORDER BY created_at;
