"""
check_source_coverage.py
Quick audit — counts rows per source in every pipeline table.
"""
import os, sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', '07586277012Luna'),
    'sslmode':  'require',
}

QUERIES = [
    ("primitives_scores",          "SELECT source, COUNT(*) FROM primitives_scores GROUP BY source ORDER BY source"),
    ("behavioral_patterns",        "SELECT source, COUNT(*) FROM behavioral_patterns GROUP BY source ORDER BY source"),
    ("pattern_venues",             "SELECT bp.source, COUNT(*) FROM pattern_venues pv JOIN behavioral_patterns bp ON bp.id = pv.pattern_id GROUP BY bp.source ORDER BY bp.source"),
    ("raw_venue_data",             "SELECT platform, COUNT(*) FROM raw_venue_data GROUP BY platform ORDER BY platform"),
    ("data_quality_metrics",       "SELECT source, COUNT(*) FROM data_quality_metrics GROUP BY source ORDER BY source"),
    ("drift_signals",              "SELECT source, COUNT(*) FROM drift_signals GROUP BY source ORDER BY source"),
    ("cluster_quality",            "SELECT source, COUNT(*) FROM cluster_quality GROUP BY source ORDER BY source"),
    ("pattern_scores",             "SELECT bp.source, COUNT(*) FROM pattern_scores ps JOIN behavioral_patterns bp ON bp.id = ps.pattern_id GROUP BY bp.source ORDER BY bp.source"),
    ("venue_fitness_dimensions",   "SELECT source, COUNT(*) FROM venue_fitness_dimensions GROUP BY source ORDER BY source"),
    ("behavioral_summary",         "SELECT source, COUNT(*) FROM behavioral_summary GROUP BY source ORDER BY source"),
    ("venue_vectors",              "SELECT source, COUNT(*) FROM venue_vectors GROUP BY source ORDER BY source"),
    ("venue_similarity",           "SELECT source, COUNT(*) FROM venue_similarity GROUP BY source ORDER BY source"),
    ("intervention_triggers",      "SELECT source, COUNT(*) FROM intervention_triggers GROUP BY source ORDER BY source"),
]

conn   = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

print("\n" + "="*60)
print("  SOURCE COVERAGE AUDIT")
print("="*60)

for table, sql in QUERIES:
    cursor.execute(sql)
    rows = cursor.fetchall()
    print(f"\n  {table}")
    if rows:
        for source, count in rows:
            print(f"    {source:<25} {count:>8,}")
    else:
        print("    (empty)")

print("\n" + "="*60 + "\n")
cursor.close()
conn.close()
