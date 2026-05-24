# Pipeline Loader Reference

> **Purpose:** Authoritative record of which loader scripts load which data into which DB tables, for every source and every city/region. Read this before writing or running any loader. This document was written after the 2026-05-25 session to prevent hallucination about what is loaded where.

---

## 1. Data Sources Registry

| Source key | Status | Venues | Regions | Raw data path |
|---|---|---|---|---|
| `google` | ✅ Live | 6,008 | mumbai-main, mumbai-sobo, navi-mumbai, thane | `Database/data/raw/google_places/<region>/` |
| `magicpin_upper` | ✅ Live | 676 | mumbai, navi-mumbai, sobo, thane | `Database/data/raw/magicpin/<region>/` |
| `google_reviews` | ✅ Live | 1,120 | **thane, navi-mumbai only** | `Database/data/raw/google_reviews/<region>/` |
| `manual_reviews` | ✅ Live | 2 | manual | `Database/scripts/manual/` |
| `zomato` | ⏳ Future | — | — | — |
| `tripadvisor` | ⏳ Future | — | — | — |

> `magicpin_lower` is **RETIRED**. Do not create loaders for it. It was superseded by `google_reviews`.

---

## 2. Pipeline Steps → Tables Mapping

Every source runs through the same 6 logical steps. Each step reads a JSON file and writes to specific DB tables.

### Step 3 — Primitive Signals
**Input file:** `step_3_signals_extracted.json`  
**Tables written:** `primitives_scores` (source=`<source_key>`)  
**Join key:** `place_id` → `venues.id`

Signal extraction has **two layers**:
1. **Venue-level aggregate** (`behavioral_primitives`) — categories: `stimuli`, `compensations`, `emotional_context`, `frictions` (google_reviews) or `stimuli`, `compensations`, `emotional_context`, `behavioral_responses` (magicpin_upper)
2. **Per-review behavioral_intelligence** — categories: `stimuli`, `frictions`, `compensations`, `emotional_responses`, `behavioral_responses`, `commercial_mechanisms`, `contexts`
   - Skip signals where `negated == True`
   - Weight raw confidence by `evidence_calibration.effective_review_weight`
   - Keep highest weighted confidence per `(venue_id, primitive_id)` across all layers/reviews

**google source (google_places)** only extracts venue-level `behavioral_primitives` — it has no per-review `behavioral_intelligence` layer.

---

### Step 4 — Clusters & Patterns
**Input files:**
- `step_4_patterns_recognized.json` → `behavioral_patterns` + `pattern_venues`
- `step_4_behavioral_clusters.json` → `raw_venue_data`

**Tables written:**
- `behavioral_patterns` (source=`<source_key>`, area=region)
- `pattern_venues` (FK to behavioral_patterns.id + venues.id)
- `raw_venue_data` (platform=`<source_key>`, data_type=`api_response`)

**Join key:** `place_id` → `venues.id` (both magicpin_upper and google_reviews embed place_id in every venue entry)

**google source** joins via `name_normalized + city` (no place_id in google_places step_4).

`step_4_patterns_recognized.json` format: `patterns_detected` is a dict keyed by pattern name. Each entry has `venue_count` and `venues` — a list of `{name, place_id}` objects (magicpin_upper and google_reviews) or plain name strings (google).

---

### Step 4b — Governance Metrics
**Input file:** `step_4b_governance_report.json`  
**Tables written:**
- `data_quality_metrics` (area=region, source=`<source_key>`)
- `cluster_quality` (area=region, source=`<source_key>`)
- `drift_signals` (area=region, source=`<source_key>`)

All are area-level (not venue-level). No venue join needed.

---

### Step 4b (Pattern Scores) — Pattern Confidence
**Input file:** `step_5_patterns_scored.json`  
**Tables written:** `pattern_scores`

**Join:** `behavioral_patterns.id` via `WHERE pattern_name = %s AND area = %s AND source = %s`  
**Critical:** `behavioral_patterns` rows for this source **must exist first** (step 4 must have run).  
**Critical:** `pattern_scores.source` is NOT NULL with **no DEFAULT** — must be explicitly inserted.

Score parsing: `frequency_score`, `consistency_score`, `recency_score` may arrive as `"40.0"` (>1) or `0.40` (≤1). Always use:
```python
def parse_score(val):
    v = float(val)
    return v / 100 if v > 1 else v
```

---

### Step 5b — Similarity & Vectors
**Input file:** `step_5b_similarity.json`  
**Tables written:**
- `venue_vectors` (source=`<source_key>`) — `fitness_vector` column is a **PostgreSQL FLOAT[] array, NOT JSONB**. Pass as Python list directly. Do NOT `json.dumps()` it.
- `venue_similarity` (source=`<source_key>`)

**Join:** For google_reviews, build a name→place_id lookup from `step_3_signals_extracted.json` (same pipeline run, guaranteed name match), then place_id→venue_id from DB. For magicpin_upper, uses `name_normalized + city` DB lookup.

`step_5b_similarity.json` structure: top-level key is `venue_similarity` (list). Each entry has `venue_name`, `fitness_vector`, `similar_venues_pool`. **No place_id embedded** — must be resolved via lookup.

---

### Step 6 — Fitness Dimensions & Interventions
**Input file:** `step_6_output.json`  
**Tables written:**
- `venue_fitness_dimensions` (source=`<source_key>`)
- `behavioral_summary` (source=`<source_key>`)
- `intervention_triggers` (source=`<source_key>`)

**Join key:** `place_id` (embedded in step_6 for all non-google sources). Google source uses `name_normalized + city`.

`step_6_output.json` structure: `venues` array, each entry has `place_id`, `fitness_dimensions` (dict of 5 dimension objects each with `score`, `match_ratio`, `confidence_basis`, `matched_signals`, `strength_tier`), `behavioral_summary` (dict with `operational_quality`, `retention_strength`, `monetization_potential`), `operational_leverage` (list of intervention objects).

---

### Blend (runs after all sources loaded)
**Script:** `Database/scripts/blend/blend_fitness.py`  
**Tables written:** `venue_fitness_dimensions` (source=`blended`), `behavioral_summary` (source=`blended`)

Automatically includes all sources except `blended` and `manual_bif`. Equal weighting per source present for that venue (1/N). Re-run after any new source is loaded — zero config changes needed.

---

## 3. Loader Scripts — Complete Inventory

### google (Google Places API)
Regions: `navi-mumbai`, `mumbai-sobo`, `mumbai-main`, `thane`

| Step | Script | Tables |
|---|---|---|
| 3 | `pipeline/google_places_api/step3_signals_extraction.py` | `primitives_scores` |
| 4 | `pipeline/google_places_api/step4_cluster_and_patterns.py` | `behavioral_patterns`, `pattern_venues`, `raw_venue_data` |
| 4b gov | `pipeline/google_places_api/step4b_governance.py` | `data_quality_metrics`, `drift_signals`, `cluster_quality` |
| 4b scores | `pipeline/google_places_api/step4b_pattern_scores.py` | `pattern_scores` |
| 5 | `pipeline/google_places_api/step5_fitness_scores.py` | `venue_fitness_dimensions`, `behavioral_summary` |
| 5b | `pipeline/google_places_api/step5b_similarity_enrichment.py` | `venue_vectors`, `venue_similarity` |
| 6 | `pipeline/google_places_api/step6_mechanisms_and_interventions.py` | `raw_venue_data`, `intervention_triggers` |

> Note: google step 5 and step 6 are separate (fitness in step 5, interventions in step 6). All other sources combine fitness + interventions in step 6.

---

### magicpin_upper
Regions: `mumbai`, `navi-mumbai`, `sobo`, `thane`

| Step | Script | Tables | DB rows (verified 2026-05-25) |
|---|---|---|---|
| 3 | `pipeline/magicpin_upper/step3_signals_extraction.py` | `primitives_scores` | 2,624 |
| 4 | `pipeline/magicpin_upper/step4_cluster_and_patterns.py` | `behavioral_patterns`, `pattern_venues`, `raw_venue_data` | 327 / 708 / 1,559 |
| 4b gov | `pipeline/magicpin_upper/step4b_governance.py` | `data_quality_metrics`, `drift_signals`, `cluster_quality` | 4 / 114 / 4 |
| 4b scores | `pipeline/magicpin_upper/step4b_pattern_scores.py` | `pattern_scores` | 327 |
| 5b | `pipeline/magicpin_upper/step5b_similarity_enrichment.py` | `venue_vectors`, `venue_similarity` | 670 / 16,890 |
| 6 | `pipeline/magicpin_upper/step6_fitness_and_interventions.py` | `venue_fitness_dimensions`, `behavioral_summary`, `intervention_triggers` | 676 / 676 / 2,704 |

**Status: ALL STEPS LOADED ✅**

---

### google_reviews
Regions: **thane, navi-mumbai only** (no mumbai-main, no sobo)

| Step | Script | Tables | DB rows (verified 2026-05-25) |
|---|---|---|---|
| 3 | `pipeline/google_reviews/step3_primitives.py` | `primitives_scores` | 25,019 |
| 4 | `pipeline/google_reviews/step4_cluster_and_patterns.py` | `behavioral_patterns`, `pattern_venues`, `raw_venue_data` | 2,624 / 10,465 / 1,120 |
| 4b gov | `pipeline/google_reviews/step4b_governance.py` | `data_quality_metrics`, `cluster_quality` | 2 / 2 |
| 4b scores | `pipeline/google_reviews/step4b_pattern_scores.py` | `pattern_scores` | 2,624 |
| 5b | `pipeline/google_reviews/step5b_similarity_loader.py` | `venue_vectors`, `venue_similarity` | 1,114 / 27,913 |
| 6 | `pipeline/google_reviews/step6_fitness_and_interventions.py` | `venue_fitness_dimensions`, `behavioral_summary`, `intervention_triggers` | 1,120 / 1,120 / 4,480 |

**Status: ALL STEPS LOADED ✅**

Run order (must be sequential — each step depends on the prior):
```
python pipeline/google_reviews/step3_primitives.py
python pipeline/google_reviews/step4_cluster_and_patterns.py
python pipeline/google_reviews/step4b_governance.py
python pipeline/google_reviews/step4b_pattern_scores.py
python pipeline/google_reviews/step5b_similarity_loader.py
python pipeline/google_reviews/step6_fitness_and_interventions.py
python blend/blend_fitness.py
```

All scripts are run from: `D:\PolyNovea\PolyNovea\Docx\Company Docx\Acquistion System\`

---

## 4. Current DB State (2026-05-25)

```
primitives_scores        google=23,821  magicpin_upper=2,624   google_reviews=25,019
behavioral_patterns      google=25,072  magicpin_upper=327     google_reviews=2,624
pattern_venues           google=61,095  magicpin_upper=708     google_reviews=10,465
raw_venue_data           google=10,230  magicpin_upper=1,559   google_reviews=1,120   manual_reviews=1
data_quality_metrics     google=4       magicpin_upper=4       google_reviews=2
drift_signals            google=7,160   magicpin_upper=114     (google_reviews=0 — no drift detected)
cluster_quality          google=4       magicpin_upper=4       google_reviews=2
pattern_scores           google=25,072  magicpin_upper=327     google_reviews=2,624
venue_fitness_dimensions google=6,008   magicpin_upper=676     google_reviews=1,120   manual_reviews=2  blended=6,009
behavioral_summary       google=6,007   magicpin_upper=676     google_reviews=1,120   manual_reviews=2  blended=6,009
venue_vectors            google=5,759   magicpin_upper=670     google_reviews=1,114   manual_reviews=1
venue_similarity         google=216,048 magicpin_upper=16,890  google_reviews=27,913  manual_reviews=50
intervention_triggers    google=27,996  magicpin_upper=2,704   google_reviews=4,480   manual_reviews=4
```

**Blend coverage:**
- `google` only → 4,408 venues
- `google` + `google_reviews` → 923 venues
- `google` + `google_reviews` + `magicpin_upper` → 196 venues
- `google` + `google_reviews` + `manual_reviews` → 1 venue
- `google` + `magicpin_upper` → 480 venues
- `manual_reviews` only → 1 venue
- **Total blended: 6,009 venues**

---

## 5. Schema Traps — Do Not Repeat These Mistakes

### `pattern_scores.source` — no DEFAULT, must be explicitly inserted
The `source` column was added by `032_add_source_to_pattern_scores.py` which **dropped the DEFAULT** after backfilling. Every INSERT into `pattern_scores` must include `source` explicitly. The `SCORE_SQL` must list `source` in the column list and the SELECT must include `%s` (the SOURCE constant) as the first value after `bp.id`.

### `venue_vectors.fitness_vector` — PostgreSQL FLOAT[] array, NOT JSON
Pass as a plain Python list. **Never `json.dumps()` it.** psycopg2 converts Python lists to PG arrays automatically. Passing a JSON string produces `malformed array literal` error.

### `pattern_scores` must be loaded after `behavioral_patterns`
The SCORE_SQL does `SELECT bp.id FROM behavioral_patterns WHERE pattern_name = %s AND area = %s AND source = %s`. If step 4 (which inserts behavioral_patterns) hasn't run for this source, zero rows match and all scores silently miss (rowcount=0). Always run step 4 before step 4b pattern scores.

### Source column is NOT NULL across all pipeline tables
Every table touched by `018_add_source_columns.py` has `source VARCHAR(50) NOT NULL`. Every INSERT must explicitly provide the source value. Do not rely on column defaults — most were dropped after backfilling.

### `fitness_vector` column is in `venue_vectors`, NOT in `venue_fitness_dimensions`
`venue_fitness_dimensions` stores the 5 scored dimensions (office_lunch, repeat_habit, social_dwell, group_energy, destination_visit) plus quality scores. `venue_vectors` stores the raw float vector used for cosine similarity. They are separate tables loaded by separate steps.

---

## 6. How to Add a New Source (e.g. zomato)

1. Create `Database/data/raw/zomato/<region>/` — drop BIF step files here
2. Copy `Database/scripts/pipeline/google_reviews/` → `Database/scripts/pipeline/zomato/`
3. Change `SOURCE = 'zomato'`, `BASE_PATH` to point to zomato raw folder, `REGIONS` to match available cities
4. Verify JSON structure matches expected fields (place_id in step_3/step_4/step_6, venue_name in step_5b)
5. If step_3 has per-review `behavioral_intelligence`, keep the two-layer extraction in step3_primitives. If not, remove the Layer 2 block.
6. Run all 6 loaders in order, then `blend_fitness.py`
7. Run `check_source_coverage.py` to verify row counts before declaring done

---

## 7. Audit Script

`Database/scripts/check_source_coverage.py` — queries all 13 pipeline tables and prints row counts by source. Run before and after any load operation to confirm what was added.

```
python Database/scripts/check_source_coverage.py
```
