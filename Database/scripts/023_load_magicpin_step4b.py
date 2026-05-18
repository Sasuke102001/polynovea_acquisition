"""
023_load_magicpin_step4b.py
Loads step_4b_governance_report.json (MagicPin BIF) for all 4 regions into:
  - data_quality_metrics  (source='magicpin_upper')
  - drift_signals         (source='magicpin_upper')
  - cluster_quality       (source='magicpin_upper')

All UPSERTs on (area, source) — Google rows are untouched.
Run after: 018_add_source_columns.py
"""

import json
import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'magicpin')
REGIONS   = ['mumbai', 'navi-mumbai', 'sobo', 'thane']

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

QUALITY_SQL = """
    INSERT INTO data_quality_metrics
        (area, source, avg_confidence, avg_reliability, reliability_score,
         high_reliability_clusters, total_clusters)
    VALUES (%s, 'magicpin_upper', %s, %s, %s, %s, %s)
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
    VALUES (%s, 'magicpin_upper', %s, %s, %s)
    ON CONFLICT (area, source) DO UPDATE SET
        total_clusters   = EXCLUDED.total_clusters,
        high_reliability = EXCLUDED.high_reliability,
        low_confidence   = EXCLUDED.low_confidence;
"""


def load_region(cursor, region: str) -> dict:
    path = os.path.join(BASE_PATH, region, 'step_4b_governance_report.json')

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cursor.execute(QUALITY_SQL, (
        region,
        data.get('avg_confidence', 0.0),
        data.get('avg_reliability', 0.0),
        data.get('reliability_score', 0.0),
        data.get('high_reliability_clusters', 0),
        data.get('total_clusters', 0),
    ))

    cursor.execute(CLUSTER_SQL, (
        region,
        data.get('total_clusters', 0),
        data.get('high_reliability_clusters', 0),
        data.get('low_confidence_clusters', 0),
    ))

    drift_rows = []
    for ds in data.get('drift_signals', []):
        direction = ds.get('drift_type', 'emerging').replace('new_pattern', 'emerging')
        drift_rows.append((
            region, 'magicpin_upper',
            ds.get('pattern', ''),
            ds.get('current_confidence', 0.0),
            direction,
        ))

    if drift_rows:
        psycopg2.extras.execute_values(cursor, DRIFT_SQL, drift_rows)

    return {'region': region, 'drift': len(drift_rows)}


def main():
    print("\n023_load_magicpin_step4b.py — MagicPin governance → data_quality_metrics\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    summary = []

    try:
        for region in REGIONS:
            print(f"  Region: {region}")
            result = load_region(cursor, region)
            summary.append(result)
            print(f"    drift signals: {result['drift']}")

        conn.commit()
        print(f"\n{'='*55}")
        print(f"  COMPLETE — {len(REGIONS)} regions, {sum(r['drift'] for r in summary)} drift signals")
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
