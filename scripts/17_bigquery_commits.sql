-- BigQuery query for GitHub commits: Nov 2025 - present
-- Optimized to minimize data scanned (stay within 1TB free tier)
--
-- IMPORTANT: Run this in BigQuery console (console.cloud.google.com/bigquery)
-- Dataset: bigquery-public-data.github_repos
--
-- Setup steps:
-- 1. Go to console.cloud.google.com/bigquery
-- 2. Sign in with Google account
-- 3. Create a new project (free, no billing required for sandbox)
-- 4. Run the query below

-- =============================================================================
-- STEP 1: First, check data availability (tiny query, ~0 bytes)
-- =============================================================================
SELECT
  MIN(committer.date) as earliest_commit,
  MAX(committer.date) as latest_commit,
  COUNT(*) as total_commits
FROM `bigquery-public-data.github_repos.commits`
WHERE committer.date IS NOT NULL
LIMIT 1;

-- =============================================================================
-- STEP 2: Sample query to test (uses sample_commits table, much smaller)
-- =============================================================================
SELECT
  author.email,
  EXTRACT(YEAR FROM committer.date) as year,
  EXTRACT(MONTH FROM committer.date) as month,
  COUNT(*) as commit_count
FROM `bigquery-public-data.github_repos.sample_commits`
WHERE
  committer.date >= '2025-11-01'
  AND author.email IS NOT NULL
  AND author.email NOT LIKE '%[bot]%'
  AND author.email NOT LIKE '%noreply%'
GROUP BY author.email, year, month
ORDER BY commit_count DESC
LIMIT 100;

-- =============================================================================
-- STEP 3: Full query for Nov 2025 onwards (CAUTION: ~100-200GB scan)
-- =============================================================================
-- This query extracts developer-level commit counts for our analysis
-- Estimated cost: Free if within 1TB/month, otherwise ~$0.50-1.00

SELECT
  author.email as author_email,
  author.name as author_name,
  EXTRACT(YEAR FROM committer.date) as year,
  EXTRACT(MONTH FROM committer.date) as month,
  COUNT(DISTINCT commit) as distinct_commits,
  COUNT(DISTINCT repo_name) as n_repos
FROM `bigquery-public-data.github_repos.commits`
WHERE
  -- Date filter: Nov 2025 onwards
  committer.date >= '2025-11-01'

  -- Exclude obvious bots (same patterns as our GH Archive analysis)
  AND author.email NOT LIKE '%[bot]%'
  AND author.email NOT LIKE '%dependabot%'
  AND author.email NOT LIKE '%renovate%'
  AND author.email NOT LIKE '%github-actions%'
  AND author.email NOT LIKE '%noreply@github.com%'
  AND author.email NOT LIKE '%codecov%'
  AND author.email NOT LIKE '%greenkeeper%'
  AND author.email NOT LIKE '%snyk%'

  -- Basic validity
  AND author.email IS NOT NULL
  AND committer.date IS NOT NULL

GROUP BY author.email, author.name, year, month

-- Apply same filters as our analysis
HAVING
  COUNT(DISTINCT commit) >= 3  -- Min 3 commits
  AND COUNT(DISTINCT commit) <= 10000  -- Max 10k commits (exclude automation)
  AND COUNT(DISTINCT repo_name) >= 2  -- Multi-repo filter

ORDER BY year, month, distinct_commits DESC;

-- =============================================================================
-- STEP 4: Export to CSV
-- =============================================================================
-- After running Step 3, click "Save Results" > "CSV (local file)"
-- Save as: bigquery_commits_2025_2026.csv
-- Then we'll process it with Python

-- =============================================================================
-- ALTERNATIVE: Aggregate by year only (smaller output)
-- =============================================================================
SELECT
  author.email as author_email,
  EXTRACT(YEAR FROM committer.date) as year,
  COUNT(DISTINCT commit) as total_commits,
  COUNT(DISTINCT repo_name) as n_repos,
  -- Org detection: check if any repo is from known orgs
  MAX(CASE
    WHEN LOWER(repo_name) LIKE 'google/%'
      OR LOWER(repo_name) LIKE 'microsoft/%'
      OR LOWER(repo_name) LIKE 'facebook/%'
      OR LOWER(repo_name) LIKE 'meta/%'
      OR LOWER(repo_name) LIKE 'apache/%'
      OR LOWER(repo_name) LIKE 'kubernetes/%'
      OR LOWER(repo_name) LIKE 'tensorflow/%'
      OR LOWER(repo_name) LIKE 'pytorch/%'
      OR LOWER(repo_name) LIKE 'aws/%'
      OR LOWER(repo_name) LIKE 'amazon/%'
      OR LOWER(repo_name) LIKE 'netflix/%'
      OR LOWER(repo_name) LIKE 'uber/%'
      OR LOWER(repo_name) LIKE 'airbnb/%'
      OR LOWER(repo_name) LIKE 'twitter/%'
      OR LOWER(repo_name) LIKE 'mozilla/%'
      OR LOWER(repo_name) LIKE 'rust-lang/%'
      OR LOWER(repo_name) LIKE 'golang/%'
      OR LOWER(repo_name) LIKE 'python/%'
      OR LOWER(repo_name) LIKE 'nodejs/%'
      OR LOWER(repo_name) LIKE 'docker/%'
      OR LOWER(repo_name) LIKE 'hashicorp/%'
      OR LOWER(repo_name) LIKE 'elastic/%'
      OR LOWER(repo_name) LIKE 'grafana/%'
      OR LOWER(repo_name) LIKE 'openai/%'
      OR LOWER(repo_name) LIKE 'anthropic/%'
      OR LOWER(repo_name) LIKE 'huggingface/%'
    THEN 1 ELSE 0
  END) as is_org
FROM `bigquery-public-data.github_repos.commits`
WHERE
  committer.date >= '2025-11-01'
  AND author.email NOT LIKE '%[bot]%'
  AND author.email NOT LIKE '%dependabot%'
  AND author.email NOT LIKE '%renovate%'
  AND author.email NOT LIKE '%github-actions%'
  AND author.email NOT LIKE '%noreply@github.com%'
  AND author.email IS NOT NULL
GROUP BY author.email, year
HAVING
  COUNT(DISTINCT commit) >= 3
  AND COUNT(DISTINCT commit) <= 10000
  AND COUNT(DISTINCT repo_name) >= 2
ORDER BY year, total_commits DESC;
