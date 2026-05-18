"""
017_load_magicpin_step6.py
Loads step_6_output.json from the MagicPin BIF pipeline into raw_venue_data.

Stores per-venue:
  - dish_signals  (data_type = 'review_batch')
  - mechanisms    (data_type = 'api_response')

Does NOT write to venue_fitness_dimensions, behavioral_summary, or
intervention_triggers — those are computed by the blend runner (024)
after all source primitives are loaded.

Idempotent: existing rows for collector_version 'magicpin-bif-1.0'
are replaced on each run.

Run after: 002_load_venues.py, 015_provenance_schema.py
"""

import json
import os
import sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH        = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'magicpin')
REGIONS          = ['mumbai', 'navi-mumbai', 'sobo', 'thane']
COLLECTOR_VERSION = 'magicpin-bif-1.0'

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

DELETE_RAW_SQL = """
    DELETE FROM raw_venue_data
    WHERE venue_id = %s
      AND platform = 'magicpin'
      AND collector_version = %s;
"""

INSERT_RAW_SQL = """
    INSERT INTO raw_venue_data
        (venue_id, platform, data_type, raw_payload, collector_version, schema_version)
    VALUES (%s, 'magicpin', %s, %s, %s, 1);
"""


def build_lookup(cursor) -> dict:
    cursor.execute("SELECT place_id, id FROM venues WHERE place_id IS NOT NULL")
    return {row[0]: row[1] for row in cursor.fetchall()}


def load_region(cursor, region: str, lookup: dict) -> dict:
    path = os.path.join(BASE_PATH, region, 'step_6_output.json')

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    venues    = data.get('venues', [])
    dish_rows = 0
    mech_rows = 0
    skipped   = 0

    for venue in venues:
        venue_id = lookup.get(venue.get('place_id'))
        if not venue_id:
            skipped += 1
            continue

        # Replace existing raw payloads for this venue+version
        cursor.execute(DELETE_RAW_SQL, (venue_id, COLLECTOR_VERSION))

        dish_signals = venue.get('dish_signals', [])
        if dish_signals:
            cursor.execute(INSERT_RAW_SQL, (
                venue_id, 'review_batch',
                json.dumps({'dish_signals': dish_signals}),
                COLLECTOR_VERSION,
            ))
            dish_rows += 1

        mechanisms = venue.get('mechanisms', [])
        if mechanisms:
            cursor.execute(INSERT_RAW_SQL, (
                venue_id, 'api_response',
                json.dumps({'mechanisms': mechanisms}),
                COLLECTOR_VERSION,
            ))
            mech_rows += 1

    return {
        'region':    region,
        'total':     len(venues),
        'dish_rows': dish_rows,
        'mech_rows': mech_rows,
        'skipped':   skipped,
    }


def main():
    print("\n017_load_magicpin_step6.py — dish signals + mechanisms → raw_venue_data\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    summary = []
    try:
        print("  Building place_id → venue_id lookup...")
        lookup = build_lookup(cursor)
        print(f"  Lookup: {len(lookup):,} venues\n")

        for region in REGIONS:
            print(f"  Region: {region}")
            result = load_region(cursor, region, lookup)
            summary.append(result)
            print(f"    dish signal rows : {result['dish_rows']}")
            print(f"    mechanism rows   : {result['mech_rows']}")
            if result['skipped']:
                print(f"    [WARN] skipped   : {result['skipped']}")
            print()

        conn.commit()
        print("=" * 55)
        print("  COMPLETE")
        print(f"  Dish signal rows : {sum(r['dish_rows'] for r in summary):,}")
        print(f"  Mechanism rows   : {sum(r['mech_rows'] for r in summary):,}")
        print(f"  Skipped          : {sum(r['skipped']   for r in summary):,}")
        print("=" * 55 + "\n")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
