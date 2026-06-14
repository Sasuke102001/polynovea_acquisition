-- ============================================================
-- 003_m3_integration.sql
-- M3 → M2 integration layer. Safe to run multiple times (idempotent).
--
-- Adds:
--   A. service_type on venues              — watch_only vs watch_and_optimise
--   B. observation_state on m3_kpi_observations
--                                          — per-reading state tag (replaces session-level session_mode)
--   C. m3_kpi_dimension_map               — KPI family → fitness dimension bridge (loader uses this)
--   D. venue_fitness_conditional           — per-stratum fitness posteriors
--   E. venue_intervention_efficacy         — intervention efficacy / Product 2
--
-- Run after 001_init_schema.sql and 002_ml_upgrade.sql.
--
-- AFTER RUNNING:
--   Populate service_type for every M3-engaged venue before M3's sync
--   runs — any venue with NULL service_type routes as untagged.
--   Use the UPDATE block at the bottom of this file.
-- ============================================================


-- ─────────────────────────────────────────────────────────────────────────────
-- A. service_type — what did this venue buy from M3?
--
-- watch_only          → acquisition-only, pure observation, no SE ever
--                       M3's cleanest natural-fitness corrector
-- watch_and_optimise  → acquisition + optimisation engagement
--                       has a baseline phase + active SE implementation phase
--
-- M3's venue sync reads this column directly via RDS:
--   SELECT id, name, area, city, types, service_type FROM venues
-- Every reading M3 ships carries this tag for blend routing on M2's side.
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE venues
    ADD COLUMN IF NOT EXISTS service_type TEXT
    CHECK (service_type IN ('watch_only', 'watch_and_optimise'));

CREATE INDEX IF NOT EXISTS idx_venues_service_type
    ON venues (service_type)
    WHERE service_type IS NOT NULL;

COMMENT ON COLUMN venues.service_type IS
    'M3 engagement track. watch_only = acquisition observation only, no SE. '
    'watch_and_optimise = acquisition + SE optimisation engagement. '
    'Must be non-null for all M3-engaged venues before M3 venue sync runs.';


-- ─────────────────────────────────────────────────────────────────────────────
-- B. observation_state on m3_kpi_observations
--
-- m3_kpi_observations currently carries session_mode at frozen-session granularity
-- using the OLD vocabulary (observation_only / engineering_active / post_intervention).
-- The new model stamps observation_state PER READING using the locked vocabulary:
--   natural    ← was observation_only
--   engineered ← was engineering_active
--   settling   ← was post_intervention
--
-- The column is added as nullable so M3 can begin stamping enriched rows
-- while historical rows carry NULL (they retain session_mode for backfill).
-- Run the UPDATE block below to backfill historical rows from session_mode.
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE m3_kpi_observations
    ADD COLUMN IF NOT EXISTS observation_state TEXT
    CHECK (observation_state IN ('natural', 'engineered', 'settling'));

ALTER TABLE m3_kpi_observations
    ADD COLUMN IF NOT EXISTS service_type TEXT
    CHECK (service_type IN ('watch_only', 'watch_and_optimise'));

ALTER TABLE m3_kpi_observations
    ADD COLUMN IF NOT EXISTS engagement_phase TEXT
    CHECK (engagement_phase IN ('baseline', 'active'));

CREATE INDEX IF NOT EXISTS idx_m3_kpi_obs_state
    ON m3_kpi_observations (venue_id, observation_state)
    WHERE observation_state IS NOT NULL;

-- Backfill observation_state from old session_mode for historical rows
UPDATE m3_kpi_observations
SET observation_state = CASE
    WHEN session_mode = 'observation_only'   THEN 'natural'
    WHEN session_mode = 'engineering_active' THEN 'engineered'
    WHEN session_mode = 'post_intervention'  THEN 'settling'
    ELSE NULL
END
WHERE observation_state IS NULL AND session_mode IS NOT NULL;

COMMENT ON COLUMN m3_kpi_observations.observation_state IS
    'Per-reading state tag (locked vocabulary). natural=no lever active, '
    'engineered=SE lever live, settling=post-lever cooldown. '
    'Only natural rows feed M2 natural-fitness correction. '
    'Backfilled from session_mode for historical rows; stamped per-reading going forward.';

COMMENT ON COLUMN m3_kpi_observations.service_type IS
    'Venue track inherited from venues.service_type at write time. '
    'watch_only = acquisition-only (highest trust). '
    'watch_and_optimise = acquisition + SE engagement.';

COMMENT ON COLUMN m3_kpi_observations.engagement_phase IS
    'For watch_and_optimise venues only. baseline = pre-SE window, active = SE period.';


-- ─────────────────────────────────────────────────────────────────────────────
-- C. m3_kpi_dimension_map
--
-- Bridge table: maps M3 KPI family slugs to M2 fitness dimensions.
-- The M2 loader reads this to translate raw M3 KPI readings into
-- fitness-dimension space before writing to primitives_scores or
-- venue_fitness_conditional.
--
-- direction: how the KPI correlates with the dimension.
--   positive → high KPI score = high dimension score
--   negative → high KPI score = low dimension score (invert: 1 - score)
-- weight:     how strongly this KPI signals this dimension (0–1)
--
-- One KPI family can map to multiple dimensions (multiple rows).
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS m3_kpi_dimension_map (
    id              SERIAL PRIMARY KEY,
    kpi_family_slug TEXT NOT NULL,
    m2_dimension    TEXT NOT NULL,
    direction       TEXT NOT NULL DEFAULT 'positive'
        CHECK (direction IN ('positive', 'negative')),
    weight          DECIMAL(4,3) NOT NULL DEFAULT 1.0
        CHECK (weight > 0 AND weight <= 1),
    notes           TEXT,
    UNIQUE (kpi_family_slug, m2_dimension)
);

CREATE INDEX IF NOT EXISTS idx_m3_kpi_map_slug
    ON m3_kpi_dimension_map (kpi_family_slug);
CREATE INDEX IF NOT EXISTS idx_m3_kpi_map_dim
    ON m3_kpi_dimension_map (m2_dimension);

COMMENT ON TABLE m3_kpi_dimension_map IS
    'Bridge: M3 KPI family slug → M2 fitness dimension. '
    'M2 loader applies this map to translate raw m3_kpi_observations '
    'into fitness-dimension space before the conjugate update and blend. '
    'direction=negative means invert (use 1-score) before feeding the NIG update.';


-- ─────────────────────────────────────────────────────────────────────────────
-- D. venue_fitness_conditional
--
-- Per-stratum fitness posteriors produced by M3's observation data.
-- The unconditional scalar stays in venue_fitness_dimensions (blended row).
-- This table holds the conditional decomposition:
--   "fitness_for_social_dwell on friday evenings = 0.78"
--   "fitness_for_social_dwell on tuesday afternoons = 0.31"
--
-- condition_type  → the stratification axis  (day_of_week | show_type | time_of_day)
-- condition_value → the specific stratum      (friday | dj_night | lunch)
-- posterior_variance → from NIG update; free confidence band per stratum
--
-- Written by M3 (or by M2's blend step once M3 writes enriched primitives).
-- Read by M2's API to serve tab-level conditional fitness to the frontend.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS venue_fitness_conditional (
    id                  BIGSERIAL PRIMARY KEY,
    venue_id            INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    dimension           TEXT NOT NULL,
        -- fitness_for_office_lunch | fitness_for_repeat_habit | fitness_for_social_dwell
        -- fitness_for_group_energy | fitness_for_destination_visit
        -- operational_quality | retention_strength | monetization_potential
    condition_type      TEXT NOT NULL
        CHECK (condition_type IN ('day_of_week', 'show_type', 'time_of_day')),
    condition_value     TEXT NOT NULL,
        -- day_of_week:  monday | tuesday | wednesday | thursday | friday | saturday | sunday
        -- show_type:    dj_night | live_music | acoustic | open_mic | no_show
        -- time_of_day:  lunch | evening | late_night
    score               DECIMAL(4,3) CHECK (score >= 0 AND score <= 1),
    session_count       INTEGER NOT NULL DEFAULT 0,
    posterior_variance  DECIMAL(8,6),
    observation_state   TEXT NOT NULL DEFAULT 'natural'
        CHECK (observation_state IN ('natural', 'engineered', 'settling')),
    service_type        TEXT
        CHECK (service_type IN ('watch_only', 'watch_and_optimise')),
    pipeline_version    TEXT DEFAULT '3.0-m3-conditional',
    computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (venue_id, dimension, condition_type, condition_value)
);

CREATE INDEX IF NOT EXISTS idx_vfc_venue_dim
    ON venue_fitness_conditional (venue_id, dimension);
CREATE INDEX IF NOT EXISTS idx_vfc_venue_stratum
    ON venue_fitness_conditional (venue_id, condition_type, condition_value);
CREATE INDEX IF NOT EXISTS idx_vfc_state
    ON venue_fitness_conditional (observation_state);

COMMENT ON TABLE venue_fitness_conditional IS
    'Per-stratum fitness posteriors from M3 direct observation. '
    'Complement to the unconditional scalar in venue_fitness_dimensions. '
    'Only observation_state=natural rows feed M2 natural fitness. '
    'engineered/settling rows are retained for reference but excluded from blend.';


-- ─────────────────────────────────────────────────────────────────────────────
-- E. venue_intervention_efficacy
--
-- Product 2: did the SE lever actually move a fitness dimension, and did it stick?
-- One row per (venue, intervention_type, target_dimension) outcome.
--
-- pre_score  → natural fitness baseline before SE (from M3 observation_only)
-- post_score → fitness observed after SE implementation
-- delta      → computed column: post_score - pre_score (the lift)
-- retention_rate → how much of the delta was retained 2–4 weeks post-show
--                  1.0 = fully structural, 0.0 = fully ephemeral
-- structural_shift → pre_score + (retention_rate × delta): the venue's new
--                    natural fitness after accounting for retained uplift
--
-- plan_id links back to m3_show_plans_feed so Prism can learn from its own
-- labeled outcomes (closed loop: prescription → outcome → improved prescription).
--
-- Written by M3 after post-show review. Read by M2 for:
--   1. blend_fitness.py — structural_shift feeds the m3_outcomes source bucket
--   2. Transform tab — shows intervention ceiling vs natural floor
--   3. Prism prescriber — learns which levers worked at this venue
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS venue_intervention_efficacy (
    id                  BIGSERIAL PRIMARY KEY,
    venue_id            INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    plan_id             BIGINT,
        -- FK intent: references m3_show_plans_feed.id when that table exists in M2.
        -- Nullable — pre-existing sessions won't have a linked plan.
    intervention_type   TEXT NOT NULL,
        -- music_change | lighting | floor_reset | programming | other
    target_dimension    TEXT NOT NULL,
        -- the fitness dimension this lever was expected to move
    pre_score           DECIMAL(4,3) CHECK (pre_score >= 0 AND pre_score <= 1),
    post_score          DECIMAL(4,3) CHECK (post_score >= 0 AND post_score <= 1),
    delta               DECIMAL(5,4) GENERATED ALWAYS AS (post_score - pre_score) STORED,
    retention_rate      DECIMAL(4,3) CHECK (retention_rate IS NULL OR (retention_rate >= 0 AND retention_rate <= 1)),
        -- measured 2–4 weeks post-show; NULL if not yet assessed
    structural_shift    DECIMAL(4,3) GENERATED ALWAYS AS (
                            pre_score + (COALESCE(retention_rate, 0) * (post_score - pre_score))
                        ) STORED,
        -- the venue's adjusted natural fitness after accounting for retained uplift
    session_count       INTEGER NOT NULL DEFAULT 1,
    conditions          JSONB,
        -- scope guard: {day_of_week, show_type, time_of_day} for the sessions this covers
    confidence          DECIMAL(4,3) CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    notes               TEXT,
    recorded_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vie_venue
    ON venue_intervention_efficacy (venue_id);
CREATE INDEX IF NOT EXISTS idx_vie_venue_dim
    ON venue_intervention_efficacy (venue_id, target_dimension);
CREATE INDEX IF NOT EXISTS idx_vie_intervention
    ON venue_intervention_efficacy (intervention_type);
CREATE INDEX IF NOT EXISTS idx_vie_plan
    ON venue_intervention_efficacy (plan_id)
    WHERE plan_id IS NOT NULL;

COMMENT ON TABLE venue_intervention_efficacy IS
    'M3 writes one row per completed intervention outcome (post-show review done). '
    'structural_shift is the key output: pre_score adjusted by retained uplift. '
    'blend_fitness.py reads structural_shift as the m3_outcomes source bucket. '
    'plan_id back-links to m3_show_plans_feed for Prism closed-loop learning.';

COMMENT ON COLUMN venue_intervention_efficacy.structural_shift IS
    'pre_score + (retention_rate × delta). The venue''s true natural fitness '
    'after the SE program — accounts for both the lift and how much stuck. '
    'This is what flows into venue_fitness_dimensions via the blend.';

COMMENT ON COLUMN venue_intervention_efficacy.retention_rate IS
    'Fraction of the SE-induced delta that persisted 2–4 weeks post-show. '
    '1.0 = fully structural (the lever rewired something permanent). '
    '0.0 = fully ephemeral (crowd returned to baseline immediately). '
    'NULL until the post-show observation window closes.';


-- ─────────────────────────────────────────────────────────────────────────────
-- POPULATE service_type for M3-engaged venues
--
-- Run this block manually after confirming which venues are M3-engaged
-- and what track they are on. Every row must be non-null before M3 sync runs.
--
-- Example:
--   UPDATE venues SET service_type = 'watch_only'         WHERE id = <venue_id>;
--   UPDATE venues SET service_type = 'watch_and_optimise' WHERE id = <venue_id>;
--
-- Query to find venues that have M3 outcome records (likely M3-engaged):
--   SELECT DISTINCT v.id, v.name, v.area
--   FROM venues v
--   JOIN m3_venue_behavioral_outcomes o ON o.venue_id = v.id
--   ORDER BY v.id;
-- ─────────────────────────────────────────────────────────────────────────────
