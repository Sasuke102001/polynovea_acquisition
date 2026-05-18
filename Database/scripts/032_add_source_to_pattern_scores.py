"""
032_add_source_to_pattern_scores.py
Adds missing `source` column to pattern_scores and backfills it
from behavioral_patterns via the existing pattern_id FK.

018_add_source_columns.py missed this table. This closes that gap.

Safe to re-run — uses IF NOT EXISTS and idempotent UPDATE.
"""

import os
import sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', 'REDACTED_DB_PASSWORD'),
    'sslmode':  'require',
}


def run():
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    # 1. Add source column if not already present
    cur.execute("""
        ALTER TABLE pattern_scores
        ADD COLUMN IF NOT EXISTS source VARCHAR(50) NOT NULL DEFAULT 'google'
    """)
    print("Step 1: source column added (or already exists)")

    # 2. Backfill from behavioral_patterns.source via pattern_id join
    cur.execute("""
        UPDATE pattern_scores ps
        SET    source = bp.source
        FROM   behavioral_patterns bp
        WHERE  ps.pattern_id = bp.id
          AND  ps.source != bp.source
    """)
    updated = cur.rowcount
    print(f"Step 2: {updated} rows backfilled from behavioral_patterns.source")

    # 3. Remove the DEFAULT now that all rows are populated
    cur.execute("""
        ALTER TABLE pattern_scores
        ALTER COLUMN source DROP DEFAULT
    """)
    print("Step 3: DEFAULT removed from source column")

    conn.commit()

    # 4. Verify
    cur.execute("SELECT source, COUNT(*) FROM pattern_scores GROUP BY source ORDER BY source")
    print("\npattern_scores rows by source:")
    for r in cur.fetchall():
        print(f"  {r[0]:<25} {r[1]:>6} rows")

    cur.execute("""
        SELECT COUNT(*) FROM pattern_scores ps
        JOIN behavioral_patterns bp ON ps.pattern_id = bp.id
        WHERE ps.source != bp.source
    """)
    mismatches = cur.fetchone()[0]
    print(f"\nSource mismatches (should be 0): {mismatches}")

    cur.close()
    conn.close()
    print("\nDone.")


if __name__ == '__main__':
    run()
