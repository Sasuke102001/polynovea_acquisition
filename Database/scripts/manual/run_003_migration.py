"""
run_003_migration.py
Applies 003_m3_integration.sql to the live RDS.
Run once. All statements are idempotent (IF NOT EXISTS / ON CONFLICT DO NOTHING).
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

for p in [
    Path(__file__).parent.parent.parent / ".env",
    Path(__file__).parent.parent.parent.parent / "App" / "backend" / ".env",
]:
    if p.exists():
        load_dotenv(p)
        break

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', ''),
    'sslmode':  'require',
}

STEPS = [
    # ── A. service_type on venues ─────────────────────────────────────────────
    ("A1: venues.service_type column", """
        ALTER TABLE venues
            ADD COLUMN IF NOT EXISTS service_type TEXT
            CHECK (service_type IN ('watch_only', 'watch_and_optimise'))
    """),
    ("A2: venues.service_type index", """
        CREATE INDEX IF NOT EXISTS idx_venues_service_type
            ON venues (service_type) WHERE service_type IS NOT NULL
    """),

    # ── B. New columns on m3_kpi_observations ─────────────────────────────────
    ("B1: m3_kpi_observations.observation_state", """
        ALTER TABLE m3_kpi_observations
            ADD COLUMN IF NOT EXISTS observation_state TEXT
            CHECK (observation_state IN ('natural', 'engineered', 'settling'))
    """),
    ("B2: m3_kpi_observations.service_type", """
        ALTER TABLE m3_kpi_observations
            ADD COLUMN IF NOT EXISTS service_type TEXT
            CHECK (service_type IN ('watch_only', 'watch_and_optimise'))
    """),
    ("B3: m3_kpi_observations.engagement_phase", """
        ALTER TABLE m3_kpi_observations
            ADD COLUMN IF NOT EXISTS engagement_phase TEXT
            CHECK (engagement_phase IN ('baseline', 'active'))
    """),
    ("B4: m3_kpi_observations state index", """
        CREATE INDEX IF NOT EXISTS idx_m3_kpi_obs_state
            ON m3_kpi_observations (venue_id, observation_state)
            WHERE observation_state IS NOT NULL
    """),
    ("B5: backfill observation_state from session_mode", """
        UPDATE m3_kpi_observations
        SET observation_state = CASE
            WHEN session_mode = 'observation_only'   THEN 'natural'
            WHEN session_mode = 'engineering_active' THEN 'engineered'
            WHEN session_mode = 'post_intervention'  THEN 'settling'
            ELSE NULL
        END
        WHERE observation_state IS NULL AND session_mode IS NOT NULL
    """),

    # ── C. m3_kpi_dimension_map ───────────────────────────────────────────────
    ("C1: create m3_kpi_dimension_map", """
        CREATE TABLE IF NOT EXISTS m3_kpi_dimension_map (
            id              SERIAL PRIMARY KEY,
            kpi_family_slug TEXT NOT NULL,
            m2_dimension    TEXT NOT NULL,
            direction       TEXT NOT NULL DEFAULT 'positive'
                CHECK (direction IN ('positive', 'negative')),
            weight          DECIMAL(4,3) NOT NULL DEFAULT 1.0
                CHECK (weight > 0 AND weight <= 1),
            notes           TEXT,
            UNIQUE (kpi_family_slug, m2_dimension)
        )
    """),
    ("C2: m3_kpi_dimension_map slug index", """
        CREATE INDEX IF NOT EXISTS idx_m3_kpi_map_slug
            ON m3_kpi_dimension_map (kpi_family_slug)
    """),
    ("C3: m3_kpi_dimension_map dim index", """
        CREATE INDEX IF NOT EXISTS idx_m3_kpi_map_dim
            ON m3_kpi_dimension_map (m2_dimension)
    """),
    ("C4: seed m3_kpi_dimension_map (3 slugs)", """
        INSERT INTO m3_kpi_dimension_map
            (kpi_family_slug, m2_dimension, direction, weight, notes)
        VALUES
            ('stimulus',            'fitness_for_social_dwell',      'positive', 0.800, 'stimuli drive social dwell'),
            ('stimulus',            'fitness_for_destination_visit', 'positive', 0.700, 'stimuli make venue worth traveling to'),
            ('stimulus',            'fitness_for_group_energy',      'positive', 0.600, 'stimuli amplify group energy'),
            ('stimulus',            'retention_strength',            'positive', 0.500, 'stimuli drive return intent'),
            ('behavioral_response', 'fitness_for_social_dwell',      'positive', 0.900, 'dwell behavior directly measures social_dwell'),
            ('behavioral_response', 'fitness_for_repeat_habit',      'positive', 0.800, 'repeat behavioral signals'),
            ('behavioral_response', 'fitness_for_group_energy',      'positive', 0.700, 'group behavioral signals'),
            ('behavioral_response', 'retention_strength',            'positive', 0.700, 'loyalty behavioral signals'),
            ('commercial_behavior', 'monetization_potential',        'positive', 0.900, 'spend signals directly measure monetization'),
            ('commercial_behavior', 'fitness_for_office_lunch',      'positive', 0.500, 'commercial lunch patterns'),
            ('commercial_behavior', 'fitness_for_repeat_habit',      'positive', 0.400, 'spend regularity = repeat habit')
        ON CONFLICT (kpi_family_slug, m2_dimension) DO NOTHING
    """),

    # ── D. venue_fitness_conditional ─────────────────────────────────────────
    ("D1: create venue_fitness_conditional", """
        CREATE TABLE IF NOT EXISTS venue_fitness_conditional (
            id                  BIGSERIAL PRIMARY KEY,
            venue_id            INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
            dimension           TEXT NOT NULL,
            condition_type      TEXT NOT NULL
                CHECK (condition_type IN ('day_of_week', 'show_type', 'time_of_day')),
            condition_value     TEXT NOT NULL,
            score               DECIMAL(4,3) CHECK (score >= 0 AND score <= 1),
            session_count       INTEGER NOT NULL DEFAULT 0,
            posterior_variance  DECIMAL(8,6),
            observation_state   TEXT NOT NULL DEFAULT 'natural'
                CHECK (observation_state IN ('natural', 'engineered', 'settling')),
            service_type        TEXT
                CHECK (service_type IN ('watch_only', 'watch_and_optimise')),
            pipeline_version    TEXT DEFAULT '3.0-m3-conditional',
            computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (venue_id, dimension, condition_type, condition_value)
        )
    """),
    ("D2: venue_fitness_conditional dim index", """
        CREATE INDEX IF NOT EXISTS idx_vfc_venue_dim
            ON venue_fitness_conditional (venue_id, dimension)
    """),
    ("D3: venue_fitness_conditional stratum index", """
        CREATE INDEX IF NOT EXISTS idx_vfc_venue_stratum
            ON venue_fitness_conditional (venue_id, condition_type, condition_value)
    """),

    # ── E. venue_intervention_efficacy ────────────────────────────────────────
    ("E1: create venue_intervention_efficacy", """
        CREATE TABLE IF NOT EXISTS venue_intervention_efficacy (
            id                  BIGSERIAL PRIMARY KEY,
            venue_id            INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
            plan_id             BIGINT,
            intervention_type   TEXT NOT NULL,
            target_dimension    TEXT NOT NULL,
            pre_score           DECIMAL(4,3) CHECK (pre_score >= 0 AND pre_score <= 1),
            post_score          DECIMAL(4,3) CHECK (post_score >= 0 AND post_score <= 1),
            delta               DECIMAL(5,4) GENERATED ALWAYS AS (post_score - pre_score) STORED,
            retention_rate      DECIMAL(4,3)
                CHECK (retention_rate IS NULL OR (retention_rate >= 0 AND retention_rate <= 1)),
            structural_shift    DECIMAL(4,3) GENERATED ALWAYS AS (
                                    pre_score + (COALESCE(retention_rate, 0) * (post_score - pre_score))
                                ) STORED,
            session_count       INTEGER NOT NULL DEFAULT 1,
            conditions          JSONB,
            confidence          DECIMAL(4,3)
                CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
            notes               TEXT,
            recorded_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """),
    ("E2: venue_intervention_efficacy venue index", """
        CREATE INDEX IF NOT EXISTS idx_vie_venue
            ON venue_intervention_efficacy (venue_id)
    """),
    ("E3: venue_intervention_efficacy dim index", """
        CREATE INDEX IF NOT EXISTS idx_vie_venue_dim
            ON venue_intervention_efficacy (venue_id, target_dimension)
    """),
    ("E4: venue_intervention_efficacy plan index", """
        CREATE INDEX IF NOT EXISTS idx_vie_plan
            ON venue_intervention_efficacy (plan_id) WHERE plan_id IS NOT NULL
    """),
]


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        for label, sql in STEPS:
            cur.execute(sql.strip())
            affected = cur.rowcount if cur.rowcount >= 0 else 0
            suffix = f"  ({affected} rows)" if affected else ""
            print(f"  OK  {label}{suffix}")

        conn.commit()
        print("\n003_m3_integration applied successfully.")

        # Verify new tables exist
        print("\nVerification:")
        for table in ["m3_kpi_dimension_map", "venue_fitness_conditional", "venue_intervention_efficacy"]:
            cur.execute("SELECT COUNT(*) FROM " + table)
            print(f"  {table}: {cur.fetchone()[0]} rows")

        cur.execute("SELECT COUNT(*) FROM m3_kpi_dimension_map")
        cur.execute("SELECT kpi_family_slug, m2_dimension, direction, weight FROM m3_kpi_dimension_map ORDER BY kpi_family_slug, m2_dimension")
        print("\nm3_kpi_dimension_map contents:")
        for r in cur.fetchall():
            print(f"  {r[0]:<22} → {r[1]:<35} dir={r[2]}  w={r[3]}")

        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='venues' AND column_name='service_type'")
        print(f"\nvenues.service_type exists: {bool(cur.fetchone())}")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR — rolled back: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
