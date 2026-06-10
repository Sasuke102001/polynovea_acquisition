"""
Train venue-level behavioral association rules from persisted primitives.

Purpose:
  - mines stable cross-signal combinations per source
  - writes a JSON artifact consumed by the live step_4 BHIF pipelines
  - keeps the training artifact inside Acquisition System, not inside each source repo

Output:
  Database/config/bhif_association_rules.json

Run after:
  all source loaders that populate primitives_scores
"""

import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

for _p in [Path(__file__).parent.parent.parent / ".env",
           Path(__file__).parent.parent.parent.parent / "App" / "backend" / ".env"]:
    if _p.exists():
        load_dotenv(_p)
        break

DB_CONFIG = {
    "host":     os.getenv("PG_HOST",     "polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com"),
    "port":     int(os.getenv("PG_PORT", 5432)),
    "dbname":   os.getenv("PG_DB",       "polynovea_module2"),
    "user":     os.getenv("PG_USER",     "polynovea_admin"),
    "password": os.getenv("PG_PASSWORD", ""),
    "sslmode":  "require",
}

SCRIPT_DIR = Path(__file__).resolve().parent
ARTIFACT_PATH = SCRIPT_DIR.parent.parent / "config" / "bhif_association_rules.json"
PIPELINE_VERSION = "bhif-association-rules-v1"
MAX_ITEMSET_SIZE = 3
MIN_SIGNAL_CONFIDENCE = 0.18
MIN_SUPPORT_SHARE = 0.015
MIN_CONFIDENCE = 0.65
MIN_LIFT = 1.10
MAX_RULES_PER_SOURCE = 400

FETCH_SQL = """
    SELECT source, venue_id, primitive_id, confidence
    FROM primitives_scores
    WHERE source IN ('google', 'google_reviews', 'magicpin_upper')
"""


def build_baskets(rows):
    baskets_by_source = defaultdict(lambda: defaultdict(dict))
    global_baskets = defaultdict(dict)

    for source, venue_id, primitive_id, confidence in rows:
        conf = float(confidence or 0.0)
        if conf < MIN_SIGNAL_CONFIDENCE:
            continue

        current = baskets_by_source[source][venue_id].get(primitive_id, 0.0)
        if conf > current:
            baskets_by_source[source][venue_id][primitive_id] = conf

        global_current = global_baskets[venue_id].get(primitive_id, 0.0)
        if conf > global_current:
            global_baskets[venue_id][primitive_id] = conf

    finalized = {}
    for source, venue_map in baskets_by_source.items():
        finalized[source] = {
            venue_id: sorted(signals.keys())
            for venue_id, signals in venue_map.items()
            if len(signals) >= 2
        }

    finalized["global"] = {
        venue_id: sorted(signals.keys())
        for venue_id, signals in global_baskets.items()
        if len(signals) >= 2
    }
    return finalized


def count_itemsets(baskets):
    counts = {size: Counter() for size in range(1, MAX_ITEMSET_SIZE + 1)}
    for signals in baskets.values():
        unique = sorted(set(signals))
        upper = min(MAX_ITEMSET_SIZE, len(unique))
        for size in range(1, upper + 1):
            for combo in combinations(unique, size):
                counts[size][combo] += 1
    return counts


def generate_rules_for_source(source, baskets):
    venue_count = len(baskets)
    if venue_count < 25:
        return []

    counts = count_itemsets(baskets)
    rules = []

    for size in range(2, MAX_ITEMSET_SIZE + 1):
        for itemset, itemset_count in counts[size].items():
            support = itemset_count / venue_count
            if support < MIN_SUPPORT_SHARE:
                continue

            itemset_set = set(itemset)
            for consequent in itemset:
                antecedent = tuple(sorted(itemset_set - {consequent}))
                if not antecedent:
                    continue

                antecedent_count = counts[len(antecedent)].get(antecedent, 0)
                consequent_count = counts[1].get((consequent,), 0)
                if antecedent_count == 0 or consequent_count == 0:
                    continue

                confidence = itemset_count / antecedent_count
                consequent_support = consequent_count / venue_count
                lift = confidence / consequent_support if consequent_support else 0.0

                if confidence < MIN_CONFIDENCE or lift < MIN_LIFT:
                    continue

                rules.append({
                    "source": source,
                    "pattern_name": " + ".join(itemset),
                    "antecedent": list(antecedent),
                    "consequent": [consequent],
                    "union": list(itemset),
                    "venue_count": itemset_count,
                    "support": round(support, 6),
                    "confidence": round(confidence, 6),
                    "lift": round(lift, 6),
                })

    rules.sort(
        key=lambda rule: (
            round(rule["confidence"] * rule["lift"], 8),
            round(rule["support"], 8),
            len(rule["union"]),
            rule["venue_count"],
        ),
        reverse=True,
    )

    deduped = []
    seen = set()
    for rule in rules:
        key = (tuple(rule["antecedent"]), tuple(rule["consequent"]))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(rule)
        if len(deduped) >= MAX_RULES_PER_SOURCE:
            break
    return deduped


def main():
    print("\ntrain_behavioral_association_rules.py -- Mining BHIF rule artifact\n")

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute(FETCH_SQL)
            rows = cursor.fetchall()

        baskets_by_source = build_baskets(rows)
        rules_by_source = {}
        coverage = {}

        for source, baskets in baskets_by_source.items():
            coverage[source] = len(baskets)
            rules_by_source[source] = generate_rules_for_source(source, baskets)
            print(
                f"  {source:<15} baskets={coverage[source]:>5}  "
                f"rules={len(rules_by_source[source]):>4}"
            )

        payload = {
            "artifact_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": PIPELINE_VERSION,
            "min_signal_confidence": MIN_SIGNAL_CONFIDENCE,
            "min_support_share": MIN_SUPPORT_SHARE,
            "min_confidence": MIN_CONFIDENCE,
            "min_lift": MIN_LIFT,
            "max_itemset_size": MAX_ITEMSET_SIZE,
            "source_coverage": coverage,
            "rules_by_source": rules_by_source,
        }

        ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(ARTIFACT_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        total_rules = sum(len(v) for v in rules_by_source.values())
        print(f"\n  Wrote {total_rules:,} rules -> {ARTIFACT_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
