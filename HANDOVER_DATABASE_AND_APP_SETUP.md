# Handover: Database & App Setup — Polynovea Module 2
**Date:** 2026-05-14
**Version:** 2.0 — Pipeline complete
**Status:** ✅ DB fully loaded — all 14 scripts complete — ready for FastAPI + Next.js build
**Working Directory:** `D:\PolyNovea\PolyNovea\Docx\Company Docx\Acquistion System`

---

## ✅ DATABASE STATUS — ALL 14 SCRIPTS COMPLETE

**RDS Endpoint:** `polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com`
**DB Name:** `polynovea_module2`
**Credentials:** `.env` file at `Database/.env`
**Pipeline Runner:** `Database/scripts/run_pipeline.py`

| Script | Tables Created | Rows |
|--------|---------------|------|
| 002_load_venues.py | `venues` | 6,007 |
| 003_load_patterns.py | `behavioral_patterns` + `venue_pattern_links` | 5,042 + 26,871 |
| 004_load_scores.py | `venue_fitness_dimensions` + `intervention_triggers` | 6,007 + 24,028 |
| 005_load_similarity.py | `venue_vectors` + `venue_similarity` | 5,758 + 146,426 |
| 006_load_pattern_scores.py | `pattern_confidence_scores` | 5,042 |
| 007_load_governance.py | `drift_signals` + `data_quality_metrics` | 5,042 |
| 008_load_surveys.py | `survey_responses` + `user_archetypes` | 42 + 42 |
| 009_load_marketing_engine.py | `behavioral_mechanism_catalog` + `channel_mechanism_mapping` + `campaign_templates` | 5 + 25 + 13 |
| 010_load_primitives.py | `primitives_scores` | 23,821 |
| 011_load_demographics.py | `demographic_segments` + `archetype_mappings` + `alignments` + `interventions` | 5 + 23 + 9 + 10 |
| 012_compute_venue_demographics.py | `venue_demographic_scores` + `venue_similarity.rank` | 30,035 + 146,426 ranked |
| 013_compute_fitness_deltas.py | `fitness_delta_rules` + `venue_similarity_deltas` | 56 + 1,171,408 |
| 014_create_optional_scaffolds.py | `venue_platform_data` + `venue_pos_summary` + `platform_performance_benchmarks` | scaffolds (empty, populate on opt-in) |

**To re-run the full pipeline:**
```powershell
# Load .env then run:
$env:PG_HOST='polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'
$env:PG_DB='polynovea_module2'
$env:PG_USER='polynovea_admin'
$env:PG_PASSWORD='<from .env>'
python Database/scripts/run_pipeline.py              # full pipeline
python Database/scripts/run_pipeline.py --from 12   # resume from script 12
python Database/scripts/run_pipeline.py --only 14   # run single script
```

**Note:** The SQL ingestion scripts documented later in this file (`005_load_venues_from_step1.sql`, etc.) are **superseded by the Python pipeline above**. They are kept for reference only — do not run them.

---

## 📁 FOLDER STRUCTURE

```
D:\PolyNovea\PolyNovea\Docx\Company Docx\Acquistion System\  ← YOU ARE HERE (clean, organized)
│
├── config/
│   ├── primitives.json              ← 54 behavioral signals (core registry)
│   ├── surface_categories.json       ← 7 venue types + fitness weights
│   ├── constants.py                 ← API masks, keywords, thresholds
│   ├── schema.json                  ← PostgreSQL table definitions
│   ├── version_control.json          ← Form version tracking
│   ├── temporal_filters.json         ← Recency weighting rules
│   ├── confidence_thresholds.json    ← Quality scores per source
│   ├── cross_primitive_rules.json    ← Constraint rules
│   └── survey_canonical_schema.json  ✅ CREATED
│
├── data/
│   ├── raw/
│   │   ├── google_places/
│   │   │   ├── navi-mumbai/
│   │   │   │   ├── step_1_venues_refined.json (venue names + locations)
│   │   │   │   ├── step_4_patterns_recognized.json (behavioral patterns)
│   │   │   │   ├── step_4b_governance_report.json (data quality metrics)
│   │   │   │   ├── step_5_behavioral_scores.json (behavioral vectors + fitness)
│   │   │   │   └── step_5b_similarity.json (similar venue rankings)
│   │   │   ├── mumbai-main/ (same 5 files)
│   │   │   ├── mumbai-sobo/ (same 5 files)
│   │   │   └── thane/ (same 5 files)
│   │   ├── zomato/                  ← Future (Phase 2)
│   │   ├── magicpin/                ← Future (Phase 2)
│   │   └── surveys/
│   │       ├── form_v1_responses.csv (9 responses)
│   │       ├── form_v2_responses.csv (36 responses)
│   │       ├── survey_responses_normalized.csv ✅ CREATED
│   │       └── canonical_schema.json ✅ CREATED
│   │
│   ├── processed/
│   │   ├── venues_enriched.json
│   │   ├── user_archetypes.json
│   │   ├── primitives_scores_google.json
│   │   ├── primitives_scores_zomato.json
│   │   └── primitives_scores_magicpin.json
│   │
│   └── vectors/
│       ├── venue_vectors_stability.json    ← Long-term behavior
│       └── venue_vectors_realtime.json     ← Current vibe
│
└── sql/
    ├── 001_init_schema.sql          ← Create all tables
    ├── 002_load_venues.sql
    ├── 003_load_reviews.sql
    └── 004_load_surveys.sql


D:\PolyNovea\Module 2\Google Places API\data\   ← SOURCE FOR VENUE DATA (CURRENT)
├── navi-mumbai/                     922 venues ✅
│   ├── step_1_venues_refined.json   (name, place_id, location, area, types)
│   ├── step_5_behavioral_scores.json
│   ├── step_5b_similarity.json
│   └── step_4_patterns_recognized.json
│
├── mumbai/main/                     3,558 venues ✅
│   ├── step_1_venues_refined.json
│   ├── step_5_behavioral_scores.json
│   ├── step_5b_similarity.json
│   └── step_4_patterns_recognized.json
│
├── mumbai/sobo/                     1,269 venues ✅
│   ├── step_1_venues_refined.json
│   ├── step_5_behavioral_scores.json
│   ├── step_5b_similarity.json
│   └── step_4_patterns_recognized.json
│
└── thane/                           515 venues ✅
    ├── step_1_venues_refined.json
    ├── step_5_behavioral_scores.json
    ├── step_5b_similarity.json
    └── step_4_patterns_recognized.json

**TOTAL DATA: 6,264 venues across 4 cities** ✅

[Ignore: Behavioral Framework, Venue Intelligence, Research Framework — outdated/legacy]
```

---

## 🎯 FEATURES: 16 BASE + 19 ADS-ENABLED = 35 TOTAL

### NOW (Phase 1-6): Build all 16 features in ONE sprint

```
Features 1-2:   Venue Comparison
├─ 1. Similar Venues Comparison     (your idea)
└─ 2. Consulting Redirect            (your idea)

Features 3-12:  Core Intelligence (8 features)
├─ 3.  Personalized Recommendations
├─ 4.  Churn Risk Scoring
├─ 5.  Archetype Segmentation
├─ 6.  Conflict Detection
├─ 7.  Satisfaction Drivers
├─ 8.  Pricing Power Analysis
├─ 9.  Cross-Venue Synergy
├─ 10. Competitive Benchmarking
├─ 11. Friction Funnel
└─ 12. Cohort Retention

Features 13-16: Foundation for Ads (4 features)
├─ 13. Content Recommendation
├─ 14. Real-Time Dynamic Recommendations
├─ 15. Operational Simulation
└─ 16. Trend Detection & Forecasting
```

### LATER (Phase 7+): When you add ads & marketing data, unlock 19 more

```
Features 17-24: Attribution & Spend Optimization (8 features)
├─ 17. Attribution Intelligence       (which source brought user?)
├─ 18. Archetype Performance          (ROI by user type)
├─ 19. Creative Optimization          (which creatives work for which archetype?)
├─ 20. Audience Expansion             (find similar users to convert)
├─ 21. Budget Allocation              (where to spend?)
├─ 22. Funnel Analysis               (where do users drop?)
├─ 23. Real-Time Bidding             (dynamic spend adjustment)
└─ 24. Seasonal / Cyclical Modeling   (predict demand waves)

Features 25-35: Advanced Targeting (11 features)
├─ 25. Competitor Intelligence       (what are they doing?)
├─ 26. Cross-Channel Attribution     (Google + Zomato + MagicPin ROI)
├─ 27. LTV by Source                 (lifetime value per acquisition channel)
├─ 28. Content Pairing               (which content + venue combo converts?)
├─ 29. Viral Coefficient             (growth loop modeling)
├─ 30. Dynamic Creative              (personalized ad creative)
├─ 31. Suppression Lists             (don't show ads to churned users)
├─ 32. Lookalike Audiences           (find users like your best customers)
├─ 33. Geo Micro-Targeting           (location-based acquisition)
├─ 34. Day-Parting                   (when to show ads?)
└─ 35. Retention Strategy            (bring back lapsed users)
```

**Total = 35 features when fully built out with ads data**

---

## 🗂️ CURRENT FILES & MIGRATION STATUS

### Data Files Ready to Copy (Phase 1: Google Places API Only)

#### Survey Data
| Source | Destination | Status |
|--------|-------------|--------|
| `C:\Users\Roy\Downloads\Research Form - Sheet1.csv` | `data/raw/surveys/form_v1_responses.csv` | ✅ Ready |
| `C:\Users\Roy\Downloads\Help us design better experiences...csv` | `data/raw/surveys/form_v2_responses.csv` | ✅ Ready |

#### Google Places API Data (4 Cities) — CRITICAL FILES

**Per city, copy these 5 files:**

| File | Purpose | Status | Has Venue Names? |
|------|---------|--------|------------------|
| `step_1_venues_refined.json` | Venue names, place_ids, locations, coordinates | ✅ Ready | ✅ YES (NEEDED FOR FEATURES 1-2) |
| `step_5_behavioral_scores.json` | Per-venue detailed scores + fitness dimensions | ✅ Ready | ❌ No (join with step_1) |
| `step_5b_similarity.json` | Venue similarity pool + shared primitives | ✅ Ready | ❌ No (join with step_1) |
| `step_5_patterns_scored.json` | Aggregated market patterns + prevalence | ✅ Ready | ❌ No (reference data) |
| `step_4b_governance_report.json` | Data quality metrics + drift signals | ✅ Ready | ❌ No (metadata) |

**Copy from all 4 city folders:**
- `D:\PolyNovea\Module 2\Google Places API\data\navi-mumbai\` (922 venues)
- `D:\PolyNovea\Module 2\Google Places API\data\mumbai\main\` (3,558 venues)
- `D:\PolyNovea\Module 2\Google Places API\data\mumbai\sobo\` (1,269 venues)
- `D:\PolyNovea\Module 2\Google Places API\data\thane\` (515 venues)

| Source | Destination |
|--------|-------------|
| `D:\PolyNovea\Module 2\Google Places API\data\navi-mumbai\step_*.json` | `data/raw/google_places/navi-mumbai/` |
| `D:\PolyNovea\Module 2\Google Places API\data\mumbai\sobo\step_*.json` | `data/raw/google_places/mumbai-sobo/` |
| `D:\PolyNovea\Module 2\Google Places API\data\mumbai\main\step_*.json` | `data/raw/google_places/mumbai-main/` |
| `D:\PolyNovea\Module 2\Google Places API\data\thane\step_*.json` | `data/raw/google_places/thane/` |

#### Reference Files (Optional)
| File | Purpose |
|------|---------|
| `step_3_signals_extracted.json` | Signal extraction validation (for reference) |
| `step_4b_governance_report_previous.json` | Track data quality evolution |

#### Future Data (Phase 2)
| Source | Destination | Status |
|--------|-------------|--------|
| MagicPin data | `data/raw/magicpin/` | ⏳ Later (issues being solved) |
| Zomato data | `data/raw/zomato/` | ⏳ Later (issues being solved) |

### Config Files Status

> ✅ All data loading is handled by the Python pipeline scripts (002–014).
> SQL-based config files and manual ingestion scripts are no longer needed.
> The pipeline scripts are the single source of truth for DB schema + data loading.

| Config | Status | Notes |
|--------|--------|-------|
| `config/primitives.json` | ✅ Embedded in pipeline | 54 signals encoded in `010_load_primitives.py` |
| `config/surface_categories.json` | ✅ Embedded in pipeline | 7 venue types in `002_load_venues.py` |
| `config/schema.json` | ✅ Replaced | Schema defined inline in each pipeline script via `CREATE TABLE IF NOT EXISTS` |
| `config/constants.py` | ✅ Not needed | Constants in each script |
| `sql/001_init_schema.sql` | ✅ Superseded | Schema auto-created by pipeline scripts |
| `sql/002_load_venues.sql` — `sql/005_load_surveys.sql` | ✅ Superseded | Replaced by `002_load_venues.py` — `008_load_surveys.py` |
| `config/version_control.json` | 🔲 Deferred | Not blocking Phase 1 |
| `config/temporal_filters.json` | 🔲 Deferred | Not blocking Phase 1 |
| `config/cross_primitive_rules.json` | 🔲 Deferred | Not blocking Phase 1 |

### Files Already Created ✅

```
✅ survey_canonical_schema.json
   └─ Normalizes Form v1 + v2 + future forms into canonical fields
   └─ Ready for new form versions

✅ survey_responses_normalized.csv
   └─ All 45 responses (9 from v1 + 36 from v2) in canonical schema
   └─ 35 distinct archetypes computed
   └─ Ready to load into PostgreSQL
```

---

## 📊 SURVEY DATA NORMALIZATION COMPLETE

**What was done:**

1. **Analyzed 3 form versions:**
   - Form v1 (Research Form): 9 responses, simple structure
   - Form v2 (Help us design): 36 responses, detailed ratings + text
   - Form new (Behavioral Intelligence): 15 questions, acquisition-focused

2. **Created canonical schema** with 8 sections:
   - Demographics (age, city, frequency, company)
   - Identity & Social Style (energy, place preference, social personality)
   - Discovery & Attention (channels, attention grabbers, crowd reaction)
   - FOMO & Decision Triggers (fomo tendency, quick triggers, overload behavior)
   - Group Dynamics (role, recommendation, group influence)
   - Environment & Habits (atmosphere, revisit vs explore, music)
   - Purpose & Spend (what they do, how much they spend)
   - Contact & Consent (email, instagram, newsletter)

3. **Normalized all 45 responses** to canonical schema:
   - 9 from Form v1 ✅
   - 36 from Form v2 ✅
   - Computed 35 distinct archetypes (e.g., "Calm Pairs", "Party Seeker", "Discovery Explorer")

4. **Ready for next form versions:**
   - When new form responses come in, map using canonical schema
   - Archetypes automatically computed from social_personality + energy_preference + place_preference

---

## 🔗 DATA FLOW: RAW → DATABASE → 16 FEATURES → ACQUISITION

```
Raw Data (Google Places API JSON + Surveys)
  Source: D:\PolyNovea\Module 2\Google Places API\data\
  4 cities: navi-mumbai (922), mumbai/main (3,558), mumbai/sobo (1,269), thane (515)

        ↓ Python Pipeline (Database/scripts/run_pipeline.py)

002_load_venues.py
  step_1_venues_refined.json × 4 cities
  → venues (6,007 rows)

003_load_patterns.py
  step_4_patterns_recognized.json × 4 cities
  → behavioral_patterns + venue_pattern_links (5,042 + 26,871)

004_load_scores.py
  step_5_patterns_scored.json × 4 cities
  → venue_fitness_dimensions + intervention_triggers (6,007 + 24,028)

005_load_similarity.py
  step_5b_similarity.json × 4 cities
  → venue_vectors + venue_similarity (5,758 + 146,426)

006_load_pattern_scores.py
  → pattern_confidence_scores (5,042)

007_load_governance.py
  step_4b_governance_report.json × 4 cities
  → drift_signals + data_quality_metrics (5,042)

008_load_surveys.py
  form_v1_responses.csv + form_v2_responses.csv
  → survey_responses + user_archetypes (42 + 42)

009_load_marketing_engine.py
  Hardcoded behavioral research data
  → behavioral_mechanism_catalog + channel_mechanism_mapping + campaign_templates (5 + 25 + 13)

010_load_primitives.py
  step_5_behavioral_scores.json × 4 cities
  → primitives_scores (23,821)

011_load_demographics.py
  Hardcoded demographic-archetype research
  → demographic_segments + archetype_mappings + alignments + interventions (5 + 23 + 9 + 10)

012_compute_venue_demographics.py  [COMPUTED — no raw source]
  venue_fitness_dimensions × SEGMENT_FITNESS_WEIGHTS
  → venue_demographic_scores (30,035) + venue_similarity.rank (146,426 ranked)

013_compute_fitness_deltas.py  [COMPUTED — no raw source]
  venue_similarity × venue_fitness_dimensions
  → fitness_delta_rules (56) + venue_similarity_deltas (1,171,408)

014_create_optional_scaffolds.py  [EMPTY SCAFFOLDS]
  → venue_platform_data + venue_pos_summary + platform_performance_benchmarks (empty)

Survey Data (42 responses)
├─ Form v1 (6 responses) → survey_responses table
├─ Form v2 (36 responses) → survey_responses table
└─ Derived → user_archetypes (42 computed)

        ↓ [Data Loading & Processing]

PostgreSQL on AWS RDS — polynovea_module2 ✅ ALL COMPLETE
├─ venues                       6,007 rows
├─ venue_vectors                5,758 rows
├─ venue_fitness_dimensions     6,007 rows  (8 dimensions)
├─ primitives_scores            23,821 rows
├─ behavioral_patterns          5,042 rows
├─ venue_pattern_links          26,871 rows
├─ pattern_confidence_scores    5,042 rows
├─ venue_similarity             146,426 rows  (ranked)
├─ venue_similarity_deltas      1,171,408 rows
├─ fitness_delta_rules          56 rows
├─ drift_signals + data_quality_metrics  5,042 rows each
├─ survey_responses + user_archetypes    42 rows each
├─ demographic_segments/mappings/alignments/interventions  5+23+9+10 rows
├─ venue_demographic_scores     30,035 rows
├─ behavioral_mechanism_catalog + channel_mechanism_mapping + campaign_templates  5+25+13
├─ venue_platform_data          0 rows  (scaffold)
├─ venue_pos_summary            0 rows  (scaffold)
└─ platform_performance_benchmarks  0 rows  (scaffold)

        ↓ Pinecone (Vector Semantic Search — Phase 2, not yet integrated)

16 Feature Endpoints
├─ Feature 1: Similar Venues Comparison ← Uses step_5b_similarity
├─ Feature 2: Consulting Redirect ← Uses step_5b_similarity
├─ Features 3-12: Core intelligence (recommendations, churn, etc.)
└─ Features 13-16: Foundation for ads (content, real-time, simulation, trends)

        ↓ (Future: Add ads & MagicPin & Zomato)

35 Feature Endpoints (With Acquisition)
├─ Features 17-24: Attribution & spend optimization
└─ Features 25-35: Advanced targeting
```

---

## 🆕 NEW PIPELINE OUTPUTS (STEP 4-5 ENRICHMENTS)

### step_4_patterns_recognized.json
**What it is:** Market-level behavioral pattern recognition

**What it contains:**
- Co-occurring primitives grouped across all venues (e.g., "food_quality + social_energy + pride")
- Which venues match each pattern
- Pattern detection count and prevalence percentage
- Total venues in city and pattern breakdown

**Why it enriches the database:**
- **Layer 1 → Layer 2 Translation:** Raw primitives → composite behavioral patterns
- **Market Intelligence:** See which primitive combinations are trending across venues
- **Pattern as Feature:** Instead of 54-dim vectors, market thinks in "High-Quality Social" or "Service Excellence" patterns
- Used for Features 5 (Archetype Segmentation), 10 (Competitive Benchmarking), 16 (Trend Detection)

### step_5_patterns_scored.json
**What it is:** Confidence-weighted market patterns with actionable metrics

**What it contains per pattern:**
- `co_occurring_primitives` — Which primitives cluster together
- `confidence_score` (0-100) — Market-level confidence this pattern is real
- `venue_count` — How many venues match this pattern
- `prevalence` — Percentage of market with this pattern
- `venues` — Which venues exemplify this pattern (up to 5)

**Why it enriches the database:**
- **Scored vs Recognized:** Adds statistical confidence to raw pattern existence
- **Fitness Dimensions:** Maps patterns to 5 business use cases:
  - `fitness_for_office_lunch` — Quick meal convenience patterns
  - `fitness_for_repeat_habit` — Loyal customer patterns
  - `fitness_for_social_dwell` — Group hangout patterns
  - `fitness_for_group_energy` — Party/event patterns
  - `fitness_for_destination_visit` — Destination/experience patterns
- **Intervention Opportunities:** Identifies actionable business plays:
  - Operational optimization (repeat visits + queue friction)
  - Premium justification (premium pricing + view appeal)
  - Dwell monetization (long dwell + multi-round ordering)
  - Friction reduction (loyal customers + slow service)
- **Behavioral Summary per Venue:**
  - `operational_quality` — How well the venue executes its patterns
  - `retention_strength` — Loyalty/repeat visit potential
  - `monetization_potential` — Revenue opportunity based on patterns

### step_5b_similarity.json
**What it is:** Pre-computed venue similarity analysis with shared primitives

**What it contains per venue:**
- Fitness vector (5 dimensions: office_lunch, repeat_habit, social_dwell, group_energy, destination_visit)
- Top 25 most similar venues (similarity_score 0-1)
- Shared primitives between each pair (e.g., "food_quality", "pride")
- Shared primitive count
- Behavioral summary for each similar venue

**Why it's critical:**
- **Feature 1 (Similar Venues Comparison):** Show a venue its top 3 similar venues with different factors
- **Feature 2 (Consulting Redirect):** Show "if you want to shift from type X to Y, here are successful Y venues"
- Eliminates need to compute similarity at query time (pre-computed, instant lookup)
- Shared primitives show exactly what to improve

### step_4b_governance_report.json
**What it is:** Data quality scorecard + pattern drift tracking

**What it contains:**
- `avg_confidence`: 0.664 (average signal confidence across all venues)
- `avg_reliability`: 0.79 (pattern stability and evidence strength)
- `reliability_score`: 0.734 (overall data quality)
- `high_reliability_clusters`: 3979 of 4313 (good quality patterns)
- `drift_signals`: List of new patterns emerging with their confidence scores

**Why it's important:**
- Tracks data quality evolution (baseline for future updates)
- Drift signals show which patterns are becoming more prevalent (market intelligence)
- Helps identify when new primitive combinations are gaining traction
- Foundation for Feature 16 (Trend Detection & Forecasting)

---

---

## 🔗 DATA INGESTION — SUPERSEDED BY PYTHON PIPELINE

> ⚠️ The SQL scripts below (`005_load_venues_from_step1.sql`, etc.) were the original plan.
> They are **fully superseded** by the Python pipeline scripts in `Database/scripts/`.
> Do not run any SQL below manually. The pipeline handles everything.
> This section is kept as reference for understanding what data flows where.

---

## 🔗 DATA INGESTION REFERENCE (HISTORICAL — DO NOT RUN)

### Data Sources (Live Location - DO NOT COPY)

All data read directly from source JSON files:
```
Source: D:\PolyNovea\Module 2\Google Places API\data\

├── navi-mumbai/
│   ├── step_1_venues_refined.json           ← Venue names + locations (Feature 1-2)
│   ├── step_4_patterns_recognized.json      ← Pattern definitions (Feature 2)
│   ├── step_4b_governance_report.json       ← Data quality metrics (Quality tracking)
│   ├── step_5_behavioral_scores.json        ← Behavioral vectors + fitness (Feature 1-2)
│   └── step_5b_similarity.json              ← Similar venue rankings (Feature 1-2)
│
├── mumbai/main/
│   ├── step_1_venues_refined.json
│   ├── step_4_patterns_recognized.json
│   ├── step_4b_governance_report.json
│   ├── step_5_behavioral_scores.json
│   └── step_5b_similarity.json
│
├── mumbai/sobo/
│   ├── step_1_venues_refined.json
│   ├── step_4_patterns_recognized.json
│   ├── step_4b_governance_report.json
│   ├── step_5_behavioral_scores.json
│   └── step_5b_similarity.json
│
└── thane/
    ├── step_1_venues_refined.json
    ├── step_4_patterns_recognized.json
    ├── step_4b_governance_report.json
    ├── step_5_behavioral_scores.json
    └── step_5b_similarity.json
```

**Read Strategy:** Load each JSON file → Parse → Insert into PostgreSQL (one-time or batch nightly)

---

### SQL: Load step_1 (Venue Names + Locations)

```sql
-- File: 005_load_venues_from_step1.sql

-- Create staging table
CREATE TEMP TABLE staging_venues_raw (
    data JSONB
);

-- Load navi-mumbai step_1_venues_refined.json
COPY staging_venues_raw (data) 
FROM PROGRAM 'cat "D:\PolyNovea\Module 2\Google Places API\data\navi-mumbai\step_1_venues_refined.json"'
WITH (FORMAT json);

-- Parse and insert into venues table
INSERT INTO venues (
    place_id, 
    venue_name, 
    latitude, 
    longitude, 
    area, 
    city,
    surface_category,
    google_types,
    source_file
)
SELECT
    data->>'place_id',
    data->>'name',
    (data->'location'->>'lat')::FLOAT,
    (data->'location'->>'lng')::FLOAT,
    data->>'area',
    'navi-mumbai',
    COALESCE(data->'types'->>0, 'restaurant'),
    data->'types',
    'step_1_venues_refined.json'
FROM staging_venues_raw;

-- Repeat for mumbai/main, mumbai/sobo, thane
-- (Same query, change path and city name)

-- Verify load
SELECT city, COUNT(*) as venue_count 
FROM venues 
GROUP BY city;
-- Expected: navi-mumbai: 922, mumbai/main: 3558, mumbai/sobo: 1269, thane: 515
```

---

### SQL: Load step_4 (Behavioral Patterns - CRITICAL FOR FEATURE 2)

```sql
-- File: 005b_load_patterns_from_step4.sql
-- MUST RUN BEFORE step_5 (patterns are referenced by venues)

CREATE TEMP TABLE staging_patterns_raw (
    data JSONB
);

-- Load navi-mumbai step_4_patterns_recognized.json
COPY staging_patterns_raw (data) 
FROM PROGRAM 'cat "D:\PolyNovea\Module 2\Google Places API\data\navi-mumbai\step_4_patterns_recognized.json"'
WITH (FORMAT json);

-- Parse and insert behavioral patterns
INSERT INTO behavioral_patterns (
    pattern_name,
    pattern_description,
    co_occurring_primitives,
    archetype_hypothesis,
    total_venues_matching,
    prevalence_percentage,
    city
)
SELECT
    data->>'pattern_name',
    data->>'pattern_description',
    data->'co_occurring_primitives',
    data->>'archetype_hypothesis',
    (data->>'total_venues_matching')::INT,
    (data->>'prevalence_percentage')::FLOAT,
    'navi-mumbai'
FROM staging_patterns_raw
WHERE data->>'pattern_name' IS NOT NULL;

-- Assign venues to patterns (which venues match which patterns)
INSERT INTO venue_pattern_assignment (
    venue_id,
    pattern_id,
    confidence_score,
    is_primary_pattern
)
SELECT
    v.id,
    bp.id,
    (item->>'confidence_score')::FLOAT,
    (item->>'is_primary')::BOOLEAN
FROM staging_patterns_raw s
CROSS JOIN LATERAL jsonb_array_elements(s.data->'venue_assignments') item
JOIN venues v ON v.place_id = item->>'venue_place_id' AND v.city = 'navi-mumbai'
JOIN behavioral_patterns bp ON bp.pattern_name = s.data->>'pattern_name';

-- Load governance/quality metrics
INSERT INTO data_quality_metrics (
    city,
    metric_name,
    metric_value,
    confidence_level
)
SELECT
    'navi-mumbai',
    key,
    value::TEXT,
    'MEDIUM'
FROM staging_patterns_raw
CROSS JOIN jsonb_each(data->'quality_metrics');

-- Verify
SELECT COUNT(*) as total_patterns FROM behavioral_patterns WHERE city = 'navi-mumbai';
-- Expected: 20-30 patterns per city
```

---

### SQL: Load step_5 (Behavioral Scores + Fitness)

```sql
-- File: 006_load_behavioral_scores_from_step5.sql

CREATE TEMP TABLE staging_scores_raw (
    data JSONB
);

-- Load navi-mumbai step_5_behavioral_scores.json
COPY staging_scores_raw (data) 
FROM PROGRAM 'cat "D:\PolyNovea\Module 2\Google Places API\data\navi-mumbai\step_5_behavioral_scores.json"'
WITH (FORMAT json);

-- Parse venue scores
INSERT INTO venue_vectors (
    venue_id,
    place_id,
    city,
    primitives_json,
    fitness_dimensions_json,
    final_confidence_score
)
SELECT
    v.id,
    v.place_id,
    'navi-mumbai',
    data->'scored_patterns'->0->'co_occurring_primitives',
    data->'fitness_dimensions',
    (data->>'confidence_score')::FLOAT
FROM staging_scores_raw s
JOIN venues v ON v.place_id = s.data->>'venue_id' AND v.city = 'navi-mumbai';

-- Parse patterns (if not already loaded from step_4)
INSERT INTO behavioral_patterns (
    pattern_name,
    co_occurring_primitives,
    archetype_hypothesis,
    total_venues_with_pattern,
    prevalence_percentage
)
SELECT DISTINCT
    data->>'pattern_name',
    data->'co_occurring_primitives',
    data->>'archetype_hypothesis',
    (data->>'total_venues')::INT,
    (data->>'prevalence_percentage')::FLOAT
FROM staging_scores_raw
WHERE data->>'pattern_name' IS NOT NULL;

-- Verify
SELECT COUNT(*) as total_venues FROM venue_vectors WHERE city = 'navi-mumbai';
-- Expected: 922
```

---

### SQL: Load step_5b (Similarity Rankings)

```sql
-- File: 007_load_similarity_from_step5b.sql

CREATE TEMP TABLE staging_similarity_raw (
    data JSONB
);

-- Load navi-mumbai step_5b_similarity.json
COPY staging_similarity_raw (data) 
FROM PROGRAM 'cat "D:\PolyNovea\Module 2\Google Places API\data\navi-mumbai\step_5b_similarity.json"'
WITH (FORMAT json);

-- Parse similarity rankings
INSERT INTO venue_similarity (
    client_venue_id,
    similar_venue_id,
    similarity_score,
    shared_primitives,
    shared_primitive_count,
    rank_position,
    city
)
SELECT
    v1.id,
    v2.id,
    (item->>'similarity_score')::FLOAT,
    item->'shared_primitives',
    (item->>'shared_primitive_count')::INT,
    (item->>'rank')::INT,
    'navi-mumbai'
FROM staging_similarity_raw s
JOIN venues v1 ON v1.place_id = s.data->>'client_place_id' AND v1.city = 'navi-mumbai'
CROSS JOIN LATERAL jsonb_array_elements(s.data->'similar_venues') item
JOIN venues v2 ON v2.place_id = item->>'similar_place_id' AND v2.city = 'navi-mumbai';

-- Verify: each venue should have up to 25 similar venues
SELECT client_venue_id, COUNT(*) as similar_count 
FROM venue_similarity 
WHERE city = 'navi-mumbai'
GROUP BY client_venue_id
HAVING COUNT(*) > 0
LIMIT 10;
-- Expected: Most venues have 20-25 matches
```

---

### SQL: Feature 1 Query (Similar Venues Comparison)

```sql
-- Feature 1: Show client venue + 3 similar venues with comparisons
-- Input: client_place_id
-- Output: Venue names, categories, primitives comparison (3 better, 3 worse)

SELECT 
    -- CLIENT VENUE
    v_client.venue_name as "Client Venue",
    v_client.area as "Location",
    v_client.google_types->>0 as "Category",
    vv_client.primitives_json,
    
    -- SIMILAR VENUES (TOP 3)
    ARRAY_AGG(
        jsonb_build_object(
            'rank', vs.rank_position,
            'venue_name', v_sim.venue_name,
            'similarity_score', vs.similarity_score,
            'shared_primitives', vs.shared_primitives,
            'primitives_client', vv_client.primitives_json,
            'primitives_similar', vv_sim.primitives_json,
            'better_than_client', (
                -- Extract 3 primitives where similar > client
                SELECT jsonb_object_agg(prim, score)
                FROM jsonb_each(vv_sim.primitives_json) AS t(prim, score)
                WHERE (score::FLOAT) > COALESCE((vv_client.primitives_json->>prim)::FLOAT, 0)
                LIMIT 3
            ),
            'worse_than_client', (
                -- Extract 3 primitives where similar < client
                SELECT jsonb_object_agg(prim, score)
                FROM jsonb_each(vv_sim.primitives_json) AS t(prim, score)
                WHERE (score::FLOAT) < COALESCE((vv_client.primitives_json->>prim)::FLOAT, 0)
                LIMIT 3
            )
        ) ORDER BY vs.rank_position ASC
    ) as "Top 3 Similar Venues"
FROM venues v_client
JOIN venue_vectors vv_client ON v_client.id = vv_client.venue_id
JOIN venue_similarity vs ON v_client.id = vs.client_venue_id
JOIN venues v_sim ON vs.similar_venue_id = v_sim.id
JOIN venue_vectors vv_sim ON v_sim.id = vv_sim.venue_id
WHERE v_client.place_id = $1  -- Input: client place_id
AND vs.rank_position <= 3     -- Top 3 only
GROUP BY v_client.id, v_client.venue_name, v_client.area, vv_client.primitives_json;
```

---

### SQL: Feature 2 Query (Consulting Redirect)

```sql
-- Feature 2: Client venue wants to transform to target type
-- Input: client_place_id, target_pattern_name
-- Output: 3 reference venues of target type + comparison

SELECT 
    -- CLIENT VENUE (CURRENT)
    v_client.venue_name as "Your Venue",
    v_client.area as "Current Location",
    bp_current.pattern_name as "Current Type",
    vv_client.primitives_json as "Your Profile",
    
    -- TARGET TYPE
    $2 as "Target Type",
    (
        -- Gap analysis: what primitives to improve
        SELECT jsonb_object_agg(prim, (target_score - current_score))
        FROM (
            SELECT 
                prim,
                COALESCE((vv_client.primitives_json->>prim)::FLOAT, 0) as current_score,
                COALESCE((
                    SELECT AVG((score::FLOAT))
                    FROM jsonb_each(vv_ref.primitives_json) AS t(p, score)
                    WHERE p = prim
                ), 0) as target_score
            FROM jsonb_object_keys(vv_client.primitives_json) as prim
        ) gaps
        WHERE target_score > current_score
        ORDER BY (target_score - current_score) DESC
        LIMIT 3  -- Top 3 areas to improve
    ) as "Top 3 Things to Improve",
    
    -- REFERENCE VENUES (Successful examples of target type, TOP 3)
    ARRAY_AGG(
        jsonb_build_object(
            'venue_name', v_ref.venue_name,
            'location', v_ref.area,
            'target_match_score', vp_ref.confidence_score,
            'better_than_yours', (
                -- 3 primitives where reference > client
                SELECT jsonb_object_agg(prim, score)
                FROM jsonb_each(vv_ref.primitives_json) AS t(prim, score)
                WHERE (score::FLOAT) > COALESCE((vv_client.primitives_json->>prim)::FLOAT, 0)
                LIMIT 3
            ),
            'you_do_better', (
                -- 3 primitives where client > reference (keep these strengths)
                SELECT jsonb_object_agg(prim, score)
                FROM jsonb_each(vv_client.primitives_json) AS t(prim, score)
                WHERE (score::FLOAT) > COALESCE((vv_ref.primitives_json->>prim)::FLOAT, 0)
                LIMIT 3
            )
        )
    ) as "Reference Venues to Study"
FROM venues v_client
JOIN venue_vectors vv_client ON v_client.id = vv_client.venue_id
JOIN venue_pattern_assignment vpa_current ON v_client.id = vpa_current.venue_id
JOIN behavioral_patterns bp_current ON vpa_current.pattern_id = bp_current.id
-- Find reference venues (target pattern type)
CROSS JOIN (
    SELECT v_ref.id, v_ref.venue_name, v_ref.area, vv_ref.primitives_json
    FROM venues v_ref
    JOIN venue_vectors vv_ref ON v_ref.id = vv_ref.venue_id
    JOIN venue_pattern_assignment vpa_ref ON v_ref.id = vpa_ref.venue_id
    JOIN behavioral_patterns bp_ref ON vpa_ref.pattern_id = bp_ref.id
    WHERE bp_ref.pattern_name = $2  -- Target pattern name
    AND v_ref.city = v_client.city
    ORDER BY vpa_ref.confidence_score DESC
    LIMIT 3
) AS ref_query(v_ref, v_ref_id, area, vv_ref)
JOIN venues v_ref ON ref_query.v_ref_id = v_ref.id
JOIN venue_vectors vv_ref ON v_ref.id = vv_ref.venue_id
JOIN venue_pattern_assignment vp_ref ON v_ref.id = vp_ref.venue_id
WHERE v_client.place_id = $1
GROUP BY v_client.id, v_client.venue_name, vv_client.primitives_json;
```

---

### Data Flow Summary

```
RAW JSON FILES (Source - D:\PolyNovea\Module 2\Google Places API\data\)
│
├── step_1_venues_refined.json
│   ↓ SQL: 005_load_venues_from_step1.sql
│   ↓
│   └─→ venues TABLE (name, location, coordinates)
│
├── step_4_patterns_recognized.json ⭐ CRITICAL FOR FEATURE 2
│   ↓ SQL: 005b_load_patterns_from_step4.sql (RUN FIRST)
│   ↓
│   ├─→ behavioral_patterns TABLE (pattern definitions)
│   └─→ venue_pattern_assignment TABLE (which venues match which patterns)
│
├── step_4b_governance_report.json
│   ↓ SQL: (Load into data_quality_metrics)
│   ↓
│   └─→ data_quality_metrics TABLE (quality tracking)
│
├── step_5_behavioral_scores.json
│   ↓ SQL: 006_load_behavioral_scores_from_step5.sql
│   ↓
│   └─→ venue_vectors TABLE (54 primitives + fitness dimensions)
│
└── step_5b_similarity.json
    ↓ SQL: 007_load_similarity_from_step5b.sql
    ↓
    └─→ venue_similarity TABLE (ranked 1-25 similar venues per venue)


FEATURE 1-2 SQL QUERIES (Joins all tables via SQL)
├── Feature 1: Similar Venues Comparison
│   Uses: venues + venue_vectors + venue_similarity
│   SQL: SELECT venue names, locations, primitives comparison (3 better, 3 worse)
│
└── Feature 2: Consulting Redirect ⭐ NEEDS step_4 PATTERNS
    Uses: venues + venue_vectors + venue_similarity + behavioral_patterns + venue_pattern_assignment
    SQL: SELECT client venue + 3 reference venues of target pattern type with comparisons

LOAD ORDER (IMPORTANT):
  1️⃣ 005_load_venues_from_step1.sql        (creates venues table)
  2️⃣ 005b_load_patterns_from_step4.sql    (creates patterns + assignments - BEFORE step_5)
  3️⃣ 006_load_behavioral_scores_from_step5.sql  (creates vectors)
  4️⃣ 007_load_similarity_from_step5b.sql  (creates similarity rankings)
```

---

## 📊 DATABASE TABLES — COMPLETE

> ✅ All tables below are live on RDS. See the DB STATUS section at the top of this document for row counts.

### PostgreSQL Schema (Actual — as of script 014)

**Venue Core:**
- `venues` — 6,007 venues (name, place_id, area, city, types, coordinates)
- `venue_vectors` — Behavioral fitness vectors per venue (5,758 with vectors)
- `venue_fitness_dimensions` — 8 fitness scores per venue: office_lunch, repeat_habit, social_dwell, group_energy, destination_visit, operational_quality, retention_strength, monetization_potential (6,007 rows)
- `primitives_scores` — 54 primitive scores per venue (23,821 rows)

**Behavioral Patterns:**
- `behavioral_patterns` — 5,042 market-level patterns (co_occurring_primitives, archetype_hypothesis, prevalence)
- `venue_pattern_links` — 26,871 venue→pattern assignments
- `pattern_confidence_scores` — 5,042 confidence-weighted scores per pattern

**Similarity (Feature 1 + 2):**
- `venue_similarity` — 146,426 pairs, ranked 1–N per venue (rank column populated by script 012)
- `venue_similarity_deltas` — 1,171,408 rows: pre-computed 8-dimension fitness delta per pair
- `fitness_delta_rules` — 56 rules (7 bands × 8 dimensions) mapping delta values to plain-English client statements

**Governance:**
- `drift_signals` — 5,042 emerging pattern signals
- `data_quality_metrics` — 5,042 quality metrics

**Surveys + Archetypes:**
- `survey_responses` — 42 normalized responses
- `user_archetypes` — 42 computed archetypes

**Demographics (Feature 2 filtering):**
- `demographic_segments` — 5 segments: office_workers, college_kids, couples, families, premium
- `archetype_mappings` — 23 archetype → segment prevalence mappings
- `demographic_behavioral_alignments` — 9 fitness weight alignments per segment
- `demographic_archetype_interventions` — 10 intervention descriptions
- `venue_demographic_scores` — 30,035 rows: alignment_score + segment_rank per venue × segment

**Marketing Engine:**
- `behavioral_mechanism_catalog` — 5 mechanisms (habit_formation, fomo, social_proof, identity_signaling, environmental_expectation)
- `channel_mechanism_mapping` — 25 channel × mechanism mappings with ROI ranges
- `campaign_templates` — 13 templates per segment × mechanism × channel

**Optional Scaffolds (empty — populate on opt-in):**
- `venue_platform_data` — Zomato/Swiggy opt-in: rating, covers, peak hours, photo_count, dineout_enabled
- `venue_pos_summary` — POS/Module 3: revenue, repeat_rate, customer_lifetime_value
- `platform_performance_benchmarks` — City-level aggregates from opt-in data

---

## 🌉 DEMOGRAPHIC-ARCHETYPE BRIDGE (NEW)

### Why This Matters
**Problem:** Venue owners think in demographics ("I want college kids"), but Module 2 thinks in behavioral archetypes ("Party Seekers").

**Solution:** A translation layer that maps demographic segments to archetypes + interventions, so:
- Venue owners can use language they understand
- Sales/pitch teams have concrete demographic categories
- App shows both layers: "College kids (mostly Party Seekers, some Discovery Explorers)"

### Bridge Data Structure

**Table: `demographic_segments`**
```
segment_id, segment_name, segment_description, demographics, city
col_1, "college_kids_weekend", "22-25, 2-4 people, weekends", age=22-25, company_size=2-4, when=weekends, navi-mumbai
col_2, "office_workers_lunch", "26-35, alone/partner, lunch", age=26-35, company_size=1-2, when=weekdays_lunch, navi-mumbai
fam_1, "families_casual_dining", "all ages, 2-6 people, weekends", age=all, company_size=2-6, when=weekends, navi-mumbai
```

**Table: `demographic_archetype_mapping`**
```
segment_id, archetype_name, prevalence_percentage, population_count, confidence_score
col_1, "Party Seeker", 70%, 31 responses, 0.85
col_1, "Discovery Explorer", 20%, 9 responses, 0.72
col_1, "Repeat Regular", 10%, 4 responses, 0.68
office_lunch_1, "Repeat Regular", 60%, 27 responses, 0.88
office_lunch_1, "Premium Prioritizer", 30%, 13 responses, 0.75
office_lunch_1, "Calm Pairs", 10%, 4 responses, 0.65
fam_1, "Calm Pairs", 50%, 22 responses, 0.81
fam_1, "Discovery Explorer", 40%, 18 responses, 0.77
fam_1, "Premium Prioritizer", 10%, 5 responses, 0.62
```

**Table: `demographic_archetype_interventions`**
```
segment_id, archetype_name, intervention_type, description, expected_roi
col_1, "Party Seeker", "music_and_energy", "120-130 BPM playlist, live music 2x/week, group seating", 1.57x revenue
col_1, "Party Seeker", "dwell_monetization", "Second drink special at 20min, multi-drink bundling", 1.28x order frequency
col_1, "Discovery Explorer", "authenticity_leverage", "Cuisine storytelling, seasonal specials, chef visibility", 1.35x premium pricing
office_lunch_1, "Repeat Regular", "operational_optimization", "Quick ordering, pre-order system, speed training", 1.18x throughput
office_lunch_1, "Repeat Regular", "friction_reduction", "Reserved tables, familiar staff, loyalty recognition", 1.42x repeat rate
fam_1, "Calm Pairs", "comfort_enhancement", "Quiet zones, comfortable seating, family-friendly ambience", 1.25x dwell time
fam_1, "Calm Pairs", "service_excellence", "Attentive staff, personalized recommendations", 1.33x satisfaction
```

**Table: `demographic_behavioral_alignment`**
```
segment_id, archetype_name, primary_primitives, secondary_primitives, critical_fitness_dimension
col_1, "Party Seeker", ["social_energy", "music", "excitement", "social_sharing"], ["staff_warmth", "food_quality"], "group_energy"
office_lunch_1, "Repeat Regular", ["quick_service", "repeat_visits", "convenience"], ["staff_warmth", "food_quality"], "repeat_habit"
fam_1, "Calm Pairs", ["comfort", "intimate", "safe_environment"], ["staff_warmth", "food_quality"], "social_dwell"
```

### App/Software Integration

**For Venue Owners (Pitch/Console):**
```
"Who do you want to attract?"

1. College kids on weekends
   → Mostly Party Seekers (70%) + some Discovery Explorers (20%)
   → They care about: social_energy, music, excitement, ability to share moments
   → Our recommendations:
      • Add 120-130 BPM upbeat playlist + 2x live music nights
      • Rearrange seating for group tables (4-8 people)
      • "Second drink special" at 20min mark
      • Brand photo op with backgrounds
   → Expected impact: 57% revenue increase, 78% more dwell time

2. Families on weekends
   → Mostly Calm Pairs (50%) + Discovery Explorers (40%)
   → They care about: comfort, intimate atmosphere, authentic food
   → Our recommendations:
      • Designated quiet zones with comfortable seating
      • Family-friendly ambience + playlist (not loud)
      • Cuisine storytelling + chef visibility
      • Special family menu options
   → Expected impact: 35% revenue increase, better loyalty
```

**For Internal Team (Sales/Consulting):**
```
NAVI MUMBAI DEMOGRAPHIC SEGMENTS & ARCHETYPES:

College Kids (22-25, Weekend):
  ├─ Party Seeker 70% → Music + Energy intervention (1.57x ROI)
  ├─ Discovery Explorer 20% → Authenticity + Newness (1.35x ROI)
  └─ Repeat Regular 10% → Speed + Familiarity (1.18x ROI)

Office Workers (26-35, Lunch):
  ├─ Repeat Regular 60% → Operational efficiency (1.42x repeat rate)
  ├─ Premium Prioritizer 30% → Premium justification (1.25x margin)
  └─ Calm Pairs 10% → Comfort + quiet space (1.33x satisfaction)

Families (All ages, Weekend):
  ├─ Calm Pairs 50% → Comfort + safety (1.25x dwell)
  ├─ Discovery Explorer 40% → Authentic experiences (1.35x premium)
  └─ Premium Prioritizer 10% → Quality justification (1.20x spend)
```

### Data Source
The demographic-archetype mapping comes from:
1. **Survey Demographics:** Age group, company size (who they go with), when (weekends/weekdays/lunch), reason, spend
2. **Computed Archetypes:** 35 types derived from survey behavioral preferences (social_personality, energy_preference, place_preference)
3. **Clustering:** Group survey respondents by demographic, compute archetype prevalence within each group

---

## 💡 HOW STEP 4-5 PATTERNS ENRICH THE DATABASE

### From Raw Signals → Composite Patterns → Market Intelligence

**Without step_4 & step_5 pattern outputs:**
- Database has raw 54-dimensional vectors per venue
- No insight into which primitives naturally cluster
- Market-level understanding requires complex vector math

**With step_4 patterns (recognized):**
- **Pattern Recognition:** Discovers "food_quality + social_energy + experience_memories" as a market pattern
- **Primitive Relationships:** Shows which primitives appear together consistently
- **Market Themes:** Groups venues into behavioral archetypes (e.g., "Social Dining", "Premium Experience")
- **Simplification:** 54 dimensions → ~20-30 named patterns (human-understandable)

**With step_5 patterns (scored):**
- **Confidence Metrics:** Not just patterns exist, but how confident we are (87% vs 40%)
- **Prevalence:** 15% of venues in market show this pattern
- **Fitness for Use Cases:** This pattern drives 85% fitness for "social_dwell" but only 20% for "office_lunch"
- **Business Actions:** When a pattern shows high repeat_visits + long_queue, recommend operational optimization
- **Behavioral Summary per Venue:** Instead of raw scores, marketing sees "operational_quality: 0.78, retention_strength: 0.65, monetization_potential: 0.71"

### Database Tables That Enable Features

| Feature | Requires Tables | What It Does |
|---------|-----------------|--------------|
| 1. Similar Venues Comparison | venues, venue_similarity (ranked), venue_similarity_deltas, fitness_delta_rules, venue_demographic_scores, archetype_mappings | Client venue vs 3 similar venues — fitness bars with delta badges + plain-English statements. Carousel pagination via rank. |
| 2. Consulting Redirect | venues, venue_similarity, venue_demographic_scores, venue_similarity_deltas, fitness_delta_rules | Filter similar venues by target demographic segment. Same comparison grid. |
| 3. Recommendations | intervention_triggers, venue_fitness_dimensions | Ranked intervention list with priority_tier badges |
| 5. Archetype Segmentation | behavioral_patterns, user_archetypes | "Group users and venues by shared patterns" |
| 10. Competitive Benchmarking | venue_fitness_dimensions, pattern_scores | "How do we stack vs competitors?" |
| 16. Trend Detection | drift_signals, pattern_scores (historical) | "Which new patterns emerging this quarter?" |

### Query Examples After Database Enrichment

**Query 1:** Find all venues matching "High-Quality Social" pattern
```sql
SELECT v.venue_name, ps.confidence_score, pd.fitness_for_social_dwell
FROM venues v
JOIN pattern_venues pv ON v.id = pv.venue_id
JOIN behavioral_patterns bp ON pv.pattern_id = bp.id
JOIN pattern_scores ps ON bp.id = ps.pattern_id
WHERE bp.pattern_name = "food_quality + social_energy + experience_memories"
  AND ps.confidence_score > 0.75
ORDER BY pd.fitness_for_social_dwell DESC;
```

**Query 2:** Recommend business actions for a venue
```sql
SELECT v.venue_name, it.intervention_trigger, it.description
FROM venues v
JOIN pattern_venues pv ON v.id = pv.venue_id
JOIN intervention_triggers it ON pv.pattern_id = it.pattern_id
WHERE v.id = $venue_id
  AND it.intervention_trigger IN ('operational_optimization', 'premium_justification');
```

---

## 🔑 KEY CONCEPTS RECAP

### Layer 1 vs Layer 2
| Concept | Layer 1 | Layer 2 |
|---------|---------|---------|
| Data | Reviews (Google/Zomato/MagicPin) | User surveys (Form v1 + v2) |
| Signals | 54 primitives (behavioral) | Archetype preferences (35 types) |
| Building Block | Venue profile (54-d vector) | User profile (n-d vector) |
| Features | 1-2: Venue comparison | 3-16: Matching, recommendations |
| Matching | Find similar venues | Find venues for users |

### Hybrid Source Weighting (Option D - Ready for Phase 2)
```
PHASE 1 (NOW): Google Places API only
├─ All 54 primitives extracted from Google reviews
├─ Single vector per venue (stability-focused)
└─ No weighting needed (single source)

PHASE 2 (LATER): Add Zomato & MagicPin
├─ Google Places   → Food, service, ambience primitives   (50% weight)
├─ Zomato          → Food, pricing, experience primitives (30% weight)
└─ MagicPin        → Realtime, crowd, energy primitives   (20% weight)

Each maintains independent scores in PostgreSQL
Create 2 vectors per venue: stability (long-term) + realtime (current)
Different features use different vectors based on their needs
```

### Amendment Logic (Source-Specific Recency)
```
When NEW review arrives (any source):
├─ Extract 54 primitives from review text
├─ Apply exponential decay: weight = 0.5^(days_since_last_update / 30)
├─ Update ONLY that source's scores (don't affect others)
├─ Regenerate that source's vector
└─ If feature requests composite score, combine with weights

Example: Google's new review → Update Google scores only
         Zomato's new review → Update Zomato scores only
         MagicPin's new check → Update MagicPin scores only
         → Combine for features that need all 3
```

---

## 🔧 RECENT FIXES (2026-05-14)

### step_5_score.py Bug Fixes
**Issue:** Thane city output showed `confidence_score: 1%` instead of ~90%, and duplicate venues appeared in venues array

**Root Causes:**
1. Averaging individual pattern confidence_scores (0.6-0.7 range) instead of final_scores (0-1 range)
2. Venues appended without deduplication when a venue matched multiple pattern clusters

**Fixes Applied:**
1. Changed aggregation to use `final_scores` instead of `confidence_scores`
2. Calculate confidence as: `sum(final_scores) / len(final_scores) * 100`
3. De-duplicate venues using `list(set(data["venues"]))`
4. Updated venues array to pull from deduplicated list

**Result:** Thane now shows correct confidence_scores (50-57%) matching Navi Mumbai pattern

### Pipeline Ready for All 4 Cities
**Command to run:**
```powershell
python run_pipeline.py          # All 4 cities (navi-mumbai, mumbai-sobo, mumbai-main, thane)
python run_pipeline.py --city thane  # Single city
```

**Each city will generate:**
- step_3_signals_extracted.json
- step_4_behavioral_clusters.json
- step_4_patterns_recognized.json ✨ NEW
- step_4b_governance_report.json
- step_5_behavioral_scores.json
- step_5b_similarity.json
- step_5_patterns_scored.json ✨ NEW
- step_6_output.json

---

---

## 🏪 FEATURES 1-2: VENUE COMPARISON ENGINE

### Feature 1: Similar Venues Comparison

**Client Experience:**
```
Client venue owner enters: "The Atrangii House, Navi Mumbai"

App shows:
┌─ THE ATRANGII HOUSE (Your Venue)
│  ├─ Category Hierarchy: Casual Dining → Bar/Lounge → Multi-Cuisine
│  ├─ Behavioral Profile: Social Energy (0.78), Food Quality (0.72), Music (0.65)
│  └─ Key Strengths: Ambience, Group seating, Mixed drinks menu

SIMILAR VENUES (Top 3):

├─ [1] Zenoa, Airoli
│  ├─ Category Hierarchy: Casual Dining → Lounge → Multicuisine
│  ├─ Similarity Score: 0.87 (very similar profile)
│  │
│  ├─ 🟢 3 THINGS THEY DO BETTER:
│  │  1. Live Music frequency (0.92 vs your 0.65) → Guest DJ 4x/week
│  │  2. Staff Warmth (0.88 vs your 0.72) → Personalized welcome, staff training
│  │  3. Social Sharing moments (0.85 vs your 0.71) → Photo-op design, branded content
│  │
│  └─ 🔴 3 THINGS YOU DO BETTER:
│     1. Quick Service Speed (0.81 vs their 0.62) → Table ordering system
│     2. Menu Innovation (0.79 vs their 0.65) → Seasonal specials, fusion items
│     3. Comfortable Seating (0.77 vs their 0.68) → Ergonomic chairs, spacing

├─ [2] Purple Olive, Thane
│  [Similar structure]

└─ [3] Sushi & Stories, Vile Parle
   [Similar structure]
```

**Data Requirements for Feature 1:**
```sql
venues (source data)
├─ venue_id (PK)
├─ venue_name
├─ location
├─ latitude, longitude
├─ surface_category (Casual Dining, Fine Dining, Cafe, etc.)
├─ subcategory_tier_1 (Bar, Lounge, Multiplex, etc.)
└─ subcategory_tier_2 (Multicuisine, Indian, Fusion, etc.)

venue_vectors (pre-computed from step_5)
├─ venue_id (FK)
├─ primitive_scores (54-dimensional: food_quality, social_energy, music, etc.)
├─ fitness_dimensions (repeat_habit, group_energy, office_lunch, etc.)
├─ behavioral_summary (aggregated: what this venue is good at)
└─ generated_from (google, zomata, magicpin, etc.)

venue_similarity (pre-computed from step_5b_similarity.json)
├─ venue_id (FK to client's venue)
├─ similar_venue_id (FK to matched venue)
├─ similarity_score (0-1)
├─ shared_primitives (array: primitives both venues score high on)
├─ shared_primitive_count (e.g., "12 shared strengths")
├─ ranked_position (1-25, we show top 3)
└─ shared_behavioral_summary (text: what they have in common)

primitive_comparison (computed at query time or pre-computed)
├─ client_venue_id
├─ similar_venue_id
├─ primitive_name
├─ client_score
├─ similar_venue_score
├─ difference (similar - client, positive = they're better)
├─ ranked_by_difference (rank all 54 primitives by gap)
└─ top_3_better, top_3_worse (filtered arrays)
```

**Algorithm:**
```
GET /api/features/similar-venues/{venue_id}

1. Fetch venue_vectors for venue_id (client's venue)
2. Query venue_similarity WHERE venue_id = {client_id} ORDER BY similarity_score DESC LIMIT 3
3. For each similar venue:
   a. Fetch its venue_vectors
   b. Compare all 54 primitives: similar_score - client_score
   c. Rank by difference (descending)
   d. Extract top 3 better (positive difference)
   e. Extract top 3 worse (negative difference)
   f. Get category hierarchy from venues table
4. Return aggregated response with categories + comparisons
```

---

### Feature 2: Consulting Redirect

**Client Experience:**
```
Client venue owner enters:
- "My venue: The Atrangii House" (Currently: Casual Dining → Bar/Lounge)
- "I want to become: Party Seeker venue" (Target: Casual Dining → Nightclub/Party)

App shows:
┌─ YOUR TRANSFORMATION GOAL
│  ├─ Current Type: Social Dining (Food + Ambience + Company)
│  ├─ Target Type: Party Seeker (High Energy + Music + Group Vibes)
│  └─ Transformation Gap: "You're 65% aligned; need +25pp on music, energy, social_sharing"

REFERENCE VENUES (Successful Party Seekers - Top 3):

├─ [1] Club Jasmine, Powai
│  ├─ Category Hierarchy: Casual Dining → Nightclub → Party Venue
│  ├─ Target Match Score: 0.94 (matches "Party Seeker" profile very well)
│  │
│  ├─ 🟢 3 THINGS THEY DO BETTER (vs YOUR current profile):
│  │  1. Music & Energy (0.95 vs your 0.65) → 120-130 BPM playlist, live DJ nightly
│  │  2. Group Seating (0.91 vs your 0.71) → Large tables, group packages
│  │  3. Social Moments (0.88 vs your 0.68) → Photo walls, LED backdrops, branded hashtags
│  │
│  └─ 🔴 3 THINGS YOU DO BETTER (can retain):
│     1. Food Quality (0.72 vs their 0.58) → Keep your menu as differentiator
│     2. Service Speed (0.81 vs their 0.62) → Your efficiency is valuable
│     3. Comfort (0.77 vs their 0.65) → Good seating/AC will attract quality guests

├─ [2] Electric Avenue, SOBO
│  [Similar structure]

└─ [3] Pulse Club, Bangalore
   [Similar structure]

RECOMMENDED ACTIONS TO TRANSFORM:
├─ Implement: Music programming (120+ BPM, 4 DJs/week)
├─ Add: Group table layout (consolidate 2-4 tables)
├─ Create: Photo ops / social moments (branding surfaces)
├─ Keep: Food quality (your strength)
├─ Keep: Service speed (your strength)
└─ Timeline: 4-6 weeks to fully transform
```

**Data Requirements for Feature 2:**
```sql
Extends Feature 1's tables + adds:

behavioral_patterns (from step_4_patterns_recognized.json)
├─ pattern_id (PK)
├─ pattern_name (e.g., "High-Energy Party", "Premium Fine Dining")
├─ co_occurring_primitives (array: food_quality + social_energy + music, etc.)
├─ archetype_hypothesis (the behavioral type this pattern represents)
├─ total_venues_matching (how many venues in market show this pattern)
├─ prevalence_percentage (% of market)
└─ pattern_description (text summary)

venue_pattern_assignment (which venues match which patterns)
├─ venue_id (FK)
├─ pattern_id (FK)
├─ confidence_score (0-1, how sure are we this venue is this pattern?)
├─ primary_pattern (is this the venue's main type?)
└─ secondary_patterns (alternative types it could be)

fitness_dimensions (from step_5_patterns_scored.json)
├─ pattern_id (FK)
├─ fitness_for_office_lunch (0-1)
├─ fitness_for_repeat_habit (0-1)
├─ fitness_for_social_dwell (0-1)
├─ fitness_for_group_energy (0-1)
└─ fitness_for_destination_visit (0-1)
```

**Algorithm:**
```
POST /api/features/consulting-redirect
{
  "client_venue_id": venue_id,
  "target_pattern_id": pattern_id OR target_type_name
}

1. Fetch client_venue_vectors (current profile)
2. Fetch target_pattern definition (target behavioral type)
3. Calculate "transformation gap":
   - For each primitive in target pattern:
     - diff = target_score - client_score
   - Sort by gap (biggest gaps first)
   - Rank top 3 things to improve

4. Find reference venues (where similar_pattern_id = target_pattern):
   a. Query venues WHERE pattern_id = target_pattern LIMIT 25
   b. Rank by fitness_for_target_dimension (descending)
   c. Select top 3 venues that match target pattern well

5. For each reference venue:
   a. Compare all 54 primitives: reference - client
   b. Extract top 3 better on target pattern alignment
   c. Extract top 3 where client is better (to keep)
   d. Get category hierarchy

6. Return transformation roadmap + reference venues + actions
```

---

### Data NOT Stored (Keep System Lean)

❌ **Reviews / Review Text:** Just extract primitives once, aggregate, delete raw reviews
❌ **Individual Review Metadata:** Summary stats only (count, date range, confidence)
❌ **User Profiles:** Not storing survey responses in Phase 1 (Feature 3+ will need this)
❌ **Campaign Data:** Phase 2 only

### Data Stored (Minimal Footprint)

✅ **Venues:** name, location, coords, categories
✅ **Behavioral Signals:** 54 primitives aggregated (not per-review)
✅ **Fitness Dimensions:** 5 fitness scores per pattern
✅ **Patterns:** Recognized market-level patterns (20-30 total)
✅ **Similarity:** Pre-computed venue pairs from step_5b
✅ **Quality Metrics:** Confidence scores, data governance flags

**Storage Estimate for 6,264 venues (current data):**
- Venue metadata (step_1): ~63MB (name, location, categories from 6,264 venues)
- Behavioral vectors (step_5): ~2.6GB (54 dims × 8 bytes × 6,264 venues)
- Similarity index (step_5b): ~850MB (top 25 matches per venue)
- Patterns + fitness (step_4/5): ~60MB
- **Total: ~3.6GB**

This fits easily on any PostgreSQL host (free tier + $1K credit will cover 12+ months)

At any point: fully reproducible from step_4 & step_5 JSON files (can delete & recompute)

---

## 🏢 FEATURES 3-12: CORE INTELLIGENCE ENGINES

### Feature 3: Personalized Recommendations

**Client Experience:**
```
User (from survey) enters: "Show me venues for next Friday night, small group"

App shows:
┌─ PERSONALIZED VENUES FOR YOU
│  └─ Based on your profile: Party Seeker, 18-25, likes social energy + music
│
├─ [1] Club Jasmine, Powai ⭐⭐⭐⭐⭐
│  ├─ Match Score: 94% (Your archetype shows 0.94 fitness for this venue)
│  ├─ Why: Social energy (0.95), Music (0.92), Group seating (0.88)
│  ├─ Friday: 9 PM - 2 AM, DJ live, group packages available
│  ├─ Similar users like it: 87% of Party Seekers rate it 5/5
│  └─ [View Details] [Book Now]
│
├─ [2] Electric Avenue, SOBO
│  [Similar structure, Match Score: 88%]
│
└─ [3] Pulse, Bangalore
   [Similar structure, Match Score: 81%]
```

**Data Requirements:**
```sql
user_archetypes (from survey responses)
├─ user_id (PK)
├─ archetype_name (Party Seeker, Calm Pairs, etc.)
├─ archetype_vector (dimensional scores for matching)
├─ demographic_profile (age, company_size, when, reason)
└─ preference_weights (which primitives matter most to this user?)

venue_vectors (from step_5_behavioral_scores.json)
├─ venue_id (FK)
├─ primitives_json (54 dimensions)
├─ fitness_dimensions (5 mechanisms)
└─ archetype_match_scores (how well does this venue match each archetype?)

venue_archetype_fit (pre-computed)
├─ venue_id (FK)
├─ archetype_name
├─ fit_score (0-1, cosine similarity between venue vector and archetype vector)
├─ matching_primitives (which 5 primitives drive the match)
└─ confidence_score
```

**Algorithm:**
```sql
-- Get personalized recommendations for a user
SELECT 
    v.venue_name,
    v.area,
    vaf.fit_score as match_percentage,
    vaf.matching_primitives,
    (SELECT COUNT(*) FROM venue_ratings WHERE venue_id = v.id AND rating >= 4) / 
    (SELECT COUNT(*) FROM venue_ratings WHERE venue_id = v.id) as satisfaction_rate,
    vaf.confidence_score
FROM users u
JOIN user_archetypes ua ON u.archetype_id = ua.id
JOIN venue_archetype_fit vaf ON ua.archetype_name = vaf.archetype_name
JOIN venues v ON vaf.venue_id = v.id
WHERE u.id = $1
  AND vaf.fit_score > 0.75  -- Only strong matches
ORDER BY vaf.fit_score DESC
LIMIT 10;
```

---

### Feature 4: Churn Risk Scoring

**Client Experience (for venue owner):**
```
Venue dashboard shows: "15% of your repeat customers show early churn signals"

CHURN RISK SUMMARY
├─ HIGH RISK (5 customers) — May stop visiting in 30 days
│  ├─ Reason: 50%+ drop in visit frequency over last 60 days
│  ├─ Last visit: 21 days ago (normally every 7 days)
│  ├─ Recommended action: Send "we miss you" WhatsApp + exclusive offer
│  └─ Expected recovery: 60-70% re-engagement within 30 days
│
├─ MEDIUM RISK (8 customers) — Declining engagement
│  ├─ Reason: Visit frequency declining slowly
│  ├─ Last visit: 14 days ago (normally every 10 days)
│  ├─ Recommended action: WhatsApp reminder + new menu highlight
│  └─ Expected recovery: 40-50%
│
└─ LOW RISK (2 customers) — Monitor but stable
   └─ [View Customer Names] [Send Campaigns]
```

**Data Requirements:**
```sql
customer_visits (transaction log from POS)
├─ customer_id
├─ venue_id
├─ visit_date
├─ order_value
├─ dwell_minutes
└─ repeat_count

customer_churn_signals (computed)
├─ customer_id (FK)
├─ venue_id (FK)
├─ churn_risk_score (0-1, how likely to churn in 30 days)
├─ days_since_last_visit
├─ historical_visit_frequency (avg days between visits)
├─ frequency_decline_percentage (current vs 60-day rolling average)
├─ risk_category (HIGH, MEDIUM, LOW)
├─ last_computed_date
└─ recommended_intervention
```

**Algorithm:**
```sql
-- Compute churn risk: declining frequency
WITH visit_frequency AS (
    SELECT 
        customer_id,
        venue_id,
        COUNT(*) as visit_count_60d,
        AVG(EXTRACT(DAY FROM (visit_date - LAG(visit_date) OVER (ORDER BY visit_date)))) as avg_frequency_days
    FROM customer_visits
    WHERE visit_date > NOW() - INTERVAL '60 days'
    GROUP BY customer_id, venue_id
),
historical_frequency AS (
    SELECT 
        customer_id,
        venue_id,
        AVG(EXTRACT(DAY FROM (visit_date - LAG(visit_date) OVER (ORDER BY visit_date)))) as historical_avg_frequency
    FROM customer_visits
    WHERE visit_date > NOW() - INTERVAL '180 days'
    GROUP BY customer_id, venue_id
),
current_state AS (
    SELECT 
        customer_id,
        venue_id,
        EXTRACT(DAY FROM (NOW() - MAX(visit_date))) as days_since_last_visit
    FROM customer_visits
    GROUP BY customer_id, venue_id
)
SELECT 
    vf.customer_id,
    vf.venue_id,
    -- Churn risk = (Days since visit / Expected frequency) × frequency_decline
    CASE 
        WHEN cs.days_since_last_visit > hf.historical_avg_frequency * 1.5 THEN 0.85  -- HIGH
        WHEN cs.days_since_last_visit > hf.historical_avg_frequency * 1.2 THEN 0.55  -- MEDIUM
        ELSE 0.20  -- LOW
    END as churn_risk_score,
    CASE 
        WHEN cs.days_since_last_visit > hf.historical_avg_frequency * 1.5 THEN 'HIGH'
        WHEN cs.days_since_last_visit > hf.historical_avg_frequency * 1.2 THEN 'MEDIUM'
        ELSE 'LOW'
    END as risk_category
FROM visit_frequency vf
JOIN historical_frequency hf ON vf.customer_id = hf.customer_id
JOIN current_state cs ON vf.customer_id = cs.customer_id;
```

---

### Feature 5: Archetype Segmentation

**Client Experience:**
```
Venue dashboard shows: "Your customer base: Who are they?"

CUSTOMER COMPOSITION
├─ 62% Repeat Regulars (277 customers)
│  ├─ Revenue contribution: 68% (high LTV)
│  ├─ Avg spend: ₹850 per visit
│  ├─ Visit frequency: Every 7.2 days
│  ├─ Churn risk: LOW (0.15)
│  └─ Growth opportunity: +25% (increase visit frequency via habits)
│
├─ 22% Calm Pairs (98 customers)
│  ├─ Revenue contribution: 20%
│  ├─ Avg spend: ₹1,200 per visit (higher but less frequent)
│  ├─ Visit frequency: Every 21 days
│  ├─ Churn risk: MEDIUM (0.45)
│  └─ Growth opportunity: Increase frequency via messaging
│
└─ 16% Discovery Explorers (71 customers)
   [Similar structure]

ACTIONS BY SEGMENT
├─ Repeat Regulars: WhatsApp habit formation (+30-40% frequency)
├─ Calm Pairs: Email storytelling + premium positioning (+15-20% spend)
└─ Discovery Explorers: Instagram content + seasonal specials (+25% new visits)
```

**Data Requirements:**
```sql
survey_responses_canonical (user profiles)
├─ user_id
├─ archetype_name (inferred from survey)
├─ archetype_confidence_score

customer_archetype_assignment (inferred from venue behavior)
├─ customer_id
├─ venue_id
├─ inferred_archetype (based on visit patterns)
├─ confidence_score
└─ last_updated

customer_segment_metrics (per-segment aggregation)
├─ venue_id
├─ archetype_name
├─ customer_count
├─ avg_order_value
├─ visit_frequency
├─ total_revenue_contribution
├─ revenue_percentage
└─ churn_rate
```

**Algorithm:**
```sql
-- Segment customers by archetype + compute metrics
SELECT 
    v.venue_id,
    ua.archetype_name,
    COUNT(DISTINCT c.customer_id) as customer_count,
    COUNT(DISTINCT c.customer_id)::FLOAT / (SELECT COUNT(DISTINCT customer_id) FROM customers WHERE venue_id = v.id) * 100 as percentage,
    ROUND(AVG(cv.order_value), 0) as avg_order_value,
    ROUND(AVG(EXTRACT(DAY FROM (NOW() - cv.visit_date))), 1) as avg_days_since_visit,
    ROUND(SUM(cv.order_value), 0) as total_revenue,
    ROUND(SUM(cv.order_value)::FLOAT / (SELECT SUM(order_value) FROM customer_visits WHERE venue_id = v.id) * 100, 1) as revenue_percentage
FROM venues v
JOIN customers c ON v.id = c.venue_id
JOIN customer_archetype_assignment caa ON c.id = caa.customer_id
JOIN user_archetypes ua ON caa.archetype_name = ua.archetype_name
JOIN customer_visits cv ON c.id = cv.customer_id AND v.id = cv.venue_id
WHERE c.venue_id = $1
GROUP BY v.venue_id, ua.archetype_name
ORDER BY total_revenue DESC;
```

---

### Feature 6: Conflict Detection

**Client Experience:**
```
Venue dashboard alert: "⚠️ Data quality issue: Review conflicts detected"

CONFLICT: Food Quality vs Menu Innovation
├─ Google Reviews mention: "Excellent fresh ingredients, consistent quality"
├─ Zomato Reviews mention: "Menu feels repetitive, same items for 2 years"
├─ Signal: food_quality scoring HIGH but menu_innovation scoring LOW
├─ Root cause: Google users (one-time visitors) vs Zomata (repeat users)
├─ Recommended investigation: Ask why repeats perceive menu as static?
│  └─ Potential issue: Seasonal specials not visible on Zomata listing
└─ Action: Update Zomata menu description + add seasonal rotation note

CONFLICT: Staff Warmth vs Long Wait Times
├─ Primitive contradiction: Staff rated warm + friendly but waits exceed 30min
├─ Possible cause: Understaffing (good staff, not enough of them)
├─ Impact: High satisfaction (friendliness) but low retention (friction)
├─ Recommendation: Operational optimization (speed) needed, not service training
└─ Expected impact: Adding 1 server could lift retention by 25%
```

**Data Requirements:**
```sql
primitive_conflicts (detected)
├─ conflict_id (PK)
├─ venue_id (FK)
├─ primitive_1 (e.g., "food_quality")
├─ score_1 (e.g., 0.87)
├─ primitive_2 (e.g., "menu_innovation")
├─ score_2 (e.g., 0.35)
├─ contradiction_type (positive/negative pair that shouldn't coexist)
├─ confidence_score (how sure are we this is a real conflict?)
├─ source_analysis (which source highlights the conflict?)
├─ interpretation (text explanation)
├─ recommended_action
└─ severity (HIGH, MEDIUM, LOW)
```

**Algorithm:**
```sql
-- Detect primitive conflicts (score inversions that indicate data quality issues)
WITH primitive_scores AS (
    SELECT 
        v.id as venue_id,
        prim as primitive,
        score::FLOAT as score
    FROM venues v
    JOIN venue_vectors vv ON v.id = vv.venue_id
    CROSS JOIN jsonb_each(vv.primitives_json) AS t(prim, score)
),
conflict_pairs AS (
    -- Define which primitives should correlate positively
    -- If one is high and other is low, flag conflict
    SELECT 
        ps1.venue_id,
        ps1.primitive as prim1,
        ps2.primitive as prim2,
        ps1.score as score1,
        ps2.score as score2,
        ABS(ps1.score - ps2.score) as conflict_magnitude
    FROM primitive_scores ps1
    JOIN primitive_scores ps2 ON ps1.venue_id = ps2.venue_id
    WHERE 
        -- Positive correlations that should exist
        (ps1.primitive IN ('staff_warmth', 'comfort') AND ps2.primitive IN ('service_speed', 'repeat_visits') AND ps1.score > 0.7 AND ps2.score < 0.3)
        OR
        (ps1.primitive = 'food_quality' AND ps2.primitive IN ('menu_innovation', 'reviews_count') AND ps1.score > 0.7 AND ps2.score < 0.3)
)
SELECT 
    v.venue_name,
    prim1,
    prim2,
    score1,
    score2,
    'HIGH' as severity,
    'Investigation needed: primitive inversion detected' as interpretation
FROM conflict_pairs cp
JOIN venues v ON cp.venue_id = v.id
WHERE cp.conflict_magnitude > 0.4;
```

---

### Feature 7: Satisfaction Drivers

**Client Experience:**
```
Venue dashboard shows: "What makes YOUR customers satisfied?"

SATISFACTION DRIVER ANALYSIS

For REPEAT REGULARS (Your 62% customer base):
├─ Top 3 drivers of satisfaction:
│  1. Quick Service (0.81 correlation with 5-star reviews)
│  2. Familiar Staff (0.78 correlation)
│  3. Consistent Quality (0.75 correlation)
├─ These 3 primitives explain 71% of satisfaction variance
├─ Action: "Your efficiency is key. Invest in speed, not new menu."
└─ Expected impact: Focus here could increase repeat rate by 18%

For CALM PAIRS (Your 22% customer base):
├─ Top 3 drivers of satisfaction:
│  1. Comfort/Ambience (0.84 correlation)
│  2. Intimate Setting (0.79 correlation)
│  3. Food Quality (0.76 correlation)
├─ These 3 explain 79% of their satisfaction
├─ Action: "Your ambience matters more than menu variety. Keep intimate."
└─ Expected impact: Focus here could increase satisfaction by 22%

MISMATCH DETECTED ⚠️
└─ You're investing in menu variety (not a driver) instead of speed (is a driver)
   └─ Recommendation: Redirect menu innovation budget to operational efficiency
```

**Data Requirements:**
```sql
satisfaction_drivers (computed via correlation analysis)
├─ venue_id (FK)
├─ archetype_name
├─ primitive_name
├─ correlation_with_satisfaction (0-1)
├─ rank_position (1, 2, 3, etc.)
├─ variance_explained_percentage (cumulative)
├─ sample_size (how many reviews used for correlation)
└─ confidence_level (HIGH, MEDIUM, LOW based on n)
```

**Algorithm:**
```python
# Pseudocode: satisfaction_driver_analysis.py
# For each venue + archetype combination:

def analyze_satisfaction_drivers(venue_id, archetype_name):
    # 1. Get all reviews from customers of this archetype at this venue
    reviews = query("""
        SELECT review_text, rating, extracted_primitives
        FROM reviews r
        JOIN customers c ON r.customer_id = c.id
        JOIN customer_archetype_assignment caa ON c.id = caa.customer_id
        WHERE c.venue_id = ? AND caa.archetype_name = ?
    """, [venue_id, archetype_name])
    
    # 2. For each primitive, compute correlation with satisfaction (rating)
    for primitive in all_54_primitives:
        correlation = pearson_correlation(
            X = [score for prim, score in review.extracted_primitives if prim == primitive],
            Y = [rating for rating in reviews]
        )
        
        # 3. Rank by correlation strength
        if correlation > 0.65:
            save_driver(venue_id, archetype_name, primitive, correlation)
    
    # 4. Return top 3 drivers + variance explained by top 3
    return sorted_by_correlation[:3]
```

---

### Feature 8: Pricing Power Analysis

**Client Experience:**
```
Venue dashboard shows: "Can you justify higher prices?"

PRICE ELASTICITY ANALYSIS

Current Pricing Segment Analysis:
├─ Current avg price: ₹850 per visit
├─ Your segment: Casual Dining → Lounge
├─ Competitor average: ₹780 per visit
├─ Price premium: +8.9%

Can You Justify It?
├─ Food Quality (0.87) ✅ YES — Above average, customers expect premium
├─ Ambience (0.73) ✅ YES — Strong differentiation
├─ Staff Warmth (0.79) ✅ YES — Personal touch justifies premium
├─ Menu Innovation (0.62) ⚠️ MAYBE — Below average, limits premium appeal
└─ Overall: 73% of your premium is justified

Recommendations:
├─ Current premium (8.9%) is sustainable
├─ Opportunity: Increase to 12-15% if you boost menu_innovation
│  └─ Investment: Add 2-3 seasonal specials/quarter
│  └─ Expected revenue lift: +4-6% with maintained visit frequency
└─ Risk: Premium becomes unjustified at 15%+ if quality slips
```

**Data Requirements:**
```sql
venue_pricing (transaction data)
├─ venue_id
├─ avg_order_value
├─ median_order_value
├─ std_dev_order_value
├─ price_tier (low, mid, premium)

competitor_pricing (aggregated from reviews + metadata)
├─ venue_id
├─ comparable_venue_ids (similar type, location, size)
├─ avg_competitor_price
├─ price_percentile (how does this venue rank?)

pricing_justification_metrics (computed)
├─ venue_id
├─ current_avg_price
├─ competitor_avg_price
├─ price_premium_percentage
├─ justification_score (0-1, based on primitives)
├─ primitives_supporting_premium (array of high-scoring primitives)
├─ maximum_supportable_premium_percentage
└─ recommendations (array of actions)
```

**Algorithm:**
```sql
-- Analyze pricing power: are high primitives correlated with higher prices?
WITH venue_financial AS (
    SELECT 
        v.id,
        AVG(cv.order_value) as avg_price,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cv.order_value) as median_price
    FROM venues v
    JOIN customer_visits cv ON v.id = cv.venue_id
    GROUP BY v.id
),
venue_scores AS (
    SELECT 
        v.id,
        ROUND(AVG((jsonb_each(vv.primitives_json)).value::FLOAT), 2) as avg_primitive_score,
        COUNT(DISTINCT (jsonb_each(vv.primitives_json)).key) FILTER (WHERE ((jsonb_each(vv.primitives_json)).value::FLOAT > 0.75)) as premium_primitives_count
    FROM venues v
    JOIN venue_vectors vv ON v.id = vv.venue_id
    GROUP BY v.id
),
competitor_comparison AS (
    SELECT 
        v.id,
        AVG(v2.vf.avg_price) as competitor_avg_price,
        COUNT(*) as competitor_count
    FROM venues v
    JOIN venues v2 ON v.surface_category = v2.surface_category AND v.city = v2.city
    JOIN venue_financial vf ON v2.id = vf.id
    WHERE v.id != v2.id
    GROUP BY v.id
)
SELECT 
    v.venue_name,
    vf.avg_price as current_price,
    cc.competitor_avg_price,
    ROUND(((vf.avg_price - cc.competitor_avg_price) / cc.competitor_avg_price * 100), 1) as price_premium_percentage,
    vs.premium_primitives_count,
    vs.avg_primitive_score,
    CASE 
        WHEN vs.avg_primitive_score > 0.75 AND vs.premium_primitives_count >= 10 THEN 'HIGH'
        WHEN vs.avg_primitive_score > 0.65 AND vs.premium_primitives_count >= 5 THEN 'MEDIUM'
        ELSE 'LOW'
    END as justification_level
FROM venues v
JOIN venue_financial vf ON v.id = vf.id
JOIN venue_scores vs ON v.id = vs.id
JOIN competitor_comparison cc ON v.id = cc.id
WHERE vf.avg_price > cc.competitor_avg_price;
```

---

### Feature 9: Cross-Venue Synergy

**Client Experience (for multi-venue operators):**
```
Portfolio dashboard shows: "How do your venues work together?"

YOUR VENUES PORTFOLIO:
├─ The Atrangii House, Navi Mumbai (casual lounge)
├─ Zenoa, Airoli (upscale lounge)
└─ Club Jasmine, Powai (nightclub)

SYNERGY ANALYSIS

Cannibalization Risk ⚠️ MODERATE
├─ Atrangii + Zenoa share 34% of customer base
├─ Shared archetypes: Calm Pairs (62% overlap), Premium Prioritizers (58%)
├─ Risk: Customers visiting Zenoa instead of Atrangii on Friday nights
├─ Expected loss: ₹12,000 - 18,000/month from Atrangii due to Zenoa
├─ Mitigation: Position Atrangii for office lunch, Zenoa for weekend premium
└─ Expected after positioning: Cannibalization drops to 8%, cross-venue visitation rises 15%

Cross-Selling Opportunity ✅ HIGH
├─ Atrangii regulars (lunch) = potential Zenoa weekend customers
├─ Expected cross-visit rate: 12% with targeted messaging
├─ Revenue opportunity: +₹45,000/month from Atrangii → Zenoa conversion
├─ Campaign: "You love lunch here; try weekend premium experience there"
└─ Channel: WhatsApp to Repeat Regulars + Instagram Reels

Portfolio Complementarity ✅ STRONG
├─ Atrangii (office lunch) + Zenoa (weekend premium) + Club Jasmine (nightlife) = full week coverage
├─ Same customer base could visit all 3 on different occasions
├─ Potential wallet share: 25-35% of customer entertainment budget
└─ Current wallet share: 12% (room to grow)
```

**Data Requirements:**
```sql
cross_venue_customer_overlap (customer sharing)
├─ venue_1_id (FK)
├─ venue_2_id (FK)
├─ shared_customer_count
├─ overlap_percentage
├─ shared_archetype_distribution (JSON: which archetypes overlap?)
└─ cannibalization_risk_score

cross_venue_opportunity (expansion potential)
├─ venue_1_id
├─ venue_2_id
├─ potential_cross_visit_rate (estimated % of v1 customers who could visit v2)
├─ estimated_additional_revenue
├─ recommended_positioning (how to differentiate the venues?)
└─ campaign_recommendation

portfolio_complementarity (full operator analysis)
├─ operator_id
├─ venue_ids (array of all venues)
├─ total_unique_customers
├─ cross_venue_visitation_percentage
├─ portfolio_coverage_score (how well does portfolio cover week/archetypes?)
├─ wallet_share_opportunity
└─ synergy_recommendations
```

---

### Feature 10: Competitive Benchmarking

**Client Experience:**
```
Venue dashboard shows: "How do you stack up against competitors?"

YOUR COMPETITIVE POSITION: The Atrangii House vs Market

OVERALL SCORE
├─ Your rank: 12th percentile in Casual Dining → Lounge
├─ Your score: 0.71 (average of top 5 primitives)
├─ Top competitor score: 0.86
├─ You're 15 percentage points behind

PRIMITIVE-BY-PRIMITIVE COMPARISON (vs top 5 competitors):
┌─ STRENGTHS (Where you beat competitors):
│  ├─ Quick Service (0.81 vs 0.68 avg) ✅ +13 points
│  ├─ Comfortable Seating (0.77 vs 0.71 avg) ✅ +6 points
│  └─ Staff Warmth (0.79 vs 0.73 avg) ✅ +6 points
│
├─ COMPETITIVE (Where you match):
│  ├─ Food Quality (0.87 vs 0.85 avg) ≈ +2 points
│  └─ Ambience (0.73 vs 0.74 avg) ≈ -1 point
│
└─ GAPS (Where you need improvement):
   ├─ Menu Innovation (0.62 vs 0.79 avg) ❌ -17 points
   ├─ Social Moments (0.68 vs 0.75 avg) ❌ -7 points
   └─ Music/Energy (0.65 vs 0.76 avg) ❌ -11 points

BENCHMARKING INSIGHT
├─ Your strength: Operational efficiency (speed + comfort)
├─ Gap: Experience newness (menu + social + energy)
├─ Recommendation: "Don't fight them on ambience. Strengthen speed, add menu rotation."
└─ Expected impact: Addressing top 2 gaps could lift you to 45th percentile
```

**Data Requirements:**
```sql
competitor_pool (venues in same segment)
├─ venue_id (FK)
├─ segment (e.g., "Casual Dining → Lounge")
├─ comparable_venues (array of similar venue IDs)
├─ comparison_basis (location, size, price tier, etc.)

competitive_benchmark_scores (percentile-based)
├─ venue_id (FK)
├─ primitive_name
├─ venue_score
├─ percentile_rank (0-100, where is this venue among competitors)
├─ competitor_avg
├─ competitor_top_quartile
├─ gap_to_leader
└─ rank_position (e.g., 12th out of 50)

competitive_position_summary (aggregated)
├─ venue_id
├─ segment
├─ overall_percentile_rank
├─ strength_primitives (where we beat market)
├─ gap_primitives (where we lag)
├─ opportunities_ranked (prioritized improvement areas)
└─ expected_impact_per_improvement (revenue lift if we improve this)
```

**Algorithm:**
```sql
-- Competitive benchmarking: percentile ranking
WITH competitor_primitives AS (
    SELECT 
        v_ref.id as reference_venue_id,
        v_comp.id as competitor_id,
        prim,
        score::FLOAT as comp_score
    FROM venues v_ref
    JOIN venues v_comp ON v_ref.surface_category = v_comp.surface_category 
        AND v_ref.city = v_comp.city
        AND v_ref.id != v_comp.id
    JOIN venue_vectors vv ON v_comp.id = vv.venue_id
    CROSS JOIN jsonb_each(vv.primitives_json) AS t(prim, score)
),
venue_percentiles AS (
    SELECT 
        reference_venue_id,
        prim,
        PERCENT_RANK() OVER (PARTITION BY reference_venue_id, prim ORDER BY comp_score) as percentile_rank,
        AVG(comp_score) OVER (PARTITION BY reference_venue_id, prim) as competitor_avg,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY comp_score) OVER (PARTITION BY reference_venue_id, prim) as top_quartile_score,
        MAX(comp_score) OVER (PARTITION BY reference_venue_id, prim) as leader_score
    FROM competitor_primitives
)
SELECT 
    v.venue_name,
    prim,
    vv_ref.primitives_json ->> prim as your_score,
    ROUND(vp.percentile_rank * 100)::INT as percentile_rank,
    ROUND(vp.competitor_avg::NUMERIC, 2) as avg_competitor,
    ROUND(vp.leader_score::NUMERIC, 2) as leader_score,
    CASE 
        WHEN vp.percentile_rank >= 0.75 THEN '🟢 STRENGTH'
        WHEN vp.percentile_rank >= 0.50 THEN '🟡 COMPETITIVE'
        ELSE '🔴 GAP'
    END as status
FROM venues v
JOIN venue_vectors vv_ref ON v.id = vv_ref.venue_id
JOIN venue_percentiles vp ON v.id = vp.reference_venue_id
WHERE v.id = $1
ORDER BY vp.percentile_rank DESC;
```

---

### Feature 11: Friction Funnel

**Client Experience:**
```
Venue dashboard shows: "Where are customers dropping off?"

CUSTOMER JOURNEY FUNNEL

Stage 1: DISCOVERY
├─ Google search (monthly): 8,420 impressions
├─ Zomata listing views: 3,210
├─ Instagram reach: 2,150
└─ Total aware audience: ~13,780 per month

Stage 2: INTENT (Click through)
├─ Google click-through rate: 12% (1,010 clicks)
├─ Zomata click-through rate: 18% (578 clicks)
├─ Instagram click-through rate: 8% (172 clicks)
└─ Total intent audience: ~1,760

FRICTION DETECTED ⚠️
├─ Drop from Discovery to Intent: 87% (13,780 → 1,760)
├─ Root cause: Zomata listing incomplete (no menu photos), Instagram outdated
├─ Quick fix: Update Zomata photos (+5-8% CTR), post 2x weekly on Instagram (+3-5% CTR)
└─ Expected improvement: 15-20 additional intent clicks/week

Stage 3: BOOKING (Payment)
├─ Intent audience: 1,760
├─ Actual bookings: 412
├─ Conversion rate: 23.4%
├─ Friction: 76.6% of interested people don't book
├─ Root cause: Booking UI complex, delivery takes 8 minutes (bad UX)

Stage 4: VISIT (Show up)
├─ Bookings: 412
├─ Actual visits: 389 (94% show-up rate)
├─ Friction: 6% no-show rate
├─ Root cause: Acceptable (industry average 5-8%)

Stage 5: REPEAT (Come back)
├─ First visits: 389
├─ Repeat visits within 60 days: 182 (47%)
├─ Friction: 53% don't come back
├─ Root cause: Low engagement retention (no WhatsApp/email follow-up)

PRIORITY IMPROVEMENTS (ROI-ranked)
1️⃣ Fix booking UI (Stage 2→3) — Quick win: +4-6% booking rate = 17-25 extra bookings/month
2️⃣ Update Zomata photos (Stage 1→2) — Easy win: +5-8% CTR = 16-26 extra intents/month
3️⃣ WhatsApp after-visit (Stage 4→5) — Medium effort: +12-18% repeat = 22-35 extra repeats/month
```

**Data Requirements:**
```sql
customer_journey_events (funnel tracking)
├─ event_id (PK)
├─ customer_id
├─ venue_id
├─ event_type (discovery_impression, discovery_click, booking_initiated, booking_completed, visit_confirmed, post_visit_follow_up)
├─ event_source (google, zomata, instagram, direct, etc.)
├─ timestamp
└─ metadata (page_viewed, campaign_id, etc.)

funnel_metrics (pre-computed per source)
├─ venue_id
├─ source
├─ stage_1_impressions
├─ stage_2_clicks
├─ stage_3_bookings
├─ stage_4_visits
├─ stage_5_repeats
├─ conversion_rate_1_2 (impressions to clicks)
├─ conversion_rate_2_3 (clicks to bookings)
├─ conversion_rate_3_4 (bookings to visits)
├─ conversion_rate_4_5 (visits to repeats)
└─ drop_off_stage (where most friction is)

friction_analysis (identified blockers)
├─ venue_id
├─ friction_stage
├─ root_cause (from data patterns + venue interviews)
├─ estimated_impact_if_fixed (% improvement)
├─ recommendation
└─ effort_level (quick_win, medium, hard)
```

---

### Feature 12: Cohort Retention

**Client Experience:**
```
Venue dashboard shows: "Lifetime value by acquisition source"

CUSTOMER COHORTS BY ACQUISITION SOURCE

📊 COHORT: Google Organic (August 2025)
├─ Size: 34 new customers acquired
├─ Avg first spend: ₹920
├─ Month 1 repeat rate: 41% (14 customers)
├─ Month 2 repeat rate: 24% (8 customers)
├─ Month 3 repeat rate: 15% (5 customers)
├─ Lifetime value (6-month avg): ₹4,250 per customer
├─ Acquisition cost: Free (organic)
└─ Return: Infinite (no cost)

📊 COHORT: Instagram Campaign (September 2025)
├─ Size: 28 new customers acquired
├─ Avg first spend: ₹780
├─ Month 1 repeat rate: 57% (16 customers) ✅ Better!
├─ Month 2 repeat rate: 39% (11 customers)
├─ Month 3 repeat rate: 28% (8 customers)
├─ Lifetime value (6-month avg): ₹3,680 per customer
├─ Acquisition cost: ₹250/customer
├─ Net LTV: ₹3,430
└─ Return: 13.7x (strong ROI!)

INSIGHT
├─ Instagram attracts more repeat-prone customers (Party Seekers)
├─ Google attracts one-time explorers (Discovery Explorers)
├─ Instagram cohort is younger, more loyal
├─ Recommendation: "Increase Instagram spend; it attracts stickier customers"

RETENTION CURVE (All cohorts combined):
└─ Month 1: 51% repeat (standard hospitality)
   Month 2: 28% repeat (expected decay)
   Month 3: 16% repeat
   Month 6: 8% repeat
```

**Data Requirements:**
```sql
acquisition_cohorts (grouped by month + source)
├─ cohort_id (PK)
├─ venue_id
├─ acquisition_source (google, instagram, zomata, referral, etc.)
├─ acquisition_month
├─ customer_ids (array of customers from this cohort)
├─ cohort_size

cohort_retention (tracked monthly)
├─ cohort_id
├─ month_0_size (initial cohort)
├─ month_1_repeats (customers who visited again)
├─ month_2_repeats
├─ month_3_repeats
├─ month_6_repeats
├─ repeat_rate_month_1 (%)
├─ repeat_rate_month_3 (%)
└─ repeat_rate_month_6 (%)

cohort_ltv (lifetime value computed)
├─ cohort_id
├─ avg_first_order_value
├─ avg_ltv_6_month
├─ avg_ltv_12_month
├─ acquisition_cost
├─ net_ltv (ltv - acq cost)
├─ roi_multiple (ltv / acq cost)
└─ recommendation (invest_more, reduce, etc.)
```

**Algorithm:**
```sql
-- Cohort retention analysis: track each acquisition cohort's repeat behavior
WITH cohorts AS (
    SELECT 
        TO_DATE(TO_CHAR(cv.visit_date, 'YYYY-MM'), 'YYYY-MM') as cohort_month,
        c.acquisition_source,
        c.id as customer_id,
        cv.venue_id
    FROM customers c
    JOIN customer_visits cv ON c.id = cv.customer_id
    WHERE cv.visit_date = (SELECT MIN(visit_date) FROM customer_visits WHERE customer_id = c.id)  -- First visit only
),
repeat_months AS (
    SELECT 
        cohorts.cohort_month,
        cohorts.acquisition_source,
        cohorts.customer_id,
        cohorts.venue_id,
        COUNT(DISTINCT DATE_TRUNC('MONTH', cv.visit_date)) as months_active
    FROM cohorts
    JOIN customer_visits cv ON cohorts.customer_id = cv.customer_id
    GROUP BY cohorts.cohort_month, cohorts.acquisition_source, cohorts.customer_id, cohorts.venue_id
)
SELECT 
    cohort_month,
    acquisition_source,
    COUNT(DISTINCT customer_id) as cohort_size,
    COUNT(DISTINCT customer_id) FILTER (WHERE months_active >= 2) * 100.0 / COUNT(DISTINCT customer_id) as repeat_rate_pct,
    ROUND(AVG(total_spent), 0) as avg_ltv
FROM repeat_months
GROUP BY cohort_month, acquisition_source
ORDER BY cohort_month DESC;
```

---

## 🔮 FEATURES 13-16: ADS FOUNDATION (PHASE 2 - PLACEHOLDER)

### Features 13-16 Overview

**Status:** Blocked by Phase 2 data dependencies  
**Unlock condition:** When ads + booking system integration is live

These 4 features require real-time campaign & booking data that doesn't exist yet.

### Feature 13: Content Recommendation (Phase 2)

**Purpose:** Recommend which marketing content (images, copy, offers) converts best for each archetype.

**Blocked by:** Need real campaign performance data (impressions, clicks, conversions by creative).

**Once unlocked (Phase 2):**
- Input: Ad creative + archetype targeting
- Output: Expected conversion rate + predicted ROI
- Database: campaign_performance, creative_analytics

### Feature 14: Real-Time Dynamic Recommendations (Phase 2)

**Purpose:** Update venue recommendations in real-time as customer behavior changes.

**Blocked by:** Need live booking + visit data pipeline.

**Once unlocked (Phase 2):**
- Input: Live venue metrics (this week's visits, spend, archetype mix)
- Output: "Your customer mix changed this week—new recommendations"
- Database: Real-time event stream

### Feature 15: Operational Simulation (Phase 2)

**Purpose:** Simulate "What if we change X?" and predict revenue impact.

**Blocked by:** Need causal models trained on venue behavior changes + outcomes.

**Once unlocked (Phase 2):**
- Input: "Add live music 3x/week" or "Increase staff by 1"
- Output: "Expected impact: +₹45,000/month, +18% repeat rate"
- Database: Intervention_outcomes, causal_models

### Feature 16: Trend Detection & Forecasting (Phase 2)

**Purpose:** Detect emerging patterns and predict what's next in your market.

**Blocked by:** Need historical pattern evolution data + market signals.

**Once unlocked (Phase 2):**
- Input: Market patterns from step_4b governance reports
- Output: "New pattern emerging: Food Delivery + Dine-In hybrid is +45% trending"
- Database: drift_signals, pattern_evolution

---

## 🎨 PHASE 1 MARKETING ENGINE (NEW SECTION)

### Why This Matters
Module 2 identifies **what behavioral signals each venue has**. Phase 1 Marketing Engine translates those signals into **which marketing channels will work** to acquire new customers and retain existing ones.

**Input:** Venue's Module 2 profile (primitives, fitness, demographic-archetype mix)  
**Output:** "Here's what marketing will work for YOUR venue" with expected ROI lifts  
**Data:** India-specific research on channel effectiveness + behavioral mechanisms

### Phase 1: Behavioral Recommendations (NOW - No Ads Integration Needed)
```
Venue Profile (Module 2)
  ├─ Primitives scores (food_quality: 0.87, social_energy: 0.72, etc.)
  ├─ Fitness dimensions (repeat_habit: 0.82, group_energy: 0.28)
  ├─ Demographic segments (60% office workers, 30% couples)
  └─ Archetype distribution (60% Repeat Regulars, 25% Calm Pairs)
       ↓
Behavioral Mechanism Matching (India-Specific)
  ├─ Habit Formation → WhatsApp broadcasts (+30-40% repeat visits)
  ├─ FOMO → SMS urgency campaigns (+15-25% same-week bookings)
  ├─ Social Proof → Zomata/Swiggy platform leverage (+25-60% uplift)
  ├─ Identity Signaling → Instagram premium aesthetic (+12-18% conversion)
  └─ Environmental Expectation → Instagram Reels (+15-25% engagement)
       ↓
Recommendations Engine Output
  ├─ Acquisition channels (ranked by expected lift)
  ├─ Retention channels (ranked by expected impact)
  ├─ Message templates (customized per archetype)
  ├─ Implementation guides (step-by-step)
  └─ Expected ROI lift percentages (with confidence levels)
```

### Implementation Plan: Week 1-3

**Week 1: Build Backend Lookup Tables**
```
Database tables (new):
├─ campaign_templates
│  ├─ template_id (PK)
│  ├─ demographic_segment (e.g., "office_workers_lunch")
│  ├─ target_archetype (e.g., "Repeat Regular")
│  ├─ behavioral_mechanism (e.g., "habit_formation")
│  ├─ channel (whatsapp, email, sms, instagram, zomata, etc.)
│  ├─ message_template (handlebars format with {{variables}})
│  ├─ suggested_roi_lift_percentage (from research)
│  ├─ confidence_level (HIGH, MEDIUM, LOW)
│  └─ implementation_guide (copy-paste instructions)
│
├─ channel_mechanism_mapping
│  ├─ channel (whatsapp, sms, email, instagram, etc.)
│  ├─ behavioral_mechanism (habit_formation, FOMO, social_proof, etc.)
│  ├─ effectiveness_score (1-10 for India hospitality)
│  ├─ baseline_roi_lift_min (%) — from PHASE_1_INDIA_BEHAVIORAL_RESEARCH.md
│  ├─ baseline_roi_lift_max (%)
│  ├─ primary_use_case (acquisition vs retention)
│  └─ research_confidence (HIGH/MEDIUM/LOW)
│
├─ behavioral_mechanism_catalog
│  ├─ mechanism_id (PK)
│  ├─ name (habit_formation, FOMO, social_proof, etc.)
│  ├─ description
│  ├─ psychological_basis
│  ├─ key_triggers (what makes it work?)
│  ├─ best_channels (array) — ranked by effectiveness
│  ├─ timeline_to_effect (weeks)
│  └─ research_citations (link to PHASE_1_INDIA_BEHAVIORAL_RESEARCH.md)
│
└─ venue_marketing_recommendations
   ├─ recommendation_id (PK)
   ├─ venue_id (FK)
   ├─ generated_at
   ├─ demographic_segment_recommendations (array)
   │  ├─ segment
   │  ├─ archetype_fit (%)
   │  ├─ top_channel_recommendation
   │  ├─ expected_roi_lift (%)
   │  └─ implementation_steps
   ├─ acquisition_channels (ranked list)
   ├─ retention_channels (ranked list)
   ├─ not_recommended (channels that won't work + why)
   └─ confidence_score_overall
```

**Data Population Source:**
All benchmarks come from: `PHASE_1_INDIA_BEHAVIORAL_RESEARCH.md`
- Section 1: Channel effectiveness (WhatsApp: 85-95% open, SMS: 98%, etc.)
- Section 2: Mechanism effectiveness (habit formation +30-40%, FOMO +15-25%, etc.)
- Section 3: Lookup tables (channel × mechanism × archetype mapping)

**SQL to populate from research:**
```sql
-- Example: Habit Formation mechanism
INSERT INTO behavioral_mechanism_catalog VALUES
('habit_formation', 'Habit Formation (Temporal Anchoring)', 
 'Regular reminders reinforce routine behavior', 'Cue-routine-reward loops',
 ['weekly reminder', 'time-based anchor'], ['whatsapp', 'email', 'sms'],
 ['Repeat Regulars'], '4-6 weeks', 'Waakif playbook, Vendor case studies');

-- Example: Channel × Mechanism mapping
INSERT INTO channel_mechanism_mapping VALUES
('whatsapp', 'habit_formation', 9, ['Repeat Regulars'], 30, 40,
 'retention', 'HIGH');
```

**Week 2: Build Recommendations Engine Logic**
```python
# pseudocode: recommendations_engine.py

def generate_venue_recommendations(venue_id):
    # 1. Fetch venue profile from Module 2
    venue = get_venue_profile(venue_id)  # primitives, fitness, demographics
    
    # 2. Get demographic-archetype breakdown
    archetypes = query("""
        SELECT archetype_name, prevalence_percentage
        FROM demographic_archetype_mapping
        WHERE segment_id IN (SELECT segment_id FROM venue_demographics WHERE venue_id = ?)
    """)
    
    # 3. For each demographic segment, find best channels
    recommendations = []
    for segment in venue.demographic_segments:
        for archetype in archetypes:
            # Find best channel for this archetype + mechanism combo
            best_channels = query("""
                SELECT c.channel, c.behavioral_mechanism, c.baseline_roi_lift_max
                FROM channel_mechanism_mapping c
                JOIN campaign_templates ct ON c.channel = ct.channel
                WHERE ct.target_archetype = ? AND ct.demographic_segment = ?
                ORDER BY c.baseline_roi_lift_max DESC
                LIMIT 1
            """, [archetype.name, segment])
            
            recommendations.append({
                'segment': segment,
                'archetype': archetype.name,
                'channel': best_channels[0].channel,
                'mechanism': best_channels[0].behavioral_mechanism,
                'expected_roi_lift': best_channels[0].baseline_roi_lift_max,
                'message_template': get_template(segment, archetype, best_channels[0].channel)
            })
    
    return {
        'venue_id': venue_id,
        'acquisition_channels': [r for r in recommendations if r['mechanism'] != 'habit_formation'],
        'retention_channels': [r for r in recommendations if r['mechanism'] == 'habit_formation'],
        'confidence_score': calculate_confidence(venue, recommendations)
    }
```

**Week 3: Build UI Dashboard**
```
MARKETING STRATEGY FOR [Venue Name]

📊 VENUE PROFILE SUMMARY
├─ Dominant archetypes: Repeat Regulars (62%), Calm Pairs (30%)
├─ Strongest fitness: repeat_habit (0.82), office_lunch (0.78)
├─ Opportunity: group_energy (0.28) - could add music/events
└─ Best demographic fit: Office workers, weekday lunch, 2 people

🎯 ACQUISITION STRATEGY (New Customers)
├─ [1] Instagram - Environmental Expectation
│  ├─ Mechanism: Pre-visit imagery shapes expectations
│  ├─ Expected: +15-25% new bookings
│  ├─ Best for: Calm Pairs, Discovery Explorers
│  ├─ Confidence: MEDIUM (Reels data; India-specific case studies)
│  └─ [Create Campaign] [Learn More] [See Example]
│
├─ [2] Zomata/Swiggy - Social Proof
│  ├─ Mechanism: High ratings + platform visibility
│  ├─ Expected: +25-60% during featured placement
│  ├─ Best for: All demographics (platform-first discovery)
│  ├─ Confidence: MEDIUM-HIGH (platform case studies)
│  └─ [Optimize Listing] [Learn More]
│
└─ [Not Recommended] TikTok
   └─ Why: Your group_energy is low; TikTok effective for Party Seekers only

💪 RETENTION STRATEGY (Keep Existing Customers)
├─ [1] WhatsApp - Habit Formation ⭐ PRIMARY
│  ├─ Mechanism: Regular reminders → reinforced routine
│  ├─ Expected: +30-40% repeat frequency
│  ├─ Best for: Repeat Regulars (your 62%)
│  ├─ Confidence: MEDIUM (vendor-reported; India playbooks)
│  ├─ Message: "Your Friday lunch spot is ready"
│  └─ [Create Campaign] [Learn More] [See Template]
│
└─ [Optional] Email
   ├─ Expected: +15-25% repeat frequency (slower than WhatsApp)
   ├─ Best for: Detailed storytelling + loyalty benefits
   └─ [Create Campaign] [Learn More]

📚 LEARNING RESOURCES
├─ Why WhatsApp works better than email in India (85-95% vs 40-44% open)
├─ How to write FOMO messages that drive urgency (2-4 hour conversion)
├─ Zomata algorithm: how to rank higher
├─ Real examples: Similar venues (office lunch spots) with +35% repeat results
└─ Glossary: What's a behavioral primitive? What's an archetype?
```

### Data Sources for Phase 1 Lookup Tables

**All India-specific benchmarks from:**
- `PHASE_1_INDIA_BEHAVIORAL_RESEARCH.md` (complete reference)
  - Section 1: Channel effectiveness with confidence levels
  - Section 2: Behavioral mechanism effectiveness
  - Section 3: Channel × Mechanism × Archetype lookup tables
  - Section 4: Expected ROI lifts by use case
  - Section 5: Data gaps (what we don't know yet)

**Key Metrics for Database:**
| Mechanism | Best Channel | Expected Lift | Timeline | Confidence |
|-----------|--------------|---------------|----------|-----------|
| Habit Formation | WhatsApp | +30-40% | 4-8 weeks | MEDIUM |
| FOMO/Scarcity | SMS | +15-25% | 2-4h to 2-8 weeks | MEDIUM |
| Social Proof | Zomata/Swiggy | +25-60% | 2-4 weeks | MEDIUM-HIGH |
| Identity Signaling | Instagram + Influencers | +12-18% | 4-16 weeks | LOW-MEDIUM |
| Environmental Expectation | Instagram Reels | +15-25% | 4-12 weeks | MEDIUM-HIGH |

### Integration with Module 2 Database

**Phase 1 Marketing Engine reads from:**
- `venues` table (venue profile)
- `demographic_segments` & `demographic_archetype_mapping` (who this venue attracts)
- `behavioral_patterns` & `fitness_dimensions` (what makes this venue work)

**Phase 1 Marketing Engine writes to:**
- `campaign_templates` (India-specific message templates)
- `channel_mechanism_mapping` (lookup for effectiveness)
- `behavioral_mechanism_catalog` (reference data)
- `venue_marketing_recommendations` (personalized recommendations per venue)

**No new data collection needed for Phase 1:**
- All inputs come from existing Module 2 analysis
- All benchmark data comes from published research (PHASE_1_INDIA_BEHAVIORAL_RESEARCH.md)
- No campaign execution, no attribution yet (that's Phase 2)

### Phase 2 (LATER): When Ads Data Arrives
```
⏳ Phase 2 launches when:
├─ Booking system can tag campaign source
├─ POS system can link transactions
├─ Module 3 tracking system operational
├─ Ads data pipeline live
└─ Customer identification system ready

Then Phase 2 adds:
├─ Real campaign performance tracking
├─ Attribution: which campaigns → which bookings → which repeats
├─ ROI measurement: predicted vs actual
├─ Model refinement: India-specific CAC/ROAS benchmarks
└─ 19 additional features (optimization, forecasting, etc.)
```

---

## 🗄️ DATABASE PLATFORM DECISION (FINAL - 2026-05-14)

**Choice: AWS RDS PostgreSQL (ap-south-1, Single-AZ)**

**Decision Factors:**
- Account created April 2026 → **Credit-based system: $100-200 in AWS credits**
- Single db.t3.micro instance (no splitting of resources)
- Private VPC (no public IPv4 charges = $0 extra)
- Light usage for client pitches (10-20 min/session) = **~$5-10/month credits burned**

**Cost Runway:**
- Free tier credits: $100-200 (until April 2027)
- AWS Activate Founders: $1,000 (apply immediately at aws.amazon.com/activate)
- Total runway: **~$1,100-1,200 (covers Phase 1 through Month 6+)**

**Migration Risk: ZERO**
- Both AWS RDS and Azure use standard PostgreSQL
- Migration time: 5-15 minutes with `pg_dump` / `pg_restore`
- No application code changes required
- Can switch platforms anytime without lock-in

**Setup Checklist:**
```
☐ Create db.t3.micro (NOT db.t3.small)
☐ Allocate 15GB storage (leave 5GB buffer under 20GB limit)
☐ Set "Publicly Accessible" to NO
☐ Deploy in ap-south-1 (Mumbai), default VPC
☐ Apply for AWS Activate Founders ($1,000) immediately
☐ Set billing alert at $50/month
☐ Do NOT run multiple databases or Aurora on free tier
```

---

## 📋 POSTGRESQL SCHEMA: ALL TABLES FOR 16 FEATURES

### Core Venue & Vector Tables

**Table: `venues`**
```sql
- venue_id (PK, SERIAL)
- place_id (VARCHAR 255, UNIQUE) — Google Place ID
- venue_name (VARCHAR 512) — Full venue name
- city (VARCHAR 100) — navi-mumbai, mumbai-main, mumbai-sobo, thane
- area (VARCHAR 255) — Neighborhood/area name
- latitude (NUMERIC(10,8))
- longitude (NUMERIC(10,8))
- surface_category (VARCHAR 100) — Casual Dining, Fine Dining, Cafe, Bar, etc.
- google_types (JSONB) — Array of Google Place types
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

**Table: `venue_vectors`**
```sql
- vector_id (PK, SERIAL)
- venue_id (FK → venues)
- place_id (VARCHAR 255)
- city (VARCHAR 100)
- primitives_json (JSONB) — 54 behavioral primitives (food_quality, social_energy, etc.)
- fitness_dimensions (JSONB) — {office_lunch, repeat_habit, social_dwell, group_energy, destination_visit}
- behavioral_summary (JSONB) — {operational_quality, retention_strength, monetization_potential}
- confidence_score (FLOAT) — 0-1, confidence in this vector
- final_confidence_percentage (FLOAT) — 0-100
- source (VARCHAR 100) — google, zomata, magicpin
- generated_from (VARCHAR 255) — step_5_behavioral_scores.json reference
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- INDEX: venue_id, place_id, city
```

**Table: `venue_fitness_dimensions`**
```sql
- fitness_id (PK, SERIAL)
- venue_id (FK → venues)
- office_lunch (FLOAT 0-1) — How well this venue serves office lunch use case
- repeat_habit (FLOAT 0-1) — How well this venue creates repeat habits
- social_dwell (FLOAT 0-1) — How well this venue supports social group hangouts
- group_energy (FLOAT 0-1) — How well this venue energizes groups/parties
- destination_visit (FLOAT 0-1) — How well this venue attracts destination visitors
- created_at (TIMESTAMP)
```

---

### Similarity Tables (Feature 1-2: Similar Venues Comparison & Consulting Redirect)

**Table: `venue_similarity`**
```sql
- similarity_id (PK, SERIAL)
- client_venue_id (FK → venues) — The venue being analyzed
- similar_venue_id (FK → venues) — A similar venue
- similarity_score (FLOAT 0-1) — Cosine similarity between vectors
- shared_primitives (JSONB) — Array of primitive names both venues score high on
- shared_primitive_count (INT) — Number of shared primitives
- rank_position (INT 1-25) — Ranking order (1=most similar)
- city (VARCHAR 100)
- created_at (TIMESTAMP)
- INDEX: client_venue_id, rank_position, city
```

---

### Behavioral Pattern Tables (Features 2, 5, 10, 16)

**Table: `behavioral_patterns`**
```sql
- pattern_id (PK, SERIAL)
- pattern_name (VARCHAR 255) — Human-readable pattern name
- pattern_description (TEXT) — What this pattern represents
- co_occurring_primitives (JSONB) — Array of primitive names that cluster together
- archetype_hypothesis (VARCHAR 255) — Inferred user archetype for this pattern
- total_venues_matching (INT) — How many venues exhibit this pattern
- prevalence_percentage (FLOAT 0-100) — % of market with this pattern
- city (VARCHAR 100)
- source_file (VARCHAR 255) — step_4_patterns_recognized.json reference
- created_at (TIMESTAMP)
- INDEX: pattern_name, city, prevalence_percentage DESC
```

**Table: `pattern_venues`**
```sql
- pattern_venue_id (PK, SERIAL)
- venue_id (FK → venues)
- pattern_id (FK → behavioral_patterns)
- confidence_score (FLOAT 0-1) — How sure we are this venue matches this pattern
- is_primary_pattern (BOOLEAN) — Is this the venue's main pattern?
- created_at (TIMESTAMP)
- INDEX: venue_id, pattern_id, confidence_score DESC
```

**Table: `pattern_scores`**
```sql
- score_id (PK, SERIAL)
- pattern_id (FK → behavioral_patterns)
- co_occurring_primitives (JSONB) — Which primitives cluster in this pattern
- confidence_score (FLOAT 0-1) — Market-level confidence in pattern
- evidence_density (FLOAT 0-1) — How densely clustered the primitives are
- temporal_consistency (FLOAT 0-1) — How stable is this pattern over time
- evidence_diversity (FLOAT 0-1) — How diverse are the venues showing this pattern
- commercial_reliability (FLOAT 0-1) — Likelihood this pattern drives business outcomes
- venue_count (INT) — How many venues match this pattern
- prevalence_percentage (FLOAT 0-100)
- source_file (VARCHAR 255) — step_5_patterns_scored.json reference
- created_at (TIMESTAMP)
- INDEX: pattern_id, confidence_score DESC
```

**Table: `pattern_fitness_dimensions`**
```sql
- fitness_id (PK, SERIAL)
- pattern_id (FK → behavioral_patterns)
- fitness_for_office_lunch (FLOAT 0-1)
- fitness_for_repeat_habit (FLOAT 0-1)
- fitness_for_social_dwell (FLOAT 0-1)
- fitness_for_group_energy (FLOAT 0-1)
- fitness_for_destination_visit (FLOAT 0-1)
- created_at (TIMESTAMP)
```

**Table: `intervention_triggers`**
```sql
- trigger_id (PK, SERIAL)
- pattern_id (FK → behavioral_patterns)
- intervention_type (VARCHAR 100) — operational_optimization, premium_justification, dwell_monetization, friction_reduction
- description (TEXT) — What business action to take
- expected_impact (JSONB) — {metric: "repeat_rate", lift: 0.25, confidence: "MEDIUM"}
- created_at (TIMESTAMP)
```

---

### Data Quality Tables (Feature 16: Trend Detection)

**Table: `data_quality_metrics`**
```sql
- metric_id (PK, SERIAL)
- city (VARCHAR 100)
- avg_confidence (FLOAT 0-1) — Average signal confidence across all venues
- avg_reliability (FLOAT 0-1) — Pattern stability and evidence strength
- reliability_score (FLOAT 0-1) — Overall data quality composite
- high_reliability_clusters (INT) — Count of good-quality pattern clusters
- total_clusters (INT) — Total pattern clusters analyzed
- metric_date (DATE) — When this metric was computed
- source_file (VARCHAR 255) — step_4b_governance_report.json reference
- created_at (TIMESTAMP)
- INDEX: city, metric_date DESC
```

**Table: `drift_signals`**
```sql
- signal_id (PK, SERIAL)
- city (VARCHAR 100)
- new_pattern_name (VARCHAR 255) — Pattern emerging in market
- confidence_score (FLOAT 0-1) — Confidence this pattern is emerging
- venue_count (INT) — How many venues show this emerging pattern
- emergence_date (DATE) — When detected
- trend_direction (VARCHAR 50) — increasing, stable, decreasing
- interpretation (TEXT) — What this drift means for the market
- source_file (VARCHAR 255) — step_4b_governance_report.json reference
- created_at (TIMESTAMP)
- INDEX: city, emergence_date DESC, confidence_score DESC
```

---

### Survey & User Tables (Features 3, 5, 12)

**Table: `survey_responses_canonical`**
```sql
- response_id (PK, SERIAL)
- user_id (VARCHAR 255, UNIQUE) — Canonical user identifier
- form_version (VARCHAR 50) — v1, v2, new
- submission_date (DATE)
- age_group (VARCHAR 50) — 18-25, 26-35, 36-50, 50+
- company_size (VARCHAR 50) — 1, 2-4, 5-10, 10+
- when_visits (VARCHAR 100) — weekdays_lunch, weekends, evenings, etc.
- reason_visit (VARCHAR 255) — office_lunch, social, celebration, explore, date, etc.
- avg_spend_rupees (INT) — ₹0-500, ₹500-1000, ₹1000+
- social_personality (VARCHAR 100) — introvert, ambivert, extrovert
- energy_preference (VARCHAR 100) — calm, balanced, high_energy
- place_preference (VARCHAR 100) — intimate, social, grand, eclectic
- discovery_channels (JSONB) — Array: google, instagram, zomata, friends, etc.
- fomo_tendency (VARCHAR 50) — low, medium, high
- group_role (VARCHAR 100) — organizer, influencer, participator, passenger
- music_preference (VARCHAR 100) — none, background, live, dancing
- revisit_vs_explore (VARCHAR 50) — revisit_loyal, balanced, explore_new
- email (VARCHAR 255)
- instagram (VARCHAR 255)
- newsletter_consent (BOOLEAN)
- created_at (TIMESTAMP)
- INDEX: user_id, form_version, age_group, energy_preference
```

**Table: `user_archetypes`**
```sql
- archetype_id (PK, SERIAL)
- archetype_name (VARCHAR 255) — Party Seeker, Calm Pairs, Discovery Explorer, Repeat Regular, Premium Prioritizer, etc.
- archetype_description (TEXT) — Behavioral profile of this archetype
- social_personality (VARCHAR 100) — dominant personality
- energy_preference (VARCHAR 100) — dominant energy preference
- place_preference (VARCHAR 100) — dominant place preference
- typical_spend_rupees (INT) — Average spend for this archetype
- revisit_frequency (VARCHAR 50) — how often they return
- discovery_channels (JSONB) — which channels work for acquisition
- response_count (INT) — How many survey responses match this archetype
- prevalence_percentage (FLOAT 0-100) — % of surveyed population
- confidence_score (FLOAT 0-1) — How distinct/reliable is this archetype
- created_at (TIMESTAMP)
- INDEX: archetype_name, prevalence_percentage DESC
```

---

### Customer & Transaction Tables (Features 3, 4, 5, 11, 12)

**Table: `customers`**
```sql
- customer_id (PK, SERIAL)
- venue_id (FK → venues)
- user_id (FK → survey_responses_canonical, nullable)
- inferred_archetype_id (FK → user_archetypes, nullable) — Inferred from behavior
- acquisition_source (VARCHAR 100) — google, instagram, zomata, referral, direct
- acquisition_date (DATE)
- first_visit_date (DATE)
- last_visit_date (DATE)
- total_visits (INT)
- total_spend_rupees (NUMERIC 10,2)
- phone (VARCHAR 20, nullable)
- email (VARCHAR 255, nullable)
- created_at (TIMESTAMP)
- INDEX: venue_id, acquisition_source, inferred_archetype_id, last_visit_date DESC
```

**Table: `customer_visits`**
```sql
- visit_id (PK, SERIAL)
- customer_id (FK → customers)
- venue_id (FK → venues)
- visit_date (DATE)
- visit_time (TIME, nullable)
- party_size (INT, nullable) — How many people in the group
- order_value (NUMERIC 10,2) — Total spend in rupees
- dwell_minutes (INT, nullable) — How long they stayed
- visit_source_tag (VARCHAR 100, nullable) — which campaign/source brought them
- notes (TEXT, nullable)
- created_at (TIMESTAMP)
- INDEX: customer_id, venue_id, visit_date DESC
```

---

### Demographic-Archetype Bridge Tables (For sales/client communication)

**Table: `demographic_segments`**
```sql
- segment_id (PK, VARCHAR 50) — col_1, office_lunch_1, fam_1, etc.
- segment_name (VARCHAR 255) — college_kids_weekend, office_workers_lunch, families_casual_dining
- segment_description (TEXT)
- age_group (VARCHAR 50) — 18-25, 26-35, etc.
- company_size (VARCHAR 50) — 1, 2-4, 5-10, etc.
- when_visits (VARCHAR 100) — weekends, weekdays_lunch, evenings
- city (VARCHAR 100)
- created_at (TIMESTAMP)
```

**Table: `demographic_archetype_mapping`**
```sql
- mapping_id (PK, SERIAL)
- segment_id (FK → demographic_segments)
- archetype_name (VARCHAR 255) — Party Seeker, Calm Pairs, etc.
- prevalence_percentage (FLOAT 0-100) — % of segment that is this archetype
- population_count (INT) — How many survey responses match this combo
- confidence_score (FLOAT 0-1)
- created_at (TIMESTAMP)
- INDEX: segment_id, prevalence_percentage DESC
```

**Table: `demographic_archetype_interventions`**
```sql
- intervention_id (PK, SERIAL)
- segment_id (FK → demographic_segments)
- archetype_name (VARCHAR 255)
- intervention_type (VARCHAR 100) — music_and_energy, dwell_monetization, authenticity_leverage, etc.
- description (TEXT) — Detailed action to take
- expected_roi (VARCHAR 50) — 1.57x revenue, 1.28x order_frequency, etc.
- implementation_effort (VARCHAR 50) — quick, medium, hard
- created_at (TIMESTAMP)
```

**Table: `demographic_behavioral_alignment`**
```sql
- alignment_id (PK, SERIAL)
- segment_id (FK → demographic_segments)
- archetype_name (VARCHAR 255)
- primary_primitives (JSONB) — Array of top 4-5 primitives for this segment-archetype combo
- secondary_primitives (JSONB) — Array of supporting primitives
- critical_fitness_dimension (VARCHAR 100) — office_lunch, repeat_habit, social_dwell, etc.
- created_at (TIMESTAMP)
```

---

### Churn & Retention Tables (Features 4, 12)

**Table: `customer_churn_signals`**
```sql
- signal_id (PK, SERIAL)
- customer_id (FK → customers)
- venue_id (FK → venues)
- churn_risk_score (FLOAT 0-1) — 0=no risk, 1=certain to churn
- churn_risk_category (VARCHAR 50) — HIGH, MEDIUM, LOW
- days_since_last_visit (INT)
- historical_visit_frequency (FLOAT) — Average days between visits
- frequency_decline_percentage (FLOAT) — How much frequency has dropped (%)
- last_computed_date (DATE)
- recommended_intervention (VARCHAR 255) — WhatsApp reminder, exclusive offer, etc.
- created_at (TIMESTAMP)
- INDEX: venue_id, churn_risk_score DESC, last_computed_date DESC
```

---

### Marketing & Campaign Tables (Phase 1 Marketing Engine)

**Table: `campaign_templates`**
```sql
- template_id (PK, SERIAL)
- demographic_segment (VARCHAR 255) — college_kids_weekend, office_workers_lunch, etc.
- target_archetype (VARCHAR 255) — Party Seeker, Repeat Regular, etc.
- behavioral_mechanism (VARCHAR 100) — habit_formation, FOMO, social_proof, identity_signaling, environmental_expectation
- channel (VARCHAR 100) — whatsapp, sms, email, instagram, zomata, tiktok
- message_template (TEXT) — Handlebars format with {{variables}}
- suggested_roi_lift_percentage (FLOAT 0-100)
- confidence_level (VARCHAR 50) — HIGH, MEDIUM, LOW
- implementation_guide (TEXT) — Step-by-step copy-paste instructions
- created_at (TIMESTAMP)
- INDEX: demographic_segment, target_archetype, channel
```

**Table: `channel_mechanism_mapping`**
```sql
- mapping_id (PK, SERIAL)
- channel (VARCHAR 100) — whatsapp, sms, email, instagram, zomata, tiktok
- behavioral_mechanism (VARCHAR 100)
- effectiveness_score (INT 1-10) — For India hospitality context
- baseline_roi_lift_min (FLOAT 0-100) — From PHASE_1_INDIA_BEHAVIORAL_RESEARCH
- baseline_roi_lift_max (FLOAT 0-100)
- primary_use_case (VARCHAR 50) — acquisition, retention
- research_confidence (VARCHAR 50) — HIGH, MEDIUM, LOW
- created_at (TIMESTAMP)
- INDEX: channel, behavioral_mechanism
```

**Table: `behavioral_mechanism_catalog`**
```sql
- mechanism_id (PK, SERIAL)
- name (VARCHAR 255) — habit_formation, FOMO, social_proof, etc.
- description (TEXT)
- psychological_basis (TEXT) — Why this mechanism works
- key_triggers (JSONB) — Array of what activates this mechanism
- best_channels (JSONB) — Array: [whatsapp, email, sms] ranked by effectiveness
- timeline_to_effect_weeks (INT) — How long before results show
- research_citations (TEXT) — References to research
- created_at (TIMESTAMP)
```

**Table: `venue_marketing_recommendations`**
```sql
- recommendation_id (PK, SERIAL)
- venue_id (FK → venues)
- generated_at (TIMESTAMP)
- demographic_segment_recommendations (JSONB) — Array of recommendations per segment
- acquisition_channels (JSONB) — Ranked list [channel, expected_lift, confidence]
- retention_channels (JSONB) — Ranked list
- not_recommended (JSONB) — [channel, reason_why]
- overall_confidence_score (FLOAT 0-1)
- created_at (TIMESTAMP)
- INDEX: venue_id, generated_at DESC
```

---

### Feature-Specific Tables

**Table: `competitive_benchmarks`** (Feature 10)
```sql
- benchmark_id (PK, SERIAL)
- venue_id (FK → venues)
- segment (VARCHAR 255) — Casual Dining → Lounge
- comparable_venue_ids (JSONB) — Array of similar venue IDs
- overall_percentile_rank (INT 0-100)
- primitive_rankings (JSONB) — {primitive: percentile_rank, venue_score, competitor_avg, gap_to_leader}
- strength_primitives (JSONB) — Where venue beats market
- gap_primitives (JSONB) — Where venue lags
- opportunities_ranked (JSONB) — Prioritized improvements
- created_at (TIMESTAMP)
- INDEX: venue_id, overall_percentile_rank DESC
```

**Table: `satisfaction_drivers`** (Feature 7)
```sql
- driver_id (PK, SERIAL)
- venue_id (FK → venues)
- archetype_name (VARCHAR 255)
- primitive_name (VARCHAR 255)
- correlation_with_satisfaction (FLOAT -1 to 1) — -1=negative, 0=none, 1=strong positive
- rank_position (INT) — 1, 2, 3 for top drivers
- variance_explained_percentage (FLOAT 0-100) — Cumulative
- sample_size (INT) — How many reviews used
- confidence_level (VARCHAR 50) — HIGH, MEDIUM, LOW
- created_at (TIMESTAMP)
- INDEX: venue_id, archetype_name, rank_position
```

---

### Summary: Table Count & Relationships

```
TOTAL TABLES: 25

Core Venue: 3 (venues, venue_vectors, venue_fitness_dimensions)
Similarity: 1 (venue_similarity)
Behavioral Patterns: 4 (behavioral_patterns, pattern_venues, pattern_scores, pattern_fitness_dimensions)
Interventions: 1 (intervention_triggers)
Data Quality: 2 (data_quality_metrics, drift_signals)
Survey/Users: 2 (survey_responses_canonical, user_archetypes)
Customers: 2 (customers, customer_visits)
Demographic Bridge: 3 (demographic_segments, demographic_archetype_mapping, demographic_archetype_interventions)
Behavioral Alignment: 1 (demographic_behavioral_alignment)
Churn: 1 (customer_churn_signals)
Marketing: 3 (campaign_templates, channel_mechanism_mapping, behavioral_mechanism_catalog)
Recommendations: 1 (venue_marketing_recommendations)
Features: 2 (competitive_benchmarks, satisfaction_drivers)

All tables have created_at timestamps and strategic indexes for fast queries.
```

---

## ✅ NEXT IMMEDIATE STEPS

### This Week (PRIORITY)
1. ✅ Clarified features (16 now, 35 with ads)
2. ✅ Created survey normalization (canonical schema + 45 responses)
3. ✅ Fixed step_5_score.py aggregation logic
4. ⏳ **TODO:** Run `python run_pipeline.py` to generate all 4 cities' pattern files
5. ⏳ **TODO:** Verify all 4 cities show consistent pattern structure
6. ⏳ **TODO:** Copy all step_*.json files to `data/raw/google_places/{city}/`

### Next Session
1. Copy raw data files to `data/raw/` subdirectories
2. Create Priority 1 config files (primitives, categories, schema, constants)
3. Run `001_init_schema.sql` to create PostgreSQL structure
4. Design detailed PostgreSQL schema incorporating step_4 and step_5 pattern outputs
5. Build amendment_service.py (source-specific recency weighting)
6. Load data into PostgreSQL
7. Build all 16 feature backend endpoints in one sprint

---

## 🚀 WHAT WE'RE BUILDING

**A complete behavioral intelligence platform:**
- Understand what venues do (Layer 1: 54 primitives from reviews)
- Understand what people want (Layer 2: 35 archetypes from surveys)
- Match them intelligently (16 features for venue operators + users + Polynovea)
- Optimize with acquisition data (35 total features when ads are added)

**No phasing. All 16 base features built in one comprehensive sprint.**

---

**Ready to proceed with Priority 1 config files?**
