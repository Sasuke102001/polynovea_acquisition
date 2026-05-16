"""
010_load_primitives.py
Loads step_3_signals_extracted.json for all 4 cities into:
  - primitives_scores  (per-venue, per-primitive confidence score)

Source: behavioral_primitives.stimuli / .compensations / .emotional_context
        Each entry has: signal (primitive_id), confidence, inference_type, mention_count
Join:   place_id → venues.id  (same lookup dict pattern as 005)

Enables: Feature 6 (Conflict Detection), Feature 7 (Satisfaction Drivers),
         Feature 10 (Competitive Benchmarking)

Run after 002_load_venues.py
"""

import json
import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'google_places')
CITIES     = ['navi-mumbai', 'mumbai-sobo', 'mumbai-main', 'thane']
BATCH_SIZE = 500

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.xxxxxxxxxxxx.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

# Primitive categories in step_3
PRIMITIVE_CATEGORIES = ('stimuli', 'compensations', 'emotional_context')

INSERT_SQL = """
    INSERT INTO primitives_scores
        (venue_id, source, primitive_id, score, confidence)
    VALUES %s
    ON CONFLICT (venue_id, source, primitive_id) DO UPDATE SET
        score        = EXCLUDED.score,
        confidence   = EXCLUDED.confidence,
        last_updated = CURRENT_TIMESTAMP;
"""


def build_lookup(cursor) -> dict:
    """Load all place_id -> venue.id mappings in one query."""
    cursor.execute("SELECT place_id, id FROM venues")
    return {row[0]: row[1] for row in cursor.fetchall()}


def load_city(cursor, city: str, lookup: dict) -> dict:
    path = os.path.join(BASE_PATH, city, 'step_3_signals_extracted.json')

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    venues  = data.get('venues', [])
    rows    = []
    skipped = 0
    dupes   = {}  # (venue_id, primitive_id) -> row — deduplicate within file

    for i, venue in enumerate(venues):
        place_id = venue.get('place_id')
        venue_id = lookup.get(place_id)
        if not venue_id:
            skipped += 1
            continue

        bp = venue.get('behavioral_primitives', {})

        for category in PRIMITIVE_CATEGORIES:
            for signal in bp.get(category, []):
                primitive_id = signal.get('signal', '')
                confidence   = float(signal.get('confidence', 0.0))
                if not primitive_id:
                    continue
                key = (venue_id, primitive_id)
                # Keep highest confidence if primitive appears in multiple categories
                if key not in dupes or confidence > dupes[key][3]:
                    dupes[key] = (venue_id, 'google', primitive_id, confidence, confidence)

        if (i + 1) % BATCH_SIZE == 0:
            print(f"  [{city}] {i+1}/{len(venues)} venues scanned...")

    rows = list(dupes.values())

    # Batch insert in chunks of 500
    for i in range(0, len(rows), 500):
        psycopg2.extras.execute_values(cursor, INSERT_SQL, rows[i:i+500])

    return {
        'city':    city,
        'venues':  len(venues),
        'rows':    len(rows),
        'skipped': skipped,
    }


def main():
    print("\n010_load_primitives.py -- Loading per-venue primitive scores\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    summary = []
    try:
        print("  Building place_id -> venue_id lookup...")
        lookup = build_lookup(cursor)
        print(f"  Lookup built: {len(lookup)} venues\n")

        for city in CITIES:
            print(f"\n  City: {city}")
            result = load_city(cursor, city, lookup)
            summary.append(result)
            print(f"  Primitive rows : {result['rows']}")
            print(f"  Venues covered : {result['venues']}")
            if result['skipped']:
                print(f"  [WARN] Skipped (no place_id match): {result['skipped']}")

        conn.commit()
        print("\n" + "="*55)
        print("  COMPLETE")
        print(f"  Total primitive rows : {sum(r['rows']     for r in summary):,}")
        print(f"  Total venues covered : {sum(r['venues']   for r in summary):,}")
        print(f"  Total skipped        : {sum(r['skipped']  for r in summary):,}")
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
