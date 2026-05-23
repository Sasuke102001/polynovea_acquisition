"""
fix_venue_areas.py
One-time bulk correction of venues.area and venues.city from the
step_1_venues_refined.json files.

Uses geo_google.all_components.sublocality_level_1 for area and
all_components.locality for city — the two fields Google resolves
most reliably from reverse geocoding.

Join key: LOWER(TRIM(name)) + city_label
(venues table uses name_normalized generated column; place_id was not
populated from these files so place_id join yields near-zero matches)

Usage (run on EC2 after copying the 4 refined JSON files):
    python fix_venue_areas.py --data-dir /path/to/google_places

Default data-dir (relative to this script):
    ../../data/raw/google_places
"""

import argparse
import json
import os
import re
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

# City label as stored in the DB (matches CITY_LABEL in step_6 loader)
CITY_LABEL: dict[str, str] = {
    'navi-mumbai':  'Navi Mumbai',
    'mumbai-main':  'Mumbai',
    'mumbai-sobo':  'Mumbai',
    'thane':        'Thane',
}


def name_normalized(name: str) -> str:
    """Matches the DB generated column: LOWER(TRIM(name))"""
    return name.strip().lower()


def extract_area_city(venue: dict) -> tuple[str | None, str | None]:
    """
    Pull area from sublocality_level_1, city from locality component.
    Falls back gracefully if fields are absent.
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

    total_queued = 0
    skipped_files = 0

    # Build update list: (area, city, name_norm, db_city_label)
    # Join: WHERE name_normalized = %s AND city = %s
    update_rows: list[tuple] = []

    for city_slug, db_city in CITY_LABEL.items():
        path = os.path.join(data_dir, city_slug, 'step_1_venues_refined.json')
        if not os.path.exists(path):
            print(f"  SKIP {city_slug} — file not found: {path}")
            skipped_files += 1
            continue

        with open(path, encoding='utf-8') as f:
            venues = json.load(f)

        city_queued = 0
        for v in venues:
            name = v.get('name', '').strip()
            if not name:
                continue

            area, city = extract_area_city(v)
            if not area:
                continue

            update_rows.append((
                area,
                city or db_city,       # new city value
                name_normalized(name), # match key 1
                db_city,               # match key 2 (current DB value)
            ))
            city_queued += 1

        total_queued += city_queued
        print(f"  {city_slug} ({db_city}): {len(venues)} venues, {city_queued} rows queued")

    if skipped_files == len(CITY_LABEL):
        print("\nERROR: No refined JSON files found. Copy them to --data-dir first.")
        sys.exit(1)

    if not update_rows:
        print("\nNothing to update.")
        return

    print(f"\nRunning bulk UPDATE for {total_queued} rows (join: name_normalized + city)...")

    psycopg2.extras.execute_values(
        cur,
        """
        UPDATE venues AS v SET
            area       = u.area,
            city       = u.city,
            updated_at = CURRENT_TIMESTAMP
        FROM (VALUES %s) AS u(area, city, name_norm, db_city)
        WHERE v.name_normalized = u.name_norm
          AND v.city             = u.db_city
        """,
        update_rows,
        template="(%s, %s, %s, %s)",
    )

    affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    print(f"Done. {affected} venue rows updated.")
    print(f"({total_queued - affected} names had no match in DB — duplicates or missing venues)")


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
