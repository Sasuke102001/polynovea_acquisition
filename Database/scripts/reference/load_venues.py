"""
002_load_venues.py
Loads step_1_venues_refined.json for all 4 cities into the venues table.
Run after 001_init_schema.sql has been executed on the Azure PostgreSQL instance.
"""

import json
import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH   = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', 'google_places')
CITIES      = ['navi-mumbai', 'mumbai-sobo', 'mumbai-main', 'thane']
BATCH_SIZE  = 500

# -------------------------------------------------------------------
# DB connection — set via environment variables or edit directly
# -------------------------------------------------------------------
DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.xxxxxxxxxxxx.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

INSERT_SQL = """
    INSERT INTO venues
        (place_id, name, area, city, types, lat, lng, locality,
         discovered_at, geo_google, geo_operational)
    VALUES %s
    ON CONFLICT (place_id) DO UPDATE SET
        name            = EXCLUDED.name,
        area            = EXCLUDED.area,
        types           = EXCLUDED.types,
        lat             = EXCLUDED.lat,
        lng             = EXCLUDED.lng,
        locality        = EXCLUDED.locality,
        discovered_at   = EXCLUDED.discovered_at,
        geo_google      = EXCLUDED.geo_google,
        geo_operational = EXCLUDED.geo_operational,
        updated_at      = CURRENT_TIMESTAMP;
"""


def build_row(venue: dict, city: str) -> tuple:
    loc      = venue.get('location', {})
    geo_op   = venue.get('geo_operational', {})
    geo_goog = venue.get('geo_google', {})
    locality = geo_op.get('canonical_locality') or geo_op.get('raw_locality')

    discovered_raw = venue.get('discovered_at')
    discovered_at  = None
    if discovered_raw:
        try:
            discovered_at = datetime.fromisoformat(discovered_raw)
        except ValueError:
            pass

    return (
        venue['place_id'],
        venue['name'],
        venue.get('area'),
        city,
        json.dumps(venue.get('types', [])),
        loc.get('lat'),
        loc.get('lng'),
        locality,
        discovered_at,
        json.dumps(geo_goog) if geo_goog else None,
        json.dumps(geo_op)   if geo_op   else None,
    )


def load_city(cursor, city: str) -> dict:
    path = os.path.join(BASE_PATH, city, 'step_1_venues_refined.json')

    with open(path, 'r', encoding='utf-8') as f:
        venues = json.load(f)

    # Deduplicate by place_id — keep last occurrence
    seen = {}
    for v in venues:
        seen[v['place_id']] = v
    dupes = len(venues) - len(seen)
    if dupes:
        print(f"  [{city}] {dupes} duplicate place_ids removed before insert")

    rows   = [build_row(v, city) for v in seen.values()]
    total  = len(rows)
    loaded = 0

    for i in range(0, total, BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        psycopg2.extras.execute_values(cursor, INSERT_SQL, batch)
        loaded += len(batch)
        print(f"  [{city}] {loaded}/{total} inserted...")

    return {'city': city, 'total': total, 'loaded': loaded}


def main():
    print("\n002_load_venues.py -- Loading venues into PostgreSQL\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    summary = []
    try:
        for city in CITIES:
            print(f"\n  City: {city}")
            result = load_city(cursor, city)
            summary.append(result)

        conn.commit()
        print("\n" + "="*55)
        print("  COMPLETE")
        for r in summary:
            print(f"  {r['city']}: {r['loaded']} venues loaded")
        print(f"  Total: {sum(r['loaded'] for r in summary)} venues")
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
