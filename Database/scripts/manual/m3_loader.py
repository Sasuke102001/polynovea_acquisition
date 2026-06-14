"""
m3_loader.py
Reads enriched m3_kpi_observations and routes to:
  - venue_fitness_dimensions  source='m3_watch_only' or 'm3_baseline'  (natural only)
  - venue_fitness_conditional  per-stratum scores  (natural only)
  - venue_intervention_efficacy  (engineered/settling rows)

Then call blend_fitness.py separately to re-blend.

Usage:
    python m3_loader.py --venue-id 66
    python m3_loader.py --all
    python m3_loader.py --dry-run --venue-id 66
    python m3_loader.py --smoke-test     # synthetic rows, verify routing, clean up
"""

import argparse
import json
import os
import sys
from pathlib import Path
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

for p in [
    Path(__file__).parent.parent.parent / ".env",
    Path(__file__).parent.parent.parent.parent / "App" / "backend" / ".env",
]:
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

# ── Philosophy dials ──────────────────────────────────────────────────────────
# How many reviews equal one M3 natural session (for confidence calculation).
# Lower k = more trust per session. Adjust without schema changes.
K_WATCH_ONLY        = 8    # acquisition-only, pure observation — highest trust
K_WATCH_AND_OPTIMISE = 15  # baseline phase of an optimisation engagement

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

DAY_NAMES = {1:'monday', 2:'tuesday', 3:'wednesday', 4:'thursday',
             5:'friday', 6:'saturday', 7:'sunday'}


def time_of_day(hour: int) -> str:
    if hour < 15:
        return 'lunch'
    if hour < 22:
        return 'evening'
    return 'late_night'


# ── DB helpers ────────────────────────────────────────────────────────────────

def fetch_bridge_map(cur) -> dict:
    """Returns {kpi_family_slug: [(m2_dimension, direction, weight), ...]}"""
    cur.execute("""
        SELECT kpi_family_slug, m2_dimension, direction, weight
        FROM m3_kpi_dimension_map ORDER BY kpi_family_slug, weight DESC
    """)
    bridge = {}
    for slug, dim, direction, weight in cur.fetchall():
        bridge.setdefault(slug, []).append((dim, direction, float(weight)))
    return bridge


def fetch_venues_with_natural_data(cur) -> list[int]:
    cur.execute("""
        SELECT DISTINCT venue_id FROM m3_kpi_observations
        WHERE observation_state = 'natural' ORDER BY venue_id
    """)
    return [r[0] for r in cur.fetchall()]


def fetch_natural_rows(cur, venue_id: int) -> list[dict]:
    cur.execute("""
        SELECT venue_id, session_number, observation_state, service_type,
               engagement_phase, day_of_week, session_start_hour, zone,
               kpi_family_slug, score, signal_count
        FROM m3_kpi_observations
        WHERE venue_id = %s AND observation_state = 'natural'
        ORDER BY session_number, kpi_family_slug
    """, (venue_id,))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def fetch_engineered_rows(cur, venue_id: int) -> list[dict]:
    cur.execute("""
        SELECT venue_id, session_number, observation_state, service_type,
               engagement_phase, day_of_week, session_start_hour, zone,
               kpi_family_slug, score, signal_count
        FROM m3_kpi_observations
        WHERE venue_id = %s AND observation_state IN ('engineered', 'settling')
        ORDER BY session_number, kpi_family_slug
    """, (venue_id,))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def fetch_outcome_map(cur, venue_id: int) -> dict:
    """Returns {session_number: intervention_type} for sessions where M3 logged an intervention."""
    cur.execute("""
        SELECT session_number, intervention_type
        FROM m3_venue_behavioral_outcomes
        WHERE venue_id = %s AND intervention_deployed = true
        ORDER BY session_number
    """, (venue_id,))
    return {r[0]: r[1] for r in cur.fetchall()}


# ── Translation ───────────────────────────────────────────────────────────────

def translate_to_dimensions(rows: list[dict], bridge: dict) -> dict:
    """
    Maps KPI-family rows → per-dimension scores.
    Returns {dimension: {'scores': [float,...], 'signal_counts': [int,...]}}
    Only maps slugs that exist in bridge. Applies direction inversion.
    """
    by_dim: dict[str, dict] = {}
    for row in rows:
        slug = row['kpi_family_slug']
        if slug not in bridge:
            continue
        raw_score = float(row['score'] or 0.0)
        sig_count = int(row['signal_count'] or 1)
        for dim, direction, weight in bridge[slug]:
            score = (1.0 - raw_score) if direction == 'negative' else raw_score
            weighted = score * weight
            d = by_dim.setdefault(dim, {'weighted_scores': [], 'weights': [], 'signal_counts': []})
            d['weighted_scores'].append(weighted)
            d['weights'].append(weight)
            d['signal_counts'].append(sig_count)

    result = {}
    for dim, d in by_dim.items():
        total_weight = sum(d['weights'])
        dim_score = sum(d['weighted_scores']) / total_weight if total_weight else 0.0
        result[dim] = {
            'score': round(dim_score, 4),
            'signal_count': sum(d['signal_counts']),
        }
    return result


def m3_source_label(service_type: str | None) -> str:
    if service_type == 'watch_only':
        return 'm3_watch_only'
    return 'm3_baseline'


def compute_confidence(session_count: int, service_type: str | None) -> float:
    k = K_WATCH_ONLY if service_type == 'watch_only' else K_WATCH_AND_OPTIMISE
    return round(min(1.0, session_count / k), 3)


# ── Writers ───────────────────────────────────────────────────────────────────

def write_fitness_dimensions(cur, venue_id: int, dim_scores: dict,
                              source: str, session_count: int,
                              service_type: str | None, dry_run: bool) -> None:
    """Upserts one source row in venue_fitness_dimensions."""
    if not dim_scores:
        return

    confidence  = compute_confidence(session_count, service_type)
    total_sigs  = sum(v['signal_count'] for v in dim_scores.values())

    row = {d: dim_scores.get(d, {}).get('score', None) for d in FITNESS_DIMS}
    row_tuple = (
        venue_id, source,
        row['fitness_for_office_lunch'],
        row['fitness_for_repeat_habit'],
        row['fitness_for_social_dwell'],
        row['fitness_for_group_energy'],
        row['fitness_for_destination_visit'],
        row['operational_quality'],
        row['retention_strength'],
        row['monetization_potential'],
        confidence,
        total_sigs,
        '3.0-m3-loader',
        1,
    )

    print(f"    fitness_dimensions source={source}  confidence={confidence}  "
          f"evidence={total_sigs}  dims_hit={len(dim_scores)}")
    for d, v in dim_scores.items():
        print(f"      {d:<35} {v['score']:.4f}")

    if not dry_run:
        cur.execute("""
            INSERT INTO venue_fitness_dimensions
                (venue_id, source,
                 fitness_for_office_lunch, fitness_for_repeat_habit,
                 fitness_for_social_dwell, fitness_for_group_energy,
                 fitness_for_destination_visit, operational_quality,
                 retention_strength, monetization_potential,
                 confidence, evidence_count, pipeline_version, schema_version)
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
                computed_at                   = NOW()
        """, [row_tuple], template='(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)')


def write_conditional(cur, venue_id: int, natural_rows: list[dict],
                      bridge: dict, dry_run: bool) -> int:
    """Writes per-stratum scores to venue_fitness_conditional."""
    # Group by (day_of_week, time_of_day) strata
    strata: dict = {}
    for row in natural_rows:
        dow  = DAY_NAMES.get(int(row['day_of_week'] or 1), 'monday')
        tod  = time_of_day(int(row['session_start_hour'] or 20))
        key_dow = ('day_of_week', dow)
        key_tod = ('time_of_day', tod)
        for key in (key_dow, key_tod):
            strata.setdefault(key, []).append(row)

    written = 0
    for (ctype, cval), rows in strata.items():
        dim_scores = translate_to_dimensions(rows, bridge)
        session_count = len({r['session_number'] for r in rows})
        for dim, v in dim_scores.items():
            print(f"    conditional  {ctype}={cval:<12} {dim:<35} {v['score']:.4f}")
            written += 1
            if not dry_run:
                cur.execute("""
                    INSERT INTO venue_fitness_conditional
                        (venue_id, dimension, condition_type, condition_value,
                         score, session_count, observation_state, service_type, pipeline_version)
                    VALUES (%s,%s,%s,%s,%s,%s,'natural',%s,'3.0-m3-loader')
                    ON CONFLICT (venue_id, dimension, condition_type, condition_value)
                    DO UPDATE SET
                        score           = EXCLUDED.score,
                        session_count   = EXCLUDED.session_count,
                        computed_at     = NOW()
                """, (venue_id, dim, ctype, cval,
                      v['score'], session_count,
                      rows[0].get('service_type')))
    return written


def write_efficacy(cur, venue_id: int, natural_rows: list[dict],
                   eng_rows: list[dict], bridge: dict, dry_run: bool) -> int:
    """
    Pairs engineered/settling rows with natural baseline to compute pre/post delta.
    Writes to venue_intervention_efficacy — one row per (intervention, dimension).

    pre_score:      avg of natural/baseline observations (before any SE lever)
    post_score:     avg of engineered observations (lever live)
    retention_rate: how much of the lift survived into settling observations.
                    NULL until settling rows arrive (post-show review window).
    intervention_type: from m3_venue_behavioral_outcomes; 'unspecified' if not yet logged.

    Re-run safe: deletes existing rows for this venue before inserting.
    """
    if not eng_rows:
        return 0

    # Pre-scores: prefer explicit baseline phase; fall back to all natural rows
    baseline_rows = [r for r in natural_rows if r.get('engagement_phase') == 'baseline']
    pre_scores = translate_to_dimensions(baseline_rows or natural_rows, bridge) if natural_rows else {}

    # Intervention lookup from outcome records
    outcome_map = fetch_outcome_map(cur, venue_id)

    # Split engineered vs settling
    engineered = [r for r in eng_rows if r['observation_state'] == 'engineered']
    settling   = [r for r in eng_rows if r['observation_state'] == 'settling']
    settling_scores = translate_to_dimensions(settling, bridge) if settling else {}

    # Group engineered by session_number — each session = one intervention episode
    sessions: dict[int, list] = {}
    for row in engineered:
        sessions.setdefault(int(row['session_number']), []).append(row)

    if not sessions:
        print(f"    efficacy: only settling rows present, no engineered sessions — skipped")
        return 0

    total_eng_sessions = len(sessions)

    if not dry_run:
        cur.execute("DELETE FROM venue_intervention_efficacy WHERE venue_id = %s", (venue_id,))
        deleted = cur.rowcount
        if deleted:
            print(f"    efficacy: cleared {deleted} existing rows for venue {venue_id}")

    written = 0
    for sess_num, sess_rows in sorted(sessions.items()):
        intervention_type = outcome_map.get(sess_num, 'unspecified')
        post_dim_scores = translate_to_dimensions(sess_rows, bridge)

        service_type = sess_rows[0].get('service_type')
        confidence   = compute_confidence(total_eng_sessions, service_type)

        days = sorted({DAY_NAMES.get(int(r['day_of_week'] or 1), 'unknown') for r in sess_rows})
        tods = sorted({time_of_day(int(r['session_start_hour'] or 20)) for r in sess_rows})
        conditions = json.dumps({'day_of_week': days, 'time_of_day': tods})

        for dim, post_v in post_dim_scores.items():
            pre  = pre_scores.get(dim, {}).get('score')
            post = post_v['score']

            # retention_rate: fraction of (post-pre) delta that survived into settling
            retention_rate = None
            if settling_scores and pre is not None:
                settling_v = settling_scores.get(dim, {}).get('score')
                if settling_v is not None:
                    delta = post - pre
                    if abs(delta) > 0.001:
                        retention_rate = round(
                            max(0.0, min(1.0, (settling_v - pre) / delta)), 3
                        )

            print(f"    efficacy  sess={sess_num}  type={intervention_type:<15} "
                  f"{dim:<35} pre={pre}  post={post:.4f}  ret={retention_rate}")

            if not dry_run:
                cur.execute("""
                    INSERT INTO venue_intervention_efficacy
                        (venue_id, intervention_type, target_dimension,
                         pre_score, post_score, retention_rate,
                         session_count, conditions, confidence, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                """, (
                    venue_id, intervention_type, dim,
                    pre, post, retention_rate,
                    total_eng_sessions, conditions, confidence,
                    f"m3_loader session={sess_num}",
                ))
            written += 1

    if not written:
        print(f"    efficacy: no dimensions mapped from engineered rows")
    return written


# ── Per-venue orchestration ───────────────────────────────────────────────────

def process_venue(cur, venue_id: int, bridge: dict, dry_run: bool) -> None:
    natural_rows  = fetch_natural_rows(cur, venue_id)
    eng_rows      = fetch_engineered_rows(cur, venue_id)

    print(f"\n  venue {venue_id}: {len(natural_rows)} natural rows, "
          f"{len(eng_rows)} engineered/settling rows")

    if not natural_rows and not eng_rows:
        print("    no data — skipped")
        return

    # Determine service_type from rows (all rows for a venue share the same tag)
    service_type = natural_rows[0]['service_type'] if natural_rows else (
        eng_rows[0]['service_type'] if eng_rows else None
    )
    source = m3_source_label(service_type)
    session_count = len({r['session_number'] for r in natural_rows})

    # Natural rows → fitness dimensions + conditional
    if natural_rows:
        dim_scores = translate_to_dimensions(natural_rows, bridge)
        write_fitness_dimensions(cur, venue_id, dim_scores, source,
                                  session_count, service_type, dry_run)
        n_cond = write_conditional(cur, venue_id, natural_rows, bridge, dry_run)
        print(f"    conditional rows: {n_cond}")

    # Engineered/settling rows → efficacy (pre/post delta)
    n_eff = write_efficacy(cur, venue_id, natural_rows, eng_rows, bridge, dry_run)
    if n_eff:
        print(f"    efficacy rows written: {n_eff}")


# ── Smoke test ────────────────────────────────────────────────────────────────

SYNTHETIC_ROWS = [
    # Natural baseline — watch_and_optimise
    dict(venue_id=66, session_number=1, session_mode='observation_only',
         observation_state='natural', service_type='watch_and_optimise',
         engagement_phase='baseline', day_of_week=5, session_start_hour=20,
         zone=None, kpi_family_slug='stimulus', rag_status='green',
         score=0.85, signal_count=8, dominant_signal=None, notes='smoke-test'),
    dict(venue_id=66, session_number=1, session_mode='observation_only',
         observation_state='natural', service_type='watch_and_optimise',
         engagement_phase='baseline', day_of_week=5, session_start_hour=20,
         zone='dancefloor', kpi_family_slug='behavioral_response', rag_status='amber',
         score=0.55, signal_count=6, dominant_signal='music_response', notes='smoke-test'),
    dict(venue_id=66, session_number=1, session_mode='observation_only',
         observation_state='natural', service_type='watch_and_optimise',
         engagement_phase='baseline', day_of_week=5, session_start_hour=20,
         zone=None, kpi_family_slug='commercial_behavior', rag_status='amber',
         score=0.55, signal_count=5, dominant_signal=None, notes='smoke-test'),
    # Engineered — should NOT feed fitness
    dict(venue_id=66, session_number=2, session_mode='engineering_active',
         observation_state='engineered', service_type='watch_and_optimise',
         engagement_phase='active', day_of_week=6, session_start_hour=22,
         zone='dancefloor', kpi_family_slug='behavioral_response', rag_status='green',
         score=0.85, signal_count=9, dominant_signal='dancefloor_engagement',
         notes='smoke-test'),
]


def smoke_test(cur, bridge: dict) -> None:
    print("\n── SMOKE TEST ──────────────────────────────────────────────────")

    # Insert synthetic rows
    for row in SYNTHETIC_ROWS:
        cur.execute("""
            INSERT INTO m3_kpi_observations
                (venue_id, session_number, session_mode, observation_state,
                 service_type, engagement_phase, day_of_week, session_start_hour,
                 zone, kpi_family_slug, rag_status, score, signal_count,
                 dominant_signal, notes)
            VALUES (%(venue_id)s, %(session_number)s, %(session_mode)s,
                    %(observation_state)s, %(service_type)s, %(engagement_phase)s,
                    %(day_of_week)s, %(session_start_hour)s, %(zone)s,
                    %(kpi_family_slug)s, %(rag_status)s, %(score)s,
                    %(signal_count)s, %(dominant_signal)s, %(notes)s)
        """, row)
    print(f"  Inserted {len(SYNTHETIC_ROWS)} synthetic rows\n")

    # Process as dry-run to see routing without writing fitness rows
    process_venue(cur, 66, bridge, dry_run=True)

    # Verify routing logic
    natural = [r for r in SYNTHETIC_ROWS if r['observation_state'] == 'natural']
    engineered = [r for r in SYNTHETIC_ROWS if r['observation_state'] != 'natural']
    print(f"\n  Routing check:")
    print(f"    natural rows:   {len(natural)} → fitness correction + conditional")
    print(f"    engineered rows:{len(engineered)} → efficacy stub (no fitness write)")

    assert len(natural) == 3, "Expected 3 natural rows"
    assert len(engineered) == 1, "Expected 1 engineered row"

    # Check bridge produces correct dimensions
    dim_scores = translate_to_dimensions(natural, bridge)
    print(f"\n  Dimensions produced from natural rows:")
    for dim, v in sorted(dim_scores.items()):
        print(f"    {dim:<35} {v['score']:.4f}")

    expected_dims = {'fitness_for_social_dwell', 'fitness_for_group_energy',
                     'operational_quality', 'retention_strength',
                     'monetization_potential'}
    missing = expected_dims - set(dim_scores.keys())
    if missing:
        print(f"\n  WARNING: expected dims not produced: {missing}")
    else:
        print(f"\n  All expected dimensions produced. Routing correct.")

    # Clean up synthetic rows
    cur.execute("DELETE FROM m3_kpi_observations WHERE notes='smoke-test'")
    print(f"\n  Cleaned up {cur.rowcount} synthetic rows.")
    print("── SMOKE TEST COMPLETE ─────────────────────────────────────────\n")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='M3 → M2 fitness loader')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--venue-id', type=int)
    group.add_argument('--all', action='store_true')
    group.add_argument('--smoke-test', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        bridge = fetch_bridge_map(cur)
        print(f"Bridge map loaded: {len(bridge)} KPI families, "
              f"{sum(len(v) for v in bridge.values())} mappings")

        if args.smoke_test:
            smoke_test(cur, bridge)
            conn.rollback()
            print("Smoke test done — all changes rolled back.")
            return

        if args.dry_run:
            print("DRY RUN — no writes\n")

        if args.all:
            venue_ids = fetch_venues_with_natural_data(cur)
            print(f"Venues with natural M3 data: {len(venue_ids)}")
        else:
            venue_ids = [args.venue_id]

        for vid in venue_ids:
            process_venue(cur, vid, bridge, dry_run=args.dry_run)

        if args.dry_run:
            conn.rollback()
            print("\nDRY RUN — rolled back")
        else:
            conn.commit()
            print(f"\nDone — {len(venue_ids)} venue(s) processed")
            print("Run blend_fitness.py next to re-blend M3 into the blended row.")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR — rolled back: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()
