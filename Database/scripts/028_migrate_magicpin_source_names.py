"""
028_migrate_magicpin_source_names.py
One-time migration: renames source='magicpin' → 'magicpin_upper' across all
tables that carry a source column.

Why:
  MagicPin provides two distinct data blocks:
    upper block = static venue metadata (already loaded)
    lower block = online reviews (arriving soon)
  These are independent evidence layers and must compound separately.
  Each gets its own source key so the blend runner weights them as distinct sources.

Source naming convention going forward:
  google          — Google Places API
  magicpin_upper  — MagicPin static block (menu, photos, venue metadata)
  magicpin_lower  — MagicPin online reviews block
  zomato          — Zomato (future)
  tripadvisor     — TripAdvisor (future)

Safe to re-run: uses UPDATE ... WHERE source = 'magicpin', no-ops if already renamed.
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

# Every table that has a source column and may have rows with source='magicpin'
TABLES = [
    'venue_fitness_dimensions',
    'behavioral_summary',
    'intervention_triggers',
    'venue_vectors',
    'venue_similarity',
    'data_quality_metrics',
    'drift_signals',
    'cluster_quality',
    'behavioral_patterns',
    'pattern_venues',
    'primitives_scores',
    'raw_venue_data',       # uses platform column, not source — handled separately
]

# Tables that use 'platform' instead of 'source'
PLATFORM_TABLES = [
    'raw_venue_data',
]

# Tables that use 'source'
# pattern_venues is a pure join table (venue_id, pattern_id) — no source column
SOURCE_TABLES = [t for t in TABLES if t not in PLATFORM_TABLES and t != 'pattern_venues']


def rename_source_column(cursor, table: str) -> int:
    cursor.execute(
        f"UPDATE {table} SET source = 'magicpin_upper' WHERE source = 'magicpin'"
    )
    return cursor.rowcount


def rename_platform_column(cursor, table: str) -> int:
    cursor.execute(
        f"UPDATE {table} SET platform = 'magicpin_upper' WHERE platform = 'magicpin'"
    )
    return cursor.rowcount


def main():
    print("\n028_migrate_magicpin_source_names.py")
    print("  magicpin → magicpin_upper across all source-keyed tables\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    total  = 0

    try:
        for table in SOURCE_TABLES:
            rows = rename_source_column(cursor, table)
            if rows:
                print(f"  {table:<40} {rows:>6} rows renamed")
            else:
                print(f"  {table:<40}      — (already renamed or no magicpin rows)")
            total += rows

        for table in PLATFORM_TABLES:
            rows = rename_platform_column(cursor, table)
            if rows:
                print(f"  {table:<40} {rows:>6} rows renamed (platform column)")
            else:
                print(f"  {table:<40}      — (already renamed or no magicpin rows)")
            total += rows

        conn.commit()
        print(f"\n{'='*55}")
        print(f"  COMPLETE — {total:,} rows renamed to source='magicpin_upper'")
        print(f"{'='*55}\n")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
