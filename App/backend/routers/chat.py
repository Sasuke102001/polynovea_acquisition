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
    """Fetch relevant venue context from RDS based on tab."""
    pool = get_pool()

    async with pool.acquire() as conn:
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

        # Correct columns: segment_id, alignment_score, segment_rank
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

        # Archetypes keyed by segment_id, not venue_id
        top_seg_ids = [r["segment_id"] for r in segments[:3]]
        archetypes = await conn.fetch(
            """
            SELECT DISTINCT ON (segment_id) segment_id, archetype_name
            FROM demographic_archetype_mapping
            WHERE segment_id = ANY($1::text[])
            ORDER BY segment_id, prevalence_percentage DESC
            """,
            top_seg_ids,
        ) if top_seg_ids else []

        # Competitors from venue_similarity (joined to venues)
        competitors = await conn.fetch(
            """
            SELECT v.id, v.name, v.area, v.city, vs.similarity_score
            FROM venue_similarity vs
            JOIN venues v ON v.id = vs.similar_venue_id
            WHERE vs.venue_id = $1
            ORDER BY vs.rank
            LIMIT 5
            """,
            venue_id,
        )

        # Risk signals — table may not exist yet; fail gracefully
        risk_signals = []
        if tab == "deep_risk":
            try:
                risk_signals = await conn.fetch(
                    """
                    SELECT signal_name, signal_impact, confidence_level
                    FROM intervention_triggers
                    WHERE venue_id = $1 AND is_active = true
                    ORDER BY signal_impact DESC
                    LIMIT 8
                    """,
                    venue_id,
                )
            except Exception:
                risk_signals = []

    context = {
        "venue_id": venue_id,
        "venue_name": venue["name"],
        "venue_type": venue["types"][0] if venue["types"] else "Restaurant",
        "city": venue["city"],
        "area": venue["area"],
        "top_segments": [
            {
                "segment_id": seg["segment_id"],
                "name": SEGMENT_LABELS.get(seg["segment_id"], {}).get("label", seg["segment_id"]),
                "fitness_score": round(float(seg["alignment_score"] or 0.0), 3),
            }
            for seg in segments
        ],
        "top_archetypes": [
            {"segment_id": arc["segment_id"], "archetype": arc["archetype_name"]}
            for arc in archetypes
        ],
        "top_fitness_dims": [],
        "top_competitors": [
            {
                "id": comp["id"],
                "name": comp["name"],
                "area": comp["area"],
                "similarity_score": round(float(comp["similarity_score"] or 0.0), 3),
            }
            for comp in competitors
        ],
    }

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
        ][:4]

    if tab == "deep_risk":
        context["risk_signals"] = [
            {
                "name": sig["signal_name"],
                "impact": float(sig["signal_impact"] or 0.0),
                "confidence": sig["confidence_level"],
            }
            for sig in risk_signals
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
