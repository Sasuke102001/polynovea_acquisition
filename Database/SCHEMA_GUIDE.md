# Database Schema Guide

## Where the Schema Lives

The RDS schema is split across two tracks — both run against the same RDS instance
(`polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com`).

---

### Track 1 — Pipeline / Venue Tables

**File:** `Database/sql/001_init_schema.sql`

The main operational schema. Contains every table the pipeline writes to:

| Table | Purpose |
|---|---|
| `venues` | Core venue records (place_id, name, area, city, types, lat/lng, geo) |
| `primitives_scores` | Per-source behavioral primitive signals |
| `venue_fitness_dimensions` | Fitness scores per source (blended, google, google_reviews, etc.) |
| `behavioral_patterns` | Area-level co-occurring primitive clusters |
| `pattern_venues` | Venue ↔ pattern membership |
| `pattern_scores` | Pattern-level scored primitives |
| `drift_signals` | Area-level trend signals per source |
| `cluster_quality` | Cluster reliability metrics per area |
| `intervention_triggers` | Recommended interventions per venue |
| `venue_similarity` | Cosine similarity pairs between venues |
| `raw_venue_data` | Immutable raw payloads (JSONB) from every platform |
| `venue_demographic_scores` | Segment alignment scores per venue |
| `venue_similarity_deltas` | Per-dimension fitness deltas between similar venues |
| `fitness_delta_rules` | Lookup table: delta range → client-facing label |
| `behavioral_summary` | Rolled-up operational/retention/monetization per venue |

**How it was applied:** Manually run once against RDS at project start. No migration runner or tracking table.

**Post-init schema changes** applied manually as needed:

| Script | What it does |
|---|---|
| `Database/scripts/schema/add_source_columns.py` | Adds `source VARCHAR(50)` to 9 tables + rebuilds unique constraints |
| `Database/scripts/schema/provenance_schema.py` | Creates `raw_venue_data` + adds `computed_at`, `pipeline_version`, `schema_version` to demographics/fitness |
| `Database/scripts/schema/add_source_to_pattern_scores.py` | Adds `source` to pattern scores table |
| `Database/scripts/schema/optional_scaffolds.py` | Optional extra scaffolding |

---

### Track 2 — Behavioral Research / AI Tables

**Files:** `App/backend/db/001_schema.sql` → `004_seed_new_archetypes_corrections.sql`

ENUMs, segments, archetypes, mechanisms, channel weights — everything the AI prompt reads from the DB.

| File | Contents |
|---|---|
| `001_schema.sql` | ENUMs, `behavioral_mechanisms`, `segment_behavioral_profiles`, `channel_segment_effectiveness`, views |
| `002_seed_segments_archetypes.sql` | Seeds all 34 demographic segments and archetype definitions |
| `003_seed_mechanisms_channels_weights.sql` | Seeds channel benchmarks, mechanism citations, trait fitness weights |
| `004_seed_new_archetypes_corrections.sql` | Corrections and additions from Kimi research |

Has a **migration runner** at `App/backend/db/seed.py`:

```bash
cd App/backend
python -m db.seed              # run all pending files
python -m db.seed --dry-run    # print SQL without executing
python -m db.seed --reset      # DROP + recreate (destructive)
```

---

### Track 3 — M3 Feedback Tables (written, not yet applied)

**File:** `App/backend/db/m3_feedback_tables.sql`

Two tables for the M3 → M2 feedback loop. M3 writes here after each session; M2 reads to recalibrate `venue_demographic_scores.alignment_score`.

| Table | Purpose |
|---|---|
| `m3_segment_validation_feedback` | Per-session: M2 predicted alignment vs M3 observed. `delta` column drives recalibration. |
| `m3_venue_behavioral_outcomes` | Per-session: dwell time, crowd energy, occupancy, intervention outcome, data quality. |

Also contains the commented-out `CREATE ROLE m3_app_user` grant block — M3 gets SELECT on all M2 tables, INSERT/UPDATE only on these two.

**Status:** Not yet applied. Run manually when M3 backend is ready to write.

---

## How to Add More Schema

### Adding to Track 1 (pipeline tables)

No runner exists — apply manually.

**Step 1** — Write your DDL as the next numbered file:
```
Database/sql/002_description.sql
```
Use `CREATE TABLE IF NOT EXISTS` and `ADD COLUMN IF NOT EXISTS` so the file is safe to re-run.

**Step 2** — Update the RDS security group if your local IP has changed:
```bash
curl -s https://api.ipify.org   # get your current IP
# Then add <your-ip>/32 to inbound rules on sg-0b6a8ad443531abf5 in AWS console
```

**Step 3** — Apply via psql:
```bash
psql "host=polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com \
      port=5432 dbname=<dbname> user=<user> sslmode=require" \
      -f Database/sql/002_description.sql
```

Or via Python (same pattern as existing schema scripts):
```python
import asyncpg, asyncio, os
from dotenv import load_dotenv
load_dotenv("App/backend/.env")

async def run():
    conn = await asyncpg.connect(
        host=os.getenv("PG_HOST"), port=int(os.getenv("PG_PORT", 5432)),
        database=os.getenv("PG_DB"), user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"), ssl="require",
    )
    await conn.execute(open("Database/sql/002_description.sql").read())
    await conn.close()

asyncio.run(run())
```

**Step 4** — If it's a column addition or constraint change, add a Python script in
`Database/scripts/schema/` (follow the pattern of `add_source_columns.py`) so it's reproducible.

---

### Adding to Track 2 (behavioral/AI tables)

Runner exists — use it.

**Step 1** — Write your SQL file:
```
App/backend/db/005_description.sql
```

**Step 2** — Register it in the runner. In `App/backend/db/seed.py`, add to `SQL_FILES`:
```python
SQL_FILES = [
    "001_schema.sql",
    "002_seed_segments_archetypes.sql",
    "003_seed_mechanisms_channels_weights.sql",
    "004_seed_new_archetypes_corrections.sql",
    "005_description.sql",   # ← add here
]
```

**Step 3** — Run:
```bash
cd App/backend
python -m db.seed
```

---

### Applying the pending M3 feedback tables

When the M3 backend is ready:

```bash
psql "host=polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com \
      port=5432 dbname=<dbname> user=<user> sslmode=require" \
      -f App/backend/db/m3_feedback_tables.sql
```

Then uncomment and run the `CREATE ROLE` / `GRANT` block in that file as superuser to create the `m3_app_user` read/write role.

---

## Important Note on Migration Tracking

There is **no `schema_migrations` tracking table**. Both tracks rely entirely on
`CREATE TABLE IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS` being idempotent.

This means:
- Re-running any file is safe — existing objects are silently skipped
- There is no record of which migrations have been applied or when
- Non-idempotent statements (bare `INSERT` without `ON CONFLICT`, `CREATE TYPE` without `IF NOT EXISTS`) will error on re-run

If a migration needs to be non-idempotent (e.g. a data backfill), wrap it in a
`DO $$ BEGIN ... EXCEPTION WHEN ... END $$;` block or guard it with an existence check.
