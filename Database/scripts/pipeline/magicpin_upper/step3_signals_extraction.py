"""
021_load_magicpin_step3.py
Loads step_3_signals_extracted.json (MagicPin BIF) for all 4 regions into:
  - primitives_scores  (source='magicpin_upper')

Extracts signals from two layers per venue:
  1. behavioral_primitives (venue-level aggregate) — categories:
       stimuli, compensations, emotional_context, behavioral_responses
  2. Per-review behavioral_intelligence — MagicPin-exclusive categories:
       frictions, commercial_mechanisms, contexts

Aggregation: per (venue, signal) keep the highest confidence value across
all reviews and categories. This means more reviews = stronger signal, never
diluted by averaging.

Join: place_id → venues.id
Run after: 002_load_venues.py
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

# Categories in behavioral_primitives (venue-level aggregate — both Google and MagicPin)
PRIMITIVE_CATEGORIES = ('stimuli', 'compensations', 'emotional_context', 'behavioral_responses')

# Categories in per-review behavioral_intelligence (MagicPin-exclusive)
BI_CATEGORIES = ('stimuli', 'frictions', 'compensations', 'emotional_responses',
                 'behavioral_responses', 'commercial_mechanisms', 'contexts')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

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
    cursor.execute("SELECT place_id, id FROM venues WHERE place_id IS NOT NULL")
    return {row[0]: row[1] for row in cursor.fetchall()}


def extract_signals(venue: dict) -> dict:
    """
    Returns {primitive_id: max_confidence} across all signal layers.
    More reviews = more opportunities to surface a signal at higher confidence.
    """
    signals = {}

    def record(signal_id, confidence):
        if signal_id:
            signals[signal_id] = max(signals.get(signal_id, 0.0), float(confidence or 0.0))

    # Layer 1: venue-level behavioral_primitives aggregate
    bp = venue.get('behavioral_primitives', {})
    for cat in PRIMITIVE_CATEGORIES:
        for s in bp.get(cat, []):
            record(s.get('signal'), s.get('confidence', 0.0))

    # Layer 2: per-review behavioral_intelligence (MagicPin-exclusive depth)
    for review in venue.get('reviews', []):
        bi = review.get('behavioral_intelligence', {})
        # Evidence calibration weight — MagicPin assigns quality scores per review
        review_weight = 1.0
        ec = review.get('evidence_calibration', {})
        if ec:
            review_weight = float(ec.get('effective_review_weight', 1.0) or 1.0)

        for cat in BI_CATEGORIES:
            for s in bi.get(cat, []):
                # Skip negated signals — they contradict the behaviour
                if s.get('negated', False):
                    continue
                raw_conf = float(s.get('confidence', 0.0) or 0.0)
                weighted  = min(raw_conf * review_weight, 1.0)
                record(s.get('signal'), weighted)

    return signals


def load_region(cursor, region: str, lookup: dict) -> dict:
    path = os.path.join(BASE_PATH, region, 'step_3_signals_extracted.json')

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    venues  = data.get('venues', [])
    rows    = []
    skipped = 0

    for venue in venues:
        venue_id = lookup.get(venue.get('place_id'))
        if not venue_id:
            skipped += 1
            continue

        for primitive_id, confidence in extract_signals(venue).items():
            rows.append((venue_id, SOURCE, primitive_id, confidence, confidence))

    for i in range(0, len(rows), 500):
        psycopg2.extras.execute_values(cursor, INSERT_SQL, rows[i:i+500])

    return {
        'region':  region,
        'venues':  len(venues),
        'rows':    len(rows),
        'skipped': skipped,
    }


def main():
    print("\n021_load_magicpin_step3.py — MagicPin primitives → primitives_scores\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    summary = []

    try:
        print("  Building place_id → venue_id lookup...")
        lookup = build_lookup(cursor)
        print(f"  Lookup: {len(lookup):,} venues\n")

        for region in REGIONS:
            print(f"  Region: {region}")
            result = load_region(cursor, region, lookup)
            summary.append(result)
            print(f"    venues   : {result['venues']}")
            print(f"    signals  : {result['rows']:,}")
            if result['skipped']:
                print(f"    skipped  : {result['skipped']}")
            print()

        conn.commit()
        print(f"{'='*55}")
        print(f"  COMPLETE")
        print(f"  Total venues  : {sum(r['venues'] for r in summary):,}")
        print(f"  Total signals : {sum(r['rows']   for r in summary):,}")
        print(f"  Skipped       : {sum(r['skipped'] for r in summary):,}")
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
