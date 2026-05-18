"""
015_provenance_schema.py
Adds provenance infrastructure to the pipeline database.

New tables:
  1. venue_platform_ids   — canonical mapping of internal venue_id to external platform IDs
                            (Google Place ID, Zomato ID, Swiggy ID, etc.)
                            Add a row per platform as each source is ingested.

  2. raw_venue_data       — immutable store for raw API payloads / HTML scrapes / review batches
                            before any parsing or inference. Enables re-parsing when models improve.

New columns (provenance) on existing tables:
  3. venue_demographic_scores  → computed_at, pipeline_version, schema_version
  4. venue_fitness_dimensions  → computed_at, pipeline_version, schema_version

Run after: 014_create_optional_scaffolds.py
"""

import os
import sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

# ── 1. Canonical platform ID mapping ─────────────────────────────────────────
CREATE_PLATFORM_IDS = """
CREATE TABLE IF NOT EXISTS venue_platform_ids (
    id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    venue_id         INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    platform         TEXT NOT NULL
                         CHECK (platform IN (
                             'google', 'zomato', 'swiggy',
                             'magicpin', 'instagram', 'dineout', 'other'
                         )),
    platform_id      TEXT NOT NULL,
    platform_url     TEXT,
    name_on_platform TEXT,
    last_verified_at TIMESTAMPTZ DEFAULT NOW(),
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (platform, platform_id)
);

CREATE INDEX IF NOT EXISTS idx_vpi_venue_id ON venue_platform_ids(venue_id);
CREATE INDEX IF NOT EXISTS idx_vpi_platform ON venue_platform_ids(platform, platform_id);
"""

# ── 2. Immutable raw payload store ────────────────────────────────────────────
CREATE_RAW_VENUE_DATA = """
CREATE TABLE IF NOT EXISTS raw_venue_data (
    id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    venue_id         INTEGER REFERENCES venues(id) ON DELETE SET NULL,
    platform         TEXT NOT NULL,
    data_type        TEXT NOT NULL
                         CHECK (data_type IN (
                             'api_response', 'html_scrape',
                             'review_batch', 'geocode_response', 'search_result'
                         )),
    raw_payload      JSONB NOT NULL,
    collected_at     TIMESTAMPTZ DEFAULT NOW(),
    collector_version TEXT DEFAULT '1.0',
    query_params     JSONB,
    schema_version   INTEGER DEFAULT 1,
    is_deleted       BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_rvd_venue_id     ON raw_venue_data(venue_id);
CREATE INDEX IF NOT EXISTS idx_rvd_platform     ON raw_venue_data(platform, data_type);
CREATE INDEX IF NOT EXISTS idx_rvd_collected_at ON raw_venue_data(collected_at DESC);
"""

# ── 3. Provenance on venue_demographic_scores ─────────────────────────────────
ALTER_DEMOGRAPHICS = """
ALTER TABLE venue_demographic_scores
    ADD COLUMN IF NOT EXISTS computed_at      TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS pipeline_version TEXT        DEFAULT '1.0',
    ADD COLUMN IF NOT EXISTS schema_version   INTEGER     DEFAULT 1;
"""

# ── 4. Provenance on venue_fitness_dimensions ─────────────────────────────────
ALTER_FITNESS = """
ALTER TABLE venue_fitness_dimensions
    ADD COLUMN IF NOT EXISTS computed_at      TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS pipeline_version TEXT        DEFAULT '1.0',
    ADD COLUMN IF NOT EXISTS schema_version   INTEGER     DEFAULT 1;
"""


def main():
    print("\n015_provenance_schema.py — Provenance infrastructure\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        print("  [1/4] venue_platform_ids (canonical external ID mapping)...")
        cursor.execute(CREATE_PLATFORM_IDS)
        print("        Created")

        print("  [2/4] raw_venue_data (immutable raw payload store)...")
        cursor.execute(CREATE_RAW_VENUE_DATA)
        print("        Created")

        print("  [3/4] Adding provenance columns to venue_demographic_scores...")
        cursor.execute(ALTER_DEMOGRAPHICS)
        print("        Altered")

        print("  [4/4] Adding provenance columns to venue_fitness_dimensions...")
        cursor.execute(ALTER_FITNESS)
        print("        Altered")

        conn.commit()

        print("\n" + "=" * 60)
        print("  COMPLETE — Provenance schema ready")
        print("")
        print("  venue_platform_ids    → populate as each platform is ingested")
        print("  raw_venue_data        → store raw before parsing (immutable)")
        print("  demographic_scores    → computed_at / pipeline_version / schema_version")
        print("  fitness_dimensions    → computed_at / pipeline_version / schema_version")
        print("=" * 60 + "\n")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
