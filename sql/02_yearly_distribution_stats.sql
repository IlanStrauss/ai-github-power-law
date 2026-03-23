-- ============================================================================
-- Yearly Distribution Statistics
-- ============================================================================
-- Purpose: Compute summary statistics for each year's commit distribution
-- to track changes in concentration over time.
--
-- Key metrics:
--   - Gini-like measures (top 1%, top 10% share)
--   - Percentiles (p50, p90, p99, max)
--   - Developer counts
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
    AND actor.login NOT LIKE 'codecov%'
    AND actor.login IS NOT NULL
  GROUP BY year, developer
  HAVING commits >= 10
),

yearly_totals AS (
  SELECT
    year,
    SUM(commits) AS total_commits,
    COUNT(*) AS n_developers
  FROM developer_commits
  GROUP BY year
),

ranked AS (
  SELECT
    dc.*,
    yt.total_commits,
    yt.n_developers,
    ROW_NUMBER() OVER (PARTITION BY dc.year ORDER BY dc.commits DESC) AS rank_desc,
    dc.commits / yt.total_commits AS share_of_total
  FROM developer_commits dc
  JOIN yearly_totals yt USING (year)
)

SELECT
  year,
  n_developers,
  total_commits,

  -- Percentiles
  APPROX_QUANTILES(commits, 100)[OFFSET(50)] AS p50_commits,
  APPROX_QUANTILES(commits, 100)[OFFSET(75)] AS p75_commits,
  APPROX_QUANTILES(commits, 100)[OFFSET(90)] AS p90_commits,
  APPROX_QUANTILES(commits, 100)[OFFSET(95)] AS p95_commits,
  APPROX_QUANTILES(commits, 100)[OFFSET(99)] AS p99_commits,
  MAX(commits) AS max_commits,

  -- Concentration metrics
  SUM(IF(rank_desc <= CAST(n_developers * 0.01 AS INT64), commits, 0)) / total_commits AS top_1pct_share,
  SUM(IF(rank_desc <= CAST(n_developers * 0.10 AS INT64), commits, 0)) / total_commits AS top_10pct_share,
  SUM(IF(rank_desc <= 100, commits, 0)) / total_commits AS top_100_devs_share,
  SUM(IF(rank_desc <= 1000, commits, 0)) / total_commits AS top_1000_devs_share,

  -- Ratio of p99 to median (simple inequality measure)
  APPROX_QUANTILES(commits, 100)[OFFSET(99)] / APPROX_QUANTILES(commits, 100)[OFFSET(50)] AS p99_p50_ratio

FROM ranked
GROUP BY year, n_developers, total_commits
ORDER BY year
