"""
Run all behavioral research SQL migrations and seed files against the
configured PostgreSQL database.

Usage:
    python -m db.seed              # run all pending files
    python -m db.seed --dry-run    # print SQL without executing
    python -m db.seed --reset      # DROP + recreate enums and tables first (destructive)

Files are executed in filename order:
    001_schema.sql
    002_seed_segments_archetypes.sql
    003_seed_mechanisms_channels_weights.sql

Requires the same env vars as the main app: PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD
"""

import asyncio
import os
import sys
import json
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

# Load .env from the backend root (one level up from db/)
load_dotenv(Path(__file__).parent.parent / ".env")


DB_DIR = Path(__file__).parent

SQL_FILES = [
    "001_schema.sql",
    "002_seed_segments_archetypes.sql",
    "003_seed_mechanisms_channels_weights.sql",
]

RESET_SQL = """
DO $$ DECLARE r RECORD;
BEGIN
    FOR r IN (
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename IN (
            'research_validation_flags','trait_fitness_weights',
            'channel_segment_effectiveness','channel_benchmarks',
            'segment_archetype_affinity','archetype_spend_triggers',
            'archetype_behavioral_profiles','segment_platform_usage',
            'segment_occasion_multipliers','segment_behavioral_profiles',
            'mechanism_signals','mechanism_citations','behavioral_mechanisms'
        )
    ) LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;

DROP VIEW IF EXISTS peer_influence_matrix CASCADE;
DROP VIEW IF EXISTS revpash_economics CASCADE;

DROP TYPE IF EXISTS affinity_level CASCADE;
DROP TYPE IF EXISTS alcohol_driver CASCADE;
DROP TYPE IF EXISTS discovery_rate CASCADE;
DROP TYPE IF EXISTS occasion_habit_orientation CASCADE;
DROP TYPE IF EXISTS revenue_curve_shape CASCADE;
DROP TYPE IF EXISTS signal_strength CASCADE;
DROP TYPE IF EXISTS platform_name CASCADE;
DROP TYPE IF EXISTS platform_usage_type CASCADE;
DROP TYPE IF EXISTS mechanism_category CASCADE;
"""


async def _setup_connection(conn: asyncpg.Connection) -> None:
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
    await conn.set_type_codec("json",  encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


async def run(dry_run: bool = False, reset: bool = False) -> None:
    conn = await asyncpg.connect(
        host=os.getenv("PG_HOST"),
        port=int(os.getenv("PG_PORT", 5432)),
        database=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        ssl="require",
    )
    await _setup_connection(conn)

    try:
        if reset:
            print("-- RESET: dropping existing behavioral research tables and types")
            if not dry_run:
                await conn.execute(RESET_SQL)
            else:
                print(RESET_SQL)

        for filename in SQL_FILES:
            path = DB_DIR / filename
            if not path.exists():
                print(f"SKIP  {filename} (not found)")
                continue

            sql = path.read_text(encoding="utf-8")
            print(f"RUN   {filename} ({len(sql):,} chars)")

            if dry_run:
                print(sql[:500], "...\n")
                continue

            try:
                await conn.execute(sql)
                print(f"OK    {filename}")
            except Exception as exc:
                print(f"FAIL  {filename}: {exc}")
                raise

    finally:
        await conn.close()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    reset   = "--reset"   in sys.argv
    asyncio.run(run(dry_run=dry_run, reset=reset))
