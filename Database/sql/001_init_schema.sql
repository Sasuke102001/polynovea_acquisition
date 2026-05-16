-- ============================================================
-- Polynovea Module 2 — PostgreSQL Schema
-- 001_init_schema.sql
-- Run once on a fresh Azure PostgreSQL instance
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- for fuzzy name matching

-- ============================================================
-- CORE TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS venues (
    id               SERIAL PRIMARY KEY,
    place_id         VARCHAR(255) UNIQUE NOT NULL,
    name             VARCHAR(500) NOT NULL,
    name_normalized  VARCHAR(500) GENERATED ALWAYS AS (LOWER(TRIM(name))) STORED,
    area             VARCHAR(255),
    city             VARCHAR(100),
    types            JSONB,
    lat              DECIMAL(9,6),
    lng              DECIMAL(9,6),
    locality         VARCHAR(255),
    discovered_at    TIMESTAMP,
    geo_google       JSONB,
    geo_operational  JSONB,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS primitives_scores (
    id           SERIAL PRIMARY KEY,
    venue_id     INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    source       VARCHAR(50) NOT NULL DEFAULT 'google',
    primitive_id VARCHAR(100) NOT NULL,
    score        DECIMAL(4,3) CHECK (score >= 0 AND score <= 1),
    confidence   DECIMAL(4,3) CHECK (confidence >= 0 AND confidence <= 1),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (venue_id, source, primitive_id)
);

CREATE TABLE IF NOT EXISTS venue_fitness_dimensions (
    id                            SERIAL PRIMARY KEY,
    venue_id                      INTEGER NOT NULL UNIQUE REFERENCES venues(id) ON DELETE CASCADE,
    fitness_for_office_lunch      DECIMAL(4,3),
    fitness_for_repeat_habit      DECIMAL(4,3),
    fitness_for_social_dwell      DECIMAL(4,3),
    fitness_for_group_energy      DECIMAL(4,3),
    fitness_for_destination_visit DECIMAL(4,3),
    operational_quality           DECIMAL(4,3),
    retention_strength            DECIMAL(4,3),
    monetization_potential        DECIMAL(4,3),
    fitness_details               JSONB  -- match_ratio, confidence_basis, matched_signals per dimension
);

CREATE TABLE IF NOT EXISTS behavioral_summary (
    id                     SERIAL PRIMARY KEY,
    venue_id               INTEGER NOT NULL UNIQUE REFERENCES venues(id) ON DELETE CASCADE,
    operational_quality    DECIMAL(4,3),
    retention_strength     DECIMAL(4,3),
    monetization_potential DECIMAL(4,3)
);

-- ============================================================
-- PATTERN TABLES (step_4_patterns_recognized + step_5_patterns_scored)
-- ============================================================

CREATE TABLE IF NOT EXISTS behavioral_patterns (
    id                      SERIAL PRIMARY KEY,
    area                    VARCHAR(100) NOT NULL,
    pattern_name            VARCHAR(500),
    co_occurring_primitives JSONB NOT NULL,
    total_venues_in_city    INTEGER,
    prevalence_percentage   DECIMAL(5,2),
    detected_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pattern_venues (
    id             SERIAL PRIMARY KEY,
    venue_id       INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    pattern_id     INTEGER NOT NULL REFERENCES behavioral_patterns(id) ON DELETE CASCADE,
    match_strength DECIMAL(4,3),
    UNIQUE (venue_id, pattern_id)
);

CREATE TABLE IF NOT EXISTS pattern_scores (
    id                   SERIAL PRIMARY KEY,
    pattern_id           INTEGER NOT NULL UNIQUE REFERENCES behavioral_patterns(id) ON DELETE CASCADE,
    confidence_score     DECIMAL(6,3),
    evidence_density     DECIMAL(4,3),
    temporal_consistency DECIMAL(4,3),
    evidence_diversity   DECIMAL(4,3),
    commercial_reliability DECIMAL(4,3),
    venue_count          INTEGER,
    prevalence           DECIMAL(5,4),
    friction_severity    VARCHAR(20)
);

-- pattern_fitness_dimensions intentionally omitted (Phase 2: computed from pattern_venues → venue_fitness_dimensions)

CREATE TABLE IF NOT EXISTS intervention_triggers (
    id                   SERIAL PRIMARY KEY,
    venue_id             INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    intervention_type    VARCHAR(100) NOT NULL,
    description          TEXT,
    fit_score            DECIMAL(4,3),
    priority_tier        VARCHAR(20),
    recommended          BOOLEAN DEFAULT FALSE,
    tier_description     TEXT,
    matched_signals      JSONB,
    missing_signals      JSONB,
    matched_signal_count VARCHAR(20),
    match_ratio          DECIMAL(4,3),
    confidence_basis     DECIMAL(4,3),
    expected_roi_impact  VARCHAR(100),
    UNIQUE (venue_id, intervention_type)
);

-- ============================================================
-- SIMILARITY TABLES (step_5b_similarity_enriched)
-- ============================================================

CREATE TABLE IF NOT EXISTS venue_vectors (
    id            SERIAL PRIMARY KEY,
    venue_id      INTEGER NOT NULL UNIQUE REFERENCES venues(id) ON DELETE CASCADE,
    fitness_vector DECIMAL(5,4)[],
    vector_source VARCHAR(50),
    last_computed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS venue_similarity (
    id                    SERIAL PRIMARY KEY,
    venue_id              INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    similar_venue_id      INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    similarity_score      DECIMAL(5,4),
    shared_primitives     JSONB,
    shared_primitive_count INTEGER,
    UNIQUE (venue_id, similar_venue_id)
);

-- ============================================================
-- DATA QUALITY TABLES (step_4b_governance_report)
-- ============================================================

CREATE TABLE IF NOT EXISTS data_quality_metrics (
    id                       SERIAL PRIMARY KEY,
    area                     VARCHAR(100) UNIQUE NOT NULL,
    avg_confidence           DECIMAL(5,4),
    avg_reliability          DECIMAL(5,4),
    reliability_score        DECIMAL(5,4),
    high_reliability_clusters INTEGER,
    total_clusters           INTEGER,
    measured_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drift_signals (
    id                  SERIAL PRIMARY KEY,
    area                VARCHAR(100) NOT NULL,
    pattern_description TEXT NOT NULL,
    confidence_score    DECIMAL(4,3),
    trend_direction     VARCHAR(50) DEFAULT 'emerging',
    detected_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cluster_quality (
    id                    SERIAL PRIMARY KEY,
    area                  VARCHAR(100) NOT NULL,
    total_clusters        INTEGER,
    high_reliability      INTEGER,
    low_confidence        INTEGER,
    measured_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- USER / SURVEY TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS survey_responses_canonical (
    id                   SERIAL PRIMARY KEY,
    response_id          VARCHAR(100) UNIQUE NOT NULL,
    form_version         VARCHAR(10),
    age_group            VARCHAR(50),
    city                 VARCHAR(100),
    company_size         VARCHAR(50),
    visit_frequency      VARCHAR(50),
    energy_preference    VARCHAR(50),
    place_preference     VARCHAR(50),
    social_personality   VARCHAR(50),
    fomo_tendency        DECIMAL(4,3),
    discovery_tendency   DECIMAL(4,3),
    group_influence      DECIMAL(4,3),
    email                VARCHAR(255),
    instagram_handle     VARCHAR(100),
    newsletter_consent   BOOLEAN DEFAULT FALSE,
    raw_responses        JSONB,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_archetypes (
    id               SERIAL PRIMARY KEY,
    response_id      VARCHAR(100) NOT NULL REFERENCES survey_responses_canonical(response_id) ON DELETE CASCADE,
    archetype_name   VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(4,3),
    primary_traits   JSONB,
    secondary_traits JSONB,
    computed_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- DEMOGRAPHIC-ARCHETYPE BRIDGE TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS demographic_segments (
    id                  SERIAL PRIMARY KEY,
    segment_id          VARCHAR(100) UNIQUE NOT NULL,
    segment_name        VARCHAR(255) NOT NULL,
    segment_description TEXT,
    age_range           VARCHAR(50),
    company_size_range  VARCHAR(50),
    visit_when          VARCHAR(100),
    area                VARCHAR(255),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS demographic_archetype_mapping (
    id                     SERIAL PRIMARY KEY,
    segment_id             VARCHAR(100) NOT NULL REFERENCES demographic_segments(segment_id) ON DELETE CASCADE,
    archetype_name         VARCHAR(100) NOT NULL,
    prevalence_percentage  DECIMAL(5,2),
    population_count       INTEGER,
    confidence_score       DECIMAL(4,3),
    UNIQUE (segment_id, archetype_name)
);

CREATE TABLE IF NOT EXISTS demographic_archetype_interventions (
    id                SERIAL PRIMARY KEY,
    segment_id        VARCHAR(100) NOT NULL REFERENCES demographic_segments(segment_id) ON DELETE CASCADE,
    archetype_name    VARCHAR(100) NOT NULL,
    intervention_type VARCHAR(100) NOT NULL,
    description       TEXT,
    expected_roi      VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS demographic_behavioral_alignment (
    id                        SERIAL PRIMARY KEY,
    segment_id                VARCHAR(100) NOT NULL REFERENCES demographic_segments(segment_id) ON DELETE CASCADE,
    archetype_name            VARCHAR(100) NOT NULL,
    primary_primitives        JSONB,
    secondary_primitives      JSONB,
    critical_fitness_dimension VARCHAR(100),
    UNIQUE (segment_id, archetype_name)
);

-- ============================================================
-- PHASE 1 MARKETING ENGINE TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS behavioral_mechanism_catalog (
    id                  SERIAL PRIMARY KEY,
    mechanism_id        VARCHAR(100) UNIQUE NOT NULL,
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    psychological_basis TEXT,
    key_triggers        JSONB,
    best_channels       JSONB,
    best_archetypes     JSONB,
    timeline_weeks      VARCHAR(50),
    research_citations  TEXT
);

CREATE TABLE IF NOT EXISTS channel_mechanism_mapping (
    id                     SERIAL PRIMARY KEY,
    channel                VARCHAR(100) NOT NULL,
    behavioral_mechanism   VARCHAR(100) NOT NULL REFERENCES behavioral_mechanism_catalog(mechanism_id),
    effectiveness_score    INTEGER CHECK (effectiveness_score BETWEEN 1 AND 10),
    best_archetypes        JSONB,
    baseline_roi_lift_min  DECIMAL(5,2),
    baseline_roi_lift_max  DECIMAL(5,2),
    primary_use_case       VARCHAR(50) CHECK (primary_use_case IN ('acquisition', 'retention', 'both')),
    research_confidence    VARCHAR(20) CHECK (research_confidence IN ('HIGH', 'MEDIUM', 'LOW')),
    UNIQUE (channel, behavioral_mechanism)
);

CREATE TABLE IF NOT EXISTS campaign_templates (
    id                          SERIAL PRIMARY KEY,
    demographic_segment         VARCHAR(100),
    target_archetype            VARCHAR(100),
    behavioral_mechanism        VARCHAR(100) REFERENCES behavioral_mechanism_catalog(mechanism_id),
    channel                     VARCHAR(100),
    message_template            TEXT,
    suggested_roi_lift_percentage DECIMAL(5,2),
    confidence_level            VARCHAR(20) CHECK (confidence_level IN ('HIGH', 'MEDIUM', 'LOW')),
    implementation_guide        TEXT,
    created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS venue_marketing_recommendations (
    id                              SERIAL PRIMARY KEY,
    venue_id                        INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    generated_at                    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acquisition_channels            JSONB,
    retention_channels              JSONB,
    not_recommended                 JSONB,
    demographic_recommendations     JSONB,
    confidence_score_overall        DECIMAL(4,3)
);

-- ============================================================
-- INDEXES
-- ============================================================

-- venues
CREATE INDEX IF NOT EXISTS idx_venues_city        ON venues(city);
CREATE INDEX IF NOT EXISTS idx_venues_area        ON venues(area);
CREATE INDEX IF NOT EXISTS idx_venues_name_norm   ON venues(name_normalized);
CREATE INDEX IF NOT EXISTS idx_venues_name_trgm   ON venues USING gin(name_normalized gin_trgm_ops);

-- primitives_scores
CREATE INDEX IF NOT EXISTS idx_prim_venue         ON primitives_scores(venue_id);
CREATE INDEX IF NOT EXISTS idx_prim_source        ON primitives_scores(source);
CREATE INDEX IF NOT EXISTS idx_prim_id            ON primitives_scores(primitive_id);

-- patterns
CREATE INDEX IF NOT EXISTS idx_bp_area            ON behavioral_patterns(area);
CREATE INDEX IF NOT EXISTS idx_pv_venue           ON pattern_venues(venue_id);
CREATE INDEX IF NOT EXISTS idx_pv_pattern         ON pattern_venues(pattern_id);
CREATE INDEX IF NOT EXISTS idx_it_venue           ON intervention_triggers(venue_id);
CREATE INDEX IF NOT EXISTS idx_it_tier            ON intervention_triggers(priority_tier);

-- similarity
CREATE INDEX IF NOT EXISTS idx_vs_venue           ON venue_similarity(venue_id);
CREATE INDEX IF NOT EXISTS idx_vs_similar         ON venue_similarity(similar_venue_id);
CREATE INDEX IF NOT EXISTS idx_vs_score           ON venue_similarity(similarity_score DESC);

-- surveys
CREATE INDEX IF NOT EXISTS idx_survey_city        ON survey_responses_canonical(city);
CREATE INDEX IF NOT EXISTS idx_archetypes_name    ON user_archetypes(archetype_name);

-- demographic bridge
CREATE INDEX IF NOT EXISTS idx_demo_area          ON demographic_segments(area);
CREATE INDEX IF NOT EXISTS idx_demo_map_segment   ON demographic_archetype_mapping(segment_id);

-- marketing
CREATE INDEX IF NOT EXISTS idx_vmr_venue          ON venue_marketing_recommendations(venue_id);
CREATE INDEX IF NOT EXISTS idx_ct_segment         ON campaign_templates(demographic_segment);
CREATE INDEX IF NOT EXISTS idx_ct_archetype       ON campaign_templates(target_archetype);

-- ============================================================
-- END OF SCHEMA
-- ============================================================
