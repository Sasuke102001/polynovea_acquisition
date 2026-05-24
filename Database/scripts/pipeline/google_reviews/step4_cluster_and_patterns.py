"""
037_load_google_reviews_step4_clusters_and_patterns.py
Loads step_4 data into:
  - behavioral_patterns + pattern_venues  (from step_4_patterns_recognized.json)
  - raw_venue_data                         (from step_4_behavioral_clusters.json)

google_reviews step_4 embeds place_id in every venue entry — no name normalization needed.

Regions: thane, navi-mumbai
Run after: 036_load_google_reviews_step3_primitives.py
"""

import json
import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH  = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'raw', 'google_reviews')
REGIONS    = ['thane', 'navi-mumbai']
SOURCE     = 'google_reviews'
COLLECTOR  = 'google-reviews-clusters-1.0'

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', '07586277012Luna'),
    'sslmode':  'require',
}

INSERT_PATTERN_SQL = """
    INSERT INTO behavioral_patterns
        (area, source, pattern_name, co_occurring_primitives, total_venues_in_city, prevalence_percentage)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id;
"""

INSERT_PATTERN_VENUE_SQL = """
    INSERT INTO pattern_venues (venue_id, pattern_id)
    VALUES (%s, %s)
    ON CONFLICT (venue_id, pattern_id) DO NOTHING;
"""

DELETE_CLUSTERS_SQL = """
    DELETE FROM raw_venue_data
    WHERE venue_id = %s AND platform = %s AND collector_version = %s
"""

INSERT_CLUSTERS_SQL = """
    INSERT INTO raw_venue_data
        (venue_id, platform, data_type, raw_payload, collector_version, schema_version)
    VALUES (%s, %s, 'api_response', %s, %s, 1)
"""


def build_place_id_lookup(cursor) -> dict:
    cursor.execute("SELECT place_id, id FROM venues WHERE place_id IS NOT NULL")
    return {row[0]: row[1] for row in cursor.fetchall()}


def load_patterns(cursor, region: str, lookup: dict) -> dict:
    path = os.path.join(BASE_PATH, region, 'step_4_patterns_recognized.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_venues  = data.get('total_venues', 0)
    patterns      = data.get('patterns_detected', {})
    pats_loaded   = 0
    venues_linked = 0
    venues_missed = 0

    for pattern_name, info in patterns.items():
        primitives = pattern_name.split(' + ')
        venue_count = info.get('venue_count', 0)
        prevalence  = round(venue_count / total_venues * 100, 2) if total_venues else 0.0

        cursor.execute(INSERT_PATTERN_SQL, (
            region, SOURCE, pattern_name,
            json.dumps(primitives), total_venues, prevalence,
        ))
        pattern_id = cursor.fetchone()[0]
        pats_loaded += 1

        # step_4_patterns_recognized venues are {name, place_id} objects
        for venue_entry in info.get('venues', []):
            place_id = venue_entry.get('place_id') if isinstance(venue_entry, dict) else None
            venue_id = lookup.get(place_id) if place_id else None

            if venue_id:
                cursor.execute(INSERT_PATTERN_VENUE_SQL, (venue_id, pattern_id))
                if cursor.rowcount > 0:
                    venues_linked += 1
                else:
                    venues_missed += 1
            else:
                venues_missed += 1

    return {'patterns_loaded': pats_loaded, 'venues_linked': venues_linked, 'venues_missed': venues_missed}


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

        cursor.execute(DELETE_CLUSTERS_SQL, (venue_id, SOURCE, COLLECTOR))
        cursor.execute(INSERT_CLUSTERS_SQL, (
            venue_id,
            SOURCE,
            json.dumps({
                'evidence_count': entry.get('evidence_count', 0),
                'clusters':       entry.get('clusters', []),
            }),
            COLLECTOR,
        ))
        loaded += 1

    return {'clusters_loaded': loaded, 'clusters_skipped': skipped, 'clusters_total': len(venue_clusters)}


def main():
    print(f"\n037_load_google_reviews_step4_clusters_and_patterns.py — source='{SOURCE}'\n")

    conn    = psycopg2.connect(**DB_CONFIG)
    cursor  = conn.cursor()
    p_summary = []
    c_summary = []

    try:
        print("  Building place_id → venue_id lookup...")
        lookup = build_place_id_lookup(cursor)
        print(f"  Lookup: {len(lookup):,} venues\n")

        for region in REGIONS:
            print(f"  Region: {region}")
            p = load_patterns(cursor, region, lookup)
            c = load_clusters(cursor, region, lookup)
            p_summary.append(p)
            c_summary.append(c)
            print(f"    patterns loaded  : {p['patterns_loaded']}")
            print(f"    venues linked    : {p['venues_linked']}")
            if p['venues_missed']:
                print(f"    venues missed    : {p['venues_missed']}")
            print(f"    clusters loaded  : {c['clusters_loaded']}/{c['clusters_total']}")
            if c['clusters_skipped']:
                print(f"    clusters skipped : {c['clusters_skipped']}")
            print()

        conn.commit()
        print(f"{'='*55}")
        print(f"  COMPLETE")
        print(f"  Total patterns   : {sum(p['patterns_loaded'] for p in p_summary):,}")
        print(f"  Total links      : {sum(p['venues_linked']   for p in p_summary):,}")
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
