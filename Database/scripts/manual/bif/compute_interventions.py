"""
compute_interventions.py
Generates intervention_triggers for a manually added venue using NVIDIA LLM.
Equivalent to the intervention section of step_6_fitness_and_interventions.py.

Reads:  primitives_scores + venue_fitness_dimensions from DB
Writes: intervention_triggers (source='manual_reviews')

Usage:
    python compute_interventions.py --venue-id 12066
"""

import argparse
import json
import os
import re
import sys
import time

import psycopg2
import psycopg2.extras
import httpx

sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    'host':     os.getenv('PG_HOST',     'polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com'),
    'port':     int(os.getenv('PG_PORT', 5432)),
    'dbname':   os.getenv('PG_DB',       'polynovea_module2'),
    'user':     os.getenv('PG_USER',     'polynovea_admin'),
    'password': os.getenv('PG_PASSWORD', '07586277012Luna'),
    'sslmode':  'require',
}

NVIDIA_API_BASE = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL    = os.getenv("NVIDIA_MODEL_NEMOTRON", "meta/llama-3.3-70b-instruct")
SOURCE          = "manual_reviews"

# Known intervention types matching the pipeline
INTERVENTION_TYPES = [
    "operational_optimization",
    "premium_justification",
    "dwell_monetization",
    "friction_reduction",
    "authenticity_leverage",
    "social_amplification",
    "segment_capture",
    "loyalty_deepening",
    "menu_engineering",
    "staff_development",
]

_INTERVENTION_SYSTEM = """You are a venue intelligence analyst. Given a venue's behavioral signals and fitness scores,
identify the most impactful operational intervention opportunities.

Return a JSON array of intervention objects. Each object must have:
  "intervention_type": one of the provided types
  "description": 1 sentence — specific, actionable, references actual signals
  "fit_score": float 0.0–1.0 — how strong a fit this intervention is for this venue
  "priority_tier": "PRIORITY" | "EXPLORE" | "MONITOR"
  "recommended": true if fit_score >= 0.6
  "matched_signals": array of signal IDs that support this intervention
  "missing_signals": array of signal IDs that would strengthen this intervention if present

Return ONLY the JSON array. No markdown, no explanation."""


def _build_intervention_prompt(
    venue_name: str,
    fitness: dict,
    signals: list[tuple],
) -> str:
    signals_str = "\n".join(f"  {sig}: {conf:.2f}" for sig, conf in signals[:15])
    fitness_str = "\n".join(f"  {k}: {v:.2f}" for k, v in fitness.items())
    types_str   = ", ".join(INTERVENTION_TYPES)

    return f"""Venue: {venue_name}

FITNESS DIMENSIONS:
{fitness_str}

BEHAVIORAL SIGNALS (signal_id: confidence):
{signals_str}

INTERVENTION TYPES (use only these):
{types_str}

Generate intervention opportunities as a JSON array:"""


def _call_nvidia(prompt: str) -> list[dict]:
    api_key = os.getenv("NVIDIA_API_KEY", "")
    if not api_key:
        return []

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model":       NVIDIA_MODEL,
        "messages":    [
            {"role": "system", "content": _INTERVENTION_SYSTEM},
            {"role": "user",   "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens":  1024,
    }

    for attempt in range(3):
        try:
            resp = httpx.post(NVIDIA_API_BASE, json=payload, headers=headers, timeout=45)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()

            match = re.search(r'\[[\s\S]*\]', content)
            if not match:
                print(f"  WARNING: No JSON array in response: {content[:200]}")
                return []

            parsed = json.loads(match.group())
            if not isinstance(parsed, list):
                return []

            # Validate each entry
            valid = []
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                itype = item.get("intervention_type", "")
                if itype not in INTERVENTION_TYPES:
                    continue
                valid.append({
                    "intervention_type":   itype,
                    "description":         str(item.get("description", "")),
                    "fit_score":           min(max(float(item.get("fit_score", 0.0)), 0.0), 1.0),
                    "priority_tier":       item.get("priority_tier", "EXPLORE"),
                    "recommended":         bool(item.get("recommended", False)),
                    "matched_signals":     list(item.get("matched_signals", [])),
                    "missing_signals":     list(item.get("missing_signals", [])),
                })
            return valid

        except Exception as exc:
            print(f"  Attempt {attempt + 1} failed: {exc}")
            if attempt < 2:
                time.sleep(2)

    return []


def _heuristic_interventions(fitness: dict, signals: list[tuple]) -> list[dict]:
    """Rule-based fallback when NVIDIA is unavailable."""
    signal_ids = {s for s, _ in signals}
    result = []

    if "long_dwell" in signal_ids or fitness.get("fitness_for_social_dwell", 0) > 0.5:
        result.append({
            "intervention_type": "dwell_monetization",
            "description":       "Strong social dwell — introduce time-based upsells and multi-round ordering incentives",
            "fit_score":         0.65,
            "priority_tier":     "PRIORITY",
            "recommended":       True,
            "matched_signals":   ["long_dwell", "comfort"],
            "missing_signals":   ["group_spend_amplification"],
        })

    if "service_failure" in signal_ids or "disappointment" in signal_ids:
        result.append({
            "intervention_type": "friction_reduction",
            "description":       "Documented service failures (order mix-ups, hygiene) are actively churning customers — ops fix required before any growth investment",
            "fit_score":         0.90,
            "priority_tier":     "PRIORITY",
            "recommended":       True,
            "matched_signals":   ["service_failure", "disappointment"],
            "missing_signals":   ["service_quality", "staff_warmth"],
        })

    if "wonder_ambience" in signal_ids or "social_sharing" in signal_ids:
        result.append({
            "intervention_type": "social_amplification",
            "description":       "Aesthetic ambience drives organic sharing — invest in visual content and UGC campaigns",
            "fit_score":         0.55,
            "priority_tier":     "EXPLORE",
            "recommended":       False,
            "matched_signals":   ["wonder_ambience", "social_sharing"],
            "missing_signals":   ["excitement"],
        })

    if "health_conscious" in signal_ids:
        result.append({
            "intervention_type": "segment_capture",
            "description":       "Health-forward positioning appeals to a specific segment — deepen menu differentiation to own the niche",
            "fit_score":         0.60,
            "priority_tier":     "EXPLORE",
            "recommended":       True,
            "matched_signals":   ["health_conscious"],
            "missing_signals":   ["premium_acceptance"],
        })

    return result


def run(venue_id: int) -> None:
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # Fetch venue name
        cur.execute("SELECT name FROM venues WHERE id = %s", (venue_id,))
        venue_row = cur.fetchone()
        if not venue_row:
            print(f"  Venue {venue_id} not found")
            return
        venue_name = venue_row["name"]

        # Fetch fitness dimensions
        cur.execute(
            """
            SELECT fitness_for_office_lunch, fitness_for_repeat_habit,
                   fitness_for_social_dwell, fitness_for_group_energy,
                   fitness_for_destination_visit, operational_quality,
                   retention_strength, monetization_potential
            FROM venue_fitness_dimensions
            WHERE venue_id = %s
            ORDER BY CASE source WHEN 'blended' THEN 0 WHEN 'manual_reviews' THEN 1 ELSE 2 END
            LIMIT 1
            """,
            (venue_id,),
        )
        fit_row = cur.fetchone()
        if not fit_row:
            print(f"  No fitness data for venue_id={venue_id} — skipping interventions")
            return
        fitness = {k: float(v or 0.0) for k, v in fit_row.items()}

        # Fetch signals
        cur.execute(
            """
            SELECT primitive_id, MAX(confidence) AS confidence
            FROM primitives_scores WHERE venue_id = %s
            GROUP BY primitive_id ORDER BY confidence DESC LIMIT 20
            """,
            (venue_id,),
        )
        signals = [(r["primitive_id"], float(r["confidence"])) for r in cur.fetchall()]
        print(f"  Found {len(signals)} signals for {venue_name}")

        # Generate interventions
        api_key = os.getenv("NVIDIA_API_KEY", "")
        if api_key and signals:
            print(f"  Calling NVIDIA for intervention generation...")
            interventions = _call_nvidia(_build_intervention_prompt(venue_name, fitness, signals))
            if not interventions:
                print("  AI returned empty — using heuristic fallback")
                interventions = _heuristic_interventions(fitness, signals)
        else:
            print("  Using heuristic intervention fallback")
            interventions = _heuristic_interventions(fitness, signals)

        if not interventions:
            print("  No interventions generated")
            return

        # Insert into intervention_triggers
        for item in interventions:
            matched_count = f"{len(item['matched_signals'])}/{len(item['matched_signals']) + len(item['missing_signals'])}"
            cur.execute(
                """
                INSERT INTO intervention_triggers
                    (venue_id, source, intervention_type, description, fit_score,
                     priority_tier, recommended, matched_signals, missing_signals,
                     matched_signal_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (venue_id, source, intervention_type) DO UPDATE SET
                    description          = EXCLUDED.description,
                    fit_score            = EXCLUDED.fit_score,
                    priority_tier        = EXCLUDED.priority_tier,
                    recommended          = EXCLUDED.recommended,
                    matched_signals      = EXCLUDED.matched_signals,
                    missing_signals      = EXCLUDED.missing_signals,
                    matched_signal_count = EXCLUDED.matched_signal_count
                """,
                (
                    venue_id, SOURCE,
                    item["intervention_type"], item["description"],
                    item["fit_score"], item["priority_tier"], item["recommended"],
                    json.dumps(item["matched_signals"]),
                    json.dumps(item["missing_signals"]),
                    matched_count,
                ),
            )

        conn.commit()
        print(f"  Inserted {len(interventions)} intervention triggers")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate intervention triggers for a manual venue")
    parser.add_argument('--venue-id', type=int, required=True)
    args = parser.parse_args()
    run(args.venue_id)
