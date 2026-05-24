"""
036_load_google_reviews_step3_primitives.py
Loads behavioral primitive scores from step_3_signals_extracted.json into:
  - primitives_scores  (source='google_reviews')

Two extraction layers per venue:
  1. behavioral_primitives (venue-level aggregate) — stimuli, compensations,
     emotional_context, frictions
  2. Per-review behavioral_intelligence — stimuli, frictions, compensations,
     emotional_responses, behavioral_responses, commercial_mechanisms, contexts
     Negated signals skipped. Confidence weighted by evidence_calibration.effective_review_weight.

Per (venue, signal) keeps the highest weighted confidence across all layers/reviews.

Join: place_id → venues.id  (place_id is embedded in step_3)

Regions: thane, navi-mumbai
Run after: reference/load_venues.py
"""

import json
import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH          = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'raw', 'google_reviews')
REGIONS            = ['thane', 'navi-mumbai']
SOURCE             = 'google_reviews'

# Venue-level aggregate categories (behavioral_primitives)
PRIMITIVE_CATEGORIES = ('stimuli', 'compensations', 'emotional_context', 'frictions')

# Per-review behavioral_intelligence categories
BI_CATEGORIES = ('stimuli', 'frictions', 'compensations', 'emotional_responses',
                 'behavioral_responses', 'commercial_mechanisms', 'contexts')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', '07586277012Luna'),
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


def build_place_id_lookup(cursor) -> dict:
    cursor.execute("SELECT place_id, id FROM venues WHERE place_id IS NOT NULL")
    return {row[0]: row[1] for row in cursor.fetchall()}


def extract_signals(venue: dict) -> dict:
    """
    Returns {primitive_id: max_confidence} across all layers.
    Layer 1: venue-level behavioral_primitives aggregate.
    Layer 2: per-review behavioral_intelligence, weighted by effective_review_weight.
    Negated signals are skipped.
    """
    signals = {}

    def record(signal_id, confidence):
        if signal_id:
            signals[signal_id] = max(signals.get(signal_id, 0.0), float(confidence or 0.0))

    # Layer 1: venue-level aggregate
    bp = venue.get('behavioral_primitives', {})
    for cat in PRIMITIVE_CATEGORIES:
        for s in bp.get(cat, []):
            record(s.get('signal'), s.get('confidence', 0.0))

    # Layer 2: per-review behavioral_intelligence
    for review in venue.get('reviews', []):
        ec = review.get('evidence_calibration', {})
        weight = float(ec.get('effective_review_weight', 1.0) or 1.0)

        bi = review.get('behavioral_intelligence', {})
        for cat in BI_CATEGORIES:
            for s in bi.get(cat, []):
                if s.get('negated', False):
                    continue
                raw_conf = float(s.get('confidence', 0.0) or 0.0)
                record(s.get('signal'), min(raw_conf * weight, 1.0))

    return signals


def load_region(cursor, region: str, lookup: dict) -> dict:
    path = os.path.join(BASE_PATH, region, 'step_3_signals_extracted.json')
    if not os.path.exists(path):
        print(f"    [SKIP] Not found: {path}")
        return {'region': region, 'venues': 0, 'rows': 0, 'skipped': 0}

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

    return {'region': region, 'venues': len(venues), 'rows': len(rows), 'skipped': skipped}


def main():
    print(f"\n036_load_google_reviews_step3_primitives.py — source='{SOURCE}'\n")

    conn    = psycopg2.connect(**DB_CONFIG)
    cursor  = conn.cursor()
    summary = []

    try:
        print("  Building place_id → venue_id lookup...")
        lookup = build_place_id_lookup(cursor)
        print(f"  Lookup: {len(lookup):,} venues\n")

        for region in REGIONS:
            print(f"  Region: {region}")
            r = load_region(cursor, region, lookup)
            summary.append(r)
            print(f"    venues    : {r['venues']}")
            print(f"    prim rows : {r['rows']:,}")
            if r['skipped']:
                print(f"    skipped   : {r['skipped']}")
            print()

        conn.commit()
        print(f"{'='*55}")
        print(f"  COMPLETE")
        print(f"  Total primitive rows : {sum(r['rows'] for r in summary):,}")
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
