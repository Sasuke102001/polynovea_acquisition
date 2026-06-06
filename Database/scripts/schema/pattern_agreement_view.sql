-- Pattern Agreement Materialized View
-- Aggregates behavioral_patterns across sources to compute cross-source confidence.
--
-- source_count   = number of independent sources that detected this pattern in this area
-- avg_prevalence = average prevalence % across those sources
-- agreement_score = avg_prevalence × source_count  (higher = more credible)
--
-- Run after all pipeline loaders are complete for a region.
-- Refresh with: REFRESH MATERIALIZED VIEW CONCURRENTLY pattern_agreement;

CREATE MATERIALIZED VIEW IF NOT EXISTS pattern_agreement AS
SELECT
    area,
    pattern_name,
    COUNT(DISTINCT source)                               AS source_count,
    ROUND(AVG(prevalence_percentage)::numeric, 4)        AS avg_prevalence,
    ROUND((AVG(prevalence_percentage) * COUNT(DISTINCT source))::numeric, 4)
                                                         AS agreement_score,
    ARRAY_AGG(DISTINCT source ORDER BY source)           AS sources
FROM behavioral_patterns
GROUP BY area, pattern_name
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS pattern_agreement_area_pattern_idx
    ON pattern_agreement (area, pattern_name);

-- To refresh after new pipeline loads:
-- REFRESH MATERIALIZED VIEW CONCURRENTLY pattern_agreement;
