-- ============================================================
-- Polynovea Module 2 — PostgreSQL Schema
-- 001_init_schema.sql
-- Consolidated schema with all columns, constraints, scaffolds,
-- materialized views, and indexes.
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
    venue_id                      INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    source                        VARCHAR(50) NOT NULL DEFAULT 'google',
    fitness_for_office_lunch      DECIMAL(4,3),
    fitness_for_repeat_habit      DECIMAL(4,3),
    fitness_for_social_dwell      DECIMAL(4,3),
    fitness_for_group_energy      DECIMAL(4,3),
    fitness_for_destination_visit DECIMAL(4,3),
    operational_quality           DECIMAL(4,3),
    retention_strength            DECIMAL(4,3),
    monetization_potential        DECIMAL(4,3),
    fitness_details               JSONB,  -- match_ratio, confidence_basis, matched_signals per dimension
    computed_at                   TIMESTAMPTZ DEFAULT NOW(),
    pipeline_version              TEXT DEFAULT '1.0',
    schema_version                INTEGER DEFAULT 1,
    UNIQUE (venue_id, source)
);

CREATE TABLE IF NOT EXISTS behavioral_summary (
    id                     SERIAL PRIMARY KEY,
    venue_id               INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    source                 VARCHAR(50) NOT NULL DEFAULT 'google',
    operational_quality    DECIMAL(4,3),
    retention_strength     DECIMAL(4,3),
    monetization_potential DECIMAL(4,3),
    UNIQUE (venue_id, source)
);

-- ============================================================
-- PATTERN TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS behavioral_patterns (
    id                      SERIAL PRIMARY KEY,
    area                    VARCHAR(100) NOT NULL,
    source                  VARCHAR(50) NOT NULL DEFAULT 'google',
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
    pattern_id           INTEGER NOT NULL REFERENCES behavioral_patterns(id) ON DELETE CASCADE,
    source               VARCHAR(50) NOT NULL DEFAULT 'google',
    confidence_score     DECIMAL(6,3),
    evidence_density     DECIMAL(4,3),
    temporal_consistency DECIMAL(4,3),
    evidence_diversity   DECIMAL(4,3),
    commercial_reliability DECIMAL(4,3),
    venue_count          INTEGER,
    prevalence           DECIMAL(5,4),
    friction_severity    VARCHAR(20),
    UNIQUE (pattern_id, source)
);

CREATE TABLE IF NOT EXISTS intervention_triggers (
    id                   SERIAL PRIMARY KEY,
    venue_id             INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    source               VARCHAR(50) NOT NULL DEFAULT 'google',
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
    UNIQUE (venue_id, source, intervention_type)
);

-- ============================================================
-- SIMILARITY TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS venue_vectors (
    id            SERIAL PRIMARY KEY,
    venue_id      INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    source        VARCHAR(50) NOT NULL DEFAULT 'google',
    fitness_vector DECIMAL(5,4)[],
    vector_source VARCHAR(50),
    vector_confidence TEXT DEFAULT 'behavioral_evidence',
    last_computed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (venue_id, source)
);

CREATE TABLE IF NOT EXISTS venue_similarity (
    id                    SERIAL PRIMARY KEY,
    venue_id              INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    source                VARCHAR(50) NOT NULL DEFAULT 'google',
    similar_venue_id      INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    similarity_score      DECIMAL(5,4),
    shared_primitives     JSONB,
    shared_primitive_count INTEGER,
    rank                  INTEGER,
    UNIQUE (venue_id, source, similar_venue_id)
);

-- ============================================================
-- DATA QUALITY TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS data_quality_metrics (
    id                       SERIAL PRIMARY KEY,
    area                     VARCHAR(100) NOT NULL,
    source                   VARCHAR(50) NOT NULL DEFAULT 'google',
    avg_confidence           DECIMAL(5,4),
    avg_reliability          DECIMAL(5,4),
    reliability_score        DECIMAL(5,4),
    high_reliability_clusters INTEGER,
    total_clusters           INTEGER,
    measured_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (area, source)
);

CREATE TABLE IF NOT EXISTS drift_signals (
    id                  SERIAL PRIMARY KEY,
    area                VARCHAR(100) NOT NULL,
    source              VARCHAR(50) NOT NULL DEFAULT 'google',
    pattern_description TEXT NOT NULL,
    confidence_score    DECIMAL(4,3),
    trend_direction     VARCHAR(50) DEFAULT 'emerging',
    detected_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (area, source, pattern_description)
);

CREATE TABLE IF NOT EXISTS cluster_quality (
    id                    SERIAL PRIMARY KEY,
    area                  VARCHAR(100) NOT NULL,
    source                VARCHAR(50) NOT NULL DEFAULT 'google',
    total_clusters        INTEGER,
    high_reliability      INTEGER,
    low_confidence        INTEGER,
    measured_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (area, source)
);

-- ============================================================
-- USER / SURVEY / DEMOGRAPHIC TABLES
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

CREATE TABLE IF NOT EXISTS venue_demographic_scores (
    id               SERIAL PRIMARY KEY,
    venue_id         INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    segment_id       VARCHAR(50) NOT NULL,
    alignment_score  FLOAT NOT NULL DEFAULT 0.0,
    segment_rank     INTEGER,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    computed_at      TIMESTAMPTZ DEFAULT NOW(),
    pipeline_version TEXT DEFAULT '1.0',
    schema_version   INTEGER DEFAULT 1,
    UNIQUE(venue_id, segment_id)
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

CREATE TABLE IF NOT EXISTS behavioral_districts (
    district_id               VARCHAR(160) PRIMARY KEY,
    source                    VARCHAR(50) NOT NULL DEFAULT 'blended',
    city                      VARCHAR(100) NOT NULL,
    geo_cell                  VARCHAR(80),
    district_label            VARCHAR(200) NOT NULL,
    behavioral_signature      JSONB NOT NULL,
    venue_count               INTEGER NOT NULL,
    avg_state_energy          DECIMAL(6,4),
    avg_behavioral_entropy    DECIMAL(6,4),
    avg_niche_saturation      DECIMAL(6,4),
    centroid_lat              DECIMAL(9,6),
    centroid_lng              DECIMAL(9,6),
    top_dimensions            JSONB,
    details                   JSONB,
    pipeline_version          VARCHAR(80),
    computed_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS venue_behavioral_market_position (
    venue_id                  INTEGER PRIMARY KEY REFERENCES venues(id) ON DELETE CASCADE,
    source                    VARCHAR(50) NOT NULL DEFAULT 'blended',
    district_id               VARCHAR(160) REFERENCES behavioral_districts(district_id) ON DELETE SET NULL,
    behavioral_district       VARCHAR(200) NOT NULL,
    state_energy              DECIMAL(6,4),
    energy_band               VARCHAR(20),
    anomaly_score             DECIMAL(8,4),
    is_anomaly                BOOLEAN DEFAULT FALSE,
    behavioral_entropy        DECIMAL(6,4),
    niche_saturation          DECIMAL(6,4),
    district_size             INTEGER,
    signature_family          VARCHAR(120),
    local_density             DECIMAL(6,4),
    top_dimensions            JSONB,
    details                   JSONB,
    pipeline_version          VARCHAR(80),
    computed_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- PROVENANCE & SCATTERED PIPELINE TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS venue_platform_ids (
    id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    venue_id         INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    platform         TEXT NOT NULL CHECK (platform IN ('google', 'zomato', 'swiggy', 'magicpin', 'instagram', 'dineout', 'other')),
    platform_id      TEXT NOT NULL,
    platform_url     TEXT,
    name_on_platform TEXT,
    last_verified_at TIMESTAMPTZ DEFAULT NOW(),
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (platform, platform_id)
);

CREATE TABLE IF NOT EXISTS raw_venue_data (
    id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    venue_id         INTEGER REFERENCES venues(id) ON DELETE SET NULL,
    platform         TEXT NOT NULL,
    data_type        TEXT NOT NULL CHECK (data_type IN ('api_response', 'html_scrape', 'review_batch', 'geocode_response', 'search_result')),
    raw_payload      JSONB NOT NULL,
    collected_at     TIMESTAMPTZ DEFAULT NOW(),
    collector_version TEXT DEFAULT '1.0',
    query_params     JSONB,
    schema_version   INTEGER DEFAULT 1,
    is_deleted       BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS venue_platform_data (
    id                      SERIAL PRIMARY KEY,
    venue_id                INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    platform                VARCHAR(20) NOT NULL,   -- 'zomato' | 'swiggy'
    opt_in_date             DATE,
    current_rating          FLOAT,
    rating_30d_ago          FLOAT,
    rating_delta            FLOAT GENERATED ALWAYS AS (current_rating - rating_30d_ago) STORED,
    total_review_count      INTEGER,
    reviews_last_30d        INTEGER,
    monthly_covers          INTEGER,
    avg_covers_per_day      FLOAT,
    peak_day                VARCHAR(20),             -- e.g. 'Saturday'
    peak_hour_range         VARCHAR(30),             -- e.g. '12:00-14:00'
    avg_order_value         FLOAT,
    avg_table_spend         FLOAT,
    photo_count             INTEGER,
    last_photo_updated      DATE,
    dineout_enabled         BOOLEAN DEFAULT FALSE,
    promoted_placement      BOOLEAN DEFAULT FALSE,
    data_as_of              DATE,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(venue_id, platform)
);

CREATE TABLE IF NOT EXISTS venue_pos_summary (
    id                      SERIAL PRIMARY KEY,
    venue_id                INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    monthly_revenue         FLOAT,
    avg_daily_revenue       FLOAT,
    revenue_per_cover       FLOAT,
    monthly_covers          INTEGER,
    avg_table_size          FLOAT,
    avg_visit_duration_mins INTEGER,
    repeat_customer_rate    FLOAT,    -- 0-1
    avg_visits_per_customer FLOAT,    -- in 30 days
    customer_lifetime_value FLOAT,    -- estimated ₹
    peak_day                VARCHAR(20),
    peak_hour_range         VARCHAR(30),
    lunch_revenue_pct       FLOAT,    -- % of revenue from lunch
    dinner_revenue_pct      FLOAT,    -- % of revenue from dinner
    data_source             VARCHAR(50) DEFAULT 'module3_field',
    data_as_of              DATE,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(venue_id)
);

CREATE TABLE IF NOT EXISTS platform_performance_benchmarks (
    id                      SERIAL PRIMARY KEY,
    platform                VARCHAR(20) NOT NULL,
    city                    VARCHAR(50),
    venue_type              VARCHAR(50),     -- casual_dine, fine_dine, bar, cafe, lounge
    sample_size             INTEGER DEFAULT 0,
    avg_rating              FLOAT,
    avg_monthly_covers      INTEGER,
    avg_review_velocity     FLOAT,           -- reviews per month
    avg_photo_count         INTEGER,
    pct_with_dineout        FLOAT,           -- % of venues with Dineout enabled
    confidence              VARCHAR(10) DEFAULT 'LOW',  -- LOW/MEDIUM/HIGH based on sample_size
    last_updated            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, city, venue_type)
);

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

CREATE TABLE IF NOT EXISTS venue_council_sessions (
    id               uuid        default gen_random_uuid() primary key,
    created_at       timestamptz default now(),
    venue_id         text        not null,
    tab              text        not null,
    question         text        not null,
    nemotron_r1      text,
    deepseek_r1      text,
    qwen_r1          text,
    nemotron_r2      text,
    deepseek_r2      text,
    qwen_r2          text,
    synthesis        text,
    consensus_reached boolean,
    duration_ms      integer
);

-- ============================================================
-- MATERIALIZED VIEWS
-- ============================================================

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
CREATE INDEX IF NOT EXISTS idx_bp_source          ON behavioral_patterns(source);
CREATE INDEX IF NOT EXISTS idx_behavioral_districts_city_source ON behavioral_districts(city, source);
CREATE INDEX IF NOT EXISTS idx_vbmp_source_district ON venue_behavioral_market_position(source, district_id);
CREATE INDEX IF NOT EXISTS idx_pv_venue           ON pattern_venues(venue_id);
CREATE INDEX IF NOT EXISTS idx_pv_pattern         ON pattern_venues(pattern_id);
CREATE INDEX IF NOT EXISTS idx_it_venue           ON intervention_triggers(venue_id);
CREATE INDEX IF NOT EXISTS idx_it_tier            ON intervention_triggers(priority_tier);

-- similarity
CREATE INDEX IF NOT EXISTS idx_vs_venue           ON venue_similarity(venue_id);
CREATE INDEX IF NOT EXISTS idx_vs_similar         ON venue_similarity(similar_venue_id);
CREATE INDEX IF NOT EXISTS idx_vs_score           ON venue_similarity(similarity_score DESC);
CREATE INDEX IF NOT EXISTS idx_vs_venue_rank      ON venue_similarity(venue_id, rank);

-- surveys & archetypes
CREATE INDEX IF NOT EXISTS idx_survey_city        ON survey_responses_canonical(city);
CREATE INDEX IF NOT EXISTS idx_archetypes_name    ON user_archetypes(archetype_name);

-- demographic bridge
CREATE INDEX IF NOT EXISTS idx_demo_area          ON demographic_segments(area);
CREATE INDEX IF NOT EXISTS idx_demo_map_segment   ON demographic_archetype_mapping(segment_id);
CREATE INDEX IF NOT EXISTS idx_vds_venue_id       ON venue_demographic_scores(venue_id);
CREATE INDEX IF NOT EXISTS idx_vds_venue_rank     ON venue_demographic_scores(venue_id, segment_rank);
CREATE INDEX IF NOT EXISTS idx_vds_segment        ON venue_demographic_scores(segment_id, alignment_score DESC);

-- marketing
CREATE INDEX IF NOT EXISTS idx_vmr_venue          ON venue_marketing_recommendations(venue_id);
CREATE INDEX IF NOT EXISTS idx_ct_segment         ON campaign_templates(demographic_segment);
CREATE INDEX IF NOT EXISTS idx_ct_archetype       ON campaign_templates(target_archetype);

-- provenance & scaffolds
CREATE INDEX IF NOT EXISTS idx_vpi_venue_id       ON venue_platform_ids(venue_id);
CREATE INDEX IF NOT EXISTS idx_vpi_platform       ON venue_platform_ids(platform, platform_id);
CREATE INDEX IF NOT EXISTS idx_rvd_venue_id       ON raw_venue_data(venue_id);
CREATE INDEX IF NOT EXISTS idx_rvd_platform       ON raw_venue_data(platform, data_type);
CREATE INDEX IF NOT EXISTS idx_rvd_collected_at   ON raw_venue_data(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_vpd_venue           ON venue_platform_data(venue_id);
CREATE INDEX IF NOT EXISTS idx_vpd_platform        ON venue_platform_data(platform, current_rating DESC);
CREATE INDEX IF NOT EXISTS idx_vps_venue           ON venue_pos_summary(venue_id);
CREATE INDEX IF NOT EXISTS idx_ppb_platform_city   ON platform_performance_benchmarks(platform, city);
CREATE INDEX IF NOT EXISTS idx_venue_subdimension_venue_id ON venue_subdimension_scores(venue_id);
CREATE INDEX IF NOT EXISTS idx_council_venue      ON venue_council_sessions (venue_id);
CREATE INDEX IF NOT EXISTS idx_council_tab        ON venue_council_sessions (tab);
CREATE INDEX IF NOT EXISTS idx_council_consensus  ON venue_council_sessions (consensus_reached);
CREATE INDEX IF NOT EXISTS idx_council_created    ON venue_council_sessions (created_at desc);

CREATE UNIQUE INDEX IF NOT EXISTS pattern_agreement_area_pattern_idx ON pattern_agreement (area, pattern_name);

-- ============================================================
-- END OF SCHEMA
-- ============================================================
