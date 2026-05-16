-- =============================================================================
-- BEHAVIORAL RESEARCH DATABASE
-- Polynovea Venue Intelligence System
-- =============================================================================
-- This schema replaces hardcoded Python dicts in utils.py with queryable
-- behavioral research backed by academic citations and quantified parameters.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- ENUMS
-- ---------------------------------------------------------------------------

CREATE TYPE affinity_level AS ENUM (
    'none', 'low', 'low_medium', 'medium', 'medium_high', 'high', 'very_high'
);

CREATE TYPE alcohol_driver AS ENUM (
    'habit', 'social_occasion', 'identity', 'fomo', 'discovery', 'none'
);

CREATE TYPE discovery_rate AS ENUM (
    'very_low', 'low', 'medium', 'medium_high', 'high', 'very_high', 'extremely_high'
);

CREATE TYPE occasion_habit_orientation AS ENUM (
    'occasion_driven', 'habit_driven', 'mixed'
);

CREATE TYPE revenue_curve_shape AS ENUM (
    'steep_front_flat_tail',
    'front_loaded_alcohol_tail',
    'steady',
    'course_paced_wine_driven',
    'linear_child_limited',
    'efficient_single_peak',
    'moderate_steady'
);

CREATE TYPE signal_strength AS ENUM ('primary', 'secondary', 'minimal');

CREATE TYPE platform_name AS ENUM (
    'instagram', 'tiktok', 'zomato', 'swiggy', 'swiggy_dineout',
    'zomato_gold', 'google_maps', 'google_reviews', 'direct', 'word_of_mouth'
);

CREATE TYPE platform_usage_type AS ENUM (
    'discovery', 'validation', 'booking', 'post_visit_review', 'wom'
);

CREATE TYPE mechanism_category AS ENUM (
    'social_influence', 'scarcity_urgency', 'identity_status',
    'habit_automaticity', 'environmental', 'loss_aversion', 'cultural_capital'
);

-- ---------------------------------------------------------------------------
-- LAYER 1: BEHAVIORAL MECHANISMS (Academic Backbone)
-- ---------------------------------------------------------------------------

CREATE TABLE behavioral_mechanisms (
    id                      SERIAL PRIMARY KEY,
    slug                    TEXT NOT NULL UNIQUE,  -- e.g. 'social_proof', 'fomo'
    label                   TEXT NOT NULL,
    category                mechanism_category NOT NULL,
    psychological_logic     TEXT,
    hospitality_context     TEXT,
    operational_implication TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE mechanism_citations (
    id              SERIAL PRIMARY KEY,
    mechanism_id    INT NOT NULL REFERENCES behavioral_mechanisms(id) ON DELETE CASCADE,
    author          TEXT NOT NULL,
    year            INT,
    framework_name  TEXT NOT NULL,
    core_claim      TEXT,
    relevance       TEXT
);

CREATE TABLE mechanism_signals (
    id              SERIAL PRIMARY KEY,
    mechanism_id    INT NOT NULL REFERENCES behavioral_mechanisms(id) ON DELETE CASCADE,
    signal_type     TEXT NOT NULL CHECK (signal_type IN ('observable', 'measurable')),
    signal_text     TEXT NOT NULL
);

-- ---------------------------------------------------------------------------
-- LAYER 2: SEGMENT BEHAVIORAL PROFILES
-- ---------------------------------------------------------------------------

CREATE TABLE segment_behavioral_profiles (
    id                              SERIAL PRIMARY KEY,
    segment_key                     TEXT NOT NULL UNIQUE,  -- matches DB segment keys
    label                           TEXT NOT NULL,

    -- Spend composition (% of total check)
    food_pct_min                    INT,
    food_pct_max                    INT,
    alcohol_pct_min                 INT,
    alcohol_pct_max                 INT,
    dessert_attach_pct_min          INT,
    dessert_attach_pct_max          INT,

    -- Check vs baseline
    avg_check_vs_baseline_pct_min   INT,   -- e.g. 25 means +25% above baseline
    avg_check_vs_baseline_pct_max   INT,

    -- Alcohol
    alcohol_affinity                affinity_level NOT NULL DEFAULT 'low',
    alcohol_primary_driver          alcohol_driver NOT NULL DEFAULT 'none',
    alcohol_secondary_driver        alcohol_driver,
    beverage_preference             TEXT,

    -- Group dynamics
    peer_influence_coefficient      NUMERIC(3,2) NOT NULL,  -- 0.00 to 1.00
    group_revenue_impact_per_member TEXT,  -- e.g. '+40% per member (alcohol multiplier)'

    -- Dwell & economics (lunch / primary context)
    dwell_min_minutes               INT,
    dwell_max_minutes               INT,
    dwell_alt_min_minutes           INT,   -- dinner / secondary context
    dwell_alt_max_minutes           INT,
    dwell_alt_label                 TEXT,  -- e.g. 'after-work/dinner'
    revpash_min_inr                 INT,   -- ₹/hour/cover, primary context
    revpash_max_inr                 INT,
    revpash_alt_min_inr             INT,   -- secondary context
    revpash_alt_max_inr             INT,
    diminishing_returns_minutes     INT,
    revenue_curve                   revenue_curve_shape,

    -- Loyalty & discovery
    repeat_tendency_pct_min         INT,
    repeat_tendency_pct_max         INT,
    repeat_window_days              INT,
    discovery_rate                  discovery_rate NOT NULL DEFAULT 'medium',
    wom_multiplier_min              NUMERIC(3,1),
    wom_multiplier_max              NUMERIC(3,1),

    -- Psychological mechanisms (FK to behavioral_mechanisms)
    primary_mechanism_id            INT REFERENCES behavioral_mechanisms(id),
    secondary_mechanism_id          INT REFERENCES behavioral_mechanisms(id),

    -- Triggers
    primary_trigger                 TEXT,
    low_to_high_spend_trigger       TEXT,

    -- Dessert
    dessert_high_conversion_trigger TEXT,
    dessert_format_preference       TEXT,

    created_at                      TIMESTAMPTZ DEFAULT NOW()
);

-- Occasion-specific spend multipliers per segment
CREATE TABLE segment_occasion_multipliers (
    id              SERIAL PRIMARY KEY,
    segment_id      INT NOT NULL REFERENCES segment_behavioral_profiles(id) ON DELETE CASCADE,
    occasion_label  TEXT NOT NULL,   -- e.g. 'Client entertainment', 'Team celebration'
    multiplier_min  NUMERIC(4,2),    -- e.g. 1.40 = +40%
    multiplier_max  NUMERIC(4,2),
    notes           TEXT
);

-- Platform usage by segment
CREATE TABLE segment_platform_usage (
    id              SERIAL PRIMARY KEY,
    segment_id      INT NOT NULL REFERENCES segment_behavioral_profiles(id) ON DELETE CASCADE,
    platform        platform_name NOT NULL,
    usage_type      platform_usage_type NOT NULL,
    strength        signal_strength NOT NULL DEFAULT 'primary',
    notes           TEXT,
    UNIQUE (segment_id, platform, usage_type)
);

-- ---------------------------------------------------------------------------
-- LAYER 3: ARCHETYPE BEHAVIORAL PROFILES
-- ---------------------------------------------------------------------------

CREATE TABLE archetype_behavioral_profiles (
    id                              SERIAL PRIMARY KEY,
    archetype_key                   TEXT NOT NULL UNIQUE,  -- matches DB archetype keys
    label                           TEXT NOT NULL,
    orientation                     occasion_habit_orientation NOT NULL DEFAULT 'mixed',

    -- Spend composition
    food_pct_min                    INT,
    food_pct_max                    INT,
    alcohol_pct_min                 INT,
    alcohol_pct_max                 INT,
    dessert_attach_pct_min          INT,
    dessert_attach_pct_max          INT,

    -- Check vs baseline
    avg_check_vs_baseline_pct_min   INT,
    avg_check_vs_baseline_pct_max   INT,

    -- Alcohol
    alcohol_affinity                affinity_level NOT NULL DEFAULT 'low',
    alcohol_primary_driver          alcohol_driver NOT NULL DEFAULT 'none',
    beverage_preference             TEXT,

    -- Group dynamics
    peer_influence_coefficient      NUMERIC(3,2) NOT NULL,
    group_ordering_pattern          TEXT,

    -- Dwell & economics
    dwell_min_minutes               INT,
    dwell_max_minutes               INT,
    revpash_min_inr                 INT,
    revpash_max_inr                 INT,
    diminishing_returns_minutes     INT,

    -- Loyalty & discovery
    repeat_tendency_pct_min         INT,
    repeat_tendency_pct_max         INT,
    repeat_window_days              INT,
    discovery_rate                  discovery_rate NOT NULL DEFAULT 'medium',
    wom_multiplier_min              NUMERIC(3,1),
    wom_multiplier_max              NUMERIC(3,1),

    -- Psychological mechanisms
    primary_mechanism_id            INT REFERENCES behavioral_mechanisms(id),
    secondary_mechanism_id          INT REFERENCES behavioral_mechanisms(id),

    created_at                      TIMESTAMPTZ DEFAULT NOW()
);

-- Spend triggers + staff scripts per archetype
CREATE TABLE archetype_spend_triggers (
    id              SERIAL PRIMARY KEY,
    archetype_id    INT NOT NULL REFERENCES archetype_behavioral_profiles(id) ON DELETE CASCADE,
    trigger_rank    INT NOT NULL CHECK (trigger_rank IN (1, 2, 3)),  -- 1=primary, 2=secondary, 3=tertiary
    trigger_text    TEXT NOT NULL,
    staff_script    TEXT,
    UNIQUE (archetype_id, trigger_rank)
);

-- ---------------------------------------------------------------------------
-- LAYER 4: SEGMENT ↔ ARCHETYPE AFFINITY
-- ---------------------------------------------------------------------------

CREATE TABLE segment_archetype_affinity (
    id              SERIAL PRIMARY KEY,
    segment_id      INT NOT NULL REFERENCES segment_behavioral_profiles(id) ON DELETE CASCADE,
    archetype_id    INT NOT NULL REFERENCES archetype_behavioral_profiles(id) ON DELETE CASCADE,
    affinity_rank   INT NOT NULL CHECK (affinity_rank BETWEEN 1 AND 5),  -- 1 = primary
    UNIQUE (segment_id, archetype_id)
);

-- ---------------------------------------------------------------------------
-- LAYER 5: CHANNEL BENCHMARKS
-- ---------------------------------------------------------------------------

CREATE TABLE channel_benchmarks (
    id                      SERIAL PRIMARY KEY,
    channel_key             TEXT NOT NULL UNIQUE,
    label                   TEXT NOT NULL,
    open_rate_pct_min       INT,
    open_rate_pct_max       INT,
    repeat_visit_lift_pct   INT,   -- % higher repeat visits vs control
    roi_multiplier_min      NUMERIC(4,1),
    roi_multiplier_max      NUMERIC(4,1),
    order_uplift_pct_min    INT,
    order_uplift_pct_max    INT,
    primary_effect          TEXT,
    geographic_context      TEXT DEFAULT 'india',
    source_citation         TEXT,
    is_validated            BOOLEAN DEFAULT FALSE,
    validation_notes        TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Channel × Segment effectiveness matrix
CREATE TABLE channel_segment_effectiveness (
    id                  SERIAL PRIMARY KEY,
    channel_id          INT NOT NULL REFERENCES channel_benchmarks(id) ON DELETE CASCADE,
    segment_id          INT NOT NULL REFERENCES segment_behavioral_profiles(id) ON DELETE CASCADE,
    effectiveness_score INT NOT NULL CHECK (effectiveness_score BETWEEN 1 AND 5),
    primary_use_case    TEXT,
    notes               TEXT,
    UNIQUE (channel_id, segment_id)
);

-- ---------------------------------------------------------------------------
-- LAYER 6: TRAIT → FITNESS DIMENSION BRIDGE
-- ---------------------------------------------------------------------------
-- Maps behavioral signal types extracted from reviews to fitness dimensions.
-- Replaces hardcoded FITNESS_SIGNAL_MAP keywords in the pipeline.

CREATE TABLE trait_fitness_weights (
    id                  SERIAL PRIMARY KEY,
    trait_key           TEXT NOT NULL,   -- e.g. 'social_proof_signal', 'identity_signal'
    fitness_dimension   TEXT NOT NULL,   -- matches venue_fitness_dimensions column names
    weight              NUMERIC(4,3) NOT NULL CHECK (weight BETWEEN -1.0 AND 1.0),
    mechanism_id        INT REFERENCES behavioral_mechanisms(id),
    rationale           TEXT,
    UNIQUE (trait_key, fitness_dimension)
);

-- ---------------------------------------------------------------------------
-- LAYER 7: RESEARCH VALIDATION FLAGS
-- ---------------------------------------------------------------------------
-- Tracks known incorrect claims in the running system so they can be fixed.

CREATE TABLE research_validation_flags (
    id                  SERIAL PRIMARY KEY,
    entity_type         TEXT NOT NULL,   -- 'segment', 'archetype', 'channel', 'mechanism'
    entity_key          TEXT NOT NULL,
    field_name          TEXT NOT NULL,
    claimed_value       TEXT,
    validated_value     TEXT,
    validation_source   TEXT,
    is_corrected        BOOLEAN DEFAULT FALSE,
    correction_notes    TEXT,
    flagged_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- PEER INFLUENCE CROSS-REFERENCE VIEW
-- ---------------------------------------------------------------------------

CREATE VIEW peer_influence_matrix AS
SELECT
    'segment'   AS entity_type,
    segment_key AS entity_key,
    label,
    peer_influence_coefficient,
    group_revenue_impact_per_member AS revenue_impact,
    wom_multiplier_min,
    wom_multiplier_max
FROM segment_behavioral_profiles
UNION ALL
SELECT
    'archetype',
    archetype_key,
    label,
    peer_influence_coefficient,
    group_ordering_pattern,
    wom_multiplier_min,
    wom_multiplier_max
FROM archetype_behavioral_profiles
ORDER BY peer_influence_coefficient DESC;

-- ---------------------------------------------------------------------------
-- REVPASH ECONOMICS VIEW
-- ---------------------------------------------------------------------------

CREATE VIEW revpash_economics AS
SELECT
    segment_key,
    label,
    dwell_min_minutes,
    dwell_max_minutes,
    revpash_min_inr,
    revpash_max_inr,
    diminishing_returns_minutes,
    revenue_curve::TEXT AS revenue_curve_shape,
    repeat_tendency_pct_min,
    repeat_tendency_pct_max,
    repeat_window_days,
    wom_multiplier_min,
    wom_multiplier_max
FROM segment_behavioral_profiles
ORDER BY revpash_max_inr DESC NULLS LAST;

-- ---------------------------------------------------------------------------
-- INDEXES
-- ---------------------------------------------------------------------------

CREATE INDEX idx_segment_profiles_key ON segment_behavioral_profiles(segment_key);
CREATE INDEX idx_archetype_profiles_key ON archetype_behavioral_profiles(archetype_key);
CREATE INDEX idx_segment_archetype_segment ON segment_archetype_affinity(segment_id);
CREATE INDEX idx_segment_archetype_archetype ON segment_archetype_affinity(archetype_id);
CREATE INDEX idx_channel_benchmarks_key ON channel_benchmarks(channel_key);
CREATE INDEX idx_trait_fitness_trait ON trait_fitness_weights(trait_key);
CREATE INDEX idx_trait_fitness_dim ON trait_fitness_weights(fitness_dimension);
CREATE INDEX idx_mechanism_signals_type ON mechanism_signals(mechanism_id, signal_type);
