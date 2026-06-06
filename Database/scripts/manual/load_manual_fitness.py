"""
load_manual_fitness.py
General-purpose loader: inserts manually analyzed fitness scores + raw reviews
for any existing venue into:
  - venue_fitness_dimensions  (source='manual_reviews')
  - behavioral_summary        (source='manual_reviews')
  - raw_venue_data            (platform='manual_reviews', data_type='review_batch')

Usage:
    python load_manual_fitness.py --venue-id 128 --config configs/gbc_vashi.json

Config JSON schema:
{
  "fitness": {
    "fitness_for_office_lunch":      float,
    "fitness_for_repeat_habit":      float,
    "fitness_for_social_dwell":      float,
    "fitness_for_group_energy":      float,
    "fitness_for_destination_visit": float,
    "operational_quality":           float,
    "retention_strength":            float,
    "monetization_potential":        float
  },
  "fitness_details": { ...any analyst notes dict... },
  "reviews": [
    {"rating": int, "text": str, "review_age_days": int (optional)}
  ]
}

After running this, execute in order:
    python bif/extract_primitives.py    --venue-id <id>
    python bif/link_patterns.py         --venue-id <id>
    python bif/compute_interventions.py --venue-id <id>
    python compute_manual_pipeline.py   --venue-id <id>
    python compute_similarity_manual.py --venue-id <id>
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
    'password': os.getenv('PG_PASSWORD', 'REDACTED_DB_PASSWORD'),
    'sslmode':  'require',
}

SOURCE           = 'manual_reviews'
PIPELINE_VERSION = 'manual-review-1.0'

FITNESS_DIMS = [
    'fitness_for_office_lunch',
    'fitness_for_repeat_habit',
    'fitness_for_social_dwell',
    'fitness_for_group_energy',
    'fitness_for_destination_visit',
    'operational_quality',
    'retention_strength',
    'monetization_potential',
]

FITNESS_SQL = """
    INSERT INTO venue_fitness_dimensions
        (venue_id, source,
         fitness_for_office_lunch, fitness_for_repeat_habit,
         fitness_for_social_dwell, fitness_for_group_energy,
         fitness_for_destination_visit,
         operational_quality, retention_strength, monetization_potential,
         fitness_details, pipeline_version, schema_version)
    VALUES (%(venue_id)s, %(source)s,
            %(fitness_for_office_lunch)s, %(fitness_for_repeat_habit)s,
            %(fitness_for_social_dwell)s, %(fitness_for_group_energy)s,
            %(fitness_for_destination_visit)s,
            %(operational_quality)s, %(retention_strength)s, %(monetization_potential)s,
            %(fitness_details)s, %(pipeline_version)s, 1)
    ON CONFLICT (venue_id, source) DO UPDATE SET
        fitness_for_office_lunch      = EXCLUDED.fitness_for_office_lunch,
        fitness_for_repeat_habit      = EXCLUDED.fitness_for_repeat_habit,
        fitness_for_social_dwell      = EXCLUDED.fitness_for_social_dwell,
        fitness_for_group_energy      = EXCLUDED.fitness_for_group_energy,
        fitness_for_destination_visit = EXCLUDED.fitness_for_destination_visit,
        operational_quality           = EXCLUDED.operational_quality,
        retention_strength            = EXCLUDED.retention_strength,
        monetization_potential        = EXCLUDED.monetization_potential,
        fitness_details               = EXCLUDED.fitness_details,
        pipeline_version              = EXCLUDED.pipeline_version,
        computed_at                   = NOW();
"""

SUMMARY_SQL = """
    INSERT INTO behavioral_summary
        (venue_id, source, operational_quality, retention_strength, monetization_potential)
    VALUES (%(venue_id)s, %(source)s, %(operational_quality)s, %(retention_strength)s, %(monetization_potential)s)
    ON CONFLICT (venue_id, source) DO UPDATE SET
        operational_quality    = EXCLUDED.operational_quality,
        retention_strength     = EXCLUDED.retention_strength,
        monetization_potential = EXCLUDED.monetization_potential;
"""

RAW_DATA_SQL = """
    INSERT INTO raw_venue_data
        (venue_id, platform, data_type, raw_payload, collector_version, schema_version)
    VALUES (%s, 'manual_reviews', 'review_batch', %s, 'manual-reviews-1.0', 1)
    ON CONFLICT DO NOTHING;
"""


def validate_config(cfg: dict) -> None:
    missing = [d for d in FITNESS_DIMS if d not in cfg.get('fitness', {})]
    if missing:
        print(f"ERROR: Config missing fitness dimensions: {missing}")
        sys.exit(1)
    if not cfg.get('reviews'):
        print("ERROR: Config has no reviews list.")
        sys.exit(1)


def run(venue_id: int, config_path: str) -> None:
    with open(config_path, encoding='utf-8') as f:
        cfg = json.load(f)

    validate_config(cfg)
    fitness   = cfg['fitness']
    details   = cfg.get('fitness_details', {})
    reviews   = cfg['reviews']

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT id, name, area, city FROM venues WHERE id = %s", (venue_id,))
    venue = cur.fetchone()
    if not venue:
        print(f"ERROR: venue_id={venue_id} not found in venues table.")
        conn.close()
        sys.exit(1)

    print(f"\nVenue: {venue['name']} — {venue['area']}, {venue['city']} (id={venue_id})")
    print(f"Reviews in config: {len(reviews)}")

    params = {
        'venue_id':  venue_id,
        'source':    SOURCE,
        **fitness,
        'fitness_details':  json.dumps(details),
        'pipeline_version': PIPELINE_VERSION,
    }

    print("Upserting venue_fitness_dimensions (source='manual_reviews')...")
    cur.execute(FITNESS_SQL, params)

    print("Upserting behavioral_summary...")
    cur.execute(SUMMARY_SQL, params)

    print("Inserting raw_venue_data (review_batch)...")
    raw_payload = json.dumps({
        "name":            venue['name'],
        "area":            venue['area'],
        "city":            venue['city'],
        "collection_date": details.get('collection_date', 'unknown'),
        "review_count":    len(reviews),
        "reviews":         reviews,
    })
    cur.execute(RAW_DATA_SQL, (venue_id, raw_payload))

    conn.commit()

    cur.execute(
        "SELECT source, operational_quality, retention_strength, "
        "fitness_for_social_dwell, fitness_for_group_energy "
        "FROM venue_fitness_dimensions WHERE venue_id = %s ORDER BY source",
        (venue_id,),
    )
    print(f"\nAll fitness rows for venue_id={venue_id}:")
    for r in cur.fetchall():
        print(f"  {dict(r)}")

    cur.close()
    conn.close()

    print(f"\nDone. Now run:")
    print(f"  python bif/extract_primitives.py    --venue-id {venue_id}")
    print(f"  python bif/link_patterns.py         --venue-id {venue_id}")
    print(f"  python bif/compute_interventions.py --venue-id {venue_id}")
    print(f"  python compute_manual_pipeline.py   --venue-id {venue_id}")
    print(f"  python compute_similarity_manual.py --venue-id {venue_id}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Load manual fitness scores + reviews for an existing venue"
    )
    parser.add_argument('--venue-id', type=int, required=True, help="Existing venue_id in DB")
    parser.add_argument('--config',   type=str, required=True, help="Path to venue config JSON")
    args = parser.parse_args()
    run(args.venue_id, args.config)
