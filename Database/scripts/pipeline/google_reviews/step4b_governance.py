"""
038_load_google_reviews_step4b_governance.py
Loads step_4b_governance_report.json into:
  - data_quality_metrics  (source='google_reviews')
  - drift_signals         (source='google_reviews')
  - cluster_quality       (source='google_reviews')

Regions: thane, navi-mumbai
Run after: schema/add_source_columns.py (018)
"""

import json
import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'raw', 'google_reviews')
REGIONS   = ['thane', 'navi-mumbai']
SOURCE    = 'google_reviews'

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', 'REDACTED_DB_PASSWORD'),
    'sslmode':  'require',
}

QUALITY_SQL = """
    INSERT INTO data_quality_metrics
        (area, source, avg_confidence, avg_reliability, reliability_score,
         high_reliability_clusters, total_clusters)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (area, source) DO UPDATE SET
        avg_confidence            = EXCLUDED.avg_confidence,
        avg_reliability           = EXCLUDED.avg_reliability,
        reliability_score         = EXCLUDED.reliability_score,
        high_reliability_clusters = EXCLUDED.high_reliability_clusters,
        total_clusters            = EXCLUDED.total_clusters,
        measured_at               = CURRENT_TIMESTAMP;
"""

DRIFT_SQL = """
    INSERT INTO drift_signals (area, source, pattern_description, confidence_score, trend_direction)
    VALUES %s
    ON CONFLICT (area, source, pattern_description) DO UPDATE SET
        confidence_score = EXCLUDED.confidence_score,
        trend_direction  = EXCLUDED.trend_direction;
"""

CLUSTER_SQL = """
    INSERT INTO cluster_quality (area, source, total_clusters, high_reliability, low_confidence)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (area, source) DO UPDATE SET
        total_clusters   = EXCLUDED.total_clusters,
        high_reliability = EXCLUDED.high_reliability,
        low_confidence   = EXCLUDED.low_confidence;
"""


def load_region(cursor, region: str) -> dict:
    path = os.path.join(BASE_PATH, region, 'step_4b_governance_report.json')
    if not os.path.exists(path):
        print(f"    [SKIP] Not found: {path}")
        return {'region': region, 'drift_count': 0, 'avg_conf': 0, 'reliability': 0}

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cursor.execute(QUALITY_SQL, (
        region, SOURCE,
        data.get('avg_confidence', 0.0),
        data.get('avg_reliability', 0.0),
        data.get('reliability_score', 0.0),
        data.get('high_reliability_clusters', 0),
        data.get('total_clusters', 0),
    ))

    cursor.execute(CLUSTER_SQL, (
        region, SOURCE,
        data.get('total_clusters', 0),
        data.get('high_reliability_clusters', 0),
        data.get('low_confidence_clusters', 0),
    ))

    drift_rows = []
    for ds in data.get('drift_signals', []):
        direction = ds.get('drift_type', 'emerging').replace('new_pattern', 'emerging')
        drift_rows.append((
            region, SOURCE,
            ds.get('pattern', ''),
            ds.get('current_confidence', 0.0),
            direction,
        ))

    if drift_rows:
        psycopg2.extras.execute_values(cursor, DRIFT_SQL, drift_rows)

    return {
        'region':      region,
        'drift_count': len(drift_rows),
        'avg_conf':    data.get('avg_confidence', 0.0),
        'reliability': data.get('reliability_score', 0.0),
    }


def main():
    print(f"\n038_load_google_reviews_step4b_governance.py — source='{SOURCE}'\n")

    conn    = psycopg2.connect(**DB_CONFIG)
    cursor  = conn.cursor()
    summary = []

    try:
        for region in REGIONS:
            print(f"  Region: {region}")
            r = load_region(cursor, region)
            summary.append(r)
            print(f"    avg confidence : {r['avg_conf']:.3f}")
            print(f"    reliability    : {r['reliability']:.3f}")
            print(f"    drift signals  : {r['drift_count']}")
            print()

        conn.commit()
        print(f"{'='*55}")
        print(f"  COMPLETE")
        print(f"  Total drift signals : {sum(r['drift_count'] for r in summary)}")
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
