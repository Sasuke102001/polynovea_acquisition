-- ─────────────────────────────────────────────────────────────────────────────
-- M2 RDS — Module 3 Feedback Tables
-- Run in the M2 PostgreSQL database (NOT Supabase)
--
-- These two tables are the only M3 writes into M2.
-- They are written by the M3 backend (read-only + limited write credentials).
-- M2 reads them to recalibrate segment alignment scores over time.
--
-- These tables are what close the feedback loop:
--   M3 measures what actually happened → writes here →
--   M2 reads here → updates venue_demographic_scores.alignment_score →
--   M2 predictions improve → M3 briefs become more accurate
-- ─────────────────────────────────────────────────────────────────────────────


-- ─────────────────────────────────────────────────────────────────────────────
-- 1. m3_segment_validation_feedback
--
-- After each session where customer survey responses were collected, M3
-- compares M2's predicted segment alignment against what was actually observed.
-- The delta column is the core signal for recalibration.
--
-- Example row:
--   venue_id=42, segment_id='working_women',
--   m2_alignment=0.68, m3_observed=0.12, delta=-0.56
--   → M2 was dramatically wrong about this segment at this venue
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS m3_segment_validation_feedback (
    id              BIGSERIAL PRIMARY KEY,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    venue_id        INT NOT NULL REFERENCES venues (id) ON DELETE CASCADE,
    session_date    DATE NOT NULL,

    segment_id      TEXT NOT NULL,           -- matches venue_demographic_scores.segment_id

    -- M2's predicted alignment before the session (snapshot at brief time)
    m2_alignment    NUMERIC(5, 4) NOT NULL,  -- 0.0000 – 1.0000

    -- M3's observed alignment from customer survey responses
    m3_observed     NUMERIC(5, 4) NOT NULL,  -- 0.0000 – 1.0000

    -- m3_observed - m2_alignment (negative = M2 over-predicted this segment)
    delta           NUMERIC(6, 4) GENERATED ALWAYS AS (m3_observed - m2_alignment) STORED,

    -- How many survey responses contributed to this observation
    survey_count    INT NOT NULL DEFAULT 0,

    -- LOW = 1-4 surveys, MEDIUM = 5-9 surveys, HIGH = 10+ surveys
    confidence      TEXT NOT NULL DEFAULT 'LOW'
        CHECK (confidence IN ('LOW', 'MEDIUM', 'HIGH'))
);

CREATE INDEX IF NOT EXISTS idx_m3_seg_val_venue
    ON m3_segment_validation_feedback (venue_id, segment_id, session_date DESC);

COMMENT ON TABLE m3_segment_validation_feedback IS
    'M3 writes validated segment observations here after each session with survey data. '
    'M2 reads this to recalibrate venue_demographic_scores.alignment_score. '
    'Core mechanism: M2 segments are behavioral hypotheses — this table is where '
    'they get tested against real demographic evidence from actual customers.';

COMMENT ON COLUMN m3_segment_validation_feedback.delta IS
    'Signed difference: m3_observed minus m2_alignment. '
    'Negative = M2 over-predicted this segment at this venue. '
    'Positive = M2 under-predicted. Large absolute values trigger recalibration.';


-- ─────────────────────────────────────────────────────────────────────────────
-- 2. m3_venue_behavioral_outcomes
--
-- High-level session outcome record written by M3 after each completed session.
-- Captures what actually happened — dwell, crowd energy, segment confirmed,
-- whether the engineered intervention worked — for M2 to use as ground truth.
--
-- This gives M2 real-world experimental evidence instead of staying theoretical.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS m3_venue_behavioral_outcomes (
    id                          BIGSERIAL PRIMARY KEY,
    recorded_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    venue_id                    INT NOT NULL REFERENCES venues (id) ON DELETE CASCADE,
    session_date                DATE NOT NULL,
    session_number              INT NOT NULL,  -- 1-based, tracks how many sessions at this venue

    -- What M3 actually measured during the session
    avg_dwell_min               INT,           -- average dwell time across logged tables
    peak_crowd_energy           TEXT           -- LOW | MEDIUM | HIGH
        CHECK (peak_crowd_energy IN ('LOW', 'MEDIUM', 'HIGH')),
    peak_occupancy_pct          NUMERIC(5, 2), -- 0.00 – 100.00 percent of capacity
    primary_segment_confirmed   TEXT,          -- which segment actually dominated

    -- Intervention outcome
    intervention_deployed       BOOLEAN NOT NULL DEFAULT FALSE,
    intervention_worked         BOOLEAN,       -- NULL if no intervention deployed
    intervention_type           TEXT,          -- music_change | lighting | floor_reset | other

    -- Free-text notes from operator or AI debrief
    notes                       TEXT,

    -- Confidence in this outcome record
    data_quality                TEXT NOT NULL DEFAULT 'OPERATOR_LOGGED'
        CHECK (data_quality IN ('SURVEY_VALIDATED', 'OPERATOR_LOGGED', 'INFERRED'))
);

CREATE INDEX IF NOT EXISTS idx_m3_outcomes_venue
    ON m3_venue_behavioral_outcomes (venue_id, session_date DESC);

CREATE INDEX IF NOT EXISTS idx_m3_outcomes_segment
    ON m3_venue_behavioral_outcomes (venue_id, primary_segment_confirmed)
    WHERE primary_segment_confirmed IS NOT NULL;

COMMENT ON TABLE m3_venue_behavioral_outcomes IS
    'One row per completed M3 session. Written by M3 backend, read by M2 for '
    'recalibration and longitudinal behavioral tracking. '
    'SURVEY_VALIDATED = survey responses back the observation. '
    'OPERATOR_LOGGED = operator manually confirmed. '
    'INFERRED = derived from KPI data alone (no survey, no manual confirmation).';

COMMENT ON COLUMN m3_venue_behavioral_outcomes.session_number IS
    'Shows 1+ at Sessions 3+ where history mode unlocks — M2 can query '
    'only rows where session_number >= 3 for higher-confidence outcomes.';


-- ─────────────────────────────────────────────────────────────────────────────
-- 3. M3 read-only role (run as superuser)
--
-- Grant M3 backend read access to all M2 tables +
-- insert/update rights on the two feedback tables only.
-- Replace 'm3_app_user' and 'your_password' with actual credentials.
-- ─────────────────────────────────────────────────────────────────────────────

-- CREATE ROLE m3_app_user WITH LOGIN PASSWORD 'your_password';

-- Read access to all existing M2 tables
-- GRANT CONNECT ON DATABASE polynovea TO m3_app_user;
-- GRANT USAGE ON SCHEMA public TO m3_app_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO m3_app_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO m3_app_user;

-- Write access ONLY to the two feedback tables
-- GRANT INSERT, UPDATE ON m3_segment_validation_feedback TO m3_app_user;
-- GRANT INSERT, UPDATE ON m3_venue_behavioral_outcomes TO m3_app_user;
-- GRANT USAGE ON SEQUENCE m3_segment_validation_feedback_id_seq TO m3_app_user;
-- GRANT USAGE ON SEQUENCE m3_venue_behavioral_outcomes_id_seq TO m3_app_user;
