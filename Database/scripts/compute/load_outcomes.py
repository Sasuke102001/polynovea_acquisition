"""
load_outcomes.py — Append ground-truth labels into venue_outcomes.

This is the capture layer for the future supervised-ML training set. It is
APPEND-ONLY: every call inserts, nothing is overwritten. Three ways in:

  1. Programmatic — `from load_outcomes import record_outcome`
       record_outcome(venue_id=128, signal_type='sales_thumbs',
                      signal_value=1.0, fitness_dim='fitness_for_social_dwell',
                      actor='sales:roy', context={'prospect_name': 'GBC'})

  2. CLI — single label:
       python compute/load_outcomes.py --venue-id 128 --type sales_thumbs \
              --value 1 --dim fitness_for_social_dwell --actor sales:roy

  3. Bulk — ingest a JSON array file (e.g. exported Supabase dismissals):
       python compute/load_outcomes.py --file outcomes_export.json

  Bulk file shape: [{"venue_id":128,"signal_type":"dismiss","signal_value":0,
                     "fitness_dim":null,"actor":"demo:abc","context":{...}}, ...]

Run anytime. No dependency on the pipeline — this stream is parallel by design.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

for p in [Path(__file__).parent.parent.parent / ".env",
          Path(__file__).parent.parent.parent.parent / "App" / "backend" / ".env"]:
    if p.exists():
        load_dotenv(p)
        break

DB_CONFIG = {
    "host":     os.getenv("PG_HOST",     "polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com"),
    "port":     int(os.getenv("PG_PORT", 5432)),
    "dbname":   os.getenv("PG_DB",       "polynovea_module2"),
    "user":     os.getenv("PG_USER",     "polynovea_admin"),
    "password": os.getenv("PG_PASSWORD", ""),
    "sslmode":  "require",
}

VALID_TYPES = {"sales_thumbs", "converted", "rejected", "dismiss", "manual_correction"}

INSERT_SQL = """
    INSERT INTO venue_outcomes
        (venue_id, signal_type, signal_value, fitness_dim, actor, context)
    VALUES %s
"""


def _validate(record: dict) -> tuple:
    venue_id = record.get("venue_id")
    signal_type = record.get("signal_type")
    if venue_id is None:
        raise ValueError("venue_id is required")
    if signal_type not in VALID_TYPES:
        raise ValueError(f"signal_type must be one of {sorted(VALID_TYPES)}, got {signal_type!r}")
    ctx = record.get("context")
    return (
        int(venue_id),
        signal_type,
        record.get("signal_value"),
        record.get("fitness_dim"),
        record.get("actor"),
        psycopg2.extras.Json(ctx) if ctx is not None else None,
    )


def record_outcomes(records: list[dict]) -> int:
    """Insert a batch of outcome records. Returns count inserted."""
    rows = [_validate(r) for r in records]
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            psycopg2.extras.execute_values(cursor, INSERT_SQL, rows, page_size=500)
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def record_outcome(venue_id, signal_type, signal_value=None,
                   fitness_dim=None, actor=None, context=None) -> int:
    """Convenience single-record insert (used by the app backend)."""
    return record_outcomes([{
        "venue_id": venue_id,
        "signal_type": signal_type,
        "signal_value": signal_value,
        "fitness_dim": fitness_dim,
        "actor": actor,
        "context": context,
    }])


def main():
    parser = argparse.ArgumentParser(description="Append ground-truth labels to venue_outcomes")
    parser.add_argument("--file", help="JSON array file of outcome records (bulk ingest)")
    parser.add_argument("--venue-id", type=int)
    parser.add_argument("--type", dest="signal_type", choices=sorted(VALID_TYPES))
    parser.add_argument("--value", dest="signal_value", type=float)
    parser.add_argument("--dim", dest="fitness_dim")
    parser.add_argument("--actor")
    parser.add_argument("--note")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            records = json.load(f)
        n = record_outcomes(records)
        print(f"  Ingested {n:,} outcome records from {args.file}")
        return

    if args.venue_id is None or args.signal_type is None:
        parser.error("provide either --file, or at minimum --venue-id and --type")

    n = record_outcome(
        venue_id=args.venue_id,
        signal_type=args.signal_type,
        signal_value=args.signal_value,
        fitness_dim=args.fitness_dim,
        actor=args.actor,
        context={"note": args.note} if args.note else None,
    )
    print(f"  Recorded {n} outcome for venue_id={args.venue_id} ({args.signal_type})")


if __name__ == "__main__":
    main()
