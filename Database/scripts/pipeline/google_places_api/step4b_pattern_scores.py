"""
006_load_pattern_scores.py
Loads step_5_patterns_scored.json for all 4 cities into:
  - pattern_scores       (confidence metrics per pattern)
Joins on behavioral_patterns.pattern_name + area (loaded by 003)
Run after 003_load_patterns.py
"""

import json
import os
import sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH  = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'raw', 'google_places')
CITIES     = ['navi-mumbai', 'mumbai-sobo', 'mumbai-main', 'thane']

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.xxxxxxxxxxxx.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

SOURCE = 'google'

SCORE_SQL = """
    INSERT INTO pattern_scores
        (pattern_id, source, confidence_score, evidence_density, temporal_consistency,
         evidence_diversity, commercial_reliability, venue_count, prevalence,
         friction_severity)
    SELECT bp.id, %s, %s, %s, %s, %s, %s, %s, %s, %s
    FROM behavioral_patterns bp
    WHERE bp.pattern_name = %s AND bp.area = %s AND bp.source = %s
    ON CONFLICT (pattern_id) DO UPDATE SET
        source                 = EXCLUDED.source,
        confidence_score       = EXCLUDED.confidence_score,
        evidence_density       = EXCLUDED.evidence_density,
        temporal_consistency   = EXCLUDED.temporal_consistency,
        evidence_diversity     = EXCLUDED.evidence_diversity,
        commercial_reliability = EXCLUDED.commercial_reliability,
        venue_count            = EXCLUDED.venue_count,
        prevalence             = EXCLUDED.prevalence,
        friction_severity      = EXCLUDED.friction_severity;
"""


def parse_prevalence(val: str) -> float:
    """Convert '1.9%' -> 0.019"""
    try:
        return float(val.strip('%')) / 100
    except Exception:
        return 0.0


def parse_score(val) -> float:
    try:
        return float(val) / 100
    except Exception:
        return 0.0


def load_city(cursor, city: str) -> dict:
    path = os.path.join(BASE_PATH, city, 'step_5_patterns_scored.json')

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_venues = data.get('total_venues', 0)
    patterns     = data.get('patterns_scored', {})
    loaded       = 0
    missed       = 0

    print(f"  [{city}] {len(patterns)} patterns to score")

    for pattern_name, info in patterns.items():
        confidence_score     = info.get('confidence_score', 0)
        venue_count          = info.get('venue_count', 0)
        prevalence           = parse_prevalence(info.get('prevalence', '0%'))
        frequency_score      = parse_score(info.get('frequency_score', 0))
        consistency_score    = parse_score(info.get('consistency_score', 0))
        recency_score        = parse_score(info.get('recency_score', 0))

        friction_severity = info.get('friction_severity', '')

        cursor.execute(SCORE_SQL, (
            SOURCE,
            confidence_score,
            frequency_score,    # evidence_density
            consistency_score,  # temporal_consistency
            recency_score,      # evidence_diversity
            0.0,                # commercial_reliability (not in file, default 0)
            venue_count,
            prevalence,
            friction_severity,
            pattern_name,
            city,
            SOURCE,
        ))

        if cursor.rowcount > 0:
            loaded += 1
        else:
            missed += 1

    return {'city': city, 'total': len(patterns), 'loaded': loaded, 'missed': missed}


def main():
    print("\n006_load_pattern_scores.py -- Loading pattern confidence scores\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    summary = []
    try:
        for city in CITIES:
            print(f"\n  City: {city}")
            result = load_city(cursor, city)
            summary.append(result)
            print(f"  Loaded : {result['loaded']}/{result['total']}")
            if result['missed']:
                print(f"  [WARN] Not matched: {result['missed']} patterns")

        conn.commit()
        print("\n" + "="*55)
        print("  COMPLETE")
        print(f"  Total loaded : {sum(r['loaded'] for r in summary)}")
        print(f"  Total missed : {sum(r['missed'] for r in summary)}")
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

