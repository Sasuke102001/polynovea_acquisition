-- E2: Sub-dimension scores table
-- Stores Food / Service / Atmosphere sub-ratings extracted from Google Raw Scrapper reviews.
-- Pattern: "Food: X/5 | Service: X/5 | Atmosphere: X/5" present in GRS review text.
-- Scores stored as 0.0–1.0 (normalised from /5).

CREATE TABLE IF NOT EXISTS venue_subdimension_scores (
    id               SERIAL PRIMARY KEY,
    venue_id         INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    source           TEXT    NOT NULL,
    food_score       NUMERIC(4, 3),
    service_score    NUMERIC(4, 3),
    atmosphere_score NUMERIC(4, 3),
    sample_size      INTEGER NOT NULL DEFAULT 0,
    pipeline_version TEXT,
    computed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_venue_subdimension_source UNIQUE (venue_id, source)
);

CREATE INDEX IF NOT EXISTS idx_venue_subdimension_venue_id
    ON venue_subdimension_scores (venue_id);

COMMENT ON TABLE venue_subdimension_scores IS
    'Per-venue Food/Service/Atmosphere sub-ratings from Google Raw Scrapper reviews. '
    'Scores are 0.0–1.0 (normalised from /5). Null = no sub-rating data found.';
