-- ============================================================================
-- Commits per Developer per Year
-- ============================================================================
-- Purpose: Extract the distribution of commits per developer for each year
-- to test whether the distribution is becoming more heavy-tailed over time.
--
-- Output: developer, year, commit_count
-- Cost estimate: ~$15-20 for full query (6TB dataset)
-- ============================================================================

-- For testing (sampled): Add WHERE RAND() < 0.01 to sample 1%

SELECT
  EXTRACT(YEAR FROM created_at) AS year,
  actor.login AS developer,
  -- Count actual commits, not just push events
  -- Each PushEvent can contain multiple commits
  SUM(
    CAST(JSON_EXTRACT_SCALAR(payload, '$.size') AS INT64)
  ) AS commits
FROM `githubarchive.year.20*`
WHERE
  type = 'PushEvent'
  AND created_at >= '2015-01-01'
  -- Exclude obvious bots
  AND actor.login NOT LIKE '%[bot]'
  AND actor.login NOT LIKE '%-bot'
  AND actor.login NOT LIKE '%Bot'
  AND actor.login NOT LIKE 'dependabot%'
  AND actor.login NOT LIKE 'renovate%'
  AND actor.login NOT LIKE 'github-actions%'
  AND actor.login NOT LIKE 'codecov%'
  AND actor.login IS NOT NULL
GROUP BY year, developer
-- Filter out very low activity (noise)
HAVING commits >= 10
ORDER BY year, commits DESC
