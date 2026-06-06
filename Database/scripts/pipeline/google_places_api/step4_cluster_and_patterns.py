"""
step4_cluster_and_patterns.py  (merged from 003_load_patterns.py + 019_load_google_step4_clusters.py)
Loads Google Places step_4 data for all 4 cities into:
  - behavioral_patterns + pattern_venues  (from step_4_patterns_recognized.json)
  - raw_venue_data                         (from step_4_behavioral_clusters.json)

Join: name_normalized + city
Run after: reference/load_venues.py, schema/provenance_schema.py
"""

import json
import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH   = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'raw', 'google_places')
CITIES      = ['navi-mumbai', 'mumbai-sobo', 'mumbai-main', 'thane']
BATCH_SIZE  = 200
COLLECTOR   = 'google-clusters-1.0'

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

INSERT_PATTERN_VENUE_SQL = """
    INSERT INTO pattern_venues (venue_id, pattern_id)
    SELECT v.id, %s
    FROM venues v
    WHERE v.name_normalized = LOWER(TRIM(%s))
      AND v.city = %s
    ON CONFLICT (venue_id, pattern_id) DO NOTHING;
"""

DELETE_CLUSTERS_SQL = """
    DELETE FROM raw_venue_data
    WHERE venue_id = %s AND platform = 'google'
      AND data_type = 'api_response' AND collector_version = %s
"""

INSERT_CLUSTERS_SQL = """
    INSERT INTO raw_venue_data
        (venue_id, platform, data_type, raw_payload, collector_version, schema_version)
    VALUES (%s, 'google', 'api_response', %s, %s, 1)
"""


def load_patterns(cursor, city: str) -> dict:
    path = os.path.join(BASE_PATH, city, 'step_4_patterns_recognized.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_venues    = data.get('total_venues', 0)
    patterns        = data.get('patterns_detected', {})
    patterns_loaded = 0
    venues_linked   = 0
    venues_missed   = 0

    for pattern_name, info in patterns.items():
        primitives  = pattern_name.split(' + ')
        venue_count = info.get('venue_count', 0)
        prevalence  = round(venue_count / total_venues * 100, 2) if total_venues else 0

        cursor.execute(
            """
            INSERT INTO behavioral_patterns
                (area, source, pattern_name, co_occurring_primitives, total_venues_in_city, prevalence_percentage)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (area, source, pattern_name) DO NOTHING
            RETURNING id;
            """,
            (city, 'google', pattern_name, json.dumps(primitives), total_venues, prevalence)
        )
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                "SELECT id FROM behavioral_patterns WHERE area=%s AND source=%s AND pattern_name=%s",
                (city, 'google', pattern_name)
            )
            row = cursor.fetchone()
        pattern_id = row[0]
        patterns_loaded += 1

        city_label = CITY_LABEL[city]
        for venue_name in info.get('venues', []):
            cursor.execute(INSERT_PATTERN_VENUE_SQL, (pattern_id, venue_name, city_label))
            if cursor.rowcount > 0:
                venues_linked += 1
            else:
                venues_missed += 1

    return {'patterns_loaded': patterns_loaded, 'venues_linked': venues_linked, 'venues_missed': venues_missed}


def load_clusters(cursor, city: str) -> dict:
    path       = os.path.join(BASE_PATH, city, 'step_4_behavioral_clusters.json')
    city_label = CITY_LABEL[city]

    cursor.execute("SELECT id, name_normalized FROM venues WHERE city = %s", (city_label,))
    lookup = {row[1]: row[0] for row in cursor.fetchall()}

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

        cursor.execute(DELETE_CLUSTERS_SQL, (venue_id, COLLECTOR))
        cursor.execute(INSERT_CLUSTERS_SQL, (
            venue_id,
            json.dumps({
                'evidence_count': entry.get('evidence_count', 0),
                'data_quality':   entry.get('data_quality', 'UNKNOWN'),
                'clusters':       entry.get('clusters', []),
            }),
            COLLECTOR,
        ))
        loaded += 1

    return {'clusters_loaded': loaded, 'clusters_skipped': skipped, 'clusters_total': len(venue_clusters)}


def main():
    print("\nstep4_cluster_and_patterns.py — Google step_4 patterns + clusters\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    p_summary = []
    c_summary = []

    try:
        for city in CITIES:
            print(f"  City: {city}")
            p = load_patterns(cursor, city)
            c = load_clusters(cursor, city)
            p_summary.append(p)
            c_summary.append(c)
            print(f"    patterns loaded  : {p['patterns_loaded']}")
            print(f"    venues linked    : {p['venues_linked']}")
            if p['venues_missed']:
                print(f"    [WARN] missed    : {p['venues_missed']}")
            print(f"    clusters loaded  : {c['clusters_loaded']}/{c['clusters_total']}")
            if c['clusters_skipped']:
                print(f"    clusters skipped : {c['clusters_skipped']}")

        conn.commit()
        print(f"\n{'='*55}")
        print(f"  COMPLETE")
        print(f"  Total patterns   : {sum(p['patterns_loaded'] for p in p_summary)}")
        print(f"  Total links      : {sum(p['venues_linked']   for p in p_summary)}")
        print(f"  Total clusters   : {sum(c['clusters_loaded'] for c in c_summary):,}")
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
