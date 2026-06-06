# M3 Recalibration — Operations Reference

**Last updated:** 2026-05-30  
**Brief source:** `Module 3 - Optimisation/docs/m2_claude_recalibration_brief.md`

M3 observes live venue sessions every weekend. The recalibration scripts pull that
data back into M2 to improve fitness scores and segment alignment predictions over time.

---

## Two separate pipelines

| # | Script | Reads from | Writes to | Status |
|---|--------|-----------|-----------|--------|
| 1 | `recalibrate_fitness_m3.py` | `m3_kpi_observations` + `m3_kpi_dimension_map` | `venue_fitness_dimensions` (source='blended') | **BUILT** |
| 2 | `recalibrate_demographics_m3.py` | `m3_segment_validation_feedback` | `venue_demographic_scores.alignment_score` | **PENDING** |

These are independent — run them separately. Neither touches the other's tables.

---

## Script 1 — Fitness recalibration

**File:** `Database/scripts/manual/recalibrate_fitness_m3.py`

### What it does

Reads M3's zone-level KPI observations (crowd energy, environment quality, commercial
signals, crowd stress) and Bayesian-blends them into the venue's existing fitness scores.

Dimensions it can update:
- `fitness_for_group_energy`
- `fitness_for_social_dwell`
- `operational_quality`
- `retention_strength`

Dimensions it **never** touches (M3 has no data for these):
- `fitness_for_office_lunch`
- `fitness_for_destination_visit`
- `fitness_for_repeat_habit`
- `monetization_potential`

### When to run

Run **after every 3–5 new `observation_only` sessions** accumulate at a venue.  
Do not run per-session — score shifts are too noisy at that granularity.

Practical trigger: after each weekend block (Friday + Saturday = 2 sessions). Run
once the venue has logged its 3rd session. Then run again every 3–5 sessions after that.

### Commands

```bash
cd "Database/scripts/manual"

# Preview changes without writing (always do this first on a new venue)
python recalibrate_fitness_m3.py --dry-run --venue-id 42

# Run for a single venue
python recalibrate_fitness_m3.py --venue-id 42

# Run for all venues with M3 data
python recalibrate_fitness_m3.py --all
```

### Safety rules

- Only modifies `source = 'blended'` rows — Google/Magicpin/manual source rows untouched
- Skips any dimension with fewer than 3 `observation_only` sessions
- M3 influence is hard-capped at 0.40 — a handful of Friday nights cannot override 2 years of platform data
- `pipeline_version` is set to `'2.0-m3-blend'` on every updated row for auditability

### Example output

```
venue 42  fitness_for_group_energy: 0.6200 → 0.6480  (m3=0.8200, strength=0.227, obs_sessions=4)
venue 42  operational_quality:      0.5100 → 0.5034  (m3=0.4800, strength=0.133, obs_sessions=3)
```

---

## Script 2 — Demographics recalibration

**File:** `Database/scripts/manual/recalibrate_demographics_m3.py`  
**Status: NOT YET BUILT**

### What it will do

Reads `m3_segment_validation_feedback` — which contains M3's post-session comparison
of M2's predicted segment alignment vs what was actually observed (survey-backed).

Updates `venue_demographic_scores.alignment_score` for segments where the delta
(observed − predicted) is large enough to warrant correction.

Example: M2 predicted `working_women` alignment of 0.68 at venue 42. M3 observed 0.12
from 8 survey responses. Delta = −0.56. M2 is dramatically wrong. The demographics
script should pull that score toward 0.12, weighted by survey confidence and session count.

### When to run (planned)

Only run when `confidence = 'HIGH'` rows exist (10+ survey responses). Low-survey
sessions are too noisy to update demographic scores.

### Confidence levels in source data

| confidence | survey_count | Action |
|------------|-------------|--------|
| HIGH | 10+ | Include in recalibration |
| MEDIUM | 5–9 | Include with 0.5× weight |
| LOW | 1–4 | Skip — too noisy |

### Commands (planned)

```bash
python recalibrate_demographics_m3.py --dry-run --venue-id 42
python recalibrate_demographics_m3.py --venue-id 42
python recalibrate_demographics_m3.py --all
```

---

## Verify M3 tables exist before first run

```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_name LIKE 'm3_%'
ORDER BY table_name;
```

Should return 6 rows:
- `m3_dwell_observations`
- `m3_kpi_dimension_map`
- `m3_kpi_observations`
- `m3_segment_table_log`
- `m3_segment_validation_feedback`
- `m3_venue_behavioral_outcomes`

If fewer rows return, M3 hasn't run its schema migration yet — check with M3 team.

---

## Automation (future)

Currently both scripts are **manual only**. Automate once:
- Script 1 has run on 3+ real venues with sensible score movements
- Script 2 is built and validated

Planned automation: EC2 cron or GitHub Actions scheduled workflow running `--all`
on Sunday nights after the weekend session window closes.
