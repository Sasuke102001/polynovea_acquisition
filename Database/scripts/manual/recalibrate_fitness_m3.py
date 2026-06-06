"""
recalibrate_fitness_m3.py
Reads M3 KPI observations, maps them to M2 fitness dimensions via
m3_kpi_dimension_map, and Bayesian-blends the result into
venue_fitness_dimensions WHERE source = 'blended'.

Usage:
    python recalibrate_fitness_m3.py --venue-id 42
    python recalibrate_fitness_m3.py --all          # all venues with M3 data
    python recalibrate_fitness_m3.py --dry-run --venue-id 42

Rules (from M3 brief 2026-05-30):
  - Min 3 observation_only sessions before updating any dimension
  - session_mode weights: observation_only=1.0, engineering_active=0.5, post_intervention=0.3
  - M3 evidence strength capped at 0.40 so live observations cannot override platform data
  - negative-direction slugs (crowd_stress) invert the observed score
  - Only touches source='blended' rows — Google/Magicpin/manual source rows are untouched
"""

import argparse
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

SESSION_MODE_WEIGHTS = {
    'observation_only':   1.0,
    'engineering_active': 0.5,
    'post_intervention':  0.3,
}

MIN_OBSERVATION_SESSIONS = 3


# ─── Core maths ───────────────────────────────────────────────────────────────

def compute_evidence_strength(session_count: int, avg_mode_weight: float) -> float:
    raw = min(session_count / 15.0, 1.0) * avg_mode_weight
    return min(raw, 0.4)


def bayesian_blend(m2_score: float, m3_score: float, evidence_strength: float) -> float:
    m2_weight = 1.0 - evidence_strength
    return round((m2_weight * m2_score) + (evidence_strength * m3_score), 6)


# ─── DB queries ───────────────────────────────────────────────────────────────

def fetch_venues_with_m3_data(cur) -> list[int]:
    cur.execute("SELECT DISTINCT venue_id FROM m3_kpi_observations ORDER BY venue_id")
    return [row[0] for row in cur.fetchall()]


def fetch_m3_kpi_evidence(cur, venue_id: int) -> list[dict]:
    """
    Aggregate M3 KPI observations per (m2_dimension, direction, weight, session_mode, day_of_week).
    Returns one row per unique combination so the caller can apply mode weighting.
    """
    cur.execute(
        """
        SELECT
            m.m2_dimension,
            m.direction,
            m.weight                                AS map_weight,
            o.session_mode,
            o.day_of_week,
            AVG(o.score)                            AS avg_score,
            COUNT(*)                                AS observation_count,
            COUNT(DISTINCT o.session_number)        AS session_count
        FROM m3_kpi_observations o
        JOIN m3_kpi_dimension_map m
          ON m.kpi_family_slug = o.kpi_family_slug
        WHERE o.venue_id = %s
        GROUP BY
            m.m2_dimension, m.direction, m.weight, o.session_mode, o.day_of_week
        ORDER BY o.session_mode, m.m2_dimension
        """,
        (venue_id,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def fetch_blended_scores(cur, venue_id: int) -> dict[str, float]:
    """Returns {dimension_column: score} for the blended row of this venue."""
    cur.execute(
        """
        SELECT
            fitness_for_office_lunch,
            fitness_for_repeat_habit,
            fitness_for_social_dwell,
            fitness_for_group_energy,
            fitness_for_destination_visit,
            operational_quality,
            retention_strength,
            monetization_potential
        FROM venue_fitness_dimensions
        WHERE venue_id = %s AND source = 'blended'
        LIMIT 1
        """,
        (venue_id,),
    )
    row = cur.fetchone()
    if row is None:
        return {}
    cols = [
        'fitness_for_office_lunch',
        'fitness_for_repeat_habit',
        'fitness_for_social_dwell',
        'fitness_for_group_energy',
        'fitness_for_destination_visit',
        'operational_quality',
        'retention_strength',
        'monetization_potential',
    ]
    return {col: float(val) if val is not None else None for col, val in zip(cols, row)}


# ─── Per-dimension computation ────────────────────────────────────────────────

def compute_dimension_updates(evidence_rows: list[dict]) -> dict[str, dict]:
    """
    Groups evidence rows by m2_dimension.
    Returns {dimension: {'new_score': float, 'evidence_strength': float, 'obs_sessions': int}}
    or skips dimensions below the minimum session threshold.
    """
    by_dim: dict[str, list[dict]] = {}
    for row in evidence_rows:
        dim = row['m2_dimension']
        by_dim.setdefault(dim, []).append(row)

    updates = {}
    for dim, rows in by_dim.items():
        # Count observation_only sessions for the threshold gate
        obs_only_sessions = sum(
            r['session_count'] for r in rows if r['session_mode'] == 'observation_only'
        )
        if obs_only_sessions < MIN_OBSERVATION_SESSIONS:
            continue

        # Weighted average of M3 observed scores across all modes
        total_weight = 0.0
        weighted_score_sum = 0.0
        total_mode_weight = 0.0
        total_sessions = 0

        for r in rows:
            mode_w = SESSION_MODE_WEIGHTS.get(r['session_mode'], 0.0)
            eff_weight = float(r['map_weight']) * mode_w
            score = float(r['avg_score'])

            if r['direction'] == 'negative':
                score = 1.0 - score

            weighted_score_sum += score * eff_weight
            total_weight += eff_weight
            total_mode_weight += mode_w * r['session_count']
            total_sessions += r['session_count']

        if total_weight == 0:
            continue

        m3_observed = weighted_score_sum / total_weight
        avg_mode_weight = total_mode_weight / total_sessions if total_sessions else 0.0
        evidence_strength = compute_evidence_strength(obs_only_sessions, avg_mode_weight)

        updates[dim] = {
            'm3_observed':        round(m3_observed, 6),
            'evidence_strength':  round(evidence_strength, 4),
            'obs_only_sessions':  obs_only_sessions,
        }

    return updates


# ─── Main recalibration for one venue ─────────────────────────────────────────

def recalibrate_venue(cur, venue_id: int, dry_run: bool) -> None:
    evidence_rows = fetch_m3_kpi_evidence(cur, venue_id)
    if not evidence_rows:
        print(f"  venue {venue_id}: no M3 evidence — skipped")
        return

    dim_updates = compute_dimension_updates(evidence_rows)
    if not dim_updates:
        print(f"  venue {venue_id}: below minimum session threshold on all dimensions — skipped")
        return

    blended = fetch_blended_scores(cur, venue_id)
    if not blended:
        print(f"  venue {venue_id}: no blended row in venue_fitness_dimensions — skipped")
        return

    for dim, meta in dim_updates.items():
        m2_existing = blended.get(dim)
        if m2_existing is None:
            print(f"  venue {venue_id}  {dim}: existing score is NULL — skipped")
            continue

        new_score = bayesian_blend(m2_existing, meta['m3_observed'], meta['evidence_strength'])

        print(
            f"  venue {venue_id}  {dim}: "
            f"{m2_existing:.4f} → {new_score:.4f}  "
            f"(m3={meta['m3_observed']:.4f}, strength={meta['evidence_strength']:.3f}, "
            f"obs_sessions={meta['obs_only_sessions']})"
        )

        if not dry_run:
            cur.execute(
                f"""
                UPDATE venue_fitness_dimensions
                SET {dim}            = %s,
                    computed_at      = NOW(),
                    pipeline_version = '2.0-m3-blend'
                WHERE venue_id = %s
                  AND source   = 'blended'
                """,
                (new_score, venue_id),
            )


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Recalibrate M2 fitness scores using M3 KPI data')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--venue-id', type=int, help='Single venue to recalibrate')
    group.add_argument('--all', action='store_true', help='All venues with M3 observations')
    parser.add_argument('--dry-run', action='store_true', help='Print changes without writing')
    args = parser.parse_args()

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        if args.all:
            venue_ids = fetch_venues_with_m3_data(cur)
            print(f"Found {len(venue_ids)} venues with M3 data")
        else:
            venue_ids = [args.venue_id]

        for vid in venue_ids:
            recalibrate_venue(cur, vid, dry_run=args.dry_run)

        if args.dry_run:
            print("\nDRY RUN — no changes written")
            conn.rollback()
        else:
            conn.commit()
            print(f"\nDone — {len(venue_ids)} venue(s) processed")

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()
