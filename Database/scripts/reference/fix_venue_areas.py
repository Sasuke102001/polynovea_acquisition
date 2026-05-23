"""
fix_venue_areas.py
One-time bulk correction of venues.area and venues.city from the
step_1_venues_refined.json files.

Uses geo_google.all_components.sublocality_level_1 for area and
all_components.locality for city — the two fields Google resolves
most reliably from reverse geocoding.

Usage (run on EC2 after copying the 4 refined JSON files):
    python fix_venue_areas.py --data-dir /path/to/google_places

The --data-dir should contain:
    navi-mumbai/step_1_venues_refined.json
    mumbai-main/step_1_venues_refined.json
    mumbai-sobo/step_1_venues_refined.json
    thane/step_1_venues_refined.json

Default data-dir (relative to this script):
    ../../data/raw/google_places
"""

import argparse
import json
import os
import sys

import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', '07586277012Luna'),
    'sslmode':  'require',
}

CITIES = ['navi-mumbai', 'mumbai-main', 'mumbai-sobo', 'thane']


def extract_area_city(venue: dict) -> tuple[str | None, str | None]:
    """
    Pull area from sublocality_level_1, city from locality.
    Both sourced from geo_google.all_components — the most reliable
    Google reverse-geocoding fields.
    Falls back to geo_google.resolved_locality for area if sublocality
    is absent, then to the raw area field.
    """
    geo_goog   = venue.get('geo_google', {})
    components = geo_goog.get('all_components', {})

    area = (
        components.get('sublocality_level_1')
        or geo_goog.get('resolved_locality')
        or venue.get('area')
    )
    city = components.get('locality')

    return area, city


def run(data_dir: str) -> None:
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    total_venues  = 0
    update_rows   = []   # (area, city, place_id)
    skipped       = 0

    for city_slug in CITIES:
        path = os.path.join(data_dir, city_slug, 'step_1_venues_refined.json')
        if not os.path.exists(path):
            print(f"  SKIP {city_slug} — file not found: {path}")
            skipped += 1
            continue

        with open(path, encoding='utf-8') as f:
            venues = json.load(f)

        city_updates = 0
        for v in venues:
            place_id = v.get('place_id')
            if not place_id:
                continue

            area, city = extract_area_city(v)
            if area or city:
                update_rows.append((area, city, place_id))
                city_updates += 1

        total_venues += len(venues)
        print(f"  {city_slug}: {len(venues)} venues, {city_updates} rows queued")

    if skipped == len(CITIES):
        print("\nERROR: No refined JSON files found. Copy them to --data-dir first.")
        sys.exit(1)

    if not update_rows:
        print("\nNothing to update.")
        return

    print(f"\nRunning bulk UPDATE for {len(update_rows)} venues...")

    # Use execute_values for efficient batch update
    psycopg2.extras.execute_values(
        cur,
        """
        UPDATE venues AS v SET
            area       = u.area,
            city       = COALESCE(u.city, v.city),
            updated_at = CURRENT_TIMESTAMP
        FROM (VALUES %s) AS u(area, city, place_id)
        WHERE v.place_id = u.place_id
        """,
        update_rows,
        template="(%s, %s, %s)",
    )

    affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    print(f"Done. {affected} venue rows updated in DB.")
    print(f"({total_venues - affected} had no matching place_id in venues table — likely expected)")


if __name__ == '__main__':
    default_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', 'google_places')
    )
    parser = argparse.ArgumentParser(description="Bulk-fix venue area + city from refined JSON files")
    parser.add_argument(
        '--data-dir',
        default=default_dir,
        help=f"Path to google_places data dir (default: {default_dir})"
    )
    args = parser.parse_args()
    print(f"\nfix_venue_areas.py — reading from: {args.data_dir}\n")
    run(args.data_dir)
