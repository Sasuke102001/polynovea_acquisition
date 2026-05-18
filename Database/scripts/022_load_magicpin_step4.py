"""
022_load_magicpin_step4.py
Loads MagicPin BIF step_4 for all 4 regions into:

  step_4_behavioral_clusters.json → raw_venue_data
      (platform='magicpin_upper', data_type='api_response', collector='magicpin-clusters-1.0')

  step_4_patterns_recognized.json → behavioral_patterns (source='magicpin_upper')
                                  → pattern_venues (by place_id)

Join: place_id → venues.id  (MagicPin step_4 includes place_id at venue level)
Run after: 002_load_venues.py, 015_provenance_schema.py
"""

import json
import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH        = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'magicpin')
REGIONS          = ['mumbai', 'navi-mumbai', 'sobo', 'thane']
CLUSTER_COLLECTOR = 'magicpin-clusters-1.0'

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
    WHERE venue_id = %s AND platform = 'magicpin_upper'
      AND data_type = 'api_response' AND collector_version = %s
"""

INSERT_RAW_SQL = """
    INSERT INTO raw_venue_data
        (venue_id, platform, data_type, raw_payload, collector_version, schema_version)
    VALUES (%s, 'magicpin_upper', 'api_response', %s, %s, 1)
"""

INSERT_PATTERN_SQL = """
    INSERT INTO behavioral_patterns
        (area, source, pattern_name, co_occurring_primitives,
         total_venues_in_city, prevalence_percentage)
    VALUES (%s, 'magicpin_upper', %s, %s, %s, %s)
    RETURNING id
"""

INSERT_PATTERN_VENUE_SQL = """
    INSERT INTO pattern_venues (venue_id, pattern_id)
    VALUES (%s, %s)
    ON CONFLICT (venue_id, pattern_id) DO NOTHING
"""


def build_lookup(cursor) -> dict:
    cursor.execute("SELECT place_id, id FROM venues WHERE place_id IS NOT NULL")
    return {row[0]: row[1] for row in cursor.fetchall()}


def load_clusters(cursor, region: str, lookup: dict) -> dict:
    path = os.path.join(BASE_PATH, region, 'step_4_behavioral_clusters.json')

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    venue_clusters = data.get('venue_clusters', [])
    loaded  = 0
    skipped = 0

    for entry in venue_clusters:
        venue_id = lookup.get(entry.get('place_id'))
        if not venue_id:
            skipped += 1
            continue

        cursor.execute(DELETE_RAW_SQL, (venue_id, CLUSTER_COLLECTOR))
        cursor.execute(INSERT_RAW_SQL, (
            venue_id,
            json.dumps({
                'evidence_count': entry.get('evidence_count', 0),
                'clusters':       entry.get('clusters', []),
            }),
            CLUSTER_COLLECTOR,
        ))
        loaded += 1

    return {'loaded': loaded, 'skipped': skipped, 'total': len(venue_clusters)}


def load_patterns(cursor, region: str, lookup: dict) -> dict:
    path = os.path.join(BASE_PATH, region, 'step_4_patterns_recognized.json')

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_venues    = data.get('total_venues', 0)
    patterns        = data.get('patterns_detected', {})
    patterns_loaded = 0
    venues_linked   = 0
    venues_missed   = 0

    for pattern_name, info in patterns.items():
        primitives  = pattern_name.split(' + ')
        venue_list  = info.get('venues', [])
        venue_count = info.get('venue_count', len(venue_list))
        prevalence  = round(venue_count / total_venues * 100, 2) if total_venues else 0.0

        cursor.execute(INSERT_PATTERN_SQL, (
            region, pattern_name,
            json.dumps(primitives),
            total_venues, prevalence,
        ))
        pattern_id = cursor.fetchone()[0]
        patterns_loaded += 1

        # MagicPin venues list contains objects with place_id
        for v in venue_list:
            place_id = v.get('place_id') if isinstance(v, dict) else None
            venue_id = lookup.get(place_id) if place_id else None
            if venue_id:
                cursor.execute(INSERT_PATTERN_VENUE_SQL, (venue_id, pattern_id))
                if cursor.rowcount > 0:
                    venues_linked += 1
            else:
                venues_missed += 1

    return {
        'patterns': patterns_loaded,
        'linked':   venues_linked,
        'missed':   venues_missed,
    }


def main():
    print("\n022_load_magicpin_step4.py — MagicPin clusters → raw_venue_data | patterns → behavioral_patterns\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    summary = []

    try:
        print("  Building place_id → venue_id lookup...")
        lookup = build_lookup(cursor)
        print(f"  Lookup: {len(lookup):,} venues\n")

        for region in REGIONS:
            print(f"  Region: {region}")
            cl = load_clusters(cursor, region, lookup)
            pt = load_patterns(cursor, region, lookup)
            summary.append({**cl, **pt, 'region': region})
            print(f"    clusters loaded   : {cl['loaded']}/{cl['total']}")
            print(f"    patterns loaded   : {pt['patterns']}")
            print(f"    venues linked     : {pt['linked']}")
            if cl['skipped'] or pt['missed']:
                print(f"    skipped/missed    : {cl['skipped']} / {pt['missed']}")
            print()

        conn.commit()
        print(f"{'='*55}")
        print(f"  COMPLETE")
        print(f"  Cluster payloads : {sum(r['loaded']   for r in summary):,}")
        print(f"  Patterns         : {sum(r['patterns'] for r in summary):,}")
        print(f"  Venue links      : {sum(r['linked']   for r in summary):,}")
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
