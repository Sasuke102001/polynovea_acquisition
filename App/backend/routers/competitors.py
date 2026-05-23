"""
routers/competitors.py
GET /api/venues/{venue_id}/similar  →  CompetitorsResponse  (Screen 2 — Competitors Tab)

Matching  — multi-type intersection waterfall (Tversky-inspired):
  Bucket A: competitor shares ALL of client's non-generic cascade types
  Bucket B: competitor shares 2+ (but not all) cascade types
  Bucket C: competitor shares exactly 1 cascade type
  Bucket D: segment fallback (same demographic segment, no type overlap)
  Buckets filled in order A→D, capped at _MAX_POOL=40.

Sorting (within each bucket) — two views:
  threat    (default): weighted cosine similarity × geography multiplier DESC
                       "who competes for the same behavioral demand pocket"
  benchmark          : composite fitness excellence score DESC
                       "who is winning this category"

Weighted cosine uses softmax-normalised weights derived from the client's own
fitness scores (α=2). This preserves emphasis on the client's strong dimensions
without collapsing matching into single-axis dominance (ChatGPT / Kimi concern).

Geography multipliers (ChatGPT / Kimi / Perplexity consensus — substantial, not cosmetic):
  same area            → ×1.00  (direct market overlap)
  same city            → ×0.70
  adjacent city        → ×0.40
  different city       → ×0.15

Deltas: computed on-the-fly from venue_fitness_dimensions + fitness_delta_rules.
"""

import json as _json
import math
import os
import re as _re

from fastapi import APIRouter, HTTPException, Path, Query

from database import get_pool
from models import (
    CompetitorsResponse, ClientVenueCard, SimilarVenueCard, FitnessDimension, DeltaBar,
    CompetitorDeepDive, CompetitorInsight,
)
from prompts import build_competitor_analysis_prompt
from routers.utils import (
    map_venue_types, make_archetype_chip,
    DIM_LABELS, ALL_DIMS,
    SEGMENT_LABELS, SEGMENT_TOP_ARCHETYPES,
)

# Nvidia API config — mirrors chat.py
_NVIDIA_API_BASE = "https://integrate.api.nvidia.com/v1"
_NVIDIA_API_KEY  = os.getenv("NVIDIA_API_KEY_CREATIVE")
_NVIDIA_MODEL    = os.getenv(
    "NVIDIA_MODEL_CREATIVE", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
)

_BUCKET_LABELS: dict[int, str] = {
    0: "Direct Peer",
    1: "Close Match",
    2: "Partial Match",
    3: "Segment Match",
}

router = APIRouter()

# ─── Type helpers ─────────────────────────────────────────────────────────────

_GENERIC_TYPES: frozenset[str] = frozenset({
    "food", "point_of_interest", "establishment",
    "store", "premise", "locality", "political",
    "street_address", "geocode",
    # Too broad for competitive matching — almost every F&B venue has these
    "restaurant", "bar", "cafe",
})

# Hard cap on the total competitor pool returned
_MAX_POOL = 40


def _venue_type_cascade(types: list[str]) -> list[str]:
    """
    Return up to 3 non-generic Google Places types in Google's original order.
    These are tried in sequence as the matching key for competitor selection.
    """
    result = []
    for t in (types or []):
        if t not in _GENERIC_TYPES:
            result.append(t)
            if len(result) == 3:
                break
    return result


# ─── Delta rule helpers ───────────────────────────────────────────────────────

def _lookup_rule(rules_by_dim: dict[str, list], dim: str, delta: float) -> dict:
    """Find the matching fitness_delta_rules entry for (dimension, delta value)."""
    for rule in rules_by_dim.get(dim, []):
        if float(rule["delta_min"]) <= delta <= float(rule["delta_max"]):
            return {
                "direction":        rule["direction"],
                "short_label":      rule["short_label"],
                "client_statement": rule["client_statement"],
            }
    return {
        "direction":        "neutral",
        "short_label":      "Equal",
        "client_statement": "Similar performance to your venue",
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _float(v) -> float:
    return float(v) if v is not None else 0.0


async def _load_delta_rules(conn) -> dict[str, list]:
    """Load all 56 fitness delta rules into memory, grouped by dimension."""
    rows = await conn.fetch(
        """
        SELECT dimension, delta_min, delta_max, direction, short_label, client_statement
        FROM   fitness_delta_rules
        ORDER  BY dimension, delta_min DESC
        """
    )
    rules: dict[str, list] = {}
    for r in rows:
        rules.setdefault(r["dimension"], []).append(dict(r))
    return rules


async def _fetch_client(conn, venue_id: int) -> ClientVenueCard:
    """Fetch full client venue card with fitness scores + archetypes + segments."""
    row = await conn.fetchrow(
        "SELECT id, name, area, city, types FROM venues WHERE id = $1",
        venue_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Venue not found")

    fd = await conn.fetchrow(
        """
        SELECT
            fitness_for_office_lunch,  fitness_for_repeat_habit,
            fitness_for_social_dwell,  fitness_for_group_energy,
            fitness_for_destination_visit, operational_quality,
            retention_strength
        FROM venue_fitness_dimensions WHERE venue_id = $1 AND source = 'blended'
        """,
        venue_id,
    )

    seg_rows = await conn.fetch(
        """
        SELECT segment_id FROM venue_demographic_scores
        WHERE venue_id = $1 ORDER BY segment_rank LIMIT 3
        """,
        venue_id,
    )
    top_seg_names = [
        SEGMENT_LABELS.get(r["segment_id"], {}).get("label", r["segment_id"])
        for r in seg_rows
    ]
    primary_seg = seg_rows[0]["segment_id"] if seg_rows else "office_workers"
    arc_names   = SEGMENT_TOP_ARCHETYPES.get(primary_seg, [])

    fitness_scores = [
        FitnessDimension(key=dim, label=DIM_LABELS[dim], score=_float(fd[dim]) if fd else 0.0)
        for dim in ALL_DIMS
    ]

    return ClientVenueCard(
        id=row["id"],
        name=row["name"],
        area=row["area"],
        city=row["city"],
        types=map_venue_types(list(row["types"] or [])),
        top_archetypes=[make_archetype_chip(n) for n in arc_names],
        top_segments=top_seg_names,
        fitness_scores=fitness_scores,
    )


# ─── Geography helpers ────────────────────────────────────────────────────────

# Mumbai MMR adjacency map — cities that share meaningful consumer catchment
_ADJACENT_CITIES: dict[str, frozenset] = {
    "Mumbai":           frozenset({"Navi Mumbai", "Thane", "Kalyan", "Mira Road",
                                   "Mira-Bhayandar", "Vasai", "Virar", "Dombivli"}),
    "Navi Mumbai":      frozenset({"Mumbai", "Thane", "Panvel", "Belapur"}),
    "Thane":            frozenset({"Mumbai", "Navi Mumbai", "Kalyan", "Mira Road",
                                   "Mira-Bhayandar", "Dombivli"}),
    "Kalyan":           frozenset({"Thane", "Mumbai", "Navi Mumbai", "Dombivli",
                                   "Ulhasnagar"}),
    "Mira Road":        frozenset({"Mumbai", "Thane", "Mira-Bhayandar"}),
    "Mira-Bhayandar":   frozenset({"Mumbai", "Thane", "Mira Road"}),
    "Pune":             frozenset({"Pimpri-Chinchwad", "Pimpri", "Chinchwad"}),
    "Pimpri-Chinchwad": frozenset({"Pune", "Pimpri", "Chinchwad"}),
}


def _geo_multiplier(client_area: str, client_city: str,
                    comp_area: str,   comp_city: str) -> float:
    """
    Geography relevance multiplier. Substantial weights per consensus:
      same micro-area  → 1.00  (direct market overlap — full weight)
      same city        → 0.70  (shared catchment, different neighbourhood)
      adjacent city    → 0.40  (MMR spillover, some market overlap)
      different market → 0.15  (aspirational benchmark only)
    """
    cc = (client_city or "").strip()
    xc = (comp_city   or "").strip()
    ca = (client_area or "").strip().lower()
    xa = (comp_area   or "").strip().lower()

    if cc and xc and cc.lower() == xc.lower():
        return 1.0 if (ca and xa and ca == xa) else 0.70

    adj = _ADJACENT_CITIES.get(cc, frozenset())
    return 0.40 if xc in adj else 0.15


# ─── Similarity helpers ───────────────────────────────────────────────────────

def _softmax_weights(fd, dims: list[str], alpha: float = 2.0) -> dict[str, float]:
    """
    Softmax-normalised weights from the client's own fitness scores.
    alpha=2 preserves relative emphasis on strong dimensions without letting
    any single dimension dominate (ChatGPT recommendation — avoids weight
    concentration collapse from raw proportional share).
    """
    scores = [float(fd.get(d) or 0.0) if fd else 0.0 for d in dims]
    exps   = [math.exp(alpha * s) for s in scores]
    total  = sum(exps) or 1.0
    return {d: exps[i] / total for i, d in enumerate(dims)}


def _weighted_cosine(c_fd, s_fd, weights: dict[str, float], dims: list[str]) -> float:
    """
    Weighted cosine similarity between two fitness vectors.
    Answers: "do these venues succeed in the same behavioral ways?"
    Returns 0.0 if either vector is zero (no fitness data).
    """
    dot   = sum(weights[d] * _float(c_fd.get(d) if c_fd else 0)
                            * _float(s_fd.get(d) if s_fd else 0) for d in dims)
    mag_c = math.sqrt(sum(weights[d] * _float(c_fd.get(d) if c_fd else 0) ** 2 for d in dims))
    mag_s = math.sqrt(sum(weights[d] * _float(s_fd.get(d) if s_fd else 0) ** 2 for d in dims))
    if mag_c < 1e-9 or mag_s < 1e-9:
        return 0.0
    return round(dot / (mag_c * mag_s), 4)


def _composite_excellence(fd, dims: list[str]) -> float:
    """Average fitness score across all dimensions — sort key for Benchmark Ladder view."""
    if not fd:
        return 0.0
    return round(sum(_float(fd.get(d)) for d in dims) / len(dims), 4)


# ─── Bucket assignment ────────────────────────────────────────────────────────

def _assign_bucket(intersection_count: int, n_cascade: int) -> int:
    """
    Tversky-inspired bucket assignment. Client's types are the prototype;
    candidates are measured against them.
      0 = A  shares ALL client cascade types       (exact type peer)
      1 = B  shares 2+ but not all                 (close type cousin)
      2 = C  shares exactly 1 type                 (partial overlap)
      3 = D  segment fallback — no type overlap
    """
    if n_cascade > 0 and intersection_count >= n_cascade:
        return 0
    if intersection_count >= 2:
        return 1
    if intersection_count == 1:
        return 2
    return 3


# ─── Main competitor fetch ────────────────────────────────────────────────────

async def _fetch_similar_venues(
    conn,
    venue_id: int,
    limit: int,
    offset: int,
    view: str = "threat",
) -> tuple[list[SimilarVenueCard], int]:
    """
    Multi-type intersection matching + weighted cosine sorting.

    view="threat"    → sort by weighted cosine × geo multiplier DESC
                       (most similar behavioral fingerprint + closest market)
    view="benchmark" → sort by composite fitness excellence DESC within each bucket
                       (best performers in the matched category)
    """
    # ── Client venue (area + city for geography) ─────────────────────────────
    client_venue = await conn.fetchrow(
        "SELECT area, city, types FROM venues WHERE id = $1", venue_id
    )
    client_area  = client_venue["area"] or ""
    client_city  = client_venue["city"] or ""
    cascade_types = _venue_type_cascade(list(client_venue["types"] or []))
    n_cascade     = len(cascade_types)

    # ── Fitness delta rules ───────────────────────────────────────────────────
    rules_by_dim = await _load_delta_rules(conn)

    # ── Client fitness ────────────────────────────────────────────────────────
    client_fd = await conn.fetchrow(
        f"SELECT {', '.join(ALL_DIMS)} FROM venue_fitness_dimensions "
        f"WHERE venue_id = $1 AND source = 'blended'",
        venue_id,
    )

    # ── Step 1: Collect all candidates sharing any cascade type ──────────────
    # One query per cascade type; deduplicate in Python.
    all_candidates: dict[int, dict] = {}

    for type_key in cascade_types:
        rows = await conn.fetch(
            """
            SELECT v.id, v.types, v.area, v.city
            FROM   venues v
            WHERE  v.types @> jsonb_build_array($1::text)
              AND  v.id != $2
            LIMIT  300
            """,
            type_key, venue_id,
        )
        for r in rows:
            vid = r["id"]
            if vid not in all_candidates:
                all_candidates[vid] = {
                    "types": list(r["types"] or []),
                    "area":  r["area"] or "",
                    "city":  r["city"] or "",
                }

    # ── Step 2: Compute type intersection count → bucket ─────────────────────
    bucketed: dict[int, list[int]] = {0: [], 1: [], 2: [], 3: []}

    for vid, info in all_candidates.items():
        comp_cascade       = _venue_type_cascade(info["types"])
        intersection_count = sum(1 for t in cascade_types if t in comp_cascade)
        bucket             = _assign_bucket(intersection_count, n_cascade)
        info["bucket"]     = bucket
        bucketed[bucket].append(vid)

    # ── Step 3: Segment fallback (Bucket D) if pool is thin ──────────────────
    total_found = sum(len(v) for v in bucketed.values())
    if total_found < _MAX_POOL:
        primary_seg = await conn.fetchval(
            "SELECT segment_id FROM venue_demographic_scores "
            "WHERE venue_id = $1 ORDER BY segment_rank LIMIT 1",
            venue_id,
        )
        if primary_seg:
            exclude_ids = list(all_candidates.keys()) + [venue_id]
            seg_rows = await conn.fetch(
                """
                SELECT v.id, v.area, v.city, v.types
                FROM   venues v
                JOIN   venue_demographic_scores vds ON vds.venue_id = v.id
                WHERE  vds.segment_id   = $1
                  AND  vds.segment_rank = 1
                  AND  v.id != ALL($2::int[])
                ORDER  BY vds.alignment_score DESC
                LIMIT  $3
                """,
                primary_seg, exclude_ids, _MAX_POOL - total_found,
            )
            for r in seg_rows:
                vid = r["id"]
                all_candidates[vid] = {
                    "types":  list(r["types"] or []),
                    "area":   r["area"] or "",
                    "city":   r["city"] or "",
                    "bucket": 3,
                }
                bucketed[3].append(vid)

    if not all_candidates:
        return [], 0

    # ── Step 4: Fetch fitness for all candidates ──────────────────────────────
    all_ids = list(all_candidates.keys())
    sim_fd_rows = await conn.fetch(
        f"SELECT venue_id, {', '.join(ALL_DIMS)} FROM venue_fitness_dimensions "
        f"WHERE venue_id = ANY($1::int[]) AND source = 'blended'",
        all_ids,
    )
    sim_fd_map = {r["venue_id"]: r for r in sim_fd_rows}

    # ── Step 5: Score each candidate ─────────────────────────────────────────
    weights = _softmax_weights(client_fd, ALL_DIMS, alpha=2.0)

    for vid, info in all_candidates.items():
        sim_fd = sim_fd_map.get(vid)
        cos    = _weighted_cosine(client_fd, sim_fd, weights, ALL_DIMS)
        geo    = _geo_multiplier(client_area, client_city, info["area"], info["city"])
        info["threat_score"]    = round(cos * geo, 4)
        info["benchmark_score"] = _composite_excellence(sim_fd, ALL_DIMS)

    # ── Step 6: Sort within each bucket, concatenate A→D ─────────────────────
    def _sort_key(vid: int) -> float:
        info = all_candidates[vid]
        return info["benchmark_score"] if view == "benchmark" else info["threat_score"]

    ordered_ids: list[int] = []
    for bucket in range(4):
        ordered_ids.extend(
            sorted(bucketed[bucket], key=_sort_key, reverse=True)
        )

    ordered_ids = ordered_ids[:_MAX_POOL]
    total       = len(ordered_ids)
    page_ids    = ordered_ids[offset: offset + limit]

    if not page_ids:
        return [], total

    # ── Step 7: Venue details for page ───────────────────────────────────────
    venue_rows = await conn.fetch(
        "SELECT id, name, area, city, types FROM venues WHERE id = ANY($1::int[])",
        page_ids,
    )
    venue_map = {r["id"]: r for r in venue_rows}

    # ── Step 8: Segment data for page ────────────────────────────────────────
    seg_rows = await conn.fetch(
        "SELECT venue_id, segment_id FROM venue_demographic_scores "
        "WHERE venue_id = ANY($1::int[]) AND segment_rank = 1",
        page_ids,
    )
    primary_seg_map = {r["venue_id"]: r["segment_id"] for r in seg_rows}

    top3_seg_rows = await conn.fetch(
        """
        SELECT venue_id, segment_id, segment_rank
        FROM   venue_demographic_scores
        WHERE  venue_id = ANY($1::int[]) AND segment_rank <= 3
        ORDER  BY venue_id, segment_rank
        """,
        page_ids,
    )
    top3_seg_map: dict[int, list[str]] = {}
    for r in top3_seg_rows:
        label = SEGMENT_LABELS.get(r["segment_id"], {}).get("label", r["segment_id"])
        top3_seg_map.setdefault(r["venue_id"], []).append(label)

    # ── Step 9: Assemble cards ────────────────────────────────────────────────
    cards: list[SimilarVenueCard] = []
    rank_offset = offset + 1

    for idx, sim_id in enumerate(page_ids):
        v = venue_map.get(sim_id)
        if not v:
            continue

        info      = all_candidates[sim_id]
        p_seg     = primary_seg_map.get(sim_id, "office_workers")
        arc_names = SEGMENT_TOP_ARCHETYPES.get(p_seg, [])
        sim_fd    = sim_fd_map.get(sim_id)

        delta_bars: list[DeltaBar] = []
        for dim in ALL_DIMS:
            c_score   = _float(client_fd.get(dim)) if client_fd else 0.0
            s_score   = _float(sim_fd.get(dim))    if sim_fd   else 0.0
            delta_val = round(s_score - c_score, 4)
            rule      = _lookup_rule(rules_by_dim, dim, delta_val)
            delta_bars.append(DeltaBar(
                dimension=dim,
                label=DIM_LABELS[dim],
                client_score=c_score,
                similar_score=max(0.0, min(1.0, s_score)),
                delta=delta_val,
                direction=rule["direction"],
                short_label=rule["short_label"],
                client_statement=rule["client_statement"],
            ))

        sim_score = (
            info["benchmark_score"] if view == "benchmark"
            else info["threat_score"]
        )

        cards.append(SimilarVenueCard(
            id=sim_id,
            name=v["name"],
            area=v["area"],
            city=v["city"],
            types=map_venue_types(list(v["types"] or [])),
            top_archetypes=[make_archetype_chip(n) for n in arc_names],
            top_segments=top3_seg_map.get(sim_id, []),
            delta_bars=delta_bars,
            similarity_score=sim_score,
            rank=rank_offset + idx,
        ))

    return cards, total


def _build_insight_callout(similar_venues: list[SimilarVenueCard]) -> str:
    """Generate the gold callout card text from the largest absolute delta across all venues."""
    if not similar_venues:
        return ""

    best_bar: DeltaBar | None = None
    best_abs = 0.0

    for venue in similar_venues:
        for bar in venue.delta_bars:
            if abs(bar.delta) > best_abs:
                best_abs = abs(bar.delta)
                best_bar = bar

    if not best_bar or best_abs < 0.05:
        return "These venues are closely matched across all fitness dimensions."

    if best_bar.delta > 0:
        return (
            f"Largest gap: {best_bar.label} — similar venues score "
            f"{round(best_abs * 100)}pts higher. {best_bar.client_statement}"
        )
    else:
        return (
            f"Your edge: {best_bar.label} — you score "
            f"{round(best_abs * 100)}pts higher than similar venues. "
            "Lean into this in your marketing."
        )


# ─── Route ────────────────────────────────────────────────────────────────────

@router.get("/{venue_id}/similar", response_model=CompetitorsResponse)
async def get_similar_venues(
    venue_id: int = Path(...),
    limit:    int = Query(default=3, ge=1, le=25),
    offset:   int = Query(default=0, ge=0),
    view:     str = Query(default="threat", pattern="^(threat|benchmark)$"),
):
    pool = get_pool()

    async with pool.acquire() as conn:
        await conn.execute("SET statement_timeout = '15s'")
        client_card    = await _fetch_client(conn, venue_id)
        similar, total = await _fetch_similar_venues(conn, venue_id, limit, offset, view)

    callout = _build_insight_callout(similar)

    return CompetitorsResponse(
        client_venue=client_card,
        similar_venues=similar,
        total_similar=total,
        offset=offset,
        limit=limit,
        insight_callout=callout,
    )


# ─── AI helper ────────────────────────────────────────────────────────────────

def _sanitize_json(text: str) -> str:
    """
    Fix the most common LLM JSON syntax errors so json.loads can parse them:
      - Trailing commas before } or ]   e.g.  "x": 1, }  →  "x": 1 }
      - Stray whitespace / newline artefacts are left to json.loads
    """
    # Trailing comma before closing brace/bracket (one or more, with optional whitespace)
    return _re.sub(r",\s*([}\]])", r"\1", text)


async def _call_nvidia_json(system_prompt: str, user_message: str) -> dict:
    """
    Non-streaming Nvidia API call. Returns parsed JSON dict.

    Parse strategy (most-lenient-last):
      1. Parse raw output directly
      2. Sanitise trailing commas, parse again
      3. Extract first {...} block, sanitise, parse
    stream is omitted intentionally — some Nvidia-compatible endpoints reject
    an explicit stream=False even though it is the default.
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=_NVIDIA_API_KEY, base_url=_NVIDIA_API_BASE)
    response = await client.chat.completions.create(
        model=_NVIDIA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.2,
        max_tokens=2000,
    )

    raw = (response.choices[0].message.content or "").strip()
    # Strip <think>...</think> blocks — reasoning models emit these before output
    raw = _re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
    # Strip markdown fences — model sometimes wraps output despite instructions
    raw = _re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()

    # ── 1. Direct parse ───────────────────────────────────────────────────────
    try:
        return _json.loads(raw)
    except _json.JSONDecodeError:
        pass

    # ── 2. Sanitise trailing commas, try again ────────────────────────────────
    sanitised = _sanitize_json(raw)
    try:
        return _json.loads(sanitised)
    except _json.JSONDecodeError:
        pass

    # ── 3. Extract first {...} block, sanitise, parse ─────────────────────────
    match = _re.search(r"\{[\s\S]*\}", sanitised)
    if match:
        try:
            return _json.loads(match.group())
        except _json.JSONDecodeError:
            pass

    # ── 4. Same on original raw (in case sanitise over-corrected) ─────────────
    match = _re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return _json.loads(_sanitize_json(match.group()))
        except _json.JSONDecodeError:
            pass

    raise ValueError(f"AI returned unparseable JSON: {raw[:400]}")


# ─── Competitor deep-dive route ───────────────────────────────────────────────

@router.get("/{venue_id}/competitor/{comp_id}", response_model=CompetitorDeepDive)
async def get_competitor_deep_dive(
    venue_id: int = Path(...),
    comp_id:  int = Path(...),
):
    """
    Competitor deep-dive — AI-generated behavioral analysis comparing the client
    against a specific competitor.

    Returns:
      learn_from : top 3 dimensions where competitor outperforms client (+narrative)
      avoid      : top 3 dimensions where client outperforms competitor (+narrative)
      strategic_brief : 2-3 sentence objective competitive positioning summary

    Narrative tone: objective, analytical, data-referenced. No marketing language.
    """
    pool = get_pool()

    async with pool.acquire() as conn:
        await conn.execute("SET statement_timeout = '20s'")

        client_v = await conn.fetchrow(
            "SELECT name, area, city, types FROM venues WHERE id = $1", venue_id
        )
        comp_v = await conn.fetchrow(
            "SELECT name, area, city, types FROM venues WHERE id = $1", comp_id
        )

        if not client_v:
            raise HTTPException(status_code=404, detail="Client venue not found")
        if not comp_v:
            raise HTTPException(status_code=404, detail="Competitor venue not found")

        dims_sel = ", ".join(ALL_DIMS)
        client_fd = await conn.fetchrow(
            f"SELECT {dims_sel} FROM venue_fitness_dimensions "
            f"WHERE venue_id = $1 AND source = 'blended'",
            venue_id,
        )
        comp_fd = await conn.fetchrow(
            f"SELECT {dims_sel} FROM venue_fitness_dimensions "
            f"WHERE venue_id = $1 AND source = 'blended'",
            comp_id,
        )

    # ── Compute deltas for all 7 dimensions ───────────────────────────────────
    all_scores = []
    for dim in ALL_DIMS:
        c = _float(client_fd.get(dim) if client_fd else 0.0)
        s = _float(comp_fd.get(dim)   if comp_fd   else 0.0)
        all_scores.append({
            "dim":          dim,
            "label":        DIM_LABELS[dim],
            "client_score": round(c, 3),
            "comp_score":   round(s, 3),
            "delta":        round(s - c, 3),
        })

    # Top 3 learn_from (competitor > client, meaningful gap > 0.02)
    learn_dims = sorted(
        [s for s in all_scores if s["delta"] > 0.02],
        key=lambda x: -x["delta"],
    )[:3]
    # Top 3 avoid (client > competitor, meaningful gap > 0.02)
    avoid_dims = sorted(
        [s for s in all_scores if s["delta"] < -0.02],
        key=lambda x: x["delta"],
    )[:3]

    # ── Bucket label ──────────────────────────────────────────────────────────
    client_cascade = _venue_type_cascade(list(client_v["types"] or []))
    comp_cascade   = _venue_type_cascade(list(comp_v["types"]   or []))
    intersection   = sum(1 for t in client_cascade if t in comp_cascade)
    bucket         = _assign_bucket(intersection, len(client_cascade))

    # ── Shared fallback builder ───────────────────────────────────────────────
    def _fallback_narrative(d: dict, is_learn: bool) -> str:
        direction = "stronger" if is_learn else "weaker"
        return (
            f"{comp_v['name']} scores {d['comp_score']:.3f} on {d['label']} "
            f"vs {d['client_score']:.3f} for {client_v['name']} "
            f"(delta {d['delta']:+.3f}). "
            f"This venue is behaviorally {direction} on this dimension."
        )

    def _build_fallback(reason: str) -> tuple[list, list, str]:
        lf = [
            CompetitorInsight(
                dimension=d["dim"], label=d["label"],
                client_score=d["client_score"], competitor_score=d["comp_score"],
                delta=d["delta"], narrative=_fallback_narrative(d, True),
            )
            for d in learn_dims
        ]
        av = [
            CompetitorInsight(
                dimension=d["dim"], label=d["label"],
                client_score=d["client_score"], competitor_score=d["comp_score"],
                delta=d["delta"], narrative=_fallback_narrative(d, False),
            )
            for d in avoid_dims
        ]
        br = (
            f"{client_v['name']} and {comp_v['name']} share {intersection} of "
            f"{len(client_cascade)} primary venue types ({_BUCKET_LABELS[bucket]}). "
            f"{reason}"
        )
        return lf, av, br

    # ── AI narrative generation ───────────────────────────────────────────────
    learn_from: list[CompetitorInsight] = []
    avoid:      list[CompetitorInsight] = []
    brief:      str = ""
    ai_used = False

    if _NVIDIA_API_KEY:
        sys_p, usr_p = build_competitor_analysis_prompt(
            client_name=client_v["name"],  client_area=client_v["area"] or "",
            client_types=list(client_v["types"] or []),
            comp_name=comp_v["name"],      comp_area=comp_v["area"] or "",
            comp_types=list(comp_v["types"] or []),
            all_scores=all_scores,
            learn_dims=learn_dims,
            avoid_dims=avoid_dims,
        )
        _ai_error: str = ""
        try:
            ai = await _call_nvidia_json(sys_p, usr_p)

            def _parse_insight(raw: dict) -> CompetitorInsight:
                return CompetitorInsight(
                    dimension=str(raw.get("dimension", "")),
                    label=str(raw.get("label", "")),
                    client_score=float(raw.get("client_score", 0)),
                    competitor_score=float(raw.get("competitor_score", 0)),
                    delta=float(raw.get("delta", 0)),
                    narrative=str(raw.get("narrative", "")),
                )

            learn_from = [_parse_insight(r) for r in ai.get("learn_from", [])]
            avoid      = [_parse_insight(r) for r in ai.get("avoid", [])]
            brief      = str(ai.get("strategic_brief", ""))
            ai_used    = True

        except Exception as _exc:
            _ai_error = str(_exc)

    if not ai_used:
        reason = (
            f"AI error: {_ai_error}"
            if _NVIDIA_API_KEY and "_ai_error" in dir() and _ai_error
            else "AI key not configured — showing raw signal data."
        )
        learn_from, avoid, brief = _build_fallback(reason)

    # ── Supabase logging (fire-and-forget) ───────────────────────────────────
    import asyncio as _asyncio
    import httpx as _httpx

    async def _log_deep_dive() -> None:
        try:
            supa_url = os.getenv("SUPABASE_URL", "").rstrip("/")
            supa_key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
            if not supa_url or not supa_key:
                return
            url = f"{supa_url}/rest/v1/competitor_deep_dive_logs"
            payload = {
                "venue_id":        str(venue_id),
                "competitor_id":   str(comp_id),
                "client_name":     client_v["name"],
                "competitor_name": comp_v["name"],
                "bucket_label":    _BUCKET_LABELS.get(bucket, "Match"),
                "ai_used":         ai_used,
                "model_version":   "nvidia-v1" if ai_used else None,
                "learn_from": [
                    {"dimension": i.dimension, "delta": i.delta, "narrative": i.narrative}
                    for i in learn_from
                ],
                "avoid": [
                    {"dimension": i.dimension, "delta": i.delta, "narrative": i.narrative}
                    for i in avoid
                ],
                "strategic_brief": brief,
                "is_demo":         False,
            }
            headers = {
                "apikey":        supa_key,
                "Authorization": f"Bearer {supa_key}",
                "Content-Type":  "application/json",
                "Prefer":        "return=minimal",
            }
            async with _httpx.AsyncClient(timeout=8) as hx:
                await hx.post(url, json=payload, headers=headers)
        except Exception:
            pass   # Never let logging block or crash the response

    _asyncio.create_task(_log_deep_dive())

    return CompetitorDeepDive(
        client_name=client_v["name"],
        competitor_id=comp_id,
        competitor_name=comp_v["name"],
        competitor_area=comp_v["area"] or "",
        competitor_city=comp_v["city"] or "",
        competitor_types=map_venue_types(list(comp_v["types"] or [])),
        bucket_label=_BUCKET_LABELS.get(bucket, "Match"),
        learn_from=learn_from,
        avoid=avoid,
        strategic_brief=brief,
    )
