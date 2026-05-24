"""
035_load_google_reviews_step5b_similarity.py
Loads venue_vectors and venue_similarity from step_5b_similarity.json
(Google Reviews BIF) into:
  - venue_vectors    (source='google_reviews')
  - venue_similarity (source='google_reviews')

Name → place_id resolution uses step_3_signals_extracted.json (same pipeline run,
guaranteed name match). place_id → venue_id from DB.

Regions: thane, navi-mumbai
Run after: 034_load_google_reviews_step6_fitness.py
Run before: 027_blend_fitness.py
"""

import json
import os
import re
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'raw', 'google_reviews')
REGIONS   = ['thane', 'navi-mumbai']
SOURCE    = 'google_reviews'

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', '07586277012Luna'),
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


def normalize(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'[–—]', '-', name)
    return name


def build_name_to_place_id(region: str) -> dict:
    """Build name → place_id from step_3 (which has both fields)."""
    path = os.path.join(BASE_PATH, region, 'step_3_signals_extracted.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    result = {}
    for v in data.get('venues', []):
        key = normalize(v.get('name', ''))
        pid = v.get('place_id')
        if key and pid and key not in result:
            result[key] = pid
    return result


def build_place_id_lookup(cursor) -> dict:
    cursor.execute("SELECT place_id, id FROM venues WHERE place_id IS NOT NULL")
    return {row[0]: row[1] for row in cursor.fetchall()}


def load_region(cursor, region: str, place_id_to_db_id: dict) -> dict:
    step5b_path = os.path.join(BASE_PATH, region, 'step_5b_similarity.json')
    if not os.path.exists(step5b_path):
        print(f"    [SKIP] Not found: {step5b_path}")
        return {'region': region, 'total': 0, 'vectors': 0, 'sim_pairs': 0, 'skipped': 0}

    name_to_pid = build_name_to_place_id(region)

    with open(step5b_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    entries     = data.get('venue_similarity', [])
    vector_rows = {}
    sim_rows    = {}
    skipped     = 0

    for entry in entries:
        pid      = name_to_pid.get(normalize(entry.get('venue_name', '')))
        venue_id = place_id_to_db_id.get(pid) if pid else None
        if not venue_id:
            skipped += 1
            continue

        vector_rows[venue_id] = (
            venue_id,
            SOURCE,
            entry.get('fitness_vector', []),   # passed as PG array, not JSON
            entry.get('vector_source', 'behavioral'),
        )

        for similar in entry.get('similar_venues_pool', []):
            sim_pid = name_to_pid.get(normalize(similar.get('venue_name', '')))
            sim_id  = place_id_to_db_id.get(sim_pid) if sim_pid else None
            if not sim_id or sim_id == venue_id:
                continue
            key = (venue_id, sim_id)
            sim_rows[key] = (
                venue_id,
                SOURCE,
                sim_id,
                float(similar.get('similarity_score', 0.0)),
                json.dumps(similar.get('shared_primitives', [])),
                int(similar.get('shared_primitive_count', 0)),
            )

    if vector_rows:
        for i in range(0, len(vector_rows), 500):
            batch = list(vector_rows.values())[i:i+500]
            psycopg2.extras.execute_values(cursor, VECTOR_SQL, batch)

    if sim_rows:
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
    print(f"\n035_load_google_reviews_step5b_similarity.py — source='{SOURCE}'\n")

    conn    = psycopg2.connect(**DB_CONFIG)
    cursor  = conn.cursor()
    summary = []

    try:
        print("  Building place_id → venue_id lookup...")
        place_id_to_db_id = build_place_id_lookup(cursor)
        print(f"  Lookup: {len(place_id_to_db_id):,} venues\n")

        for region in REGIONS:
            print(f"  Region: {region}")
            r = load_region(cursor, region, place_id_to_db_id)
            summary.append(r)
            print(f"    vectors    : {r['vectors']}/{r['total']}")
            print(f"    sim pairs  : {r['sim_pairs']:,}")
            if r['skipped']:
                print(f"    skipped    : {r['skipped']} (name not in step_3 or place_id not in DB)")
            print()

        conn.commit()
        print(f"{'='*55}")
        print(f"  COMPLETE")
        print(f"  Vectors    : {sum(r['vectors']   for r in summary):,}")
        print(f"  Sim pairs  : {sum(r['sim_pairs'] for r in summary):,}")
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
