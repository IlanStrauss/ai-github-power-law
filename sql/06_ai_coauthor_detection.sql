-- ============================================================================
-- AI Co-Author Detection in Commit Messages
-- ============================================================================
-- Purpose: Detect commits that explicitly mention AI assistance in commit
-- messages (Co-authored-by: Claude, Copilot, etc.)
--
-- CAVEAT: This massively undercounts AI usage since most AI-assisted code
-- has no attribution. But it can show the TREND in explicit attribution.
-- ============================================================================

SELECT
  EXTRACT(YEAR FROM created_at) AS year,
  EXTRACT(MONTH FROM created_at) AS month,

  -- Total push events for baseline
  COUNT(*) AS total_push_events,

  -- Commits mentioning AI co-authors
  COUNTIF(
    REGEXP_CONTAINS(
      JSON_EXTRACT_SCALAR(payload, '$.commits[0].message'),
      r'(?i)co-authored-by:\s*(claude|anthropic|copilot|github\s*copilot|openai|gpt|cursor|aider|codeium|tabnine)'
    )
  ) AS ai_coauthor_commits,

  -- Commits mentioning AI in message body (broader)
  COUNTIF(
    REGEXP_CONTAINS(
      JSON_EXTRACT_SCALAR(payload, '$.commits[0].message'),
      r'(?i)(generated\s*(by|with|using)|assisted\s*by|written\s*by|created\s*by)\s*(claude|copilot|gpt|ai|llm|chatgpt|cursor)'
    )
  ) AS ai_mentioned_commits,

  -- Claude specifically
  COUNTIF(
    REGEXP_CONTAINS(
      JSON_EXTRACT_SCALAR(payload, '$.commits[0].message'),
      r'(?i)(claude|anthropic)'
    )
  ) AS claude_mentioned,

  -- Copilot specifically
  COUNTIF(
    REGEXP_CONTAINS(
      JSON_EXTRACT_SCALAR(payload, '$.commits[0].message'),
      r'(?i)(copilot|github\s*copilot)'
    )
  ) AS copilot_mentioned,

  -- GPT/OpenAI specifically
  COUNTIF(
    REGEXP_CONTAINS(
      JSON_EXTRACT_SCALAR(payload, '$.commits[0].message'),
      r'(?i)(openai|chatgpt|gpt-[34])'
    )
  ) AS gpt_mentioned

FROM `githubarchive.year.20*`
WHERE
  type = 'PushEvent'
  AND created_at >= '2020-01-01'  -- AI tools weren't prevalent before
GROUP BY year, month
ORDER BY year, month
