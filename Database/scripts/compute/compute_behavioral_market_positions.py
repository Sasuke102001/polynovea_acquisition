"""
Compute venue-level behavioral market positioning after blend.

Outputs:
  - behavioral_districts
  - venue_behavioral_market_position

This is the post-blend step 5c layer:
  - behavioral_district
  - state_energy
  - is_anomaly
  - behavioral_entropy
  - niche_saturation
"""

import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

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

PIPELINE_VERSION = "market-position-v1"
SOURCE_KEY = "blended"
GRID_SIZE_DEGREES = 0.02

SCRIPT_DIR = Path(__file__).resolve().parent
SCHEMA_SQL_PATH = SCRIPT_DIR.parent / "schema" / "venue_behavioral_market_position.sql"

FETCH_SQL = """
    SELECT
        v.id,
        v.place_id,
        v.name,
        COALESCE(v.city, 'unknown') AS city,
        COALESCE(v.area, 'unknown') AS area,
        v.lat,
        v.lng,
        f.fitness_for_office_lunch,
        f.fitness_for_repeat_habit,
        f.fitness_for_social_dwell,
        f.fitness_for_group_energy,
        f.fitness_for_destination_visit,
        f.operational_quality,
        f.retention_strength,
        f.monetization_potential
    FROM venues v
    JOIN venue_fitness_dimensions f
      ON f.venue_id = v.id
     AND f.source = %s
"""

DELETE_VENUE_SQL = "DELETE FROM venue_behavioral_market_position WHERE source = %s"
DELETE_DISTRICT_SQL = "DELETE FROM behavioral_districts WHERE source = %s"

UPSERT_DISTRICT_SQL = """
    INSERT INTO behavioral_districts (
        district_id, source, city, geo_cell, district_label, behavioral_signature,
        venue_count, avg_state_energy, avg_behavioral_entropy, avg_niche_saturation,
        centroid_lat, centroid_lng, top_dimensions, details, pipeline_version, computed_at
    )
    VALUES %s
    ON CONFLICT (district_id) DO UPDATE SET
        source                 = EXCLUDED.source,
        city                   = EXCLUDED.city,
        geo_cell               = EXCLUDED.geo_cell,
        district_label         = EXCLUDED.district_label,
        behavioral_signature   = EXCLUDED.behavioral_signature,
        venue_count            = EXCLUDED.venue_count,
        avg_state_energy       = EXCLUDED.avg_state_energy,
        avg_behavioral_entropy = EXCLUDED.avg_behavioral_entropy,
        avg_niche_saturation   = EXCLUDED.avg_niche_saturation,
        centroid_lat           = EXCLUDED.centroid_lat,
        centroid_lng           = EXCLUDED.centroid_lng,
        top_dimensions         = EXCLUDED.top_dimensions,
        details                = EXCLUDED.details,
        pipeline_version       = EXCLUDED.pipeline_version,
        computed_at            = EXCLUDED.computed_at
"""

UPSERT_VENUE_SQL = """
    INSERT INTO venue_behavioral_market_position (
        venue_id, source, district_id, behavioral_district, state_energy, energy_band,
        anomaly_score, is_anomaly, behavioral_entropy, niche_saturation, district_size,
        signature_family, local_density, top_dimensions, details, pipeline_version, computed_at
    )
    VALUES %s
    ON CONFLICT (venue_id) DO UPDATE SET
        source               = EXCLUDED.source,
        district_id          = EXCLUDED.district_id,
        behavioral_district  = EXCLUDED.behavioral_district,
        state_energy         = EXCLUDED.state_energy,
        energy_band          = EXCLUDED.energy_band,
        anomaly_score        = EXCLUDED.anomaly_score,
        is_anomaly           = EXCLUDED.is_anomaly,
        behavioral_entropy   = EXCLUDED.behavioral_entropy,
        niche_saturation     = EXCLUDED.niche_saturation,
        district_size        = EXCLUDED.district_size,
        signature_family     = EXCLUDED.signature_family,
        local_density        = EXCLUDED.local_density,
        top_dimensions       = EXCLUDED.top_dimensions,
        details              = EXCLUDED.details,
        pipeline_version     = EXCLUDED.pipeline_version,
        computed_at          = EXCLUDED.computed_at
"""

FITNESS_KEYS = [
    ("fitness_for_office_lunch", "office_lunch"),
    ("fitness_for_repeat_habit", "repeat_habit"),
    ("fitness_for_social_dwell", "social_dwell"),
    ("fitness_for_group_energy", "group_energy"),
    ("fitness_for_destination_visit", "destination_visit"),
]

ALL_NUMERIC_KEYS = [
    "fitness_for_office_lunch",
    "fitness_for_repeat_habit",
    "fitness_for_social_dwell",
    "fitness_for_group_energy",
    "fitness_for_destination_visit",
    "operational_quality",
    "retention_strength",
    "monetization_potential",
]


def safe_float(value):
    return round(float(value or 0.0), 4)


def geo_cell(lat, lng, fallback_area):
    if lat is None or lng is None:
        return f"no-geo:{str(fallback_area).strip().lower()}"
    lat_cell = math.floor(float(lat) / GRID_SIZE_DEGREES)
    lng_cell = math.floor(float(lng) / GRID_SIZE_DEGREES)
    return f"g{lat_cell}_{lng_cell}"


def top_dimensions(row):
    ranked = sorted(
        ((label, safe_float(row[key])) for key, label in FITNESS_KEYS),
        key=lambda item: item[1],
        reverse=True,
    )
    return ranked[:2], ranked


def entropy_from_fitness(row):
    values = [max(safe_float(row[key]), 0.0) for key, _ in FITNESS_KEYS]
    total = sum(values)
    if total <= 0:
        return 0.0
    entropy = 0.0
    for value in values:
        if value <= 0:
            continue
        p = value / total
        entropy -= p * math.log(p, 2)
    max_entropy = math.log(len(values), 2)
    return round(entropy / max_entropy if max_entropy else 0.0, 4)


def state_energy(row):
    score = (
        safe_float(row["fitness_for_group_energy"]) * 0.42
        + safe_float(row["fitness_for_social_dwell"]) * 0.24
        + safe_float(row["fitness_for_destination_visit"]) * 0.14
        + safe_float(row["monetization_potential"]) * 0.10
        + safe_float(row["retention_strength"]) * 0.10
    )
    return round(score, 4)


def energy_band(score):
    if score >= 0.72:
        return "HIGH"
    if score >= 0.48:
        return "MEDIUM"
    return "LOW"


def cosine_similarity(vec_a, vec_b):
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def robust_city_stats(rows):
    by_city = defaultdict(list)
    for row in rows:
        by_city[row["city"]].append(row)

    stats = {}
    for city, city_rows in by_city.items():
        city_stats = {}
        for key in ALL_NUMERIC_KEYS:
            values = [safe_float(r[key]) for r in city_rows]
            median = statistics.median(values) if values else 0.0
            abs_dev = [abs(v - median) for v in values]
            mad = statistics.median(abs_dev) if abs_dev else 0.0
            city_stats[key] = {
                "median": median,
                "mad": mad if mad > 0 else 0.01,
            }
        stats[city] = city_stats
    return stats


def anomaly_score(row, city_stats):
    z_scores = []
    components = {}
    for key in ALL_NUMERIC_KEYS:
        value = safe_float(row[key])
        stats = city_stats[key]
        robust_z = abs(value - stats["median"]) / (1.4826 * stats["mad"])
        components[key] = round(robust_z, 4)
        z_scores.append(robust_z)

    z_scores.sort(reverse=True)
    score = sum(z_scores[:3]) / max(1, min(3, len(z_scores)))
    return round(score, 4), components


def signature_family(top_two):
    return "-".join(label for label, _ in top_two)


def district_label(city, top_two, cell):
    return f"{city}:{signature_family(top_two)}:{cell}"


def load_rows(cursor):
    cursor.execute(FETCH_SQL, (SOURCE_KEY,))
    cols = [desc[0] for desc in cursor.description]
    rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
    return rows


def main():
    print("\ncompute_behavioral_market_positions.py -- Post-blend market positioning\n")

    schema_sql = SCHEMA_SQL_PATH.read_text(encoding="utf-8")

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute(schema_sql)
            cursor.execute(DELETE_VENUE_SQL, (SOURCE_KEY,))
            cursor.execute(DELETE_DISTRICT_SQL, (SOURCE_KEY,))
            rows = load_rows(cursor)

        if not rows:
            print("  No blended venue rows found. Nothing to compute.")
            conn.commit()
            return

        city_stats = robust_city_stats(rows)
        city_counts = Counter(row["city"] for row in rows)
        signature_counts = Counter()
        district_groups = defaultdict(list)

        enriched = []
        for row in rows:
            top_two, ranked_dims = top_dimensions(row)
            sig_family = signature_family(top_two)
            signature_counts[(row["city"], sig_family)] += 1
            cell = geo_cell(row["lat"], row["lng"], row["area"])
            district_id = district_label(row["city"], top_two, cell)

            feature_vector = [safe_float(row[key]) for key, _ in FITNESS_KEYS]
            energy = state_energy(row)
            entropy = entropy_from_fitness(row)
            outlier_score, anomaly_components = anomaly_score(row, city_stats[row["city"]])

            item = {
                **row,
                "top_two": top_two,
                "ranked_dims": ranked_dims,
                "signature_family": sig_family,
                "geo_cell": cell,
                "district_id": district_id,
                "state_energy": energy,
                "energy_band": energy_band(energy),
                "behavioral_entropy": entropy,
                "anomaly_score": outlier_score,
                "is_anomaly": outlier_score >= 3.25,
                "anomaly_components": anomaly_components,
                "feature_vector": feature_vector,
            }
            district_groups[district_id].append(item)
            enriched.append(item)

        district_centroids = {}
        district_summaries = []
        for district_id, members in district_groups.items():
            centroid = [
                round(sum(member["feature_vector"][idx] for member in members) / len(members), 4)
                for idx in range(len(FITNESS_KEYS))
            ]
            district_centroids[district_id] = centroid
            city = members[0]["city"]
            top_counter = Counter(label for member in members for label, _ in member["top_two"])

            lat_values = [float(m["lat"]) for m in members if m["lat"] is not None]
            lng_values = [float(m["lng"]) for m in members if m["lng"] is not None]

            district_summaries.append({
                "district_id": district_id,
                "source": SOURCE_KEY,
                "city": city,
                "geo_cell": members[0]["geo_cell"],
                "district_label": district_id,
                "behavioral_signature": [label for label, _ in members[0]["top_two"]],
                "venue_count": len(members),
                "avg_state_energy": round(sum(m["state_energy"] for m in members) / len(members), 4),
                "avg_behavioral_entropy": round(sum(m["behavioral_entropy"] for m in members) / len(members), 4),
                "centroid_lat": round(sum(lat_values) / len(lat_values), 6) if lat_values else None,
                "centroid_lng": round(sum(lng_values) / len(lng_values), 6) if lng_values else None,
                "top_dimensions": [
                    {"dimension": dim, "count": count}
                    for dim, count in top_counter.most_common(4)
                ],
            })

        venue_rows = []
        district_niche_values = defaultdict(list)
        for item in enriched:
            district_members = district_groups[item["district_id"]]
            centroid = district_centroids[item["district_id"]]
            avg_similarity = sum(
                cosine_similarity(item["feature_vector"], other["feature_vector"])
                for other in district_members
            ) / len(district_members)
            district_share = len(district_members) / city_counts[item["city"]]
            signature_share = signature_counts[(item["city"], item["signature_family"])] / city_counts[item["city"]]
            saturation = round(
                min(1.0, max(0.0, 0.45 * signature_share + 0.35 * district_share + 0.20 * avg_similarity)),
                4,
            )
            district_niche_values[item["district_id"]].append(saturation)

            details = {
                "city": item["city"],
                "area": item["area"],
                "geo_cell": item["geo_cell"],
                "district_share": round(district_share, 4),
                "signature_share": round(signature_share, 4),
                "district_avg_similarity": round(avg_similarity, 4),
                "anomaly_components": item["anomaly_components"],
            }
            top_dims_json = [
                {"dimension": dim, "score": score}
                for dim, score in item["ranked_dims"][:4]
            ]

            venue_rows.append((
                item["id"],
                SOURCE_KEY,
                item["district_id"],
                item["district_id"],
                item["state_energy"],
                item["energy_band"],
                item["anomaly_score"],
                item["is_anomaly"],
                item["behavioral_entropy"],
                saturation,
                len(district_members),
                item["signature_family"],
                round(avg_similarity, 4),
                psycopg2.extras.Json(top_dims_json),
                psycopg2.extras.Json(details),
                PIPELINE_VERSION,
                datetime.now(timezone.utc),
            ))

        district_rows = []
        for summary in district_summaries:
            details = {
                "district_share": round(summary["venue_count"] / city_counts[summary["city"]], 4),
                "pipeline_version": PIPELINE_VERSION,
            }
            district_rows.append((
                summary["district_id"],
                summary["source"],
                summary["city"],
                summary["geo_cell"],
                summary["district_label"],
                psycopg2.extras.Json(summary["behavioral_signature"]),
                summary["venue_count"],
                summary["avg_state_energy"],
                summary["avg_behavioral_entropy"],
                round(sum(district_niche_values[summary["district_id"]]) / len(district_niche_values[summary["district_id"]]), 4),
                summary["centroid_lat"],
                summary["centroid_lng"],
                psycopg2.extras.Json(summary["top_dimensions"]),
                psycopg2.extras.Json(details),
                PIPELINE_VERSION,
                datetime.now(timezone.utc),
            ))

        with conn.cursor() as cursor:
            psycopg2.extras.execute_values(cursor, UPSERT_DISTRICT_SQL, district_rows, page_size=200)
            psycopg2.extras.execute_values(cursor, UPSERT_VENUE_SQL, venue_rows, page_size=500)
        conn.commit()

        anomalies = sum(1 for row in venue_rows if row[7])
        print(
            f"  districts={len(district_rows):,}  venues={len(venue_rows):,}  "
            f"anomalies={anomalies:,}"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()
