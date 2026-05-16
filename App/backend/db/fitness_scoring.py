"""
db/fitness_scoring.py
DB-backed fitness dimension scoring using trait_fitness_weights.

Replaces the hardcoded FITNESS_SIGNAL_MAP keyword approach with weighted
behavioral signal scores sourced from the behavioral research DB.

Usage (in a scoring pipeline / batch job):
    from db.fitness_scoring import load_weights, score_venue_fitness

    weights = await load_weights(conn)
    scores  = score_venue_fitness(extracted_signals, weights)
    # → {"fitness_for_social_dwell": 0.72, "fitness_for_repeat_habit": 0.61, ...}

Extracted signals dict maps trait_key → signal_strength (0.0–1.0).
Signal strength is derived from review text:
    e.g. "crowd_density_signal" = count of social proof terms / total review sentences
         "habit_signal"         = count of repeat/regular language / total sentences
"""

from __future__ import annotations

import asyncpg
from collections import defaultdict


FitnessWeights = dict[str, dict[str, float]]  # {trait_key: {fitness_dim: weight}}


async def load_weights(conn: asyncpg.Connection) -> FitnessWeights:
    """Load all trait→fitness weights from DB into an in-memory dict."""
    rows = await conn.fetch(
        "SELECT trait_key, fitness_dimension, weight FROM trait_fitness_weights"
    )
    weights: FitnessWeights = defaultdict(dict)
    for r in rows:
        weights[r["trait_key"]][r["fitness_dimension"]] = float(r["weight"])
    return dict(weights)


def score_venue_fitness(
    signals: dict[str, float],
    weights: FitnessWeights,
) -> dict[str, float]:
    """
    Compute fitness dimension scores from extracted behavioral signals.

    Args:
        signals: {trait_key: signal_strength (0.0–1.0)}
                 Signal strength is the normalised prevalence of that behavioral
                 trait in this venue's review corpus.
        weights: loaded from load_weights() — {trait_key: {fitness_dim: weight}}

    Returns:
        {fitness_dimension: score (0.0–1.0)} — clipped to [0, 1]

    Signal keys (match trait_fitness_weights.trait_key):
        crowd_density_signal     → social proof in reviews ("packed", "full", "crowded")
        group_energy_signal      → group atmosphere mentions
        fomo_signal              → FOMO/scarcity language ("worth the wait", "finally got in")
        identity_signal          → identity/status language ("vibe", "crowd", "felt I belonged")
        habit_signal             → repeat/regular language ("my regular", "always come here")
        consistency_signal       → reliability/consistency mentions
        proximity_signal         → office/work proximity mentions
        familiarity_signal       → staff recognition / "usual" mentions
        ambiance_signal          → atmosphere/ambiance mentions
        service_signal           → service quality mentions
        value_signal             → value/pricing mentions
        loyalty_signal           → explicit loyalty statements
        music_energy_signal      → music/BPM/atmosphere energy mentions
        quick_service_signal     → speed of service mentions
        social_proof_signal      → broader social proof (incl. reviews, ratings)
        quality_signal           → explicit quality endorsements
        scarcity_signal          → limited availability / exclusivity mentions
    """
    dim_scores: dict[str, float] = defaultdict(float)
    dim_weights: dict[str, float] = defaultdict(float)

    for trait_key, signal_strength in signals.items():
        if trait_key not in weights:
            continue
        for dim, weight in weights[trait_key].items():
            dim_scores[dim]   += signal_strength * weight
            dim_weights[dim]  += abs(weight)

    result: dict[str, float] = {}
    for dim in dim_scores:
        w = dim_weights[dim]
        result[dim] = min(1.0, max(0.0, dim_scores[dim] / w if w > 0 else 0.0))

    return result


# ─── Keyword extractor (replaces hardcoded FITNESS_SIGNAL_MAP) ───────────────
#
# Maps surface-level review keywords → trait_key signals.
# This is a lightweight NLP layer sitting ABOVE the trait_fitness_weights table.
# The table handles trait → fitness dimension; this handles text → trait.

_KEYWORD_TRAIT_MAP: dict[str, list[str]] = {
    # Social proof / crowd density
    "packed":            ["crowd_density_signal", "social_proof_signal"],
    "full":              ["crowd_density_signal"],
    "crowded":           ["crowd_density_signal", "social_proof_signal"],
    "busy":              ["crowd_density_signal"],
    "buzzing":           ["crowd_density_signal", "group_energy_signal"],
    "lively":            ["group_energy_signal", "social_proof_signal"],

    # FOMO / scarcity
    "worth the wait":    ["fomo_signal"],
    "finally got":       ["fomo_signal"],
    "booked out":        ["fomo_signal", "scarcity_signal"],
    "sold out":          ["scarcity_signal"],
    "exclusive":         ["scarcity_signal", "identity_signal"],
    "limited":           ["scarcity_signal"],

    # Identity / status
    "vibe":              ["identity_signal"],
    "ambiance":          ["ambiance_signal", "identity_signal"],
    "atmosphere":        ["ambiance_signal"],
    "feel":              ["ambiance_signal"],
    "felt at home":      ["identity_signal", "familiarity_signal"],
    "belonged":          ["identity_signal"],
    "instagram":         ["identity_signal", "social_proof_signal"],
    "aesthetic":         ["identity_signal"],

    # Habit / repeat
    "regular":           ["habit_signal", "loyalty_signal"],
    "regular spot":      ["habit_signal", "loyalty_signal"],
    "always come":       ["habit_signal"],
    "come back":         ["habit_signal", "consistency_signal"],
    "weekly":            ["habit_signal"],
    "every week":        ["habit_signal"],
    "my usual":          ["habit_signal", "familiarity_signal"],

    # Familiarity / staff recognition
    "by name":           ["familiarity_signal"],
    "remembered":        ["familiarity_signal"],
    "knows us":          ["familiarity_signal"],
    "staff":             ["service_signal"],

    # Service quality
    "service":           ["service_signal", "operational_quality_signal"],
    "quick":             ["quick_service_signal"],
    "fast":              ["quick_service_signal"],
    "efficient":         ["quick_service_signal"],
    "slow":              ["service_signal"],  # negative — weight in scoring handles direction

    # Consistency / reliability
    "consistent":        ["consistency_signal"],
    "never disappoints": ["consistency_signal", "loyalty_signal"],
    "reliable":          ["consistency_signal"],
    "never miss":        ["consistency_signal"],

    # Quality signals
    "best":              ["quality_signal"],
    "excellent":         ["quality_signal"],
    "highly recommend":  ["quality_signal", "social_proof_signal"],
    "worth the trip":    ["quality_signal", "scarcity_signal"],
    "destination":       ["quality_signal"],

    # Value / price
    "value":             ["value_signal"],
    "affordable":        ["value_signal"],
    "worth the price":   ["value_signal", "quality_signal"],
    "expensive":         ["value_signal"],  # direction handled by weights

    # Group / social
    "group":             ["group_energy_signal"],
    "friends":           ["group_energy_signal", "social_proof_signal"],
    "team":              ["group_energy_signal"],
    "birthday":          ["group_energy_signal", "fomo_signal"],

    # Proximity / office
    "near office":       ["proximity_signal"],
    "office lunch":      ["proximity_signal", "quick_service_signal"],
    "nearby":            ["proximity_signal"],
    "walking distance":  ["proximity_signal"],

    # Music / energy environment
    "music":             ["music_energy_signal", "ambiance_signal"],
    "dj":                ["music_energy_signal", "group_energy_signal"],
    "loud":              ["music_energy_signal"],
    "quiet":             ["ambiance_signal"],
    "romantic":          ["ambiance_signal"],
    "cozy":              ["ambiance_signal"],
}


def extract_signals_from_text(review_text: str) -> dict[str, float]:
    """
    Extract behavioral signal strengths from raw review text.

    Returns {trait_key: signal_strength (0.0–1.0)} where signal_strength
    is the normalised hit rate for that trait across the text.

    This is a simple keyword-counting approach. Replace with an embeddings
    or LLM-based extractor when review volume justifies it.
    """
    text_lower = review_text.lower()
    sentences  = [s.strip() for s in text_lower.replace(".", ".\n").split("\n") if s.strip()]
    total      = max(len(sentences), 1)

    trait_hits: dict[str, int] = defaultdict(int)

    for sentence in sentences:
        for keyword, traits in _KEYWORD_TRAIT_MAP.items():
            if keyword in sentence:
                for trait in traits:
                    trait_hits[trait] += 1

    return {
        trait: min(1.0, hits / total)
        for trait, hits in trait_hits.items()
    }


async def score_venue_from_reviews(
    venue_id: int,
    review_texts: list[str],
    conn: asyncpg.Connection,
    weights: FitnessWeights | None = None,
) -> dict[str, float]:
    """
    Full pipeline: review texts → extracted signals → fitness scores.

    Args:
        venue_id:     venue identifier (for logging)
        review_texts: list of raw review strings
        conn:         asyncpg connection
        weights:      pre-loaded weights dict (pass to avoid re-fetching per venue)

    Returns:
        {fitness_dimension: score} — ready to upsert into venue_fitness_dimensions
    """
    if weights is None:
        weights = await load_weights(conn)

    combined_text = " ".join(review_texts)
    signals = extract_signals_from_text(combined_text)
    return score_venue_fitness(signals, weights)
