-- ============================================================================
-- Commit Velocity Change: Pre vs Post Copilot
-- ============================================================================
-- Purpose: For developers active in both periods, compare their commit
-- velocity before Copilot (2019-2021) vs after (2022-2024).
--
-- Hypothesis: If AI amplifies productivity, top developers should show
-- larger velocity increases than median developers.
-- ============================================================================

WITH developer_yearly AS (
  SELECT
    EXTRACT(YEAR FROM created_at) AS year,
    actor.login AS developer,
    SUM(CAST(JSON_EXTRACT_SCALAR(payload, '$.size') AS INT64)) AS commits
  FROM `githubarchive.year.20*`
  WHERE
    type = 'PushEvent'
    AND EXTRACT(YEAR FROM created_at) BETWEEN 2019 AND 2024
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

-- Developers active in at least 2 years of each period
pre_copilot AS (
  SELECT
    developer,
    AVG(commits) AS avg_commits_pre,
    SUM(commits) AS total_commits_pre,
    COUNT(*) AS years_active_pre
  FROM developer_yearly
  WHERE year BETWEEN 2019 AND 2021
  GROUP BY developer
  HAVING years_active_pre >= 2
),

post_copilot AS (
  SELECT
    developer,
    AVG(commits) AS avg_commits_post,
    SUM(commits) AS total_commits_post,
    COUNT(*) AS years_active_post
  FROM developer_yearly
  WHERE year BETWEEN 2022 AND 2024
  GROUP BY developer
  HAVING years_active_post >= 2
),

combined AS (
  SELECT
    pre.developer,
    pre.avg_commits_pre,
    post.avg_commits_post,
    post.avg_commits_post / pre.avg_commits_pre AS velocity_ratio,
    pre.total_commits_pre,
    post.total_commits_post,
    -- Classify by pre-period productivity
    NTILE(10) OVER (ORDER BY pre.avg_commits_pre) AS pre_decile
  FROM pre_copilot pre
  JOIN post_copilot post USING (developer)
)

-- Summary by pre-period decile
SELECT
  pre_decile,
  COUNT(*) AS n_developers,
  AVG(avg_commits_pre) AS avg_commits_pre,
  AVG(avg_commits_post) AS avg_commits_post,
  AVG(velocity_ratio) AS mean_velocity_ratio,
  APPROX_QUANTILES(velocity_ratio, 100)[OFFSET(50)] AS median_velocity_ratio,
  APPROX_QUANTILES(velocity_ratio, 100)[OFFSET(25)] AS p25_velocity_ratio,
  APPROX_QUANTILES(velocity_ratio, 100)[OFFSET(75)] AS p75_velocity_ratio
FROM combined
GROUP BY pre_decile
ORDER BY pre_decile
