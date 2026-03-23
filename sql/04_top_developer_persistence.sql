-- ============================================================================
-- Top Developer Persistence Year-over-Year
-- ============================================================================
-- Purpose: Measure how much the top developer cohort changes year-to-year.
-- If AI amplifies existing top developers, we'd expect MORE persistence
-- (same people staying at the top) after 2022.
-- ============================================================================

WITH developer_commits AS (
  SELECT
    EXTRACT(YEAR FROM created_at) AS year,
    actor.login AS developer,
    SUM(CAST(JSON_EXTRACT_SCALAR(payload, '$.size') AS INT64)) AS commits
  FROM `githubarchive.year.20*`
  WHERE
    type = 'PushEvent'
    AND created_at >= '2015-01-01'
    AND actor.login NOT LIKE '%[bot]'
    AND actor.login NOT LIKE '%-bot'
    AND actor.login NOT LIKE '%Bot'
    AND actor.login NOT LIKE 'dependabot%'
    AND actor.login NOT LIKE 'renovate%'
    AND actor.login NOT LIKE 'github-actions%'
    AND actor.login IS NOT NULL
  GROUP BY year, developer
  HAVING commits >= 10
),

ranked AS (
  SELECT
    year,
    developer,
    commits,
    ROW_NUMBER() OVER (PARTITION BY year ORDER BY commits DESC) AS rank
  FROM developer_commits
)

-- Count overlap between consecutive years for different top-N thresholds
SELECT
  a.year AS year_from,
  a.year + 1 AS year_to,

  -- Top 100 overlap
  COUNTIF(a.rank <= 100 AND b.rank <= 100) AS top_100_overlap,
  100 AS top_100_possible,
  COUNTIF(a.rank <= 100 AND b.rank <= 100) / 100.0 AS top_100_retention_rate,

  -- Top 1000 overlap
  COUNTIF(a.rank <= 1000 AND b.rank <= 1000) AS top_1000_overlap,
  1000 AS top_1000_possible,
  COUNTIF(a.rank <= 1000 AND b.rank <= 1000) / 1000.0 AS top_1000_retention_rate,

  -- Top 10000 overlap
  COUNTIF(a.rank <= 10000 AND b.rank <= 10000) AS top_10000_overlap,
  10000 AS top_10000_possible,
  COUNTIF(a.rank <= 10000 AND b.rank <= 10000) / 10000.0 AS top_10000_retention_rate

FROM ranked a
JOIN ranked b ON a.developer = b.developer AND b.year = a.year + 1
WHERE a.year >= 2015 AND a.year <= 2024
GROUP BY year_from, year_to
ORDER BY year_from
