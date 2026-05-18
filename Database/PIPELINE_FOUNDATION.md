# Polynovea Module 2 — Database Pipeline Foundation
> Last updated: 2026-05-18

---

## Architecture Principle

Every data source that produces a BIF pipeline output **compounds** in the database. Nothing overwrites anything. Each source gets its own keyed row in every table. The blend runner averages only the sources that are present for each individual venue.

**Rule:** If venue X exists on 2 platforms → each contributes 50%. On 4 platforms → 25% each. A venue on only 1 platform gets that platform's score verbatim. No dilution, no penalty for missing sources.

---

## Source Key Registry

| Key | What it represents |
|---|---|
| `google` | Google Places API |
| `magicpin_upper` | MagicPin static block (venue metadata, menus, photos) |
| `magicpin_lower` | MagicPin online reviews block *(loader ready, data arriving)* |
| `zomato` | Zomato *(future)* |
| `tripadvisor` | TripAdvisor *(future)* |

---

## Raw Data Paths

| Source | Local path | Regions / Cities |
|---|---|---|
| Google Places | `data/raw/google_places/` | `navi-mumbai`, `mumbai-sobo`, `mumbai-main`, `thane` |
| MagicPin upper | `data/raw/magicpin/` | `mumbai`, `navi-mumbai`, `sobo`, `thane` |
| MagicPin lower | `data/raw/magicpin_lower/` | `mumbai`, `navi-mumbai`, `sobo`, `thane` |

> **Join method:**
> - Google `step_5`, `step_6`: `name_normalized + city` (no place_id in these files)
> - Google `step_5b`: `place_id` (enriched by `enrich_step5b.py` before loading)
> - MagicPin `step_3`, `step_4`, `step_6`: `place_id`
> - MagicPin `step_5b`: `name_normalized + city` (no place_id in this file — same as Google step_5b before enrichment)

---

## Script Inventory

### Foundation & Schema (run once, in order)

| # | Script | What it does |
|---|---|---|
| — | `001_init_schema.sql` | Creates all tables. Run first, manually on the DB. |
| — | `015_provenance_schema.py` | Creates `raw_venue_data` immutable store. |
| — | `018_add_source_columns.py` | **One-time migration.** Adds `source` column to 9 tables; backfills `'google'`. |
| — | `028_migrate_magicpin_source_names.py` | **One-time migration.** Renames `source='magicpin'` → `'magicpin_upper'` across all tables. |

---

### Google Places BIF Pipeline

**Source:** `data/raw/google_places/` — 4 cities

| # | Script | BIF file | Tables written | Source key |
|---|---|---|---|---|
| 002 | `002_load_venues.py` | `step_1_venues_refined.json` | `venues` | — |
| 010 | `010_load_primitives.py` | `step_3_signals_extracted.json` | `primitives_scores` | `google` |
| 003 | `003_load_patterns.py` | `step_4_patterns_recognized.json` | `behavioral_patterns`, `pattern_venues` | `google` |
| 019 | `019_load_google_step4_clusters.py` | `step_4_behavioral_clusters.json` | `raw_venue_data` | platform=`google` |
| 007 | `007_load_governance.py` | `step_4b_governance_report.json` | `data_quality_metrics`, `drift_signals`, `cluster_quality` | `google` |
| 004 | `004_load_scores.py` | `step_5_behavioral_scores.json` | `venue_fitness_dimensions`, `behavioral_summary` | `google` |
| 006 | `006_load_pattern_scores.py` | `step_5_patterns_scored.json` | `pattern_scores` | — |
| — | `enrich_step5b.py` | Pre-process: adds place_ids to `step_5b_similarity.json` | Outputs `step_5b_similarity_enriched.json` | — |
| 005 | `005_load_similarity.py` | `step_5b_similarity_enriched.json` | `venue_vectors`, `venue_similarity` | `google` |
| 020 | `020_load_google_step6.py` | `step_6_output.json` | `raw_venue_data` (mechanisms + leverage) | platform=`google` |

---

### MagicPin Upper Block BIF Pipeline

**Source:** `data/raw/magicpin/` — 4 regions

| # | Script | BIF file | Tables written | Source key |
|---|---|---|---|---|
| 021 | `021_load_magicpin_step3.py` | `step_3_signals_extracted.json` | `primitives_scores` | `magicpin_upper` |
| 022 | `022_load_magicpin_step4.py` | `step_4_behavioral_clusters.json` | `raw_venue_data` | platform=`magicpin_upper` |
| 022 | `022_load_magicpin_step4.py` | `step_4_patterns_recognized.json` | `behavioral_patterns`, `pattern_venues` | `magicpin_upper` |
| 023 | `023_load_magicpin_step4b.py` | `step_4b_governance_report.json` | `data_quality_metrics`, `drift_signals`, `cluster_quality` | `magicpin_upper` |
| 024 | `024_load_magicpin_step5_scores.py` | `step_5_patterns_scored.json` | `pattern_scores` | — |
| 025 | `025_load_magicpin_step5b.py` | `step_5b_similarity.json` | `venue_vectors`, `venue_similarity` | `magicpin_upper` |
| 017 | `017_load_magicpin_step6.py` | `step_6_output.json` | `raw_venue_data` (dish_signals + mechanisms only) | platform=`magicpin_upper` |
| 026 | `026_load_magicpin_step6_fitness.py` | `step_6_output.json` | `venue_fitness_dimensions`, `behavioral_summary`, `intervention_triggers` | `magicpin_upper` |

> **Note:** 017 only stores raw payloads. 026 stores the fitness scores. Both should run.

---

### MagicPin Lower Block BIF Pipeline

**Source:** `data/raw/magicpin_lower/` — 4 regions *(data arriving)*

| # | Script | BIF file | Tables written | Source key |
|---|---|---|---|---|
| 029 | `029_load_magicpin_lower_step6_fitness.py` | `step_6_output.json` | `venue_fitness_dimensions`, `behavioral_summary`, `intervention_triggers` | `magicpin_lower` |
| TBD | *(build when data arrives)* | `step_3_signals_extracted.json` | `primitives_scores` | `magicpin_lower` |
| TBD | *(build when data arrives)* | `step_4_behavioral_clusters.json` | `raw_venue_data` | platform=`magicpin_lower` |
| TBD | *(build when data arrives)* | `step_4_patterns_recognized.json` | `behavioral_patterns`, `pattern_venues` | `magicpin_lower` |
| TBD | *(build when data arrives)* | `step_4b_governance_report.json` | `data_quality_metrics`, `drift_signals`, `cluster_quality` | `magicpin_lower` |
| TBD | *(build when data arrives)* | `step_5_patterns_scored.json` | `pattern_scores` | — |
| TBD | *(build when data arrives)* | `step_5b_similarity.json` | `venue_vectors`, `venue_similarity` | `magicpin_lower` |

---

### Blend Runner (run after every source load)

| # | Script | What it does |
|---|---|---|
| 027 | `027_blend_fitness.py` | Reads all non-blended rows from `venue_fitness_dimensions`. Averages equally across however many sources are present per venue. Writes `source='blended'` to `venue_fitness_dimensions` + `behavioral_summary`. |

---

### Compute Scripts (run after all sources are loaded)

| # | Script | What it does |
|---|---|---|
| 012 | `012_compute_venue_demographics.py` | Ranks `venue_similarity` pairs; computes `venue_demographic_scores` (Bayesian, 7 segments) |
| 013 | `013_compute_fitness_deltas.py` | Pre-computes `fitness_delta_rules` (56 rules) + `venue_similarity_deltas` (~1.17M rows) |

---

### Static / Reference Data (run once)

| # | Script | Source | Tables written |
|---|---|---|---|
| 008 | `008_load_surveys.py` | `surveys/form_v1_responses.csv`, `form_v2_responses.csv` | `survey_responses_canonical`, `user_archetypes` |
| 009 | `009_load_marketing_engine.py` | India behavioral research MD | `behavioral_mechanism_catalog`, `channel_mechanism_mapping`, `campaign_templates` |
| 011 | `011_load_demographics.py` | India research MD | `demographic_segments`, `demographic_archetype_mapping`, `demographic_behavioral_alignment`, `demographic_archetype_interventions` |
| 016 | `016_load_audience_profiles.py` | Kimi research MD | `segment_behavioral_profiles`, `archetype_behavioral_profiles`, `segment_archetype_affinity`, `segment_platform_usage` |

> ⚠️ **016 — DO NOT RUN.** Conflicts with `db/` ENUM schema. The `db/` system is authoritative.

---

### Utilities

| Script | Purpose |
|---|---|
| `enrich_step5b.py` | Pre-processing. Adds place_ids to `step_5b_similarity.json` for all sources before their similarity loaders run. Outputs `step_5b_similarity_enriched.json` per city/region + mismatch report. Must run for: Google, MagicPin upper, MagicPin lower, Zomato, TripAdvisor. |
| `amendment_service.py` | `AmendmentService` class — composite score / decay logic, used by the app (not a loader). |
| `run_pipeline.py` | Runs the full pipeline in dependency order. Supports `--from N` and `--only N`. **Needs updating** — currently only covers scripts 002–014, missing all MagicPin loaders and blend runner. |
| `014_create_optional_scaffolds.py` | Optional table scaffolds — run only if those features are needed. |

---

## Amendment Workflow (Monthly Data Refresh)

When new data arrives for any source (e.g. MagicPin lower block, Zomato first load, monthly refresh):

1. Run `enrich_step5b.py` for the new source's step_5b file
2. Run the source's loaders in BIF order: step_3 → step_4 → step_4b → step_5 scores → step_5b → step_6 fitness
3. Run `027_blend_fitness.py`
4. Run `012_compute_venue_demographics.py`
5. Run `013_compute_fitness_deltas.py`

All loaders use `ON CONFLICT (venue_id, source) DO UPDATE` — re-running is always safe.

---

## Tables with Source Column

All tables below have a `source` column. Each source gets its own row per venue. Nothing overwrites anything.

| Table | Unique constraint |
|---|---|
| `venue_fitness_dimensions` | `(venue_id, source)` |
| `behavioral_summary` | `(venue_id, source)` |
| `intervention_triggers` | `(venue_id, source, intervention_type)` |
| `venue_vectors` | `(venue_id, source)` |
| `venue_similarity` | `(venue_id, source, similar_venue_id)` |
| `data_quality_metrics` | `(area, source)` |
| `drift_signals` | `(area, source, pattern_description)` |
| `cluster_quality` | `(area, source)` |
| `behavioral_patterns` | `(area, source, pattern_name)` |
| `primitives_scores` | `(venue_id, source, primitive_id)` |

> `raw_venue_data` uses `platform` instead of `source` — same compounding principle, different column name.

---

## Known Issues / Debt

| Item | Status |
|---|---|
| `run_pipeline.py` PIPELINE list is stale — only covers 002–014 | **Fix needed** |
| MagicPin lower block step_3/4/4b/5/5b loaders don't exist yet | Waiting for data to arrive |
| `chat.py` `fetch_venue_context()` queries without source filter | **Fix needed** — should prefer `source='blended'` |
| `016_load_audience_profiles.py` conflicts with db/ ENUM schema | DO NOT RUN |
