"""
golden_check.py — Regression guard for the fitness pipeline.

A "golden set" is a frozen snapshot of blended fitness scores for venues you
trust. Before/after any pipeline change (blend math, confidence, embeddings),
run --check to see exactly which venues drifted and by how much. This is what
turns "did that change help or hurt?" into a number, and what would have caught
the sys.path import breakage immediately.

Workflow:
  1. Freeze current known-good state (do this once, when scores look right):
       python utils/golden_check.py --snapshot --venue-ids 128 223 12066 ...
     or snapshot the top-N highest-evidence venues automatically:
       python utils/golden_check.py --snapshot --top 50

  2. After any change, verify nothing regressed:
       python utils/golden_check.py --check
     Exit code 0 = within tolerance, 1 = drift detected (CI-friendly).

Artifact: Database/config/golden_set.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
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

ARTIFACT_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "golden_set.json"
DEFAULT_TOLERANCE = 0.03  # absolute drift allowed per dimension before it's flagged

DIMENSIONS = [
    "fitness_for_office_lunch",
    "fitness_for_repeat_habit",
    "fitness_for_social_dwell",
    "fitness_for_group_energy",
    "fitness_for_destination_visit",
    "operational_quality",
    "retention_strength",
    "monetization_potential",
]

SELECT_BY_IDS = f"""
    SELECT f.venue_id, v.name, {', '.join('f.' + d for d in DIMENSIONS)}
    FROM venue_fitness_dimensions f
    JOIN venues v ON v.id = f.venue_id
    WHERE f.source = 'blended' AND f.venue_id = ANY(%s)
"""

SELECT_TOP = f"""
    SELECT f.venue_id, v.name, {', '.join('f.' + d for d in DIMENSIONS)}
    FROM venue_fitness_dimensions f
    JOIN venues v ON v.id = f.venue_id
    WHERE f.source = 'blended'
    ORDER BY COALESCE(f.evidence_count, 0) DESC, f.venue_id
    LIMIT %s
"""


def _fetch(cursor, sql, param):
    cursor.execute(sql, (param,))
    out = {}
    for row in cursor.fetchall():
        venue_id, name = row[0], row[1]
        out[str(venue_id)] = {
            "name": name,
            "scores": {dim: float(row[2 + i] or 0.0) for i, dim in enumerate(DIMENSIONS)},
        }
    return out


def snapshot(venue_ids, top):
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            if venue_ids:
                data = _fetch(cursor, SELECT_BY_IDS, venue_ids)
            else:
                data = _fetch(cursor, SELECT_TOP, top)
    finally:
        conn.close()

    payload = {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "tolerance": DEFAULT_TOLERANCE,
        "source": "blended",
        "venues": data,
    }
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"  Froze {len(data):,} venues → {ARTIFACT_PATH}")


def check(tolerance):
    if not ARTIFACT_PATH.exists():
        print(f"  No golden set at {ARTIFACT_PATH}. Run --snapshot first.")
        sys.exit(1)

    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        golden = json.load(f)
    tol = tolerance if tolerance is not None else golden.get("tolerance", DEFAULT_TOLERANCE)
    venue_ids = [int(v) for v in golden["venues"].keys()]

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            current = _fetch(cursor, SELECT_BY_IDS, venue_ids)
    finally:
        conn.close()

    drift_rows = []
    missing = []
    for vid, expected in golden["venues"].items():
        if vid not in current:
            missing.append((vid, expected["name"]))
            continue
        for dim in DIMENSIONS:
            exp = expected["scores"].get(dim, 0.0)
            act = current[vid]["scores"].get(dim, 0.0)
            delta = round(act - exp, 4)
            if abs(delta) > tol:
                drift_rows.append((vid, expected["name"], dim, exp, act, delta))

    print(f"\n  Golden set: {len(golden['venues'])} venues | tolerance ±{tol}")
    if missing:
        print(f"\n  [MISSING] {len(missing)} golden venue(s) absent from blended output:")
        for vid, name in missing:
            print(f"    venue_id={vid:<7} {name}")
    if drift_rows:
        print(f"\n  [DRIFT] {len(drift_rows)} dimension(s) outside tolerance:")
        for vid, name, dim, exp, act, delta in drift_rows:
            sign = "+" if delta > 0 else ""
            print(f"    {name[:28]:<28} {dim:<32} {exp:.3f} → {act:.3f} ({sign}{delta})")
    if not missing and not drift_rows:
        print("\n  PASS — all golden venues within tolerance.")
        sys.exit(0)

    print(f"\n  FAIL — {len(drift_rows)} drift, {len(missing)} missing.")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Golden-set regression guard for blended fitness")
    parser.add_argument("--snapshot", action="store_true", help="Freeze current blended scores")
    parser.add_argument("--check", action="store_true", help="Compare current vs frozen (default)")
    parser.add_argument("--venue-ids", type=int, nargs="*", help="Specific venue ids to snapshot")
    parser.add_argument("--top", type=int, default=50, help="Snapshot top-N by evidence (if no ids)")
    parser.add_argument("--tolerance", type=float, default=None, help="Override drift tolerance")
    args = parser.parse_args()

    if args.snapshot:
        snapshot(args.venue_ids, args.top)
    else:
        check(args.tolerance)


if __name__ == "__main__":
    main()
