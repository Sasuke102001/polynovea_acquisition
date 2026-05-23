"""
compute_manual_pipeline.py
Post-load pipeline for a manually added venue.

Runs 3 steps in order:
  1. Blend fitness         — merges all source rows into a single source='blended' row
  2. Similarity            — cosine similarity against all other venues → venue_similarity
  3. Demographics          — Bayesian segment scoring → venue_demographic_scores

This is the equivalent of running steps 027 + 012 but scoped to one venue,
so it's fast and safe to re-run without touching the rest of the DB.

NOTE: BIF steps (primitives / interventions / patterns) are handled by the
actual BIF pipeline. Run before calling this script:
  1. python format_manual_for_pipeline.py [--venue-id N]
  2. (in Scripts_upper/) python step_3_extract.py --city manual
                          python step_4_pattern.py --city manual
                          python step_4b_governance_validate.py --city manual
                          python step_5_score.py --city manual
                          python step_5b_similarity.py --city manual
                          python step_6_output.py --city manual
  3. python 033_load_manual_step6_fitness.py
  4. python compute_manual_pipeline.py --venue-id N   ← this script

Can also be run standalone:
    python compute_manual_pipeline.py --venue-id 12066
    python compute_manual_pipeline.py --venue-id 12066 --skip-blend
"""

import argparse
import json
import math
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
    'password': os.getenv('PG_PASSWORD', 'REDACTED_DB_PASSWORD'),
    'sslmode':  'require',
}

# ─── Dimensions ───────────────────────────────────────────────────────────────

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

SIM_DIMS = [
    'fitness_for_office_lunch',
    'fitness_for_repeat_habit',
    'fitness_for_social_dwell',
    'fitness_for_group_energy',
    'fitness_for_destination_visit',
]

TOP_N_SIMILAR = 25

# ─── Demographics config (mirrors compute_venue_demographics.py) ──────────────

DIM_MAP = {
    "operational_quality":  "operational_quality",
    "repeat_habit":         "fitness_for_repeat_habit",
    "retention_strength":   "retention_strength",
    "friction_tolerance":   None,
    "social_dwell":         "fitness_for_social_dwell",
    "destination_visit":    "fitness_for_destination_visit",
    "office_lunch":         "fitness_for_office_lunch",
    "group_energy":         "fitness_for_group_energy",
}

CONFIDENCE_DISCOUNT = {"HIGH": 1.0, "MED": 0.80, "LOW": 0.60}

SEGMENT_FITNESS_WEIGHTS = {
    "solo_diners": {
        "operational_quality": (0.45, "HIGH"),
        "repeat_habit":        (0.20, "MED"),
        "retention_strength":  (0.15, "MED"),
        "social_dwell":        (0.05, "LOW"),
        "destination_visit":   (0.05, "LOW"),
    },
    "working_women": {
        "operational_quality": (0.30, "HIGH"),
        "office_lunch":        (0.25, "HIGH"),
        "retention_strength":  (0.15, "MED"),
        "social_dwell":        (0.10, "MED"),
        "destination_visit":   (0.05, "LOW"),
    },
    "couples": {
        "destination_visit":   (0.40, "HIGH"),
        "social_dwell":        (0.20, "HIGH"),
        "operational_quality": (0.15, "MED"),
        "repeat_habit":        (0.10, "MED"),
        "retention_strength":  (0.10, "MED"),
    },
    "premium": {
        "destination_visit":   (0.35, "HIGH"),
        "social_dwell":        (0.25, "HIGH"),
        "operational_quality": (0.20, "HIGH"),
        "retention_strength":  (0.10, "MED"),
        "repeat_habit":        (0.05, "LOW"),
    },
    "college_kids": {
        "group_energy":        (0.35, "HIGH"),
        "social_dwell":        (0.25, "HIGH"),
        "repeat_habit":        (0.10, "MED"),
        "operational_quality": (0.10, "MED"),
        "destination_visit":   (0.05, "LOW"),
    },
    "office_workers": {
        "office_lunch":        (0.35, "HIGH"),
        "repeat_habit":        (0.25, "HIGH"),
        "operational_quality": (0.20, "HIGH"),
        "retention_strength":  (0.05, "MED"),
        "social_dwell":        (0.05, "LOW"),
    },
    "families": {
        "repeat_habit":        (0.30, "HIGH"),
        "operational_quality": (0.25, "HIGH"),
        "retention_strength":  (0.20, "MED"),
        "social_dwell":        (0.05, "LOW"),
        "destination_visit":   (0.05, "LOW"),
    },
}

ALL_SEGMENTS = list(SEGMENT_FITNESS_WEIGHTS.keys())
FLAT_PRIOR = 1.0 / len(ALL_SEGMENTS)

_PRIOR_GENERIC = frozenset({
    "food", "point_of_interest", "establishment", "store",
    "premise", "locality", "political", "street_address", "geocode",
})

# Venue-type priors — same as compute_venue_demographics.py (abbreviated to key types)
VENUE_TYPE_SEGMENT_PRIORS = {
    "cafe": {
        "college_kids":   (0.25, "HIGH", ""),
        "working_women":  (0.20, "HIGH", ""),
        "solo_diners":    (0.20, "HIGH", ""),
        "office_workers": (0.15, "MED",  ""),
        "couples":        (0.10, "MED",  ""),
        "families":       (0.07, "LOW",  ""),
        "premium":        (0.03, "LOW",  ""),
    },
    "restaurant": {
        "families":       (0.25, "MED",  ""),
        "couples":        (0.20, "MED",  ""),
        "office_workers": (0.15, "MED",  ""),
        "college_kids":   (0.12, "MED",  ""),
        "solo_diners":    (0.10, "MED",  ""),
        "premium":        (0.10, "MED",  ""),
        "working_women":  (0.08, "LOW",  ""),
    },
    "bar": {
        "college_kids":   (0.30, "HIGH", ""),
        "couples":        (0.20, "MED",  ""),
        "office_workers": (0.15, "MED",  ""),
        "solo_diners":    (0.10, "MED",  ""),
        "premium":        (0.10, "MED",  ""),
        "working_women":  (0.08, "LOW",  ""),
        "families":       (0.07, "LOW",  ""),
    },
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _get_prior(raw_types: list[str]) -> dict[str, float]:
    for t in (raw_types or []):
        if t in _PRIOR_GENERIC:
            continue
        if t in VENUE_TYPE_SEGMENT_PRIORS:
            return {seg: entry[0] for seg, entry in VENUE_TYPE_SEGMENT_PRIORS[t].items()}
    return {seg: FLAT_PRIOR for seg in ALL_SEGMENTS}


def _compute_demo_scores(prior: dict[str, float], fitness: dict[str, float]) -> list[tuple]:
    raw = {}
    for segment_id, weights in SEGMENT_FITNESS_WEIGHTS.items():
        evidence_sum = 0.0
        for dim, (weight, conf) in weights.items():
            col = DIM_MAP.get(dim)
            if col is None:
                continue
            evidence_sum += fitness.get(col, 0.0) * weight * CONFIDENCE_DISCOUNT[conf]
        raw[segment_id] = prior.get(segment_id, FLAT_PRIOR) * (1.0 + evidence_sum)

    total = sum(raw.values()) or 1.0
    ranked = sorted(raw.items(), key=lambda x: x[1], reverse=True)
    return [(seg, round(v / total, 6), rank + 1) for rank, (seg, v) in enumerate(ranked)]


# ─── Steps ────────────────────────────────────────────────────────────────────

def step_blend(cur, venue_id: int) -> dict[str, float]:
    """Blend all source fitness rows into source='blended' for this venue."""
    dims_sql = ', '.join(f'AVG({d}) AS {d}' for d in FITNESS_DIMS)
    cur.execute(
        f"""
        SELECT {dims_sql},
               AVG(operational_quality)    AS operational_quality,
               AVG(retention_strength)     AS retention_strength,
               AVG(monetization_potential) AS monetization_potential
        FROM venue_fitness_dimensions
        WHERE venue_id = %s AND source != 'blended'
        """,
        (venue_id,),
    )
    row = cur.fetchone()
    if not row or all(v is None for v in row.values()):
        print(f"  [blend] No non-blended fitness rows found for venue_id={venue_id}")
        return {}

    fitness = {k: float(v or 0.0) for k, v in row.items()}

    cur.execute(
        """
        INSERT INTO venue_fitness_dimensions
            (venue_id, source,
             fitness_for_office_lunch, fitness_for_repeat_habit,
             fitness_for_social_dwell, fitness_for_group_energy,
             fitness_for_destination_visit,
             operational_quality, retention_strength, monetization_potential,
             pipeline_version, schema_version)
        VALUES (%s, 'blended', %s, %s, %s, %s, %s, %s, %s, %s, 'manual-blend-1.0', 1)
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
            computed_at                   = NOW()
        """,
        (
            venue_id,
            fitness['fitness_for_office_lunch'],
            fitness['fitness_for_repeat_habit'],
            fitness['fitness_for_social_dwell'],
            fitness['fitness_for_group_energy'],
            fitness['fitness_for_destination_visit'],
            fitness['operational_quality'],
            fitness['retention_strength'],
            fitness['monetization_potential'],
        ),
    )

    cur.execute(
        """
        INSERT INTO behavioral_summary
            (venue_id, source, operational_quality, retention_strength, monetization_potential)
        VALUES (%s, 'blended', %s, %s, %s)
        ON CONFLICT (venue_id, source) DO UPDATE SET
            operational_quality    = EXCLUDED.operational_quality,
            retention_strength     = EXCLUDED.retention_strength,
            monetization_potential = EXCLUDED.monetization_potential
        """,
        (venue_id, fitness['operational_quality'],
         fitness['retention_strength'], fitness['monetization_potential']),
    )

    print(f"  [blend] Upserted blended fitness row for venue_id={venue_id}")
    return fitness


def step_similarity(cur, venue_id: int) -> None:
    """Compute cosine similarity against all other venues → venue_similarity + venue_vectors."""
    cur.execute(
        f"""
        SELECT {', '.join(SIM_DIMS)}
        FROM venue_fitness_dimensions
        WHERE venue_id = %s
        ORDER BY CASE source WHEN 'blended' THEN 0 WHEN 'manual_reviews' THEN 1 ELSE 2 END
        LIMIT 1
        """,
        (venue_id,),
    )
    target_row = cur.fetchone()
    if not target_row:
        print(f"  [similarity] No fitness data for venue_id={venue_id} — skipping")
        return

    target_vec = [float(target_row[d] or 0.0) for d in SIM_DIMS]

    cur.execute(
        f"""
        SELECT DISTINCT ON (venue_id) venue_id, {', '.join(SIM_DIMS)}
        FROM venue_fitness_dimensions
        WHERE venue_id != %s
        ORDER BY venue_id,
                 CASE source WHEN 'blended' THEN 0 WHEN 'google' THEN 1 ELSE 2 END
        """,
        (venue_id,),
    )
    all_rows = cur.fetchall()

    scored = sorted(
        [(row['venue_id'], round(cosine_similarity(target_vec, [float(row[d] or 0.0) for d in SIM_DIMS]), 6))
         for row in all_rows],
        key=lambda x: x[1], reverse=True,
    )
    top = scored[:TOP_N_SIMILAR]

    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO venue_similarity
            (venue_id, source, similar_venue_id, similarity_score, shared_primitives, shared_primitive_count)
        VALUES %s
        ON CONFLICT (venue_id, source, similar_venue_id) DO UPDATE SET
            similarity_score = EXCLUDED.similarity_score
        """,
        [(venue_id, 'manual_reviews', sim_id, score, json.dumps([]), 0) for sim_id, score in top],
    )

    cur.execute(
        """
        INSERT INTO venue_vectors (venue_id, source, fitness_vector, vector_source)
        VALUES (%s, 'manual_reviews', %s, 'manual_review_analysis')
        ON CONFLICT (venue_id, source) DO UPDATE SET
            fitness_vector = EXCLUDED.fitness_vector,
            last_computed  = CURRENT_TIMESTAMP
        """,
        (venue_id, target_vec),
    )

    print(f"  [similarity] {len(top)} similarity rows + vector upserted for venue_id={venue_id}")


def step_demographics(cur, venue_id: int) -> None:
    """Compute Bayesian segment alignment scores → venue_demographic_scores."""
    fitness_cols = ['fitness_for_office_lunch', 'fitness_for_repeat_habit',
                    'fitness_for_social_dwell', 'fitness_for_group_energy',
                    'fitness_for_destination_visit', 'operational_quality', 'retention_strength']
    cols_sql = ', '.join(fitness_cols)

    cur.execute(
        f"""
        SELECT {cols_sql}
        FROM venue_fitness_dimensions
        WHERE venue_id = %s
        ORDER BY CASE source WHEN 'blended' THEN 0 WHEN 'manual_reviews' THEN 1 ELSE 2 END
        LIMIT 1
        """,
        (venue_id,),
    )
    fit_row = cur.fetchone()
    if not fit_row:
        print(f"  [demographics] No fitness data for venue_id={venue_id} — skipping")
        return

    fitness = {k: float(fit_row[k] or 0.0) for k in fitness_cols}

    cur.execute("SELECT types FROM venues WHERE id = %s", (venue_id,))
    venue_row = cur.fetchone()
    raw_types = list(venue_row['types'] or []) if venue_row else []

    prior  = _get_prior(raw_types)
    scored = _compute_demo_scores(prior, fitness)

    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO venue_demographic_scores
            (venue_id, segment_id, alignment_score, segment_rank)
        VALUES %s
        ON CONFLICT (venue_id, segment_id) DO UPDATE SET
            alignment_score = EXCLUDED.alignment_score,
            segment_rank    = EXCLUDED.segment_rank
        """,
        [(venue_id, seg, score, rank) for seg, score, rank in scored],
    )

    top3 = [(seg, score) for seg, score, _ in scored[:3]]
    print(f"  [demographics] {len(scored)} segment scores upserted. Top 3: {top3}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def run(venue_id: int, skip_blend: bool = False) -> None:
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # Verify venue exists
        cur.execute("SELECT name, area, city, types FROM venues WHERE id = %s", (venue_id,))
        venue = cur.fetchone()
        if not venue:
            print(f"ERROR: No venue found with id={venue_id}")
            sys.exit(1)

        print(f"\n{'='*60}")
        print(f"  compute_manual_pipeline.py — venue_id={venue_id}")
        print(f"  {venue['name']} — {venue['area']}, {venue['city']}")
        print(f"  Types: {list(venue['types'] or [])}")
        print(f"{'='*60}\n")

        if not skip_blend:
            step_blend(cur, venue_id)
        else:
            print("  [blend] Skipped (--skip-blend flag)")

        step_similarity(cur, venue_id)
        step_demographics(cur, venue_id)

        conn.commit()

        print(f"\n{'='*60}")
        print(f"  COMPLETE — venue_id={venue_id} fully processed")
        print(f"  - Fitness blend    : {'skipped' if skip_blend else '✓'}")
        print(f"  - Competitors tab  : ✓ (venue_similarity populated)")
        print(f"  - Customer segments: ✓ (venue_demographic_scores populated)")
        print(f"{'='*60}\n")

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        print(f"\n[ERROR] {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Run post-load pipeline for a manually added venue (blend + similarity + demographics)"
    )
    parser.add_argument('--venue-id',   type=int,  required=True,  help="venue_id of the manual venue")
    parser.add_argument('--skip-blend', action='store_true', help="Skip the blend step (if fitness already blended)")
    args = parser.parse_args()
    run(args.venue_id, skip_blend=args.skip_blend)
