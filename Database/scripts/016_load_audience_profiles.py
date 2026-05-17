"""
016_load_audience_profiles.py
Creates and seeds 4 tables required by routers/audience.py.

Tables:
  1. segment_behavioral_profiles   — per-segment spend, dwell, WOM, trigger data
  2. archetype_behavioral_profiles — archetype key + label registry
  3. segment_archetype_affinity    — top archetypes per segment (ranked)
  4. segment_platform_usage        — platform discovery/validation/booking/review per segment

Source: behavioral_intelligence_module.md (Kimi, v1.0)
        Indian_FB_Consumer_Segmentation_Validation_Report.md
Run after: 011_load_demographics.py
Idempotent: safe to re-run.

Confidence levels used:
  VALIDATED  — peer influence coefficients (University of Illinois study)
  INFERRED   — platform usage patterns (Zomato/Swiggy India reports)
  SYNTHESIZED — RevPASH, spend composition, dwell estimates (framework-derived)
  HYPOTHESIS — archetype identities (internally constructed, not published-validated)
"""

import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'localhost'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', ''),
    'sslmode':  'require',
}


# ─── DDL ──────────────────────────────────────────────────────────────────────

DDL = """
CREATE TABLE IF NOT EXISTS segment_behavioral_profiles (
    id                              SERIAL PRIMARY KEY,
    segment_key                     TEXT        NOT NULL UNIQUE,
    label                           TEXT        NOT NULL,
    food_pct_min                    INT,
    food_pct_max                    INT,
    alcohol_pct_min                 INT,
    alcohol_pct_max                 INT,
    dessert_attach_pct_min          INT,
    dessert_attach_pct_max          INT,
    avg_check_vs_baseline_pct_min   INT,
    avg_check_vs_baseline_pct_max   INT,
    alcohol_affinity                TEXT,
    alcohol_primary_driver          TEXT,
    beverage_preference             TEXT,
    peer_influence_coefficient      NUMERIC(4,2),
    dwell_min_minutes               INT,
    dwell_max_minutes               INT,
    revpash_min_inr                 INT,
    revpash_max_inr                 INT,
    diminishing_returns_minutes     INT,
    repeat_tendency_pct_min         INT,
    repeat_tendency_pct_max         INT,
    repeat_window_days              INT,
    wom_multiplier_min              NUMERIC(4,2),
    wom_multiplier_max              NUMERIC(4,2),
    discovery_rate                  TEXT,
    primary_trigger                 TEXT,
    low_to_high_spend_trigger       TEXT,
    confidence_level                VARCHAR(20) DEFAULT 'SYNTHESIZED'
);

CREATE TABLE IF NOT EXISTS archetype_behavioral_profiles (
    id               SERIAL PRIMARY KEY,
    archetype_key    TEXT        NOT NULL UNIQUE,
    label            TEXT        NOT NULL,
    confidence_level VARCHAR(20) DEFAULT 'HYPOTHESIS'
);

CREATE TABLE IF NOT EXISTS segment_archetype_affinity (
    id            SERIAL PRIMARY KEY,
    segment_id    INT NOT NULL REFERENCES segment_behavioral_profiles(id) ON DELETE CASCADE,
    archetype_id  INT NOT NULL REFERENCES archetype_behavioral_profiles(id) ON DELETE CASCADE,
    affinity_rank INT NOT NULL,
    UNIQUE (segment_id, archetype_id)
);

CREATE TABLE IF NOT EXISTS segment_platform_usage (
    id          SERIAL PRIMARY KEY,
    segment_id  INT  NOT NULL REFERENCES segment_behavioral_profiles(id) ON DELETE CASCADE,
    platform    TEXT NOT NULL,
    usage_type  TEXT NOT NULL,
    strength    TEXT NOT NULL,
    UNIQUE (segment_id, platform, usage_type)
);
"""


# ─── 1. SEGMENT BEHAVIORAL PROFILES ──────────────────────────────────────────
# Source: behavioral_intelligence_module.md Section 1
# segment_key must match vds.segment_id values in venue_demographic_scores

SEGMENT_PROFILES = [
    {
        'segment_key':                   'office_workers',
        'label':                         'Office Workers',
        # Spend composition (% of check)
        'food_pct_min':                  65,
        'food_pct_max':                  70,
        'alcohol_pct_min':               15,
        'alcohol_pct_max':               22,
        'dessert_attach_pct_min':        12,
        'dessert_attach_pct_max':        18,
        'avg_check_vs_baseline_pct_min': 0,
        'avg_check_vs_baseline_pct_max': 15,
        # Alcohol
        'alcohol_affinity':              'low_medium',
        'alcohol_primary_driver':        'habit',
        'beverage_preference':           'Beer, whisky',
        # Group dynamics — VALIDATED (University of Illinois peer influence study)
        'peer_influence_coefficient':    0.30,
        # Dwell economics (lunch window; primary visit occasion)
        'dwell_min_minutes':             35,
        'dwell_max_minutes':             50,
        'revpash_min_inr':               180,
        'revpash_max_inr':               250,
        'diminishing_returns_minutes':   60,
        # Loyalty
        'repeat_tendency_pct_min':       60,
        'repeat_tendency_pct_max':       70,
        'repeat_window_days':            30,
        'wom_multiplier_min':            1.2,
        'wom_multiplier_max':            1.5,
        'discovery_rate':                'low',
        # Triggers
        'primary_trigger':               'Convenience (proximity to office) + Habit (routine lunch spot)',
        'low_to_high_spend_trigger':     '"Client is joining" identity shift; staff recognition by name (belonging cue); lunch combo upgrade to premium protein',
        'confidence_level':              'SYNTHESIZED',
    },
    {
        'segment_key':                   'college_kids',
        'label':                         'College Students',
        # Drink-heavy: 55-65% of check is alcohol
        'food_pct_min':                  20,
        'food_pct_max':                  28,
        'alcohol_pct_min':               55,
        'alcohol_pct_max':               65,
        'dessert_attach_pct_min':        22,
        'dessert_attach_pct_max':        28,
        'avg_check_vs_baseline_pct_min': 40,
        'avg_check_vs_baseline_pct_max': 80,
        'alcohol_affinity':              'high',
        'alcohol_primary_driver':        'social_occasion',
        'beverage_preference':           'Cocktails, shots, beer buckets',
        # VALIDATED
        'peer_influence_coefficient':    0.70,
        'dwell_min_minutes':             120,
        'dwell_max_minutes':             180,
        'revpash_min_inr':               400,
        'revpash_max_inr':               600,
        'diminishing_returns_minutes':   150,
        'repeat_tendency_pct_min':       20,
        'repeat_tendency_pct_max':       30,
        'repeat_window_days':            90,
        'wom_multiplier_min':            3.5,
        'wom_multiplier_max':            4.5,
        'discovery_rate':                'high',
        'primary_trigger':               'Peer plan (group chat coordination) + Occasion (birthday, promotion, weekend)',
        'low_to_high_spend_trigger':     'First round anchor (premium cocktail by alpha sets table spend); "last round" scarcity nudge; group bundle discount on bottles',
        'confidence_level':              'SYNTHESIZED',
    },
    {
        'segment_key':                   'couples',
        'label':                         'Couples',
        # Balanced: ~40-50% food, ~20-30% alcohol, high dessert attach
        'food_pct_min':                  40,
        'food_pct_max':                  50,
        'alcohol_pct_min':               18,
        'alcohol_pct_max':               28,
        'dessert_attach_pct_min':        35,
        'dessert_attach_pct_max':        45,
        'avg_check_vs_baseline_pct_min': 25,
        'avg_check_vs_baseline_pct_max': 50,
        'alcohol_affinity':              'medium',
        'alcohol_primary_driver':        'identity',
        'beverage_preference':           'Wine, cocktails',
        # VALIDATED
        'peer_influence_coefficient':    0.50,
        'dwell_min_minutes':             90,
        'dwell_max_minutes':             120,
        'revpash_min_inr':               350,
        'revpash_max_inr':               500,
        'diminishing_returns_minutes':   105,
        'repeat_tendency_pct_min':       40,
        'repeat_tendency_pct_max':       50,
        'repeat_window_days':            60,
        'wom_multiplier_min':            2.0,
        'wom_multiplier_max':            2.5,
        'discovery_rate':                'medium',
        'primary_trigger':               'Occasion (anniversary, birthday, date night ritual) + Habit (weekly date night spot)',
        'low_to_high_spend_trigger':     '"Chef\'s special for two" framing; wine pairing suggestion; dessert presented as "perfect way to end the evening"',
        'confidence_level':              'SYNTHESIZED',
    },
    {
        'segment_key':                   'families',
        'label':                         'Families',
        # Food-heavy (includes kid food + dessert); very low alcohol
        'food_pct_min':                  75,
        'food_pct_max':                  80,
        'alcohol_pct_min':               8,
        'alcohol_pct_max':               12,
        'dessert_attach_pct_min':        40,
        'dessert_attach_pct_max':        50,
        'avg_check_vs_baseline_pct_min': 10,
        'avg_check_vs_baseline_pct_max': 30,
        'alcohol_affinity':              'low_medium',
        'alcohol_primary_driver':        'habit',
        'beverage_preference':           'Beer, wine (1-2 only); soft drinks for children',
        # VALIDATED
        'peer_influence_coefficient':    0.40,
        'dwell_min_minutes':             60,
        'dwell_max_minutes':             90,
        'revpash_min_inr':               200,
        'revpash_max_inr':               300,
        'diminishing_returns_minutes':   75,
        'repeat_tendency_pct_min':       50,
        'repeat_tendency_pct_max':       60,
        'repeat_window_days':            30,
        'wom_multiplier_min':            1.5,
        'wom_multiplier_max':            2.0,
        'discovery_rate':                'low',
        'primary_trigger':               'Habit (Sunday lunch tradition) + Convenience (kid-friendly menu, high chairs, parking)',
        'low_to_high_spend_trigger':     '"Family feast" bundle (perceived value); kids\' activity pack upsell; dessert presented as reward for children\'s patience',
        'confidence_level':              'SYNTHESIZED',
    },
    {
        'segment_key':                   'premium',
        'label':                         'Premium Diners',
        # Wine drives 40-50% of check; food ~35-45%
        'food_pct_min':                  35,
        'food_pct_max':                  45,
        'alcohol_pct_min':               40,
        'alcohol_pct_max':               50,
        'dessert_attach_pct_min':        50,
        'dessert_attach_pct_max':        65,
        'avg_check_vs_baseline_pct_min': 150,
        'avg_check_vs_baseline_pct_max': 300,
        'alcohol_affinity':              'high',
        'alcohol_primary_driver':        'identity',
        'beverage_preference':           'Wine (red dominant), single malts, craft cocktails',
        # VALIDATED
        'peer_influence_coefficient':    0.20,
        'dwell_min_minutes':             120,
        'dwell_max_minutes':             180,
        'revpash_min_inr':               800,
        'revpash_max_inr':               1500,
        'diminishing_returns_minutes':   150,
        'repeat_tendency_pct_min':       30,
        'repeat_tendency_pct_max':       40,
        'repeat_window_days':            90,
        'wom_multiplier_min':            3.0,
        'wom_multiplier_max':            3.5,
        'discovery_rate':                'medium',
        'primary_trigger':               'Occasion (celebration, business deal, milestone) + Identity (venue as extension of self-image)',
        'low_to_high_spend_trigger':     'Sommelier recommendation with story; chef\'s table exclusivity framing; limited vintage availability; anchoring with highest-price item first',
        'confidence_level':              'SYNTHESIZED',
    },
    {
        'segment_key':                   'solo_diners',
        'label':                         'Solo Diners',
        # Single-cover efficiency; no sharing economy loss
        'food_pct_min':                  70,
        'food_pct_max':                  75,
        'alcohol_pct_min':               12,
        'alcohol_pct_max':               18,
        'dessert_attach_pct_min':        18,
        'dessert_attach_pct_max':        25,
        'avg_check_vs_baseline_pct_min': -10,
        'avg_check_vs_baseline_pct_max': 0,
        'alcohol_affinity':              'low_medium',
        'alcohol_primary_driver':        'habit',
        'beverage_preference':           'Beer, wine by glass',
        # Peer influence: 0.0 — no table peers (VALIDATED by definition)
        'peer_influence_coefficient':    0.00,
        'dwell_min_minutes':             30,
        'dwell_max_minutes':             50,
        'revpash_min_inr':               250,
        'revpash_max_inr':               400,
        'diminishing_returns_minutes':   45,
        'repeat_tendency_pct_min':       25,
        'repeat_tendency_pct_max':       35,
        'repeat_window_days':            60,
        'wom_multiplier_min':            2.2,
        'wom_multiplier_max':            2.5,
        # Highest discovery rate of all segments (experimental, low coordination cost)
        'discovery_rate':                'very_high',
        'primary_trigger':               'Habit (regular solo lunch/dinner) + Discovery (trying new place alone) + Convenience (quick solo seat at bar)',
        'low_to_high_spend_trigger':     'Bartender rapport and recommendation; chef\'s special exclusivity; bar counter seat with kitchen view (experience upgrade)',
        'confidence_level':              'INFERRED',
    },
    {
        'segment_key':                   'working_women',
        'label':                         'Working Women',
        # Balanced, health-conscious; zero-proof options relevant
        'food_pct_min':                  50,
        'food_pct_max':                  55,
        'alcohol_pct_min':               18,
        'alcohol_pct_max':               25,
        'dessert_attach_pct_min':        25,
        'dessert_attach_pct_max':        32,
        'avg_check_vs_baseline_pct_min': 15,
        'avg_check_vs_baseline_pct_max': 35,
        'alcohol_affinity':              'medium',
        'alcohol_primary_driver':        'identity',
        'beverage_preference':           'Wine, gin cocktails, zero-proof options',
        # VALIDATED (university peer influence study extended to female professional groups)
        'peer_influence_coefficient':    0.60,
        # Using group dwell as primary window
        'dwell_min_minutes':             45,
        'dwell_max_minutes':             105,
        'revpash_min_inr':               200,
        'revpash_max_inr':               500,
        'diminishing_returns_minutes':   90,
        'repeat_tendency_pct_min':       40,
        'repeat_tendency_pct_max':       50,
        'repeat_window_days':            60,
        'wom_multiplier_min':            2.8,
        'wom_multiplier_max':            3.2,
        'discovery_rate':                'medium_high',
        'primary_trigger':               'Peer plan (group coordination) + Habit (regular after-work spot) + Discovery (new "safe" venue)',
        'low_to_high_spend_trigger':     '"Wellness" positioning of premium items; zero-proof cocktail menu (identity-aligned); "guilt-free" dessert framing',
        'confidence_level':              'SYNTHESIZED',
    },
]


# ─── 2. ARCHETYPE PROFILES ────────────────────────────────────────────────────
# Source: behavioral_intelligence_module.md Section 2
# Archetypes are internally constructed — confidence: HYPOTHESIS
# (per Indian_FB_Consumer_Segmentation_Validation_Report.md finding)

ARCHETYPE_PROFILES = [
    {'archetype_key': 'party_seeker',         'label': 'Party Seeker'},
    {'archetype_key': 'scene_seeker',          'label': 'Scene Seeker'},
    {'archetype_key': 'trusted_regular',       'label': 'Trusted Regular'},
    {'archetype_key': 'habit_former',          'label': 'Habit Former'},
    {'archetype_key': 'calm_pairs',            'label': 'Calm Pairs'},
    {'archetype_key': 'lifestyle_regular',     'label': 'Lifestyle Regular'},
    {'archetype_key': 'quiet_discoverer',      'label': 'Quiet Discoverer'},
    {'archetype_key': 'trend_hunter',          'label': 'Trend Hunter'},
    {'archetype_key': 'premium_prioritizer',   'label': 'Premium Prioritizer'},
    {'archetype_key': 'discovery_explorer',    'label': 'Discovery Explorer'},
]


# ─── 3. SEGMENT → ARCHETYPE AFFINITY ─────────────────────────────────────────
# Source: behavioral_intelligence_module.md Section 1 "Archetype alignment" per segment
# rank 1 = dominant archetype; rank 2 = secondary
# audience.py loads rank <= 2 only

AFFINITY_DATA = [
    # segment_key           archetype_key           rank
    ('office_workers',      'habit_former',             1),
    ('office_workers',      'trusted_regular',          2),

    ('college_kids',        'party_seeker',             1),
    ('college_kids',        'scene_seeker',             2),

    ('couples',             'calm_pairs',               1),
    ('couples',             'quiet_discoverer',         2),

    ('families',            'habit_former',             1),
    ('families',            'lifestyle_regular',        2),

    ('premium',             'premium_prioritizer',      1),
    ('premium',             'trusted_regular',          2),

    ('solo_diners',         'quiet_discoverer',         1),
    ('solo_diners',         'habit_former',             2),

    ('working_women',       'lifestyle_regular',        1),
    ('working_women',       'trusted_regular',          2),
]


# ─── 4. PLATFORM USAGE ───────────────────────────────────────────────────────
# Source: behavioral_intelligence_module.md Section 3D
# Columns: (segment_key, platform, usage_type, strength)
# platform: instagram | zomato | swiggy | swiggy_dineout | zomato_gold |
#           google_maps | google_reviews | direct | word_of_mouth
# usage_type: discovery | validation | booking | review | wom
# strength: primary | secondary | tertiary

PLATFORM_DATA = [
    # ── Office Workers ──────────────────────────────────────────────────────
    ('office_workers', 'google_maps',   'discovery',        'primary'),
    ('office_workers', 'zomato',        'validation',       'primary'),
    ('office_workers', 'zomato',        'booking',          'primary'),
    ('office_workers', 'swiggy',        'booking',          'secondary'),
    ('office_workers', 'zomato',        'post_visit_review','primary'),
    ('office_workers', 'word_of_mouth', 'wom',              'primary'),

    # ── College Students (Social Crowd) ─────────────────────────────────────
    ('college_kids', 'instagram',       'discovery',        'primary'),
    ('college_kids', 'zomato',          'validation',       'primary'),
    ('college_kids', 'zomato',          'booking',          'primary'),
    ('college_kids', 'swiggy_dineout',  'booking',          'secondary'),
    ('college_kids', 'instagram',       'post_visit_review','primary'),
    ('college_kids', 'word_of_mouth',   'wom',              'primary'),

    # ── Couples ─────────────────────────────────────────────────────────────
    ('couples', 'instagram',            'discovery',        'primary'),
    ('couples', 'google_reviews',       'validation',       'primary'),
    ('couples', 'zomato',               'booking',          'primary'),
    ('couples', 'zomato',               'post_visit_review','primary'),
    ('couples', 'instagram',            'post_visit_review','secondary'),
    ('couples', 'word_of_mouth',        'wom',              'primary'),

    # ── Families ────────────────────────────────────────────────────────────
    ('families', 'zomato',              'discovery',        'primary'),
    ('families', 'google_maps',         'validation',       'primary'),
    ('families', 'zomato',              'booking',          'primary'),
    ('families', 'zomato',              'post_visit_review','primary'),
    ('families', 'word_of_mouth',       'wom',              'primary'),

    # ── Premium Diners ───────────────────────────────────────────────────────
    ('premium', 'google_maps',          'discovery',        'primary'),
    ('premium', 'word_of_mouth',        'discovery',        'secondary'),
    ('premium', 'zomato',               'validation',       'primary'),
    ('premium', 'google_reviews',       'validation',       'secondary'),
    ('premium', 'direct',               'booking',          'primary'),
    ('premium', 'zomato_gold',          'booking',          'secondary'),
    ('premium', 'zomato',               'post_visit_review','primary'),
    ('premium', 'instagram',            'post_visit_review','secondary'),
    ('premium', 'word_of_mouth',        'wom',              'primary'),

    # ── Solo Diners ──────────────────────────────────────────────────────────
    ('solo_diners', 'zomato',           'discovery',        'primary'),
    ('solo_diners', 'google_maps',      'discovery',        'secondary'),
    ('solo_diners', 'zomato',           'validation',       'primary'),
    ('solo_diners', 'zomato',           'booking',          'primary'),
    ('solo_diners', 'zomato',           'post_visit_review','primary'),
    ('solo_diners', 'word_of_mouth',    'wom',              'secondary'),

    # ── Working Women ────────────────────────────────────────────────────────
    ('working_women', 'instagram',      'discovery',        'primary'),
    ('working_women', 'zomato',         'validation',       'primary'),
    ('working_women', 'google_reviews', 'validation',       'secondary'),
    ('working_women', 'zomato',         'booking',          'primary'),
    ('working_women', 'swiggy',         'booking',          'secondary'),
    ('working_women', 'instagram',      'post_visit_review','primary'),
    ('working_women', 'zomato',         'post_visit_review','secondary'),
    ('working_women', 'word_of_mouth',  'wom',              'primary'),
]


# ─── LOADERS ─────────────────────────────────────────────────────────────────

def create_tables(cursor) -> None:
    cursor.execute(DDL)


def load_segments(cursor) -> dict[str, int]:
    """Insert segment profiles; return {segment_key: id} map."""
    sql = """
        INSERT INTO segment_behavioral_profiles (
            segment_key, label,
            food_pct_min, food_pct_max,
            alcohol_pct_min, alcohol_pct_max,
            dessert_attach_pct_min, dessert_attach_pct_max,
            avg_check_vs_baseline_pct_min, avg_check_vs_baseline_pct_max,
            alcohol_affinity, alcohol_primary_driver, beverage_preference,
            peer_influence_coefficient,
            dwell_min_minutes, dwell_max_minutes,
            revpash_min_inr, revpash_max_inr, diminishing_returns_minutes,
            repeat_tendency_pct_min, repeat_tendency_pct_max, repeat_window_days,
            wom_multiplier_min, wom_multiplier_max,
            discovery_rate, primary_trigger, low_to_high_spend_trigger,
            confidence_level
        ) VALUES (
            %(segment_key)s, %(label)s,
            %(food_pct_min)s, %(food_pct_max)s,
            %(alcohol_pct_min)s, %(alcohol_pct_max)s,
            %(dessert_attach_pct_min)s, %(dessert_attach_pct_max)s,
            %(avg_check_vs_baseline_pct_min)s, %(avg_check_vs_baseline_pct_max)s,
            %(alcohol_affinity)s, %(alcohol_primary_driver)s, %(beverage_preference)s,
            %(peer_influence_coefficient)s,
            %(dwell_min_minutes)s, %(dwell_max_minutes)s,
            %(revpash_min_inr)s, %(revpash_max_inr)s, %(diminishing_returns_minutes)s,
            %(repeat_tendency_pct_min)s, %(repeat_tendency_pct_max)s, %(repeat_window_days)s,
            %(wom_multiplier_min)s, %(wom_multiplier_max)s,
            %(discovery_rate)s, %(primary_trigger)s, %(low_to_high_spend_trigger)s,
            %(confidence_level)s
        )
        ON CONFLICT (segment_key) DO UPDATE SET
            label                           = EXCLUDED.label,
            food_pct_min                    = EXCLUDED.food_pct_min,
            food_pct_max                    = EXCLUDED.food_pct_max,
            alcohol_pct_min                 = EXCLUDED.alcohol_pct_min,
            alcohol_pct_max                 = EXCLUDED.alcohol_pct_max,
            dessert_attach_pct_min          = EXCLUDED.dessert_attach_pct_min,
            dessert_attach_pct_max          = EXCLUDED.dessert_attach_pct_max,
            avg_check_vs_baseline_pct_min   = EXCLUDED.avg_check_vs_baseline_pct_min,
            avg_check_vs_baseline_pct_max   = EXCLUDED.avg_check_vs_baseline_pct_max,
            alcohol_affinity                = EXCLUDED.alcohol_affinity,
            alcohol_primary_driver          = EXCLUDED.alcohol_primary_driver,
            beverage_preference             = EXCLUDED.beverage_preference,
            peer_influence_coefficient      = EXCLUDED.peer_influence_coefficient,
            dwell_min_minutes               = EXCLUDED.dwell_min_minutes,
            dwell_max_minutes               = EXCLUDED.dwell_max_minutes,
            revpash_min_inr                 = EXCLUDED.revpash_min_inr,
            revpash_max_inr                 = EXCLUDED.revpash_max_inr,
            diminishing_returns_minutes     = EXCLUDED.diminishing_returns_minutes,
            repeat_tendency_pct_min         = EXCLUDED.repeat_tendency_pct_min,
            repeat_tendency_pct_max         = EXCLUDED.repeat_tendency_pct_max,
            repeat_window_days              = EXCLUDED.repeat_window_days,
            wom_multiplier_min              = EXCLUDED.wom_multiplier_min,
            wom_multiplier_max              = EXCLUDED.wom_multiplier_max,
            discovery_rate                  = EXCLUDED.discovery_rate,
            primary_trigger                 = EXCLUDED.primary_trigger,
            low_to_high_spend_trigger       = EXCLUDED.low_to_high_spend_trigger,
            confidence_level                = EXCLUDED.confidence_level
        RETURNING id
    """
    seg_id_map: dict[str, int] = {}
    for seg in SEGMENT_PROFILES:
        cursor.execute(sql, seg)
        seg_id_map[seg['segment_key']] = cursor.fetchone()[0]
    return seg_id_map


def load_archetypes(cursor) -> dict[str, int]:
    """Insert archetype registry; return {archetype_key: id} map."""
    sql = """
        INSERT INTO archetype_behavioral_profiles (archetype_key, label, confidence_level)
        VALUES (%(archetype_key)s, %(label)s, 'HYPOTHESIS')
        ON CONFLICT (archetype_key) DO UPDATE SET
            label            = EXCLUDED.label,
            confidence_level = EXCLUDED.confidence_level
        RETURNING id
    """
    arc_id_map: dict[str, int] = {}
    for arc in ARCHETYPE_PROFILES:
        cursor.execute(sql, arc)
        arc_id_map[arc['archetype_key']] = cursor.fetchone()[0]
    return arc_id_map


def load_affinity(cursor, seg_id_map: dict[str, int], arc_id_map: dict[str, int]) -> int:
    """Insert segment↔archetype affinity ranks."""
    sql = """
        INSERT INTO segment_archetype_affinity (segment_id, archetype_id, affinity_rank)
        VALUES %s
        ON CONFLICT (segment_id, archetype_id) DO UPDATE SET
            affinity_rank = EXCLUDED.affinity_rank
    """
    rows = []
    for seg_key, arc_key, rank in AFFINITY_DATA:
        seg_id = seg_id_map.get(seg_key)
        arc_id = arc_id_map.get(arc_key)
        if seg_id and arc_id:
            rows.append((seg_id, arc_id, rank))
        else:
            print(f"  [WARN] affinity: unknown segment '{seg_key}' or archetype '{arc_key}'")
    psycopg2.extras.execute_values(cursor, sql, rows)
    return len(rows)


def load_platform_usage(cursor, seg_id_map: dict[str, int]) -> int:
    """Insert platform usage rows per segment."""
    sql = """
        INSERT INTO segment_platform_usage (segment_id, platform, usage_type, strength)
        VALUES %s
        ON CONFLICT (segment_id, platform, usage_type) DO UPDATE SET
            strength = EXCLUDED.strength
    """
    rows = []
    for seg_key, platform, usage_type, strength in PLATFORM_DATA:
        seg_id = seg_id_map.get(seg_key)
        if seg_id:
            rows.append((seg_id, platform, usage_type, strength))
        else:
            print(f"  [WARN] platform: unknown segment '{seg_key}'")
    psycopg2.extras.execute_values(cursor, sql, rows)
    return len(rows)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("\n016_load_audience_profiles.py — Audience Behavioral Intelligence Tables\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        print("  [DDL] Creating tables if not exist ...")
        create_tables(cursor)
        print("        segment_behavioral_profiles, archetype_behavioral_profiles,")
        print("        segment_archetype_affinity, segment_platform_usage")

        print("\n  [1/4] segment_behavioral_profiles ...")
        seg_id_map = load_segments(cursor)
        print(f"        {len(seg_id_map)} segments: {', '.join(seg_id_map.keys())}")

        print("  [2/4] archetype_behavioral_profiles ...")
        arc_id_map = load_archetypes(cursor)
        print(f"        {len(arc_id_map)} archetypes loaded")

        print("  [3/4] segment_archetype_affinity ...")
        n_aff = load_affinity(cursor, seg_id_map, arc_id_map)
        print(f"        {n_aff} affinity rows (top 2 archetypes per segment)")

        print("  [4/4] segment_platform_usage ...")
        n_plat = load_platform_usage(cursor, seg_id_map)
        print(f"        {n_plat} platform usage rows")

        conn.commit()
        print("\n" + "=" * 60)
        print("  AUDIENCE PROFILES COMPLETE")
        print(f"  Segments   : {len(SEGMENT_PROFILES)}")
        print(f"  Archetypes : {len(ARCHETYPE_PROFILES)}")
        print(f"  Affinity   : {n_aff}")
        print(f"  Platforms  : {n_plat}")
        print("=" * 60)
        print("\n  /api/venues/{id}/audience is now unblocked.\n")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
