"""
039_load_google_reviews_step4b_pattern_scores.py
Loads pattern confidence scores from step_5_patterns_scored.json into:
  - pattern_scores  (joins via behavioral_patterns.pattern_name + area)

Requires behavioral_patterns rows to exist first (loaded by step4_cluster_and_patterns.py).

Regions: thane, navi-mumbai
Run after: 037_load_google_reviews_step4_clusters_and_patterns.py
"""

import argparse
import json
import os
import sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'raw', 'google_reviews')
REGIONS   = ['thane', 'navi-mumbai', 'sobo']
_p = argparse.ArgumentParser(); _p.add_argument('regions', nargs='*', default=REGIONS, metavar='REGION')
REGIONS   = _p.parse_args().regions or REGIONS
SOURCE    = 'google_reviews'

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', 'REDACTED_DB_PASSWORD'),
    'sslmode':  'require',
}

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


def parse_prevalence(val) -> float:
    """Convert '0.3%' → 0.003"""
    try:
        return float(str(val).strip('%')) / 100
    except Exception:
        return 0.0


def parse_score(val) -> float:
    """Convert '40.0' → 0.40, but leave 0.40 as-is (handles both formats)."""
    try:
        v = float(val)
        return v / 100 if v > 1 else v
    except Exception:
        return 0.0


def load_region(cursor, region: str) -> dict:
    path = os.path.join(BASE_PATH, region, 'step_5_patterns_scored.json')
    if not os.path.exists(path):
        print(f"    [SKIP] Not found: {path}")
        return {'region': region, 'total': 0, 'loaded': 0, 'missed': 0}

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    patterns = data.get('patterns_scored', {})
    loaded   = 0
    missed   = 0

    for pattern_name, info in patterns.items():
        cursor.execute(SCORE_SQL, (
            SOURCE,
            info.get('confidence_score', 0),
            parse_score(info.get('frequency_score', 0)),    # evidence_density
            parse_score(info.get('consistency_score', 0)),  # temporal_consistency
            parse_score(info.get('recency_score', 0)),      # evidence_diversity
            0.0,                                             # commercial_reliability (not in file)
            info.get('venue_count', 0),
            parse_prevalence(info.get('prevalence', '0%')),
            info.get('friction_severity', ''),
            pattern_name,
            region,
            SOURCE,
        ))

        if cursor.rowcount > 0:
            loaded += 1
        else:
            missed += 1

    return {'region': region, 'total': len(patterns), 'loaded': loaded, 'missed': missed}


def main():
    print(f"\n039_load_google_reviews_step4b_pattern_scores.py — source='{SOURCE}'\n")

    conn    = psycopg2.connect(**DB_CONFIG)
    cursor  = conn.cursor()
    summary = []

    try:
        for region in REGIONS:
            print(f"  Region: {region}")
            r = load_region(cursor, region)
            summary.append(r)
            print(f"    loaded : {r['loaded']}/{r['total']}")
            if r['missed']:
                print(f"    missed : {r['missed']} (pattern_name not in behavioral_patterns — run step4 first)")
            print()

        conn.commit()
        print(f"{'='*55}")
        print(f"  COMPLETE")
        print(f"  Total loaded : {sum(r['loaded'] for r in summary):,}")
        print(f"  Total missed : {sum(r['missed'] for r in summary):,}")
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
