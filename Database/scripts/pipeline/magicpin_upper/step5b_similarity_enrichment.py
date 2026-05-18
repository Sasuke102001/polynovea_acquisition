"""
025_load_magicpin_step5b.py
Loads step_5b_similarity.json (MagicPin BIF) for all 4 regions into:
  - venue_vectors    (source='magicpin_upper')
  - venue_similarity (source='magicpin_upper')

Join: venue_name → name_normalized + city
      (MagicPin step_5b has no place_id — uses venue names like Google step_5b)

Google rows (source='google') are untouched.
Run after: 002_load_venues.py, 018_add_source_columns.py
"""

import json
import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'raw', 'magicpin')
REGIONS   = ['mumbai', 'navi-mumbai', 'sobo', 'thane']
SOURCE    = 'magicpin_upper'

REGION_LABEL = {
    'mumbai':      'Mumbai',
    'sobo':        'Mumbai',
    'navi-mumbai': 'Navi Mumbai',
    'thane':       'Thane',
}

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

VECTOR_SQL = """
    INSERT INTO venue_vectors (venue_id, source, fitness_vector, vector_source)
    VALUES %s
    ON CONFLICT (venue_id, source) DO UPDATE SET
        fitness_vector = EXCLUDED.fitness_vector,
        vector_source  = EXCLUDED.vector_source,
        last_computed  = CURRENT_TIMESTAMP;
"""

SIMILARITY_SQL = """
    INSERT INTO venue_similarity
        (venue_id, source, similar_venue_id, similarity_score,
         shared_primitives, shared_primitive_count)
    VALUES %s
    ON CONFLICT (venue_id, source, similar_venue_id) DO UPDATE SET
        similarity_score       = EXCLUDED.similarity_score,
        shared_primitives      = EXCLUDED.shared_primitives,
        shared_primitive_count = EXCLUDED.shared_primitive_count;
"""


def build_name_lookup(cursor, city_label: str) -> dict:
    cursor.execute(
        "SELECT name_normalized, id FROM venues WHERE city = %s",
        (city_label,)
    )
    return {row[0]: row[1] for row in cursor.fetchall()}


def load_region(cursor, region: str) -> dict:
    path       = os.path.join(BASE_PATH, region, 'step_5b_similarity.json')
    city_label = REGION_LABEL[region]
    lookup     = build_name_lookup(cursor, city_label)

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    entries     = data.get('venue_similarity', [])
    vector_rows = {}
    sim_rows    = {}
    skipped     = 0

    for entry in entries:
        name_norm = entry.get('venue_name', '').lower().strip()
        venue_id  = lookup.get(name_norm)
        if not venue_id:
            skipped += 1
            continue

        vector_rows[venue_id] = (
            venue_id,
            SOURCE,
            entry.get('fitness_vector', []),
            entry.get('vector_source', 'behavioral'),
        )

        for similar in entry.get('similar_venues_pool', []):
            sim_norm = similar.get('venue_name', '').lower().strip()
            sim_id   = lookup.get(sim_norm)
            if not sim_id or sim_id == venue_id:
                skipped += 1
                continue
            key = (venue_id, sim_id)
            sim_rows[key] = (
                venue_id,
                SOURCE,
                sim_id,
                similar.get('similarity_score', 0.0),
                json.dumps(similar.get('shared_primitives', [])),
                similar.get('shared_primitive_count', 0),
            )

    for i in range(0, len(vector_rows), 500):
        batch = list(vector_rows.values())[i:i+500]
        psycopg2.extras.execute_values(cursor, VECTOR_SQL, batch)

    for i in range(0, len(sim_rows), 500):
        batch = list(sim_rows.values())[i:i+500]
        psycopg2.extras.execute_values(cursor, SIMILARITY_SQL, batch)

    return {
        'region':    region,
        'total':     len(entries),
        'vectors':   len(vector_rows),
        'sim_pairs': len(sim_rows),
        'skipped':   skipped,
    }


def main():
    print("\n025_load_magicpin_step5b.py — MagicPin similarity → venue_vectors + venue_similarity\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    summary = []

    try:
        for region in REGIONS:
            print(f"  Region: {region}")
            result = load_region(cursor, region)
            summary.append(result)
            print(f"    vectors    : {result['vectors']}/{result['total']}")
            print(f"    sim pairs  : {result['sim_pairs']:,}")
            if result['skipped']:
                print(f"    skipped    : {result['skipped']}")
            print()

        conn.commit()
        print(f"{'='*55}")
        print(f"  COMPLETE")
        print(f"  Vectors    : {sum(r['vectors']   for r in summary):,}")
        print(f"  Sim pairs  : {sum(r['sim_pairs'] for r in summary):,}")
        print(f"  Skipped    : {sum(r['skipped']   for r in summary):,}")
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
