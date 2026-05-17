"""
routers/chat.py
AI chat endpoint for venue intelligence across Marketing, Competitors, Transform, and Deep/Risk tabs.
Supports fast (single-model) and council (3-model debate) modes.
Logs all conversations to Supabase for training data collection.
"""

import asyncio
import json
import os
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from database import get_pool
from models import ChatRequest, ChatMessage
from prompts import get_system_prompt
from routers.utils import SEGMENT_LABELS
from routers.council import run_council, COUNCIL_DELIBERATING
import httpx

router = APIRouter()

_SUPABASE_URL = None
_SUPABASE_KEY = None

def _supabase_headers() -> dict:
    global _SUPABASE_URL, _SUPABASE_KEY
    if not _SUPABASE_URL:
        _SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
        _SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
    return {
        "apikey":        _SUPABASE_KEY,
        "Authorization": f"Bearer {_SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal",
    }

# Nvidia API config — single model for all tabs
NVIDIA_API_BASE        = "https://integrate.api.nvidia.com/v1"
NVIDIA_API_KEY_CREATIVE = os.getenv("NVIDIA_API_KEY_CREATIVE")
NVIDIA_MODEL_CREATIVE   = os.getenv("NVIDIA_MODEL_CREATIVE", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning")


async def fetch_venue_context(venue_id: int, tab: str) -> dict:
    """
    Fetch all relevant venue context from RDS.
    Pulls: basic venue info, fitness dimensions, segment alignment,
    full behavioral profiles, archetypes, platform usage,
    channel effectiveness, campaign templates, and interventions.
    All enriched queries are wrapped in try/except — chat degrades
    gracefully if any optional table is not yet populated.
    """
    pool = get_pool()

    async with pool.acquire() as conn:
        # ── Core venue ──────────────────────────────────────────────────────
        venue = await conn.fetchrow(
            "SELECT id, name, city, area, types FROM venues WHERE id = $1",
            venue_id,
        )
        if not venue:
            raise HTTPException(status_code=404, detail="Venue not found")

        fitness = await conn.fetchrow(
            "SELECT * FROM venue_fitness_dimensions WHERE venue_id = $1",
            venue_id,
        )

        segments = await conn.fetch(
            """
            SELECT segment_id, alignment_score, segment_rank
            FROM venue_demographic_scores
            WHERE venue_id = $1
            ORDER BY segment_rank
            LIMIT 5
            """,
            venue_id,
        )

        top_seg_ids = [r["segment_id"] for r in segments[:3]]

        # ── Competitors ─────────────────────────────────────────────────────
        # venue_similarity has no rank column — order by similarity_score
        competitors = await conn.fetch(
            """
            SELECT v.id, v.name, v.area, v.city, vs.similarity_score
            FROM venue_similarity vs
            JOIN venues v ON v.id = vs.similar_venue_id
            WHERE vs.venue_id = $1
            ORDER BY vs.similarity_score DESC
            LIMIT 5
            """,
            venue_id,
        )

        # ── Full segment behavioral profiles (016 tables) ───────────────────
        seg_behavioral: list = []
        try:
            seg_behavioral = await conn.fetch(
                """
                SELECT
                    vds.segment_id,
                    vds.alignment_score,
                    vds.segment_rank,
                    sbp.label,
                    sbp.food_pct_min,            sbp.food_pct_max,
                    sbp.alcohol_pct_min,         sbp.alcohol_pct_max,
                    sbp.dessert_attach_pct_min,  sbp.dessert_attach_pct_max,
                    sbp.avg_check_vs_baseline_pct_min,
                    sbp.avg_check_vs_baseline_pct_max,
                    sbp.alcohol_affinity,        sbp.alcohol_primary_driver,
                    sbp.beverage_preference,
                    sbp.peer_influence_coefficient,
                    sbp.dwell_min_minutes,       sbp.dwell_max_minutes,
                    sbp.revpash_min_inr,         sbp.revpash_max_inr,
                    sbp.diminishing_returns_minutes,
                    sbp.repeat_tendency_pct_min, sbp.repeat_tendency_pct_max,
                    sbp.repeat_window_days,
                    sbp.wom_multiplier_min,      sbp.wom_multiplier_max,
                    sbp.discovery_rate,
                    sbp.primary_trigger,
                    sbp.low_to_high_spend_trigger
                FROM venue_demographic_scores vds
                LEFT JOIN segment_behavioral_profiles sbp
                       ON sbp.segment_key = vds.segment_id
                WHERE vds.venue_id = $1
                ORDER BY vds.segment_rank
                LIMIT 3
                """,
                venue_id,
            )
        except Exception:
            pass

        # ── Top archetypes per segment (016 tables, fall back to old table) ─
        arch_by_seg: dict[str, list[str]] = {k: [] for k in top_seg_ids}
        try:
            arch_rows = await conn.fetch(
                """
                SELECT sbp.segment_key, abp.label AS archetype_label
                FROM segment_archetype_affinity saa
                JOIN segment_behavioral_profiles sbp ON sbp.id = saa.segment_id
                JOIN archetype_behavioral_profiles abp ON abp.id = saa.archetype_id
                WHERE sbp.segment_key = ANY($1::text[])
                  AND saa.affinity_rank <= 2
                ORDER BY sbp.segment_key, saa.affinity_rank
                """,
                top_seg_ids,
            )
            for r in arch_rows:
                arch_by_seg.setdefault(r["segment_key"], []).append(r["archetype_label"])
        except Exception:
            # Fall back to demographic_archetype_mapping
            try:
                old_arches = await conn.fetch(
                    """
                    SELECT DISTINCT ON (segment_id) segment_id, archetype_name
                    FROM demographic_archetype_mapping
                    WHERE segment_id = ANY($1::text[])
                    ORDER BY segment_id, prevalence_percentage DESC
                    """,
                    top_seg_ids,
                ) if top_seg_ids else []
                for r in old_arches:
                    arch_by_seg[r["segment_id"]] = [r["archetype_name"]]
            except Exception:
                pass

        # ── Primary discovery platform per segment ──────────────────────────
        disc_by_seg: dict[str, list[str]] = {k: [] for k in top_seg_ids}
        try:
            plat_rows = await conn.fetch(
                """
                SELECT sbp.segment_key, spu.platform
                FROM segment_platform_usage spu
                JOIN segment_behavioral_profiles sbp ON sbp.id = spu.segment_id
                WHERE sbp.segment_key = ANY($1::text[])
                  AND spu.usage_type = 'discovery'
                  AND spu.strength   = 'primary'
                """,
                top_seg_ids,
            )
            for r in plat_rows:
                disc_by_seg.setdefault(r["segment_key"], []).append(r["platform"])
        except Exception:
            pass

        # ── Channel mechanism effectiveness (research DB) ───────────────────
        channel_rows: list = []
        try:
            channel_rows = await conn.fetch(
                """
                SELECT channel, behavioral_mechanism,
                       effectiveness_score,
                       baseline_roi_lift_min, baseline_roi_lift_max,
                       primary_use_case
                FROM channel_mechanism_mapping
                ORDER BY effectiveness_score DESC
                LIMIT 10
                """,
            )
        except Exception:
            pass

        # ── Campaign templates for primary segment ──────────────────────────
        template_rows: list = []
        try:
            primary_seg_id = segments[0]["segment_id"] if segments else None
            if primary_seg_id:
                template_rows = await conn.fetch(
                    """
                    SELECT demographic_segment, target_archetype, channel,
                           message_template, suggested_roi_lift_percentage,
                           confidence_level
                    FROM campaign_templates
                    WHERE demographic_segment = $1
                    LIMIT 5
                    """,
                    primary_seg_id,
                )
        except Exception:
            pass

        # ── Intervention triggers (all tabs; not just deep_risk) ────────────
        intervention_rows: list = []
        try:
            intervention_rows = await conn.fetch(
                """
                SELECT intervention_type, description, priority_tier,
                       fit_score, recommended
                FROM intervention_triggers
                WHERE venue_id = $1
                ORDER BY fit_score DESC
                LIMIT 10
                """,
                venue_id,
            )
        except Exception:
            pass

    # ── Assemble context dict ────────────────────────────────────────────────

    context: dict = {
        "venue_id":   venue_id,
        "venue_name": venue["name"],
        "venue_type": venue["types"][0] if venue["types"] else "Restaurant",
        "city":       venue["city"],
        "area":       venue["area"],
        "top_competitors": [
            {
                "id":               comp["id"],
                "name":             comp["name"],
                "area":             comp["area"],
                "similarity_score": round(float(comp["similarity_score"] or 0.0), 3),
            }
            for comp in competitors
        ],
    }

    # Fitness dimensions
    context["top_fitness_dims"] = []
    if fitness:
        dims = [
            ("Office Lunch",        fitness.get("fitness_for_office_lunch",      0.0)),
            ("Repeat Habit",        fitness.get("fitness_for_repeat_habit",       0.0)),
            ("Social Dwell",        fitness.get("fitness_for_social_dwell",       0.0)),
            ("Group Energy",        fitness.get("fitness_for_group_energy",       0.0)),
            ("Destination Visit",   fitness.get("fitness_for_destination_visit",  0.0)),
            ("Operational Quality", fitness.get("operational_quality",            0.0)),
            ("Retention Strength",  fitness.get("retention_strength",             0.0)),
        ]
        context["top_fitness_dims"] = [
            {"label": label, "score": round(float(score or 0.0), 3)}
            for label, score in dims
            if score and float(score) > 0
        ]

    # Basic segment list (always present)
    context["top_segments"] = [
        {
            "segment_id":   seg["segment_id"],
            "name":         SEGMENT_LABELS.get(seg["segment_id"], {}).get("label", seg["segment_id"]),
            "fitness_score": round(float(seg["alignment_score"] or 0.0), 3),
        }
        for seg in segments
    ]

    # Enriched segment behavioral profiles
    context["seg_profiles"] = []
    for r in seg_behavioral:
        seg_id = r["segment_id"]
        food_min   = r["food_pct_min"]
        food_max   = r["food_pct_max"]
        alc_min    = r["alcohol_pct_min"]
        alc_max    = r["alcohol_pct_max"]
        dess_min   = r["dessert_attach_pct_min"]
        dess_max   = r["dessert_attach_pct_max"]
        chk_min    = r["avg_check_vs_baseline_pct_min"]
        chk_max    = r["avg_check_vs_baseline_pct_max"]
        rev_min    = r["revpash_min_inr"]
        rev_max    = r["revpash_max_inr"]
        dwell_min  = r["dwell_min_minutes"]
        dwell_max  = r["dwell_max_minutes"]
        rep_min    = r["repeat_tendency_pct_min"]
        rep_max    = r["repeat_tendency_pct_max"]
        wom_min    = r["wom_multiplier_min"]
        wom_max    = r["wom_multiplier_max"]

        context["seg_profiles"].append({
            "segment_id":       seg_id,
            "label":            r["label"] or SEGMENT_LABELS.get(seg_id, {}).get("label", seg_id),
            "rank":             r["segment_rank"],
            "alignment_score":  float(r["alignment_score"] or 0),
            "food_pct":         f"{food_min}–{food_max}%" if food_min is not None else None,
            "alcohol_pct":      f"{alc_min}–{alc_max}%"  if alc_min  is not None else None,
            "dessert_pct":      f"{dess_min}–{dess_max}%" if dess_min is not None else None,
            "check_vs_baseline":f"{chk_min:+d}% to {chk_max:+d}%" if chk_min is not None else None,
            "alcohol_affinity": r["alcohol_affinity"],
            "alcohol_driver":   r["alcohol_primary_driver"],
            "beverage_preference": r["beverage_preference"],
            "peer_influence":   float(r["peer_influence_coefficient"] or 0),
            "dwell":            f"{dwell_min}–{dwell_max} min" if dwell_min is not None else None,
            "revpash":          f"₹{rev_min}–{rev_max}/hr"   if rev_min  is not None else None,
            "diminishing_returns_min": r["diminishing_returns_minutes"],
            "repeat_tendency":  f"{rep_min}–{rep_max}%"      if rep_min  is not None else None,
            "repeat_window_days": r["repeat_window_days"],
            "wom_multiplier":   f"{wom_min}–{wom_max}x"      if wom_min  is not None else None,
            "discovery_rate":   r["discovery_rate"],
            "primary_trigger":  r["primary_trigger"],
            "spend_trigger":    r["low_to_high_spend_trigger"],
            "archetypes":       arch_by_seg.get(seg_id, []),
            "discovery_platforms": disc_by_seg.get(seg_id, []),
        })

    # Channel effectiveness
    context["channel_effectiveness"] = [
        {
            "channel":     r["channel"],
            "mechanism":   r["behavioral_mechanism"],
            "effectiveness": int(r["effectiveness_score"] or 0),
            "roi_min":     float(r["baseline_roi_lift_min"] or 0),
            "roi_max":     float(r["baseline_roi_lift_max"] or 0),
            "use_case":    r["primary_use_case"] or "",
        }
        for r in channel_rows
    ]

    # Campaign templates
    context["campaign_templates"] = [
        {
            "segment":    r["demographic_segment"] or "",
            "archetype":  r["target_archetype"] or "",
            "channel":    r["channel"] or "",
            "template":   r["message_template"] or "",
            "roi_lift":   float(r["suggested_roi_lift_percentage"] or 0),
            "confidence": r["confidence_level"] or "",
        }
        for r in template_rows
    ]

    # Interventions
    context["interventions"] = [
        {
            "type":        r["intervention_type"],
            "description": r["description"] or "",
            "tier":        r["priority_tier"] or "",
            "fit_score":   float(r["fit_score"] or 0),
            "recommended": bool(r["recommended"]),
        }
        for r in intervention_rows
    ]

    # Risk signals for deep_risk tab
    if tab == "deep_risk":
        context["risk_signals"] = [
            i for i in context["interventions"]
            if i["tier"] in ("CRITICAL", "HIGH")
        ]

    return context


async def stream_from_nvidia(
    system_prompt: str, user_question: str, tab: str
) -> AsyncGenerator[str, None]:
    """
    Stream response from Nvidia API using the creative model for all tabs.
    Temperature varies by tab type — higher for content/creative, lower for analytical.
    """
    try:
        from openai import AsyncOpenAI

        api_key = NVIDIA_API_KEY_CREATIVE
        model   = NVIDIA_MODEL_CREATIVE

        # Creative tabs: higher temperature for engaging copy
        # Analytical tabs: lower temperature for accuracy
        creative_tabs = {"marketing", "overview", "audience"}
        temperature = 0.8 if tab in creative_tabs else 0.4

        if not api_key:
            yield "[Error: NVIDIA_API_KEY_CREATIVE is not configured]"
            return

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=NVIDIA_API_BASE,
        )

        max_tokens = {
            "marketing":   4096,
            "overview":    3000,
            "audience":    3000,
            "competitors": 3000,
            "transform":   3000,
            "deep_risk":   3000,
        }.get(tab, 2000)

        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        yield f"\n\n[Error: {str(e)}]"


async def log_chat_to_supabase(
    venue_id: int, tab: str, question: str, context_snapshot: dict, response: str
) -> None:
    """Fire-and-forget: POST one row to Supabase REST API via httpx."""
    try:
        url = f"{_SUPABASE_URL or os.getenv('SUPABASE_URL', '').rstrip('/')}/rest/v1/venue_chat_logs"
        payload = {
            "venue_id":         str(venue_id),
            "tab":              tab,
            "question":         question,
            "context_snapshot": context_snapshot,
            "response":         response,
            "model_version":    "kimi-v1",
            "source_type":      "ai_generated",
            "schema_version":   1,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json=payload, headers=_supabase_headers())
    except Exception as e:
        print(f"Supabase logging failed: {e}")


@router.post("/{venue_id}/chat")
async def chat_with_venue(venue_id: int, request: ChatRequest):
    """
    Stream AI chat response for a venue, guardrailed by tab.
    """
    # Validate tab
    valid_tabs = ["marketing", "competitors", "transform", "deep_risk", "overview", "audience"]
    if request.tab not in valid_tabs:
        raise HTTPException(status_code=400, detail=f"Invalid tab. Must be one of: {valid_tabs}")

    # Fetch venue context
    try:
        context = await fetch_venue_context(venue_id, request.tab)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching venue context: {str(e)}")

    # Build system prompt (guardrailed per tab)
    try:
        system_prompt = get_system_prompt(request.tab, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building prompt: {str(e)}")

    async def response_generator():
        try:
            if request.mode == "council":
                # Council of Models: 3-model debate → Nemotron synthesis (15–20s)
                async for chunk in run_council(
                    venue_id, request.tab, request.question, system_prompt
                ):
                    yield chunk
            else:
                # Fast path: single Nemotron stream, responds in ~3s
                async for chunk in stream_from_nvidia(
                    system_prompt, request.question, request.tab
                ):
                    yield chunk
        except Exception as exc:
            yield f"\n\n[Error: {exc}]"

    return StreamingResponse(response_generator(), media_type="text/event-stream")
