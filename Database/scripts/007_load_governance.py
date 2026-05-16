"""
007_load_governance.py
Loads step_4b_governance_report.json for all 4 cities into:
  - data_quality_metrics  (overall quality per city)
  - drift_signals         (emerging patterns per city)
  - cluster_quality       (cluster reliability stats)
Run after 001_init_schema.sql (independent of other loaders)
"""

import json
import os
import sys
import psycopg2
import psycopg2.extras

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'google_places')
CITIES     = ['navi-mumbai', 'mumbai-sobo', 'mumbai-main', 'thane']

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.xxxxxxxxxxxx.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

QUALITY_SQL = """
    INSERT INTO data_quality_metrics
        (area, avg_confidence, avg_reliability, reliability_score,
         high_reliability_clusters, total_clusters)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (area) DO UPDATE SET
        avg_confidence            = EXCLUDED.avg_confidence,
        avg_reliability           = EXCLUDED.avg_reliability,
        reliability_score         = EXCLUDED.reliability_score,
        high_reliability_clusters = EXCLUDED.high_reliability_clusters,
        total_clusters            = EXCLUDED.total_clusters,
        measured_at               = CURRENT_TIMESTAMP;
"""

DRIFT_SQL = """
    INSERT INTO drift_signals (area, pattern_description, confidence_score, trend_direction)
    VALUES %s;
"""

CLUSTER_SQL = """
    INSERT INTO cluster_quality (area, total_clusters, high_reliability, low_confidence)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT DO NOTHING;
"""


def load_city(cursor, city: str) -> dict:
    path = os.path.join(BASE_PATH, city, 'step_4b_governance_report.json')

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # data_quality_metrics
    cursor.execute(QUALITY_SQL, (
        city,
        data.get('avg_confidence', 0.0),
        data.get('avg_reliability', 0.0),
        data.get('reliability_score', 0.0),
        data.get('high_reliability_clusters', 0),
        data.get('total_clusters', 0),
    ))

    # cluster_quality
    cursor.execute(CLUSTER_SQL, (
        city,
        data.get('total_clusters', 0),
        data.get('high_reliability_clusters', 0),
        data.get('low_confidence_clusters', 0),
    ))

    # drift_signals — batch insert
    drift_rows = []
    for ds in data.get('drift_signals', []):
        direction = ds.get('drift_type', 'emerging').replace('new_pattern', 'emerging')
        drift_rows.append((
            city,
            ds.get('pattern', ''),
            ds.get('current_confidence', 0.0),
            direction,
        ))

    if drift_rows:
        psycopg2.extras.execute_values(cursor, DRIFT_SQL, drift_rows)

    return {
        'city':         city,
        'drift_count':  len(drift_rows),
        'avg_conf':     data.get('avg_confidence', 0.0),
        'reliability':  data.get('reliability_score', 0.0),
    }


def main():
    print("\n007_load_governance.py -- Loading data quality metrics & drift signals\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    summary = []
    try:
        for city in CITIES:
            print(f"\n  City: {city}")
            result = load_city(cursor, city)
            summary.append(result)
            print(f"  Avg confidence : {result['avg_conf']}")
            print(f"  Reliability    : {result['reliability']}")
            print(f"  Drift signals  : {result['drift_count']}")

        conn.commit()
        print("\n" + "="*55)
        print("  COMPLETE")
        print(f"  Cities loaded  : {len(summary)}")
        print(f"  Total drift    : {sum(r['drift_count'] for r in summary)} signals")
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

