-- ============================================================================
-- Commits per Repository per Year
-- ============================================================================
-- Purpose: Extract the distribution of commits per repository for each year
-- to test whether activity is concentrating into fewer mega-projects.
-- ============================================================================

SELECT
  EXTRACT(YEAR FROM created_at) AS year,
  repo.name AS repository,
  repo.id AS repo_id,
  SUM(CAST(JSON_EXTRACT_SCALAR(payload, '$.size') AS INT64)) AS commits,
  COUNT(DISTINCT actor.login) AS unique_contributors
FROM `githubarchive.year.20*`
WHERE
  type = 'PushEvent'
  AND created_at >= '2015-01-01'
  AND repo.name IS NOT NULL
GROUP BY year, repository, repo_id
HAVING commits >= 10
ORDER BY year, commits DESC
