"""
018_add_source_columns.py
Schema migration: add `source` column to every table that holds
pipeline-computed data, so Google / MagicPin / Zomato / TripAdvisor
(and any future source) all sit side-by-side and compound — never
overwrite each other.

Tables changed:
  venue_fitness_dimensions  UNIQUE (venue_id)                      → (venue_id, source)
  behavioral_summary        UNIQUE (venue_id)                      → (venue_id, source)
  intervention_triggers     UNIQUE (venue_id, intervention_type)   → (venue_id, source, intervention_type)
  venue_vectors             UNIQUE (venue_id)                      → (venue_id, source)
  venue_similarity          UNIQUE (venue_id, similar_venue_id)    → (venue_id, source, similar_venue_id)
  data_quality_metrics      UNIQUE (area)                          → (area, source)
  drift_signals             (no unique)                            → UNIQUE (area, source, pattern_description)
  cluster_quality           (broken ON CONFLICT DO NOTHING)        → UNIQUE (area, source)
  behavioral_patterns       (no unique)                            → source column added; no unique needed

All existing rows backfilled with source = 'google'.

Safe to re-run — uses IF NOT EXISTS / IF EXISTS throughout.
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


def drop_constraint_if_exists(cursor, table: str, *columns):
    """
    Find and drop the UNIQUE constraint covering exactly the given columns
    on the given table. Safe to call when constraint may not exist.
    """
    col_list = list(columns)
    n = len(col_list)

    # pg_constraint stores column positions; join with pg_attribute to get names
    cursor.execute("""
        SELECT c.conname
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        WHERE t.relname = %s
          AND c.contype = 'u'
          AND array_length(c.conkey, 1) = %s
          AND NOT EXISTS (
              SELECT 1 FROM unnest(c.conkey) AS k(attnum)
              WHERE NOT EXISTS (
                  SELECT 1 FROM pg_attribute a
                  WHERE a.attrelid = c.conrelid
                    AND a.attnum = k.attnum
                    AND a.attname = ANY(%s)
              )
          )
    """, (table, n, col_list))

    rows = cursor.fetchall()
    for (conname,) in rows:
        cursor.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS "{conname}"')
        print(f"      dropped constraint: {conname}")


def add_source_column(cursor, table: str, default: str = 'google'):
    """Add source column if missing, then backfill NULLs."""
    cursor.execute(f"""
        ALTER TABLE {table}
            ADD COLUMN IF NOT EXISTS source VARCHAR(50) NOT NULL DEFAULT '{default}'
    """)
    cursor.execute(f"""
        UPDATE {table} SET source = '{default}' WHERE source IS NULL OR source = ''
    """)


def run_migration(cursor):
    steps = []

    # ── 1. venue_fitness_dimensions ──────────────────────────────────────────
    print("\n  [1/9] venue_fitness_dimensions")
    add_source_column(cursor, 'venue_fitness_dimensions')
    drop_constraint_if_exists(cursor, 'venue_fitness_dimensions', 'venue_id')
    cursor.execute("""
        ALTER TABLE venue_fitness_dimensions
            ADD CONSTRAINT vfd_venue_source_unique UNIQUE (venue_id, source)
    """) if not _constraint_exists(cursor, 'venue_fitness_dimensions', 'vfd_venue_source_unique') else None
    _safe_add_constraint(cursor, 'venue_fitness_dimensions',
                         'vfd_venue_source_unique', 'UNIQUE (venue_id, source)')
    steps.append('venue_fitness_dimensions ✓')

    # ── 2. behavioral_summary ─────────────────────────────────────────────────
    print("  [2/9] behavioral_summary")
    add_source_column(cursor, 'behavioral_summary')
    drop_constraint_if_exists(cursor, 'behavioral_summary', 'venue_id')
    _safe_add_constraint(cursor, 'behavioral_summary',
                         'bs_venue_source_unique', 'UNIQUE (venue_id, source)')
    steps.append('behavioral_summary ✓')

    # ── 3. intervention_triggers ──────────────────────────────────────────────
    print("  [3/9] intervention_triggers")
    add_source_column(cursor, 'intervention_triggers')
    drop_constraint_if_exists(cursor, 'intervention_triggers', 'venue_id', 'intervention_type')
    _safe_add_constraint(cursor, 'intervention_triggers',
                         'it_venue_source_type_unique', 'UNIQUE (venue_id, source, intervention_type)')
    steps.append('intervention_triggers ✓')

    # ── 4. venue_vectors ──────────────────────────────────────────────────────
    print("  [4/9] venue_vectors")
    add_source_column(cursor, 'venue_vectors')
    drop_constraint_if_exists(cursor, 'venue_vectors', 'venue_id')
    _safe_add_constraint(cursor, 'venue_vectors',
                         'vv_venue_source_unique', 'UNIQUE (venue_id, source)')
    steps.append('venue_vectors ✓')

    # ── 5. venue_similarity ───────────────────────────────────────────────────
    print("  [5/9] venue_similarity")
    add_source_column(cursor, 'venue_similarity')
    drop_constraint_if_exists(cursor, 'venue_similarity', 'venue_id', 'similar_venue_id')
    _safe_add_constraint(cursor, 'venue_similarity',
                         'vs_venue_source_similar_unique', 'UNIQUE (venue_id, source, similar_venue_id)')
    steps.append('venue_similarity ✓')

    # ── 6. data_quality_metrics ───────────────────────────────────────────────
    print("  [6/9] data_quality_metrics")
    add_source_column(cursor, 'data_quality_metrics')
    drop_constraint_if_exists(cursor, 'data_quality_metrics', 'area')
    _safe_add_constraint(cursor, 'data_quality_metrics',
                         'dqm_area_source_unique', 'UNIQUE (area, source)')
    steps.append('data_quality_metrics ✓')

    # ── 7. drift_signals ──────────────────────────────────────────────────────
    print("  [7/9] drift_signals")
    add_source_column(cursor, 'drift_signals')
    # Deduplicate before adding UNIQUE — keep highest confidence row per key
    cursor.execute("""
        DELETE FROM drift_signals a
        USING drift_signals b
        WHERE a.id > b.id
          AND a.area = b.area
          AND a.source = b.source
          AND a.pattern_description = b.pattern_description
    """)
    deduped = cursor.rowcount
    if deduped:
        print(f"      deduplicated {deduped} duplicate drift_signal rows")
    _safe_add_constraint(cursor, 'drift_signals',
                         'ds_area_source_pattern_unique',
                         'UNIQUE (area, source, pattern_description)')
    steps.append('drift_signals ✓')

    # ── 8. cluster_quality ────────────────────────────────────────────────────
    print("  [8/9] cluster_quality")
    add_source_column(cursor, 'cluster_quality')
    # Deduplicate before adding UNIQUE
    cursor.execute("""
        DELETE FROM cluster_quality a
        USING cluster_quality b
        WHERE a.id > b.id
          AND a.area = b.area
          AND a.source = b.source
    """)
    deduped = cursor.rowcount
    if deduped:
        print(f"      deduplicated {deduped} duplicate cluster_quality rows")
    _safe_add_constraint(cursor, 'cluster_quality',
                         'cq_area_source_unique', 'UNIQUE (area, source)')
    steps.append('cluster_quality ✓')

    # ── 9. behavioral_patterns ────────────────────────────────────────────────
    print("  [9/9] behavioral_patterns")
    add_source_column(cursor, 'behavioral_patterns')
    # No UNIQUE needed — patterns from different sources are distinct rows
    # Add index for fast source-filtered queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_bp_source ON behavioral_patterns(source)
    """)
    steps.append('behavioral_patterns ✓')

    return steps


def _constraint_exists(cursor, table: str, name: str) -> bool:
    cursor.execute("""
        SELECT 1 FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        WHERE t.relname = %s AND c.conname = %s
    """, (table, name))
    return cursor.fetchone() is not None


def _safe_add_constraint(cursor, table: str, name: str, definition: str):
    if not _constraint_exists(cursor, table, name):
        cursor.execute(f'ALTER TABLE {table} ADD CONSTRAINT "{name}" {definition}')
        print(f"      added constraint: {name}")
    else:
        print(f"      constraint already exists: {name}")


def main():
    print("\n018_add_source_columns.py — Adding source column to all pipeline tables\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        steps = run_migration(cursor)
        conn.commit()

        print("\n" + "=" * 60)
        print("  COMPLETE — All tables updated")
        print()
        for s in steps:
            print(f"    {s}")
        print()
        print("  Every existing row has been backfilled with source='google'.")
        print("  New pipelines (magicpin, zomato, tripadvisor) can now load")
        print("  data without overwriting existing rows.")
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
