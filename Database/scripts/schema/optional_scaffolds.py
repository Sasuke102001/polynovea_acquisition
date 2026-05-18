"""
014_create_optional_scaffolds.py
Creates empty scaffold tables for optional data sources.

Core Principle: Never gate an insight behind missing data.
  These tables add REFINEMENT when populated.
  Their absence has zero impact on base recommendations.
  Every venue gets full recommendations from day one.

Scaffold tables:
  1. venue_platform_data   — Zomato/Swiggy opt-in dining data (venue shares voluntarily)
  2. venue_pos_summary     — POS financial data (from Module 3 field work)

When to populate:
  - venue_platform_data:   When a venue opts in and shares their Zomato/Swiggy
                           for Business dashboard export
  - venue_pos_summary:     When Module 3 POS integration is live

Run after: 013_compute_fitness_deltas.py
"""

import os
import sys
import psycopg2

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'your-db-instance.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'your_user'),
    'password': os.getenv('PG_PASSWORD', 'your_password'),
    'sslmode':  'require',
}

CREATE_PLATFORM_DATA = """
CREATE TABLE IF NOT EXISTS venue_platform_data (
    id                      SERIAL PRIMARY KEY,
    venue_id                INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    platform                VARCHAR(20) NOT NULL,   -- 'zomato' | 'swiggy'
    opt_in_date             DATE,
    -- Ratings & reviews
    current_rating          FLOAT,
    rating_30d_ago          FLOAT,
    rating_delta            FLOAT GENERATED ALWAYS AS (current_rating - rating_30d_ago) STORED,
    total_review_count      INTEGER,
    reviews_last_30d        INTEGER,
    -- Cover & traffic
    monthly_covers          INTEGER,
    avg_covers_per_day      FLOAT,
    peak_day                VARCHAR(20),             -- e.g. 'Saturday'
    peak_hour_range         VARCHAR(30),             -- e.g. '12:00-14:00'
    -- Financial (if shared)
    avg_order_value         FLOAT,
    avg_table_spend         FLOAT,
    -- Platform presence
    photo_count             INTEGER,
    last_photo_updated      DATE,
    dineout_enabled         BOOLEAN DEFAULT FALSE,
    promoted_placement      BOOLEAN DEFAULT FALSE,
    -- Metadata
    data_as_of              DATE,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(venue_id, platform)
);

CREATE INDEX IF NOT EXISTS idx_vpd_venue     ON venue_platform_data(venue_id);
CREATE INDEX IF NOT EXISTS idx_vpd_platform  ON venue_platform_data(platform, current_rating DESC);
"""

CREATE_POS_SUMMARY = """
CREATE TABLE IF NOT EXISTS venue_pos_summary (
    id                      SERIAL PRIMARY KEY,
    venue_id                INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    -- Revenue
    monthly_revenue         FLOAT,
    avg_daily_revenue       FLOAT,
    revenue_per_cover       FLOAT,
    -- Volume
    monthly_covers          INTEGER,
    avg_table_size          FLOAT,
    avg_visit_duration_mins INTEGER,
    -- Repeat behaviour
    repeat_customer_rate    FLOAT,    -- 0-1
    avg_visits_per_customer FLOAT,    -- in 30 days
    customer_lifetime_value FLOAT,    -- estimated ₹
    -- Timing
    peak_day                VARCHAR(20),
    peak_hour_range         VARCHAR(30),
    lunch_revenue_pct       FLOAT,    -- % of revenue from lunch
    dinner_revenue_pct      FLOAT,    -- % of revenue from dinner
    -- Module 3 source
    data_source             VARCHAR(50) DEFAULT 'module3_field',
    data_as_of              DATE,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(venue_id)
);

CREATE INDEX IF NOT EXISTS idx_vps_venue ON venue_pos_summary(venue_id);
"""

# Platform performance benchmarks (city-level aggregates built from opt-in data)
CREATE_PLATFORM_BENCHMARKS = """
CREATE TABLE IF NOT EXISTS platform_performance_benchmarks (
    id                      SERIAL PRIMARY KEY,
    platform                VARCHAR(20) NOT NULL,
    city                    VARCHAR(50),
    venue_type              VARCHAR(50),     -- casual_dine, fine_dine, bar, cafe, lounge
    sample_size             INTEGER DEFAULT 0,
    avg_rating              FLOAT,
    avg_monthly_covers      INTEGER,
    avg_review_velocity     FLOAT,           -- reviews per month
    avg_photo_count         INTEGER,
    pct_with_dineout        FLOAT,           -- % of venues with Dineout enabled
    confidence              VARCHAR(10) DEFAULT 'LOW',  -- LOW/MEDIUM/HIGH based on sample_size
    last_updated            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, city, venue_type)
);

CREATE INDEX IF NOT EXISTS idx_ppb_platform_city ON platform_performance_benchmarks(platform, city);
"""


def main():
    print("\n014_create_optional_scaffolds.py -- Optional data scaffold tables\n")
    print("  Principle: Never gate an insight behind missing data.")
    print("  These tables add refinement. Absence = zero impact on base recommendations.\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        print("  [1/3] venue_platform_data (Zomato/Swiggy opt-in)...")
        cursor.execute(CREATE_PLATFORM_DATA)
        print("        Created")

        print("  [2/3] venue_pos_summary (Module 3 POS data)...")
        cursor.execute(CREATE_POS_SUMMARY)
        print("        Created")

        print("  [3/3] platform_performance_benchmarks (city-level aggregates)...")
        cursor.execute(CREATE_PLATFORM_BENCHMARKS)
        print("        Created")

        conn.commit()

        print("\n" + "=" * 55)
        print("  COMPLETE — 3 scaffold tables ready")
        print("  Populate when:")
        print("    venue_platform_data     → venue opts in to share Zomato/Swiggy data")
        print("    venue_pos_summary       → Module 3 POS integration is live")
        print("    platform_benchmarks     → auto-built from opt-in data as venues join")
        print("=" * 55 + "\n")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
