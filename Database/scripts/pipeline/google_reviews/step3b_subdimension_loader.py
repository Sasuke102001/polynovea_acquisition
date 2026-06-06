"""
E2: step3b_subdimension_loader.py
Load venue_subdimension_scores from Google Raw Scrapper step_3 output.

Reads:  Data/<region>/step_3_signals_extracted.json  (Google Raw Scrapper BIF output)
Writes: venue_subdimension_scores  (source='google_reviews')

Only writes rows where at least one sub-dimension score was parsed.
Venues with no "Food: X/5 | Service: X/5 | Atmosphere: X/5" pattern are skipped.

Run AFTER step3_primitives.py (needs venue place_id lookup to exist).
"""

import argparse
import json
import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

# Google Raw Scrapper BIF output
BASE_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', '..', '..',
    'Module 2', 'Google Raw Scrapper', 'Behavioural_Intelligence_Framework', 'Data'
)

REGIONS   = ['thane', 'navi-mumbai', 'sobo']
_p = argparse.ArgumentParser()
_p.add_argument('regions', nargs='*', default=REGIONS, metavar='REGION')
REGIONS   = _p.parse_args().regions or REGIONS
SOURCE    = 'google_reviews'
PIPELINE_VERSION = 'grs-subdim-1.0'

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', 'REDACTED_DB_PASSWORD'),
    'sslmode':  'require',
}

UPSERT_SQL = """
    INSERT INTO venue_subdimension_scores
        (venue_id, source, food_score, service_score, atmosphere_score, sample_size, pipeline_version)
    VALUES %s
    ON CONFLICT (venue_id, source) DO UPDATE SET
        food_score       = EXCLUDED.food_score,
        service_score    = EXCLUDED.service_score,
        atmosphere_score = EXCLUDED.atmosphere_score,
        sample_size      = EXCLUDED.sample_size,
        pipeline_version = EXCLUDED.pipeline_version,
        computed_at      = NOW();
"""


def load_region(cursor, region: str, lookup: dict) -> dict:
    path = os.path.join(BASE_PATH, region, 'step_3_signals_extracted.json')
    if not os.path.exists(path):
        print(f"  [SKIP] {region}: file not found at {path}")
        return {'loaded': 0, 'skipped': 0, 'no_data': 0}

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    venues = data.get('venues', data) if isinstance(data, dict) else data
    rows   = []
    skipped = 0
    no_data = 0

    for venue in venues:
        place_id = venue.get('place_id')
        venue_id = lookup.get(place_id)
        if not venue_id:
            skipped += 1
            continue

        sd = venue.get('subdimension_scores', {})
        sample = sd.get('sample_size', 0)
        if sample == 0:
            no_data += 1
            continue

        rows.append((
            venue_id,
            SOURCE,
            sd.get('food'),
            sd.get('service'),
            sd.get('atmosphere'),
            sample,
            PIPELINE_VERSION,
        ))

    if rows:
        psycopg2.extras.execute_values(cursor, UPSERT_SQL, rows)

    return {'loaded': len(rows), 'skipped': skipped, 'no_data': no_data}


def main():
    print(f"\nstep3b_subdimension_loader.py — E2 sub-dimension scores → venue_subdimension_scores\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT place_id, id FROM venues WHERE place_id IS NOT NULL")
        lookup = {row[0]: row[1] for row in cursor.fetchall()}
        print(f"  Lookup: {len(lookup):,} venues\n")

        totals = {'loaded': 0, 'skipped': 0, 'no_data': 0}
        for region in REGIONS:
            print(f"  Region: {region}")
            r = load_region(cursor, region, lookup)
            for k in totals:
                totals[k] += r[k]
            print(f"    loaded   : {r['loaded']}")
            print(f"    no_data  : {r['no_data']}  (no Food/Service/Atmosphere pattern)")
            if r['skipped']:
                print(f"    skipped  : {r['skipped']}  (place_id not in venues)")
            print()

        conn.commit()
        print(f"{'='*55}")
        print(f"  COMPLETE — {totals['loaded']:,} rows upserted")
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
