"""
034_load_google_reviews_step6_fitness.py
Loads fitness dimensions from step_6_output.json (Google Reviews BIF) into:
  - venue_fitness_dimensions  (source='google_reviews')
  - behavioral_summary        (source='google_reviews')
  - intervention_triggers     (source='google_reviews')

These rows sit ALONGSIDE Google Places (source='google') and MagicPin rows.
The blend runner (027_blend_fitness.py) combines all sources into source='blended'.

Join: place_id (embedded in step_6_output) → venues.id
Run after: 018_add_source_columns.py
Run before: 027_blend_fitness.py
"""

import json
import os
import sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH        = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'raw', 'google_reviews')
REGIONS          = ['thane', 'navi-mumbai']
SOURCE           = 'google_reviews'
PIPELINE_VERSION = 'google-reviews-bif-1.0'

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', 'REDACTED_DB_PASSWORD'),
    'sslmode':  'require',
}

FITNESS_SQL = """
    INSERT INTO venue_fitness_dimensions
        (venue_id, source,
         fitness_for_office_lunch, fitness_for_repeat_habit,
         fitness_for_social_dwell, fitness_for_group_energy,
         fitness_for_destination_visit,
         operational_quality, retention_strength, monetization_potential,
         fitness_details, pipeline_version, schema_version)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
    ON CONFLICT (venue_id, source) DO UPDATE SET
        fitness_for_office_lunch      = EXCLUDED.fitness_for_office_lunch,
        fitness_for_repeat_habit      = EXCLUDED.fitness_for_repeat_habit,
        fitness_for_social_dwell      = EXCLUDED.fitness_for_social_dwell,
        fitness_for_group_energy      = EXCLUDED.fitness_for_group_energy,
        fitness_for_destination_visit = EXCLUDED.fitness_for_destination_visit,
        operational_quality           = EXCLUDED.operational_quality,
        retention_strength            = EXCLUDED.retention_strength,
        monetization_potential        = EXCLUDED.monetization_potential,
        fitness_details               = EXCLUDED.fitness_details,
        pipeline_version              = EXCLUDED.pipeline_version,
        computed_at                   = NOW();
"""

SUMMARY_SQL = """
    INSERT INTO behavioral_summary
        (venue_id, source, operational_quality, retention_strength, monetization_potential)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (venue_id, source) DO UPDATE SET
        operational_quality    = EXCLUDED.operational_quality,
        retention_strength     = EXCLUDED.retention_strength,
        monetization_potential = EXCLUDED.monetization_potential;
"""

INTERVENTION_SQL = """
    INSERT INTO intervention_triggers
        (venue_id, source, intervention_type, description, fit_score,
         priority_tier, recommended, matched_signals, missing_signals,
         matched_signal_count)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (venue_id, source, intervention_type) DO UPDATE SET
        description          = EXCLUDED.description,
        fit_score            = EXCLUDED.fit_score,
        priority_tier        = EXCLUDED.priority_tier,
        recommended          = EXCLUDED.recommended,
        matched_signals      = EXCLUDED.matched_signals,
        missing_signals      = EXCLUDED.missing_signals,
        matched_signal_count = EXCLUDED.matched_signal_count;
"""


def fd_score(fd, key):
    return float(fd.get(key, {}).get('score', 0.0))


def fd_details(fd):
    dims = (
        'fitness_for_office_lunch', 'fitness_for_repeat_habit',
        'fitness_for_social_dwell', 'fitness_for_group_energy',
        'fitness_for_destination_visit',
    )
    return json.dumps({
        d: {
            'match_ratio':      fd.get(d, {}).get('match_ratio', 0.0),
            'confidence_basis': fd.get(d, {}).get('confidence_basis', 0.0),
            'matched_signals':  fd.get(d, {}).get('matched_signals', []),
            'strength_tier':    fd.get(d, {}).get('strength_tier', ''),
        }
        for d in dims
    })


def build_place_id_lookup(cursor):
    cursor.execute("SELECT place_id, id FROM venues WHERE place_id IS NOT NULL")
    return {row[0]: row[1] for row in cursor.fetchall()}


def load_region(cursor, region, lookup):
    path = os.path.join(BASE_PATH, region, 'step_6_output.json')
    if not os.path.exists(path):
        print(f"    [SKIP] Not found: {path}")
        return {'region': region, 'total': 0, 'loaded': 0, 'skipped': 0, 'interventions': 0}

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    venues        = data.get('venues', [])
    loaded        = 0
    skipped       = 0
    interventions = 0

    for v in venues:
        venue_id = lookup.get(v.get('place_id'))
        if not venue_id:
            skipped += 1
            continue

        fd = v.get('fitness_dimensions', {})
        bs = v.get('behavioral_summary', {})

        cursor.execute(FITNESS_SQL, (
            venue_id, SOURCE,
            fd_score(fd, 'fitness_for_office_lunch'),
            fd_score(fd, 'fitness_for_repeat_habit'),
            fd_score(fd, 'fitness_for_social_dwell'),
            fd_score(fd, 'fitness_for_group_energy'),
            fd_score(fd, 'fitness_for_destination_visit'),
            float(bs.get('operational_quality',    0.0)),
            float(bs.get('retention_strength',     0.0)),
            float(bs.get('monetization_potential', 0.0)),
            fd_details(fd),
            PIPELINE_VERSION,
        ))

        cursor.execute(SUMMARY_SQL, (
            venue_id, SOURCE,
            float(bs.get('operational_quality',    0.0)),
            float(bs.get('retention_strength',     0.0)),
            float(bs.get('monetization_potential', 0.0)),
        ))

        for lev in v.get('operational_leverage', []):
            cursor.execute(INTERVENTION_SQL, (
                venue_id, SOURCE,
                lev.get('intervention', ''),
                lev.get('operational_lever', ''),
                float(lev.get('fit_score', 0.0)),
                lev.get('priority_tier', 'EXPLORE'),
                bool(lev.get('recommended', False)),
                json.dumps(lev.get('matched_signals', [])),
                json.dumps(lev.get('missing_signals', [])),
                str(lev.get('matched_signal_count', '')),
            ))
            interventions += 1

        loaded += 1

    return {
        'region': region, 'total': len(venues),
        'loaded': loaded, 'skipped': skipped,
        'interventions': interventions,
    }


def main():
    print(f"\n034_load_google_reviews_step6_fitness.py — source='{SOURCE}'\n")

    conn    = psycopg2.connect(**DB_CONFIG)
    cursor  = conn.cursor()
    summary = []

    try:
        print("  Building place_id → venue_id lookup...")
        lookup = build_place_id_lookup(cursor)
        print(f"  Lookup: {len(lookup):,} venues\n")

        for region in REGIONS:
            print(f"  Region: {region}")
            r = load_region(cursor, region, lookup)
            summary.append(r)
            print(f"    fitness upserted : {r['loaded']}/{r['total']}")
            print(f"    interventions    : {r['interventions']}")
            if r['skipped']:
                print(f"    skipped          : {r['skipped']} (place_id not in DB)")
            print()

        conn.commit()
        print(f"{'='*55}")
        print(f"  COMPLETE")
        print(f"  Venues     : {sum(r['loaded']        for r in summary):,}")
        print(f"  Interventions: {sum(r['interventions'] for r in summary):,}")
        print(f"{'='*55}")
        print("\nNext: python blend/blend_fitness.py")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
