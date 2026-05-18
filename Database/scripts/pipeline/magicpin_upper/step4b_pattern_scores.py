"""
024_load_magicpin_step5_scores.py
Loads step_5_patterns_scored.json (MagicPin BIF) for all 4 regions into:
  - pattern_scores  (joined to behavioral_patterns by pattern_name + area + source='magicpin_upper')

Run after: 022_load_magicpin_step4.py  (patterns must exist)
"""

import json
import os
import sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'raw', 'magicpin')
REGIONS   = ['mumbai', 'navi-mumbai', 'sobo', 'thane']

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

SCORE_SQL = """
    INSERT INTO pattern_scores
        (pattern_id, confidence_score, evidence_density, temporal_consistency,
         evidence_diversity, commercial_reliability, venue_count, prevalence, friction_severity)
    SELECT bp.id, %s, %s, %s, %s, %s, %s, %s, %s
    FROM behavioral_patterns bp
    WHERE bp.pattern_name = %s AND bp.area = %s AND bp.source = 'magicpin_upper'
    ON CONFLICT (pattern_id) DO UPDATE SET
        confidence_score       = EXCLUDED.confidence_score,
        evidence_density       = EXCLUDED.evidence_density,
        temporal_consistency   = EXCLUDED.temporal_consistency,
        evidence_diversity     = EXCLUDED.evidence_diversity,
        commercial_reliability = EXCLUDED.commercial_reliability,
        venue_count            = EXCLUDED.venue_count,
        prevalence             = EXCLUDED.prevalence,
        friction_severity      = EXCLUDED.friction_severity;
"""


def parse_score(val) -> float:
    try:
        return float(val) / 100 if float(val) > 1 else float(val)
    except Exception:
        return 0.0


def parse_prevalence(val) -> float:
    try:
        return float(str(val).strip('%')) / 100
    except Exception:
        return 0.0


def load_region(cursor, region: str) -> dict:
    path = os.path.join(BASE_PATH, region, 'step_5_patterns_scored.json')

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    patterns = data.get('patterns_scored', {})
    loaded   = 0
    missed   = 0

    for pattern_name, info in patterns.items():
        cursor.execute(SCORE_SQL, (
            info.get('confidence_score', 0.0),
            parse_score(info.get('frequency_score', 0)),
            parse_score(info.get('consistency_score', 0)),
            parse_score(info.get('recency_score', 0)),
            0.0,  # commercial_reliability not in file
            info.get('venue_count', 0),
            parse_prevalence(info.get('prevalence', '0%')),
            info.get('friction_severity', ''),
            pattern_name,
            region,
        ))
        if cursor.rowcount > 0:
            loaded += 1
        else:
            missed += 1

    return {'region': region, 'total': len(patterns), 'loaded': loaded, 'missed': missed}


def main():
    print("\n024_load_magicpin_step5_scores.py — MagicPin pattern scores → pattern_scores\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    summary = []

    try:
        for region in REGIONS:
            print(f"  Region: {region}")
            result = load_region(cursor, region)
            summary.append(result)
            print(f"    loaded : {result['loaded']}/{result['total']}")
            if result['missed']:
                print(f"    missed : {result['missed']} (run 022 first)")

        conn.commit()
        print(f"\n{'='*55}")
        print(f"  COMPLETE — {sum(r['loaded'] for r in summary):,} pattern scores stored")
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
