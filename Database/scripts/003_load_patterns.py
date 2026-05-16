"""
003_load_patterns.py
Loads step_4_patterns_recognized.json for all 4 cities into:
  - behavioral_patterns
  - pattern_venues (joins on venues.name_normalized)
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
BATCH_SIZE = 200

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

INSERT_PATTERN_SQL = """
    INSERT INTO behavioral_patterns
        (area, pattern_name, co_occurring_primitives, total_venues_in_city, prevalence_percentage)
    VALUES %s
    RETURNING id;
"""

INSERT_PATTERN_VENUE_SQL = """
    INSERT INTO pattern_venues (venue_id, pattern_id)
    SELECT v.id, %s
    FROM venues v
    WHERE v.name_normalized = LOWER(TRIM(%s))
      AND v.city = %s
    ON CONFLICT (venue_id, pattern_id) DO NOTHING;
"""


def load_city(cursor, city: str) -> dict:
    path = os.path.join(BASE_PATH, city, 'step_4_patterns_recognized.json')

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_venues   = data.get('total_venues', 0)
    patterns       = data.get('patterns_detected', {})
    patterns_loaded = 0
    venues_linked  = 0
    venues_missed  = 0

    print(f"  [{city}] {len(patterns)} patterns | {total_venues} total venues")

    for pattern_name, info in patterns.items():
        primitives   = pattern_name.split(' + ')
        venue_count  = info.get('venue_count', 0)
        prevalence   = round(venue_count / total_venues * 100, 2) if total_venues else 0

        # Insert pattern
        cursor.execute(
            """
            INSERT INTO behavioral_patterns
                (area, pattern_name, co_occurring_primitives, total_venues_in_city, prevalence_percentage)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (city, pattern_name, json.dumps(primitives), total_venues, prevalence)
        )
        pattern_id = cursor.fetchone()[0]
        patterns_loaded += 1

        # Link venues to this pattern
        city_label = CITY_LABEL[city]
        for venue_name in info.get('venues', []):
            cursor.execute(INSERT_PATTERN_VENUE_SQL, (pattern_id, venue_name, city_label))
            if cursor.rowcount > 0:
                venues_linked += 1
            else:
                venues_missed += 1

    return {
        'city':            city,
        'patterns_loaded': patterns_loaded,
        'venues_linked':   venues_linked,
        'venues_missed':   venues_missed,
    }


def main():
    print("\n003_load_patterns.py -- Loading behavioral patterns\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    summary = []
    try:
        for city in CITIES:
            print(f"\n  City: {city}")
            result = load_city(cursor, city)
            summary.append(result)
            print(f"  Patterns loaded : {result['patterns_loaded']}")
            print(f"  Venues linked   : {result['venues_linked']}")
            if result['venues_missed']:
                print(f"  [WARN] Venues not matched: {result['venues_missed']}")

        conn.commit()
        print("\n" + "="*55)
        print("  COMPLETE")
        print(f"  Total patterns  : {sum(r['patterns_loaded'] for r in summary)}")
        print(f"  Total links     : {sum(r['venues_linked']   for r in summary)}")
        print(f"  Total missed    : {sum(r['venues_missed']   for r in summary)}")
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

