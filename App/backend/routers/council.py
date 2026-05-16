"""
routers/council.py
The Council of Models — multi-agent debate engine for Polynovea venue intelligence.

Architecture:
  Round 1  — All 3 models answer independently (parallel, ~5s)
  Round 2  — Each model reviews the other two's answers (parallel, ~5s)
  Round 3  — Nemotron synthesises into one answer or two labelled perspectives (streamed live)

The full debate tree is stored in Supabase as proprietary training data.
The user sees only the final synthesised answer.
"""

import asyncio
import os
import re
import time
from typing import AsyncGenerator

import httpx
from openai import AsyncOpenAI

# ─── Config ───────────────────────────────────────────────────────────────────

NVIDIA_API_BASE = "https://integrate.api.nvidia.com/v1"

# Sentinel: first chunk tells the frontend to show the deliberating spinner.
COUNCIL_DELIBERATING = "[COUNCIL:DELIBERATING]"

# Council member definitions
_NEMOTRON = {
    "name":    "nemotron",
    "key_env": "NVIDIA_API_KEY_CREATIVE",
    "model":   "nvidia/llama-3.1-nemotron-70b-instruct",
    "temp":    0.30,
}
_DEEPSEEK = {
    "name":    "deepseek",
    "key_env": "NVIDIA_API_KEY_ANALYTICAL",
    "model":   "deepseek/deepseek-v4-pro",
    "temp":    0.40,
}
_QWEN = {
    "name":    "qwen",
    "key_env": "NVIDIA_API_KEY_COUNCIL",
    "model":   "qwen/qwen3.5-397b-a17b",
    "temp":    0.50,
}

_ALL = [_NEMOTRON, _DEEPSEEK, _QWEN]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks (DeepSeek R1 / Qwen thinking mode).
    Also strips unclosed <think> blocks that hit max_tokens mid-thought."""
    # Complete blocks
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Unclosed block — model hit token limit inside thinking
    text = re.sub(r"<think>.*$", "", text, flags=re.DOTALL)
    return text.strip()


async def _call(member: dict, messages: list, max_tokens: int = 700) -> str:
    """Non-streaming call to one council member. Returns the full response text."""
    api_key = os.getenv(member["key_env"])
    if not api_key:
        return f"[{member['name']} unavailable — {member['key_env']} not set]"
    try:
        client = AsyncOpenAI(api_key=api_key, base_url=NVIDIA_API_BASE)
        # Disable thinking mode on Qwen — otherwise it burns all tokens on <think> blocks
        extra = {"chat_template_kwargs": {"enable_thinking": False}} if member["name"] == "qwen" else {}
        resp = await client.chat.completions.create(
            model=member["model"],
            messages=messages,
            temperature=member["temp"],
            max_tokens=max_tokens,
            extra_body=extra if extra else None,
        )
        return _strip_thinking(resp.choices[0].message.content or "")
    except Exception as exc:
        return f"[{member['name']} error: {exc}]"


# ─── Round 1: Independent analysis ───────────────────────────────────────────

_R1_INSTRUCTION = """

Answer the user's question based on the venue data above.
Structure your response exactly as:

POSITION: [one sentence — your core conclusion or recommendation]
ANSWER: [your full response, 150–250 words, specific and actionable]
CONFIDENCE: [HIGH / MEDIUM / LOW]"""


async def _round1(system_prompt: str, question: str) -> dict[str, str]:
    """All 3 models answer independently, in parallel."""
    tasks = [
        _call(m, [
            {"role": "system", "content": system_prompt + _R1_INSTRUCTION},
            {"role": "user",   "content": question},
        ], max_tokens=400)
        for m in _ALL
    ]
    results = await asyncio.gather(*tasks)
    return {m["name"]: r for m, r in zip(_ALL, results)}


# ─── Round 2: Cross-review debate ────────────────────────────────────────────

def _r2_user_message(my_name: str, my_r1: str, r1: dict[str, str]) -> str:
    others = "\n\n".join(
        f"Expert {name.upper()}:\n{answer}"
        for name, answer in r1.items()
        if name != my_name
    )
    return f"""You gave this answer:

YOUR ANSWER:
{my_r1}

Two other independent experts answered the same question:

{others}

Review their reasoning. Then respond:

AGREE_ON: [points you agree with from the other experts]
DISAGREE_ON: [points you disagree with, and why]
REFINED_POSITION: [your final stance — maintain if confident, adjust if they raised valid points]
CHANGE_FROM_R1: [MAJOR / MINOR / NONE]"""


async def _round2(system_prompt: str, question: str, r1: dict[str, str]) -> dict[str, str]:
    """Each model reviews the others' Round 1 answers, in parallel."""
    tasks = [
        _call(m, [
            {"role": "system",    "content": system_prompt + _R1_INSTRUCTION},
            {"role": "user",      "content": question},
            {"role": "assistant", "content": r1[m["name"]]},
            {"role": "user",      "content": _r2_user_message(m["name"], r1[m["name"]], r1)},
        ], max_tokens=300)
        for m in _ALL
    ]
    results = await asyncio.gather(*tasks)
    return {m["name"]: r for m, r in zip(_ALL, results)}


# ─── Round 3: Synthesis (Nemotron as judge, streamed) ────────────────────────

_SYNTHESIS_SYSTEM = """You are the final synthesiser. Three expert venue intelligence analysts have independently answered a question and debated their positions. Your job is to produce the single best answer for the venue owner.

Rules:
- If the experts broadly agree (even with different nuances): write ONE unified answer incorporating the strongest insights. Be direct and specific. 200–300 words.
- If there is genuine, irreconcilable strategic disagreement: present exactly TWO clearly labelled options using this format:
  **Option A — [short label]**
  [explanation, 100–150 words]

  **Option B — [short label]**
  [explanation, 100–150 words]

End your response on its own line with exactly one of:
[CONSENSUS]
[SPLIT]

Do not mention the council, the debate process, or how you reached the answer. Just give the answer."""


def _synthesis_user_message(question: str, r1: dict, r2: dict) -> str:
    return f"""QUESTION:
{question}

EXPERT ANALYSES (Initial answer → position after debate):

NEMOTRON:
Round 1: {r1['nemotron']}
After debate: {r2['nemotron']}

DEEPSEEK:
Round 1: {r1['deepseek']}
After debate: {r2['deepseek']}

QWEN:
Round 1: {r1['qwen']}
After debate: {r2['qwen']}

Synthesise the best answer now."""


async def _stream_synthesis(
    question: str, r1: dict, r2: dict
) -> AsyncGenerator[str, None]:
    """Stream the Nemotron synthesis directly to the user."""
    api_key = os.getenv(_NEMOTRON["key_env"])
    if not api_key:
        yield "[Council synthesis unavailable — NVIDIA_API_KEY_CREATIVE not set]"
        return
    try:
        client = AsyncOpenAI(api_key=api_key, base_url=NVIDIA_API_BASE)
        stream = await client.chat.completions.create(
            model=_NEMOTRON["model"],
            messages=[
                {"role": "system", "content": _SYNTHESIS_SYSTEM},
                {"role": "user",   "content": _synthesis_user_message(question, r1, r2)},
            ],
            temperature=0.25,
            max_tokens=2048,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta
    except Exception as exc:
        yield f"\n\n[Synthesis error: {exc}]"


# ─── Supabase logging ─────────────────────────────────────────────────────────

def _supabase_headers() -> dict:
    key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
    return {
        "apikey":        key,
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal",
    }


async def _log_session(
    venue_id: int, tab: str, question: str,
    r1: dict, r2: dict, synthesis: str,
    consensus: bool, duration_ms: int,
) -> None:
    """Fire-and-forget: store the full debate tree in Supabase."""
    try:
        base = os.getenv("SUPABASE_URL", "").rstrip("/")
        url  = f"{base}/rest/v1/venue_council_sessions"
        payload = {
            "venue_id":         str(venue_id),
            "tab":              tab,
            "question":         question,
            "nemotron_r1":      r1.get("nemotron", ""),
            "deepseek_r1":      r1.get("deepseek", ""),
            "qwen_r1":          r1.get("qwen", ""),
            "nemotron_r2":      r2.get("nemotron", ""),
            "deepseek_r2":      r2.get("deepseek", ""),
            "qwen_r2":          r2.get("qwen", ""),
            "synthesis":        synthesis,
            "consensus_reached": consensus,
            "duration_ms":      duration_ms,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json=payload, headers=_supabase_headers())
    except Exception as exc:
        print(f"Council logging failed: {exc}")


# ─── Main orchestrator ────────────────────────────────────────────────────────

async def run_council(
    venue_id: int,
    tab: str,
    question: str,
    system_prompt: str,
) -> AsyncGenerator[str, None]:
    """
    Full council pipeline. Yields:
      1. COUNCIL_DELIBERATING sentinel (frontend shows spinner)
      2. Synthesised answer chunks (streamed live from Nemotron)
    """
    # Signal frontend to show deliberating state
    yield COUNCIL_DELIBERATING

    t0 = time.monotonic()

    # Round 1 then Round 2 (sequential — R2 needs R1 results)
    r1 = await _round1(system_prompt, question)
    r2 = await _round2(system_prompt, question, r1)

    # Round 3 — stream live to user while collecting for logging
    synthesis_chunks: list[str] = []

    async for chunk in _stream_synthesis(question, r1, r2):
        # Strip the trailing marker tags before sending to user
        clean = chunk.replace("[CONSENSUS]", "").replace("[SPLIT]", "")
        if clean:
            synthesis_chunks.append(chunk)   # store raw (with markers) for logging
            yield clean

    synthesis_full = "".join(synthesis_chunks)
    consensus      = "[SPLIT]" not in synthesis_full
    duration_ms    = int((time.monotonic() - t0) * 1000)

    # Log full debate tree asynchronously
    asyncio.create_task(_log_session(
        venue_id, tab, question, r1, r2, synthesis_full, consensus, duration_ms,
    ))
