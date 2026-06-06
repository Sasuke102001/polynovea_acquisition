"""
routers/council.py
The Council of Models — multi-agent debate engine for Polynovea venue intelligence.

Architecture:
  Round 1  — All 3 models answer independently (parallel, ~5s)
  Round 2  — Each model reviews the other two's answers (parallel, ~5s)
  Round 3  — Nemotron synthesises into one answer or two labelled perspectives (streamed live)

Council members:
  - Nemotron  (NVIDIA NIM) — synthesiser + analyst
  - DeepSeek  (NVIDIA NIM) — reasoning specialist
  - Mistral   (Mistral API if MISTRAL_API_KEY set, else falls back to NVIDIA Qwen)

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

_NVIDIA_BASE = "https://integrate.api.nvidia.com/v1"

# Sentinel: first chunk tells the frontend to show the deliberating spinner.
COUNCIL_DELIBERATING = "[COUNCIL:DELIBERATING]"

# ─── Dedicated council keys (one per seat, no shared round-robin) ─────────────
# KEY_1 = NVIDIA_API_KEY  (Samhit 2nd)   → Seat 1 Nemotron  meta/llama-3.3-70b
# KEY_2 = NVIDIA_API_KEY_2 (Khushi)      → Seat 2 Analyst   deepseek-ai/deepseek-v4-flash
# KEY_3 = NVIDIA_API_KEY_3 (Payal)       → Seat 3 Mistral   mistralai/mistral-medium-3.5-128b

_KEY1 = os.getenv("NVIDIA_API_KEY", "")
_KEY2 = os.getenv("NVIDIA_API_KEY_2", "")
_KEY3 = os.getenv("NVIDIA_API_KEY_3", "")

# Council member definitions — each seat has its own key
_NEMOTRON = {
    "name":  "nemotron",
    "model": os.getenv("NVIDIA_MODEL_NEMOTRON", "meta/llama-3.3-70b-instruct"),
    "key":   _KEY1,
    "temp":  0.30,
}
_DEEPSEEK = {
    "name":  "deepseek",
    "model": os.getenv("NVIDIA_MODEL_DEEPSEEK", "deepseek-ai/deepseek-v4-flash"),
    "key":   _KEY2,
    "temp":  0.40,
}
_MISTRAL = {
    "name":  "mistral",
    "model": os.getenv("NVIDIA_MODEL_QWEN", "mistralai/mistral-medium-3.5-128b"),
    "key":   _KEY3,
    "temp":  0.50,
}

_ALL = [_NEMOTRON, _DEEPSEEK, _MISTRAL]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks (DeepSeek R1 / Qwen thinking mode).
    Also strips unclosed <think> blocks that hit max_tokens mid-thought."""
    # Complete blocks
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Unclosed block — model hit token limit inside thinking
    text = re.sub(r"<think>.*$", "", text, flags=re.DOTALL)
    return text.strip()


_CALL_TIMEOUT = 45  # seconds — deepseek-v4-flash can be slow to cold-start


async def _call(member: dict, messages: list, max_tokens: int = 700) -> str:
    """Call one council member using its dedicated key. Returns full response text."""
    key = member.get("key", "")
    if not key:
        return f"[{member['name']} unavailable — key not configured]"
    try:
        client = AsyncOpenAI(api_key=key, base_url=_NVIDIA_BASE)
        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model=member["model"],
                messages=messages,
                temperature=member["temp"],
                max_tokens=max_tokens,
            ),
            timeout=_CALL_TIMEOUT,
        )
        return _strip_thinking(resp.choices[0].message.content or "")
    except asyncio.TimeoutError:
        return f"[{member['name']} timed out after {_CALL_TIMEOUT}s]"
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


def _first_sentence(text: str, max_len: int = 160) -> str:
    """Extract first meaningful sentence from free-form text (fallback for unformatted responses)."""
    for line in text.split("\n"):
        l = line.strip()
        # Skip error strings, short lines, markdown headers
        if not l or l.startswith("[") or l.startswith("#") or len(l) < 20:
            continue
        m = re.match(r"([^.!?]{10,}[.!?])", l)
        snippet = m.group(1) if m else l
        return snippet[:max_len]
    return ""


def _extract_r1(text: str) -> tuple[str, str]:
    """Extract (position, confidence) from a Round 1 response."""
    position = ""
    confidence = "MEDIUM"
    for line in text.split("\n"):
        l = line.strip()
        if l.startswith("POSITION:"):
            position = l[9:].strip()
        elif l.startswith("CONFIDENCE:"):
            confidence = l[11:].strip()
    # Fallback: model didn't use structured labels — pull first sentence
    if not position:
        position = _first_sentence(text)
    return position, confidence


def _extract_r2(text: str) -> tuple[str, str]:
    """Extract (refined_position, change) from a Round 2 response."""
    refined = ""
    change = "MINOR"
    for line in text.split("\n"):
        l = line.strip()
        if l.startswith("REFINED_POSITION:"):
            refined = l[17:].strip()
        elif l.startswith("CHANGE_FROM_R1:"):
            change = l[15:].strip()
    # Fallback: model didn't use structured labels — pull first sentence
    if not refined:
        refined = _first_sentence(text)
    return refined, change


def _synthesis_user_message(question: str, r1: dict, r2: dict) -> str:
    third     = _MISTRAL["name"]
    third_lbl = third.upper()
    return f"""QUESTION:
{question}

EXPERT ANALYSES (Initial answer → position after debate):

NEMOTRON:
Round 1: {r1['nemotron']}
After debate: {r2['nemotron']}

DEEPSEEK:
Round 1: {r1['deepseek']}
After debate: {r2['deepseek']}

{third_lbl}:
Round 1: {r1.get(third, '')}
After debate: {r2.get(third, '')}

Synthesise the best answer now."""


async def _stream_synthesis(
    question: str, r1: dict, r2: dict
) -> AsyncGenerator[str, None]:
    """Stream the Nemotron synthesis directly to the user using Seat 1 key."""
    if not _KEY1:
        yield "[Council synthesis unavailable — NVIDIA_API_KEY not set]"
        return
    try:
        client = AsyncOpenAI(api_key=_KEY1, base_url=_NVIDIA_BASE)
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
    # Separate clean responses from error strings per model
    def _model_entry(name: str) -> dict:
        r1_val = r1.get(name, "")
        r2_val = r2.get(name, "")
        is_error = r1_val.startswith(f"[{name}")
        return {
            "r1":    None if is_error else r1_val,
            "r2":    None if is_error else r2_val,
            "error": r1_val if is_error else None,
        }

    third_key = _MISTRAL["name"]
    models_errored = [
        name for name in ("nemotron", "deepseek", third_key)
        if r1.get(name, "").startswith(f"[{name}")
    ]

    try:
        base = os.getenv("SUPABASE_URL", "").rstrip("/")
        url  = f"{base}/rest/v1/venue_council_sessions"
        payload = {
            "venue_id":        str(venue_id),
            "tab":             tab,
            "question":        question,
            "debate_tree": {
                "nemotron": _model_entry("nemotron"),
                "deepseek":  _model_entry("deepseek"),
                third_key:   _model_entry(third_key),
            },
            "models_errored":  models_errored,
            "synthesis_model": "nemotron",
            "synthesis":       synthesis,
            "consensus_reached": consensus,
            "duration_ms":     duration_ms,
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
      1. COUNCIL_DELIBERATING sentinel
      2. [COUNCIL:PHASE:r1:{model}:{confidence}]{position}\\n  — one per model after Round 1
      3. [COUNCIL:PHASE:r2:{model}:{change}]{refined_position}\\n — one per model after Round 2
      4. [COUNCIL:SYNTHESIS]\\n sentinel
      5. Synthesised answer chunks streamed live from Nemotron
    """
    yield COUNCIL_DELIBERATING

    t0 = time.monotonic()

    r1 = await _round1(system_prompt, question)

    for m in _ALL:
        pos, conf = _extract_r1(r1.get(m["name"], ""))
        if pos:
            yield f"[COUNCIL:PHASE:r1:{m['name']}:{conf}]{pos}\n"

    r2 = await _round2(system_prompt, question, r1)

    for m in _ALL:
        refined, change = _extract_r2(r2.get(m["name"], ""))
        if refined:
            yield f"[COUNCIL:PHASE:r2:{m['name']}:{change}]{refined}\n"

    yield "[COUNCIL:SYNTHESIS]\n"

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
