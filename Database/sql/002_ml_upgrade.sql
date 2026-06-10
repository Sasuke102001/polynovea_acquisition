-- 002_ml_upgrade.sql
-- Additive ML-readiness migration. Safe to run multiple times (idempotent).
--
-- Adds:
--   A. confidence + evidence_count as first-class columns on venue_fitness_dimensions
--   B. venue_outcomes        — ground-truth feedback stream (sales / demo / manual labels)
--   E. city_dimension_baselines — per-city median/MAD for relative scoring
--
-- None of this drops or rewrites existing data. Run after 001_init_schema.sql.

-- ─────────────────────────────────────────────────────────────────────────────
-- A. Confidence as a first-class signal
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE venue_fitness_dimensions
    ADD COLUMN IF NOT EXISTS confidence     DECIMAL(4,3)
        CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1));

ALTER TABLE venue_fitness_dimensions
    ADD COLUMN IF NOT EXISTS evidence_count INTEGER DEFAULT 0;

COMMENT ON COLUMN venue_fitness_dimensions.confidence IS
    'Per-row confidence in [0,1]. For source=blended this is derived from source count + evidence volume. For raw sources it is the BIF step_4 SNR/floor confidence once emitted.';
COMMENT ON COLUMN venue_fitness_dimensions.evidence_count IS
    'Total behavioral evidence units behind this row (reviews / mentions). Compounds as more data loads → confidence rises automatically.';

-- ─────────────────────────────────────────────────────────────────────────────
-- B. Ground-truth feedback stream — the ML training set, captured from day one
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS venue_outcomes (
    id            SERIAL PRIMARY KEY,
    venue_id      INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    signal_type   VARCHAR(40)  NOT NULL,   -- 'sales_thumbs' | 'converted' | 'rejected' | 'dismiss' | 'manual_correction'
    signal_value  DECIMAL(6,4),            -- numeric label (e.g. 1.0 / 0.0 / a corrected score)
    fitness_dim   VARCHAR(60),             -- which dimension this judges (nullable = whole-venue)
    actor         VARCHAR(80),             -- 'sales:<name>' | 'demo:<token>' | 'system' | 'analyst'
    context       JSONB,                   -- prospect_name, demo_token, free-text notes, etc.
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_venue_outcomes_venue  ON venue_outcomes(venue_id);
CREATE INDEX IF NOT EXISTS idx_venue_outcomes_type   ON venue_outcomes(signal_type);
CREATE INDEX IF NOT EXISTS idx_venue_outcomes_dim    ON venue_outcomes(fitness_dim);

COMMENT ON TABLE venue_outcomes IS
    'Append-only ground-truth labels. Every sales thumbs-up, demo dismissal, and manual correction lands here so supervised ML has a training set later. Never overwrite — always insert.';

-- ─────────────────────────────────────────────────────────────────────────────
-- E. Per-city baselines — lets scores be read RELATIVE to local market
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS city_dimension_baselines (
    id            SERIAL PRIMARY KEY,
    city          VARCHAR(120) NOT NULL,
    source        VARCHAR(50)  NOT NULL DEFAULT 'blended',
    dimension     VARCHAR(60)  NOT NULL,
    median        DECIMAL(6,4),
    mad           DECIMAL(6,4),            -- median absolute deviation (robust spread)
    p25           DECIMAL(6,4),
    p75           DECIMAL(6,4),
    venue_count   INTEGER,
    pipeline_version TEXT,
    computed_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (city, source, dimension)
);

CREATE INDEX IF NOT EXISTS idx_city_baselines_city ON city_dimension_baselines(city, source);

COMMENT ON TABLE city_dimension_baselines IS
    'Per-city robust statistics per fitness dimension. A score is interpreted vs its city median/MAD, so "high social_dwell" means something local. Sharpens automatically as more venues load per city.';
