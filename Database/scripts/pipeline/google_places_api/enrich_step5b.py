"""
enrich_step5b.py
Adds place_id to each entry in step_5b_similarity.json by matching
venue_name → name_normalized lookup in the DB.
Writes step_5b_similarity_enriched.json for use by step5b_similarity_enrichment.py.

Run before step5b_similarity_enrichment.py.
"""

import json
import os
import sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'raw', 'google_places')
CITIES    = ['navi-mumbai', 'mumbai-sobo', 'mumbai-main', 'thane']

CITY_LABEL = {
    'mumbai-main': 'Mumbai',
    'mumbai-sobo': 'Mumbai',
    'navi-mumbai':  'Navi Mumbai',
    'thane':        'Thane',
}

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.xxxxxxxxxxxx.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}


def build_name_lookup(cursor, city_label: str) -> dict:
    """name_normalized → (place_id, venue_id)"""
    cursor.execute(
        "SELECT name_normalized, place_id, id FROM venues WHERE city = %s",
        (city_label,)
    )
    return {row[0]: (row[1], row[2]) for row in cursor.fetchall()}


def enrich_city(cursor, city: str) -> dict:
    src_path = os.path.join(BASE_PATH, city, 'step_5b_similarity.json')
    dst_path = os.path.join(BASE_PATH, city, 'step_5b_similarity_enriched.json')

    with open(src_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    entries    = data.get('venue_similarity', [])
    city_label = CITY_LABEL[city]
    lookup     = build_name_lookup(cursor, city_label)

    matched  = 0
    missed   = 0
    enriched = []

    for entry in entries:
        name_norm = entry.get('venue_name', '').lower().strip()
        row       = lookup.get(name_norm)
        if not row:
            missed += 1
            # Still include entry without place_id so structure is preserved
            entry['place_id'] = None
        else:
            entry['place_id'] = row[0]
            matched += 1

        # Also enrich similar_venues_pool entries with place_ids
        enriched_pool = []
        for sim in entry.get('similar_venues_pool', []):
            sim_norm = sim.get('venue_name', '').lower().strip()
            sim_row  = lookup.get(sim_norm)
            sim['place_id'] = sim_row[0] if sim_row else None
            enriched_pool.append(sim)
        entry['similar_venues_pool'] = enriched_pool
        enriched.append(entry)

    data['venue_similarity'] = enriched
    with open(dst_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)

    return {'city': city, 'total': len(entries), 'matched': matched, 'missed': missed}


def main():
    print("\nenrich_step5b.py -- Adding place_ids to step_5b_similarity.json\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        for city in CITIES:
            print(f"  City: {city}")
            result = enrich_city(cursor, city)
            print(f"    matched : {result['matched']}/{result['total']}")
            if result['missed']:
                print(f"    [WARN] no place_id: {result['missed']} venues")

        print("\n  COMPLETE — enriched files written as step_5b_similarity_enriched.json\n")
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
