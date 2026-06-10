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
from pathlib import Path
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

# Load database environment variables from .env
for p in [Path(__file__).parent.parent.parent / ".env", Path(__file__).parent.parent.parent.parent / "App" / "backend" / ".env"]:
    if p.exists():
        load_dotenv(p)
        break

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', ''),
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
           operational_quality, retention_strength, monetization_potential,
           confidence, evidence_count
    FROM venue_fitness_dimensions
    WHERE source NOT IN ('blended', 'manual_bif')
    ORDER BY venue_id, source
"""

# Confidence proxy tuning. Saturation points: 3 distinct sources agreeing, and
# ~50 reviews of evidence, each count as "fully confident" on their axis.
CONF_SOURCE_SATURATION   = 3.0
CONF_EVIDENCE_SATURATION = 50.0

UPSERT_FITNESS_SQL = """
    INSERT INTO venue_fitness_dimensions
        (venue_id, source,
         fitness_for_office_lunch, fitness_for_repeat_habit,
         fitness_for_social_dwell, fitness_for_group_energy,
         fitness_for_destination_visit,
         operational_quality, retention_strength, monetization_potential,
         confidence, evidence_count,
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
        confidence                    = EXCLUDED.confidence,
        evidence_count                = EXCLUDED.evidence_count,
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


def _source_variances(by_venue: dict) -> dict:
    """
    E10: Compute per-source variance across all venues for each fitness dimension.
    A consistent source (low variance) gets higher Kalman gain.
    Returns {source: {dim: variance}}.
    """
    source_vals: dict = {}
    for rows in by_venue.values():
        for row in rows:
            src = row["source"]
            source_vals.setdefault(src, {d: [] for d in FITNESS_DIMS})
            for dim in FITNESS_DIMS:
                val = float(row.get(dim) or 0.0)
                if val > 0.0:
                    source_vals[src][dim].append(val)

    variances = {}
    for src, dim_vals in source_vals.items():
        variances[src] = {}
        for dim, vals in dim_vals.items():
            if len(vals) < 2:
                variances[src][dim] = 1.0  # unknown variance → neutral weight
            else:
                mean = sum(vals) / len(vals)
                variances[src][dim] = sum((v - mean) ** 2 for v in vals) / len(vals)
    return variances


def blend_venue(source_rows: list[dict], source_variances: dict | None = None) -> dict:
    """
    E10: Inverse-variance (Kalman) weighted blend per dimension.

    Each source's weight = 1/variance for that dimension, normalised so weights sum to 1.
    A consistent source (low variance across all venues) contributes more than a noisy one.
    Falls back to equal weight when variance data is unavailable.

    A 0.0 value means "no signal detected" and is excluded from the blend (same as before).
    If ALL sources are 0.0 → blended stays 0.0.
    """
    if not source_rows:
        return {d: 0.0 for d in FITNESS_DIMS}

    result = {}
    for dim in FITNESS_DIMS:
        active = [
            (float(row.get(dim) or 0.0), row["source"])
            for row in source_rows
            if float(row.get(dim) or 0.0) > 0.0
        ]
        if not active:
            result[dim] = 0.0
            continue

        if source_variances:
            # Inverse-variance weights — clamp variance floor at 0.001 to avoid division by zero
            inv_vars = [
                1.0 / max(source_variances.get(src, {}).get(dim, 1.0), 0.001)
                for _, src in active
            ]
            total_inv = sum(inv_vars)
            weights = [iv / total_inv for iv in inv_vars]
        else:
            n = len(active)
            weights = [1.0 / n] * n

        result[dim] = round(sum(v * w for (v, _), w in zip(active, weights)), 4)

    return result


def blend_confidence(source_rows: list[dict]) -> tuple[float, int]:
    """
    A: Derive a blended confidence in [0,1] and a total evidence_count.

    Two independent axes of trust, averaged:
      - source agreement : more distinct platforms carrying signal → more trust
      - evidence volume   : more reviews/mentions behind the venue → more trust

    If raw sources have already emitted per-source confidence (BIF step_4), we
    fold their evidence-weighted mean in as a floor so real signal confidence is
    never thrown away. Until then this proxy still rises automatically as new
    sources and reviews load — the "grows better over time" property.
    """
    sources_with_signal = {
        row["source"]
        for row in source_rows
        if any(float(row.get(d) or 0.0) > 0.0 for d in FITNESS_DIMS)
    }
    source_count = len(sources_with_signal)

    evidence_total = sum(int(row.get("evidence_count") or 0) for row in source_rows)

    source_factor   = min(1.0, source_count / CONF_SOURCE_SATURATION)
    evidence_factor = min(1.0, evidence_total / CONF_EVIDENCE_SATURATION)
    proxy = 0.5 * source_factor + 0.5 * evidence_factor

    # Fold in real per-source confidence if any source emitted it.
    real_confs = [float(row["confidence"]) for row in source_rows
                  if row.get("confidence") is not None]
    if real_confs:
        evidenced_mean = sum(real_confs) / len(real_confs)
        # agreement across sources lifts a single-source confidence ceiling
        confidence = min(1.0, evidenced_mean * (0.7 + 0.3 * source_factor))
        confidence = max(confidence, proxy * 0.5)  # proxy as a soft floor
    else:
        confidence = proxy

    return round(confidence, 3), evidence_total


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

        # E10: compute source reliability variances once across all venues
        src_variances = _source_variances(by_venue)
        src_list = sorted(src_variances.keys())
        print(f"\n  Source reliability (avg variance across dims):")
        for src in src_list:
            avg_var = sum(src_variances[src].values()) / max(1, len(src_variances[src]))
            print(f"    {src:<25} avg_var={avg_var:.4f}")
        print()

        blended_fitness  = []
        blended_summary  = []
        source_breakdown = {}

        for venue_id, source_rows in by_venue.items():
            sources = [r['source'] for r in source_rows]
            key = '+'.join(sorted(set(sources)))
            source_breakdown[key] = source_breakdown.get(key, 0) + 1

            blended = blend_venue(source_rows, src_variances)
            conf, evidence_total = blend_confidence(source_rows)
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
                conf,
                evidence_total,
                'blend-runner-3.1-kalman-iv-conf',
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
