SELECT length(output_markdown) AS chars,
       generation_mode,
       status,
       substring(output_markdown, 1, 500) AS preview
FROM content_generation_runs
WHERE id = '2355e8ef-82b1-4bc5-aea7-59b4efcc7268';
