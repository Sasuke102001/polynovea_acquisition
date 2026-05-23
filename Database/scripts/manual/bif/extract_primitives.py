"""
extract_primitives.py
Extracts behavioral primitive signals from manual venue reviews using NVIDIA LLM.
Equivalent to step_3_signals_extraction.py for MagicPin — populates primitives_scores.

Input:  raw_venue_data (platform='manual_reviews', data_type='review_batch')
Output: primitives_scores (source='manual_reviews')

Usage:
    python extract_primitives.py --venue-id 12066
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

# Canonical signal vocabulary — must match what is already in primitives_scores
SIGNAL_VOCAB = [
    "food_quality", "pride", "staff_warmth", "service_quality", "social_energy",
    "comfort", "long_dwell", "experience_memories", "excitement", "crowding",
    "authentic_taste", "satisfaction", "nostalgia", "disappointment", "wonder_ambience",
    "great_view", "live_music", "relief", "social_company", "social_sharing",
    "health_conscious", "premium_price", "premium_acceptance", "quick_meal",
    "scenic_value", "service_failure", "price_resistance", "wait_time",
    "fast_service", "repeat_visit_intent", "office_crowd", "convenient_location",
    "group_spend_amplification", "space_compression", "destination_driven_retention",
    "noise_overload", "crowding_rejection", "social_dwell_amplification",
    "willingness_to_wait", "women_friendly",
]

_EXTRACTION_SYSTEM = """You are a behavioral signal extractor for F&B venue intelligence.
Given a set of customer reviews, identify which behavioral signals are present and assign a confidence score (0.0–1.0) to each.

Rules:
- Only use signal IDs from the provided vocabulary list. No other signal names.
- Confidence = how strongly and consistently the signal appears across reviews.
  0.8–1.0: multiple strong explicit mentions
  0.5–0.7: moderate evidence, mentioned 2–3 times
  0.2–0.4: weak or implied signal, single mention
  0.0: absent — do not include
- Negative signals (disappointment, service_failure, price_resistance, wait_time, etc.)
  should be included when clearly present — they are valid behavioral data.
- Return ONLY a JSON object: {"signal_id": confidence_score, ...}
- No explanation, no markdown, no extra text."""


def _build_prompt(venue_name: str, reviews: list[dict]) -> str:
    review_text = "\n".join(
        f"[{r.get('rating', '?')}★] {r.get('text', '').strip()}"
        for r in reviews
    )
    vocab_str = ", ".join(SIGNAL_VOCAB)
    return f"""Venue: {venue_name}

SIGNAL VOCABULARY (use only these IDs):
{vocab_str}

REVIEWS:
{review_text}

Extract behavioral signals as JSON {{signal_id: confidence}}:"""


def _call_nvidia(prompt: str) -> dict[str, float]:
    api_key = os.getenv("NVIDIA_API_KEY", "")
    if not api_key:
        print("  WARNING: NVIDIA_API_KEY not set — using heuristic fallback")
        return {}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model":       NVIDIA_MODEL,
        "messages":    [
            {"role": "system",  "content": _EXTRACTION_SYSTEM},
            {"role": "user",    "content": prompt},
        ],
        "temperature": 0.1,
        "max_tokens":  512,
    }

    for attempt in range(3):
        try:
            resp = httpx.post(NVIDIA_API_BASE, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()

            # Extract JSON block
            match = re.search(r'\{[\s\S]*\}', content)
            if not match:
                print(f"  WARNING: No JSON found in response: {content[:200]}")
                return {}

            parsed = json.loads(match.group())
            # Validate — keep only known signals with valid scores
            return {
                k: min(max(float(v), 0.0), 1.0)
                for k, v in parsed.items()
                if k in SIGNAL_VOCAB and v > 0
            }

        except Exception as exc:
            print(f"  Attempt {attempt + 1} failed: {exc}")
            if attempt < 2:
                time.sleep(2)

    return {}


def _heuristic_fallback(reviews: list[dict]) -> dict[str, float]:
    """
    Rule-based signal detection when NVIDIA is unavailable.
    Scans review text for keyword patterns.
    """
    text_all = " ".join(r.get("text", "").lower() for r in reviews)
    ratings  = [r.get("rating", 3) for r in reviews]
    avg_rating = sum(ratings) / len(ratings) if ratings else 3.0

    signals: dict[str, float] = {}

    keyword_map = {
        "food_quality":        ["food", "dish", "taste", "delicious", "good food", "amazing food"],
        "wonder_ambience":     ["ambience", "atmosphere", "vibe", "aesthetic", "serene", "calm", "cozy"],
        "comfort":             ["comfortable", "cozy", "peaceful", "quiet", "relaxed"],
        "long_dwell":          ["hours", "study session", "lingered", "sat for", "spent time"],
        "staff_warmth":        ["staff", "friendly", "helpful", "attentive", "warm", "polite"],
        "health_conscious":    ["healthy", "health-forward", "vegan", "organic", "clean eating"],
        "social_sharing":      ["instagram", "aesthetic", "photo", "worth posting"],
        "repeat_visit_intent": ["will return", "will visit again", "repeat visitor", "definitely back"],
        "price_resistance":    ["overpriced", "expensive", "not worth", "too costly", "value"],
        "service_failure":     ["mix-up", "wrong order", "mistake", "manager", "not apologise"],
        "disappointment":      ["disappointing", "avoid", "don't visit", "terrible", "worst"],
        "wait_time":           ["waiting", "wait", "slow service", "took long", "30 min"],
        "service_quality":     ["service", "quick", "efficient", "professional"],
        "satisfaction":        ["satisfied", "happy", "great experience", "loved it"],
        "convenient_location": ["location", "near", "accessible", "close to", "r city"],
    }

    for signal, keywords in keyword_map.items():
        hits = sum(1 for kw in keywords if kw in text_all)
        if hits > 0:
            conf = min(0.3 + (hits * 0.1), 0.8)
            signals[signal] = round(conf, 2)

    # Adjust for avg rating
    if avg_rating < 3.0:
        signals["disappointment"] = max(signals.get("disappointment", 0), 0.6)
    elif avg_rating > 4.0:
        signals["satisfaction"] = max(signals.get("satisfaction", 0), 0.6)

    return signals


def run(venue_id: int) -> dict[str, float]:
    # ── Load reviews from raw_venue_data ──────────────────────────────────────
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute("SELECT name FROM venues WHERE id = %s", (venue_id,))
        v = cur.fetchone()
        venue_name = v["name"] if v else f"venue_{venue_id}"

        cur.execute(
            """
            SELECT raw_payload FROM raw_venue_data
            WHERE venue_id = %s AND platform = 'manual_reviews' AND data_type = 'review_batch'
            ORDER BY collected_at DESC LIMIT 1
            """,
            (venue_id,),
        )
        row = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if not row:
        print(f"  No review_batch found in raw_venue_data for venue_id={venue_id}")
        print(f"  Ensure manual_reviews_*.py was run first to load reviews into the DB")
        return {}

    payload = row["raw_payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)

    reviews = payload.get("reviews", [])
    print(f"  Loaded {len(reviews)} reviews for {venue_name}")

    # ── Extract signals ───────────────────────────────────────────────────────
    api_key = os.getenv("NVIDIA_API_KEY", "")
    if api_key:
        print(f"  Calling NVIDIA ({NVIDIA_MODEL}) for signal extraction...")
        signals = _call_nvidia(_build_prompt(venue_name, reviews))
        if not signals:
            print("  AI extraction returned empty — falling back to heuristics")
            signals = _heuristic_fallback(reviews)
    else:
        print("  No NVIDIA_API_KEY — using heuristic fallback")
        signals = _heuristic_fallback(reviews)

    if not signals:
        print("  No signals extracted — skipping primitives_scores insert")
        return {}

    print(f"  Extracted {len(signals)} signals: {dict(list(signals.items())[:5])}...")

    # ── Insert into primitives_scores ─────────────────────────────────────────
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()
    try:
        rows = [(venue_id, SOURCE, sig, score, score) for sig, score in signals.items()]
        psycopg2.extras.execute_values(
            cur,
            """
            INSERT INTO primitives_scores
                (venue_id, source, primitive_id, score, confidence)
            VALUES %s
            ON CONFLICT (venue_id, source, primitive_id) DO UPDATE SET
                score        = EXCLUDED.score,
                confidence   = EXCLUDED.confidence,
                last_updated = CURRENT_TIMESTAMP
            """,
            rows,
        )
        conn.commit()
        print(f"  Inserted {len(rows)} primitive signal rows into primitives_scores")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

    return signals


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract behavioral primitives from manual venue reviews")
    parser.add_argument('--venue-id', type=int, required=True)
    args = parser.parse_args()
    run(args.venue_id)
