"""
005_load_similarity.py
Loads step_5b_similarity_enriched.json for all 4 cities into:
  - venue_vectors     (5-d fitness vector per venue)
  - venue_similarity  (top 25 similar venues per venue with shared primitives)
Joins on place_id (reliable — enriched by enrich_step5b.py)
Run after 002_load_venues.py and enrich_step5b.py
"""

import json
import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'google_places')
CITIES     = ['navi-mumbai', 'mumbai-sobo', 'mumbai-main', 'thane']
BATCH_SIZE = 200

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.xxxxxxxxxxxx.ap-south-1.rds.amazonaws.com'),
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
        (venue_id, source, similar_venue_id, similarity_score, shared_primitives, shared_primitive_count)
    VALUES %s
    ON CONFLICT (venue_id, source, similar_venue_id) DO UPDATE SET
        similarity_score       = EXCLUDED.similarity_score,
        shared_primitives      = EXCLUDED.shared_primitives,
        shared_primitive_count = EXCLUDED.shared_primitive_count;
"""


def build_lookup(cursor) -> dict:
    """Load all place_id → venue.id mappings in one query."""
    cursor.execute("SELECT place_id, id FROM venues")
    return {row[0]: row[1] for row in cursor.fetchall()}


def load_city(cursor, city: str, lookup: dict) -> dict:
    path = os.path.join(BASE_PATH, city, 'step_5b_similarity_enriched.json')

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    entries        = data.get('venue_similarity', [])
    vector_rows    = []
    sim_rows       = []
    vectors_loaded = 0
    sim_loaded     = 0
    skipped        = 0

    for i, entry in enumerate(entries):
        place_id       = entry.get('place_id')
        fitness_vector = entry.get('fitness_vector', [])
        vector_source  = entry.get('vector_source', 'unknown')

        venue_id = lookup.get(place_id)
        if not venue_id:
            skipped += 1
            continue

        vector_rows.append((venue_id, 'google', fitness_vector, vector_source))

        for similar in entry.get('similar_venues_pool', []):
            sim_place_id = similar.get('place_id')
            sim_venue_id = lookup.get(sim_place_id)
            if not sim_venue_id:
                skipped += 1
                continue
            sim_rows.append((
                venue_id,
                'google',
                sim_venue_id,
                similar.get('similarity_score', 0.0),
                json.dumps(similar.get('shared_primitives', [])),
                similar.get('shared_primitive_count', 0),
            ))

        if (i + 1) % BATCH_SIZE == 0:
            print(f"  [{city}] {i+1}/{len(entries)} venues prepared...")

    # Deduplicate vectors by venue_id (keep last)
    vec_dedup = {}
    for row in vector_rows:
        vec_dedup[row[0]] = row
    vector_rows = list(vec_dedup.values())

    # Deduplicate sim pairs by (venue_id, sim_venue_id) (keep last)
    sim_dedup = {}
    for row in sim_rows:
        sim_dedup[(row[0], row[1])] = row
    sim_rows = list(sim_dedup.values())

    # Batch insert vectors
    for i in range(0, len(vector_rows), 500):
        psycopg2.extras.execute_values(cursor, VECTOR_SQL, vector_rows[i:i+500])
    vectors_loaded = len(vector_rows)

    # Batch insert similarity pairs
    for i in range(0, len(sim_rows), 500):
        psycopg2.extras.execute_values(cursor, SIMILARITY_SQL, sim_rows[i:i+500])
    sim_loaded = len(sim_rows)

    return {
        'city':           city,
        'total':          len(entries),
        'vectors_loaded': vectors_loaded,
        'sim_loaded':     sim_loaded,
        'skipped':        skipped,
    }


def main():
    print("\n005_load_similarity.py -- Loading venue vectors & similarity pairs\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    summary = []
    try:
        print("  Building place_id → venue_id lookup...")
        lookup = build_lookup(cursor)
        print(f"  Lookup built: {len(lookup)} venues\n")

        for city in CITIES:
            print(f"\n  City: {city}")
            result = load_city(cursor, city, lookup)
            summary.append(result)
            print(f"  Vectors loaded : {result['vectors_loaded']}/{result['total']}")
            print(f"  Sim pairs      : {result['sim_loaded']}")
            if result['skipped']:
                print(f"  [WARN] Skipped (no place_id): {result['skipped']}")

        conn.commit()
        print("\n" + "="*55)
        print("  COMPLETE")
        print(f"  Total vectors  : {sum(r['vectors_loaded'] for r in summary)}")
        print(f"  Total sim pairs: {sum(r['sim_loaded']     for r in summary)}")
        print(f"  Total skipped  : {sum(r['skipped']        for r in summary)}")
        print("="*55 + "\n")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()

