"""
019_load_google_step4_clusters.py
Loads step_4_behavioral_clusters.json (Google Places) for all 4 cities
into raw_venue_data as immutable cluster payloads per venue.

Platform : google
Data type: api_response
Version  : google-clusters-1.0

Idempotent: existing rows for this collector_version are replaced.
Join: name_normalized + city (Google step_4 has no place_id at venue level)
Run after: 002_load_venues.py, 015_provenance_schema.py
"""

import json
import os
import sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'google_places')
CITIES     = ['navi-mumbai', 'mumbai-sobo', 'mumbai-main', 'thane']
COLLECTOR  = 'google-clusters-1.0'

CITY_LABEL = {
    'mumbai-main': 'Mumbai',
    'mumbai-sobo': 'Mumbai',
    'navi-mumbai':  'Navi Mumbai',
    'thane':        'Thane',
}

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

LOOKUP_SQL = """
    SELECT id, name_normalized FROM venues WHERE city = %s
"""

DELETE_SQL = """
    DELETE FROM raw_venue_data
    WHERE venue_id = %s AND platform = 'google'
      AND data_type = 'api_response' AND collector_version = %s
"""

INSERT_SQL = """
    INSERT INTO raw_venue_data
        (venue_id, platform, data_type, raw_payload, collector_version, schema_version)
    VALUES (%s, 'google', 'api_response', %s, %s, 1)
"""


def load_city(cursor, city: str) -> dict:
    path = os.path.join(BASE_PATH, city, 'step_4_behavioral_clusters.json')
    city_label = CITY_LABEL[city]

    cursor.execute(LOOKUP_SQL, (city_label,))
    lookup = {row[1]: row[0] for row in cursor.fetchall()}  # name_normalized → venue_id

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    venue_clusters = data.get('venue_clusters', [])
    loaded  = 0
    skipped = 0

    for entry in venue_clusters:
        name_norm = entry.get('name', '').lower().strip()
        venue_id  = lookup.get(name_norm)
        if not venue_id:
            skipped += 1
            continue

        cursor.execute(DELETE_SQL, (venue_id, COLLECTOR))
        cursor.execute(INSERT_SQL, (
            venue_id,
            json.dumps({
                'evidence_count': entry.get('evidence_count', 0),
                'clusters':       entry.get('clusters', []),
            }),
            COLLECTOR,
        ))
        loaded += 1

    return {'city': city, 'total': len(venue_clusters), 'loaded': loaded, 'skipped': skipped}


def main():
    print("\n019_load_google_step4_clusters.py — Google behavioral clusters → raw_venue_data\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    summary = []

    try:
        for city in CITIES:
            print(f"  City: {city}")
            result = load_city(cursor, city)
            summary.append(result)
            print(f"    loaded  : {result['loaded']}/{result['total']}")
            if result['skipped']:
                print(f"    skipped : {result['skipped']}")

        conn.commit()
        print(f"\n{'='*55}")
        print(f"  COMPLETE — {sum(r['loaded'] for r in summary):,} cluster payloads stored")
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
