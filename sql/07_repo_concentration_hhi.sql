-- ============================================================================
-- Repository Concentration Index (HHI)
-- ============================================================================
-- Purpose: Calculate the Herfindahl-Hirschman Index for commit concentration
-- across repositories. Higher HHI = more concentrated activity.
--
-- Also calculates top-N repository shares.
-- ============================================================================

WITH repo_commits AS (
  SELECT
    EXTRACT(YEAR FROM created_at) AS year,
    repo.name AS repository,
    SUM(CAST(JSON_EXTRACT_SCALAR(payload, '$.size') AS INT64)) AS commits
  FROM `githubarchive.year.20*`
  WHERE
    type = 'PushEvent'
    AND created_at >= '2015-01-01'
    AND repo.name IS NOT NULL
  GROUP BY year, repository
  HAVING commits >= 10
),

yearly_totals AS (
  SELECT
    year,
    SUM(commits) AS total_commits,
    COUNT(*) AS n_repos
  FROM repo_commits
  GROUP BY year
),

ranked AS (
  SELECT
    rc.*,
    yt.total_commits,
    yt.n_repos,
    rc.commits / yt.total_commits AS market_share,
    ROW_NUMBER() OVER (PARTITION BY rc.year ORDER BY rc.commits DESC) AS rank
  FROM repo_commits rc
  JOIN yearly_totals yt USING (year)
)

SELECT
  year,
  n_repos,
  total_commits,

  -- HHI: sum of squared market shares (x10000 for standard HHI scale)
  -- Higher = more concentrated
  SUM(POW(market_share, 2)) * 10000 AS hhi_index,

  -- Top N repo shares
  SUM(IF(rank <= 10, market_share, 0)) AS top_10_share,
  SUM(IF(rank <= 50, market_share, 0)) AS top_50_share,
  SUM(IF(rank <= 100, market_share, 0)) AS top_100_share,
  SUM(IF(rank <= 500, market_share, 0)) AS top_500_share,
  SUM(IF(rank <= 1000, market_share, 0)) AS top_1000_share,

  -- Equivalent number of equal-sized repos (1/HHI in units)
  1 / SUM(POW(market_share, 2)) AS equivalent_n_repos

FROM ranked
GROUP BY year, n_repos, total_commits
ORDER BY year
