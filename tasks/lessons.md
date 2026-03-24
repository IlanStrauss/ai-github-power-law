# Lessons Learned

## Data Processing

### ALWAYS SAVE PROCESSED DATA FILES
**Date:** 2024-03-24

**Mistake:** Script 12 (`org_developer_analysis.py`) computed org vs personal developer classification but only saved SUMMARY STATISTICS, not the developer-level data. This required re-extracting from 328 raw files when we needed the split data later.

**Rule:** When processing data:
1. ALWAYS save the processed/filtered data at the most granular level (developer-level, not just summaries)
2. Save split versions when creating subgroups (e.g., `developers_org_filtered.parquet` AND `developers_personal_filtered.parquet`)
3. Include the classification column in the main processed file (e.g., `is_org_developer`)
4. Use parquet format for efficiency, CSV for inspection

**Files that should exist after any major processing:**
- Raw combined: `all_developers_with_org.parquet`
- Split org: `developers_org_filtered.parquet`
- Split personal: `developers_personal_filtered.parquet`

### RUN ANALYSES ON PROPER SUBSAMPLES
**Date:** 2024-03-24

**Mistake:** Ran Zipf plots and transition matrix on combined (pooled) sample instead of separately for org vs personal developers.

**Rule:** When analyzing developer behavior:
1. NEVER pool org and personal developers without justification
2. Always run analyses separately on each subsample
3. Only use combined sample if explicitly comparing across groups

## Analysis Best Practices

- Org developers (professional/company) have different commit patterns than personal-only developers
- Mixing them obscures actual dynamics in each group
- Split analyses reveal heterogeneity that pooled analyses hide
