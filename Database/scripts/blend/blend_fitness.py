"""
027_blend_fitness.py
Blend runner — combines venue_fitness_dimensions from all loaded sources
into a single source='blended' row per venue.

Weighting rule: equal weight per source PRESENT FOR THAT VENUE (1/N).
  Venue on 4 platforms  → each source contributes 25%
  Venue on 2 platforms  → each source contributes 50%
  Venue on 1 platform   → that source's values verbatim (no dilution)

This means a venue that only exists on Google gets a clean Google score.
A venue across Google + MagicPin upper + Google Reviews gets each weighted 1/3.
No hardcoded weights — the blend auto-adjusts as new sources are loaded.

Source naming convention:
  google          — Google Places API (004_load_scores.py)
  magicpin_upper  — MagicPin static block (026_load_magicpin_step6_fitness.py)
  google_reviews  — Google Search review extraction (031_load_google_reviews_*.py — pending)
  zomato          — Zomato (future)
  tripadvisor     — TripAdvisor (future)

Amendment workflow (e.g. google_reviews arrives):
  1. Run 031_load_google_reviews_*.py  → writes source='google_reviews' rows
  2. Re-run this script                → recomputes source='blended'
  No schema changes, no migrations needed.

Writes:
  - venue_fitness_dimensions  source='blended'
  - behavioral_summary        source='blended'

Run after any source loader. Re-run every time new data is added.
"""

import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', '07586277012Luna'),
    'sslmode':  'require',
}

FITNESS_DIMS = [
    'fitness_for_office_lunch',
    'fitness_for_repeat_habit',
    'fitness_for_social_dwell',
    'fitness_for_group_energy',
    'fitness_for_destination_visit',
    'operational_quality',
    'retention_strength',
    'monetization_potential',
]

FETCH_SQL = """
    SELECT venue_id, source,
           fitness_for_office_lunch, fitness_for_repeat_habit,
           fitness_for_social_dwell, fitness_for_group_energy,
           fitness_for_destination_visit,
           operational_quality, retention_strength, monetization_potential
    FROM venue_fitness_dimensions
    WHERE source NOT IN ('blended', 'manual_bif')
    ORDER BY venue_id, source
"""

UPSERT_FITNESS_SQL = """
    INSERT INTO venue_fitness_dimensions
        (venue_id, source,
         fitness_for_office_lunch, fitness_for_repeat_habit,
         fitness_for_social_dwell, fitness_for_group_energy,
         fitness_for_destination_visit,
         operational_quality, retention_strength, monetization_potential,
         pipeline_version, schema_version)
    VALUES %s
    ON CONFLICT (venue_id, source) DO UPDATE SET
        fitness_for_office_lunch      = EXCLUDED.fitness_for_office_lunch,
        fitness_for_repeat_habit      = EXCLUDED.fitness_for_repeat_habit,
        fitness_for_social_dwell      = EXCLUDED.fitness_for_social_dwell,
        fitness_for_group_energy      = EXCLUDED.fitness_for_group_energy,
        fitness_for_destination_visit = EXCLUDED.fitness_for_destination_visit,
        operational_quality           = EXCLUDED.operational_quality,
        retention_strength            = EXCLUDED.retention_strength,
        monetization_potential        = EXCLUDED.monetization_potential,
        pipeline_version              = EXCLUDED.pipeline_version,
        computed_at                   = NOW();
"""

UPSERT_SUMMARY_SQL = """
    INSERT INTO behavioral_summary
        (venue_id, source, operational_quality, retention_strength, monetization_potential)
    VALUES %s
    ON CONFLICT (venue_id, source) DO UPDATE SET
        operational_quality    = EXCLUDED.operational_quality,
        retention_strength     = EXCLUDED.retention_strength,
        monetization_potential = EXCLUDED.monetization_potential;
"""


def blend_venue(source_rows: list[dict]) -> dict:
    """
    Equal weight per source that has a non-zero value for each dimension.
    N is computed per-dimension, not globally.

    Rationale: a 0.0 from a source means "no signal detected", not "genuinely zero
    performance". Averaging a real score with a no-signal zero would dilute it
    incorrectly. Only sources that detected signal (> 0.0) contribute to the average
    for that dimension.

    If ALL sources are 0.0 for a dimension → blended stays 0.0 (correct: no signal
    anywhere means no basis for a non-zero score).
    """
    if not source_rows:
        return {d: 0.0 for d in FITNESS_DIMS}

    totals = {d: 0.0 for d in FITNESS_DIMS}
    counts = {d: 0   for d in FITNESS_DIMS}

    for row in source_rows:
        for dim in FITNESS_DIMS:
            val = float(row.get(dim) or 0.0)
            if val > 0.0:
                totals[dim] += val
                counts[dim] += 1

    return {
        d: round(totals[d] / counts[d], 4) if counts[d] > 0 else 0.0
        for d in FITNESS_DIMS
    }


def main():
    print("\n027_blend_fitness.py — Blending fitness dimensions across all sources\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        print("  Fetching all source rows from venue_fitness_dimensions...")
        cursor.execute(FETCH_SQL)
        rows = cursor.fetchall()
        print(f"  {len(rows):,} source rows fetched\n")

        # Group by venue_id
        by_venue: dict[int, list] = {}
        for row in rows:
            by_venue.setdefault(row['venue_id'], []).append(dict(row))

        blended_fitness  = []
        blended_summary  = []
        source_breakdown = {}

        for venue_id, source_rows in by_venue.items():
            sources = [r['source'] for r in source_rows]
            key = '+'.join(sorted(set(sources)))
            source_breakdown[key] = source_breakdown.get(key, 0) + 1

            blended = blend_venue(source_rows)
            blended_fitness.append((
                venue_id,
                'blended',
                blended['fitness_for_office_lunch'],
                blended['fitness_for_repeat_habit'],
                blended['fitness_for_social_dwell'],
                blended['fitness_for_group_energy'],
                blended['fitness_for_destination_visit'],
                blended['operational_quality'],
                blended['retention_strength'],
                blended['monetization_potential'],
                'blend-runner-2.0-equal-weight',
                1,
            ))
            blended_summary.append((
                venue_id,
                'blended',
                blended['operational_quality'],
                blended['retention_strength'],
                blended['monetization_potential'],
            ))

        # Batch upsert fitness
        write_cursor = conn.cursor()
        for i in range(0, len(blended_fitness), 500):
            psycopg2.extras.execute_values(
                write_cursor, UPSERT_FITNESS_SQL, blended_fitness[i:i+500]
            )

        # Batch upsert summary
        for i in range(0, len(blended_summary), 500):
            psycopg2.extras.execute_values(
                write_cursor, UPSERT_SUMMARY_SQL, blended_summary[i:i+500]
            )

        conn.commit()

        print(f"{'='*55}")
        print(f"  COMPLETE")
        print(f"  Venues blended : {len(blended_fitness):,}")
        print()
        print(f"  Source coverage:")
        for combo, count in sorted(source_breakdown.items()):
            print(f"    {combo:<30} {count:>5} venues")
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
