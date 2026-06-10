"""
compute_city_baselines.py — Persist per-city robust baselines per fitness dimension.

For every (city, dimension) over source='blended' rows it computes:
  median, MAD (median absolute deviation), p25, p75, venue_count
and upserts into city_dimension_baselines.

Why this exists:
  Scores are absolute today. A "high social_dwell" in SoBo is not the same as in
  Thane. These baselines let the app and downstream ML read a venue's position
  RELATIVE to its local market. The baselines sharpen automatically as more
  venues load per city — old venues get more accurate with zero code changes.

Run: after blend_fitness.py (needs source='blended' rows).
"""

import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

for p in [Path(__file__).parent.parent.parent / ".env",
          Path(__file__).parent.parent.parent.parent / "App" / "backend" / ".env"]:
    if p.exists():
        load_dotenv(p)
        break

DB_CONFIG = {
    "host":     os.getenv("PG_HOST",     "polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com"),
    "port":     int(os.getenv("PG_PORT", 5432)),
    "dbname":   os.getenv("PG_DB",       "polynovea_module2"),
    "user":     os.getenv("PG_USER",     "polynovea_admin"),
    "password": os.getenv("PG_PASSWORD", ""),
    "sslmode":  "require",
}

PIPELINE_VERSION = "city-baselines-v1"
SOURCE_KEY = "blended"

DIMENSIONS = [
    "fitness_for_office_lunch",
    "fitness_for_repeat_habit",
    "fitness_for_social_dwell",
    "fitness_for_group_energy",
    "fitness_for_destination_visit",
    "operational_quality",
    "retention_strength",
    "monetization_potential",
]

FETCH_SQL = f"""
    SELECT COALESCE(v.city, 'unknown') AS city,
           {', '.join('f.' + d for d in DIMENSIONS)}
    FROM venue_fitness_dimensions f
    JOIN venues v ON v.id = f.venue_id
    WHERE f.source = %s
"""

DELETE_SQL = "DELETE FROM city_dimension_baselines WHERE source = %s"

UPSERT_SQL = """
    INSERT INTO city_dimension_baselines
        (city, source, dimension, median, mad, p25, p75, venue_count,
         pipeline_version, computed_at)
    VALUES %s
    ON CONFLICT (city, source, dimension) DO UPDATE SET
        median           = EXCLUDED.median,
        mad              = EXCLUDED.mad,
        p25              = EXCLUDED.p25,
        p75              = EXCLUDED.p75,
        venue_count      = EXCLUDED.venue_count,
        pipeline_version = EXCLUDED.pipeline_version,
        computed_at      = NOW()
"""


def _percentile(sorted_vals, pct):
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * pct
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = k - lo
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac


def main():
    print("\ncompute_city_baselines.py — Per-city robust baselines\n")

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute(FETCH_SQL, (SOURCE_KEY,))
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]

        if not rows:
            print("  No blended rows found. Run blend_fitness.py first. Nothing to do.")
            return

        by_city = defaultdict(list)
        for row in rows:
            by_city[row["city"]].append(row)

        upserts = []
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        for city, city_rows in by_city.items():
            for dim in DIMENSIONS:
                vals = sorted(float(r[dim] or 0.0) for r in city_rows)
                if not vals:
                    continue
                median = statistics.median(vals)
                mad = statistics.median([abs(v - median) for v in vals]) or 0.0
                upserts.append((
                    city, SOURCE_KEY, dim,
                    round(median, 4),
                    round(mad, 4),
                    round(_percentile(vals, 0.25), 4),
                    round(_percentile(vals, 0.75), 4),
                    len(vals),
                    PIPELINE_VERSION,
                    now,
                ))

        with conn.cursor() as cursor:
            cursor.execute(DELETE_SQL, (SOURCE_KEY,))
            psycopg2.extras.execute_values(cursor, UPSERT_SQL, upserts, page_size=500)
        conn.commit()

        print(f"  Cities: {len(by_city):,}   Baseline rows written: {len(upserts):,}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
