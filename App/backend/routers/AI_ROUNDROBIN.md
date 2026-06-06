# AI Round-Robin Setup

## Two Layers: Key Rotation + Provider Rotation

### Layer 1 — NVIDIA Key Rotation (`providers.py`)

At startup, `_load_nvidia_keys()` collects keys from three env var patterns, deduped, into a list:

```
NVIDIA_API_KEY          # primary (backward compat)
NVIDIA_API_KEYS         # comma-separated batch: key1,key2,key3
NVIDIA_API_KEY_2..19    # numbered extras
```

Then `itertools.cycle(keys)` wraps the list. Every call to `next_nvidia_key()` advances the cycle.
With 3 keys: key1 → key2 → key3 → key1 → ...

### Layer 2 — Provider Rotation (NVIDIA keys + Mistral)

`_build_fast_cycle()` builds a provider list:

```python
["nvidia"] * N + (["mistral"] if MISTRAL_API_KEY set else [])
```

Also wrapped in `itertools.cycle`. With 2 NVIDIA keys + Mistral:
nvidia → nvidia → mistral → nvidia → nvidia → mistral → ...

Each call to `next_fast_client(model)`:
1. Advances the provider cycle → `"nvidia"` or `"mistral"`
2. If nvidia: calls `get_nvidia_client(model)` which advances the key cycle
3. Returns a `ProviderClient(client=AsyncOpenAI(...), model=..., name=..., key_hint=...)`

---

## Fast Mode (Chat)

Single call per user message. One provider selected from the cycle per request.

```python
pc = next_fast_client(NVIDIA_MODEL_CREATIVE)
stream = await pc.client.chat.completions.create(
    model=pc.model, messages=[...], stream=True
)
```

Tab controls temperature and token budget:

| Tab | Temperature | Max Tokens |
|---|---|---|
| marketing, overview, audience | 0.8 | 3000–4096 |
| competitors, transform, deep_risk | 0.4 | 3000 |
| fallback | 0.4 | 2000 |

---

## Council Mode (3-Model Debate)

Three fixed models — not rotated — each with a distinct role:

| Seat | Env Var | Default Model | Role | Temp |
|---|---|---|---|---|
| Nemotron | `NVIDIA_MODEL_NEMOTRON` | `meta/llama-3.3-70b-instruct` | Analyst + final synthesiser | 0.30 |
| DeepSeek | `NVIDIA_MODEL_DEEPSEEK` | `deepseek-ai/deepseek-r1` | Reasoning specialist | 0.40 |
| Mistral / Qwen | `MISTRAL_API_KEY` / `NVIDIA_MODEL_QWEN` | `mistral-large-latest` or `qwen/qwen2.5-72b-instruct` | Third perspective | 0.50 |

### Three Rounds

**Round 1** — All 3 answer independently, `asyncio.gather` in parallel (~5s each)

Each model is instructed to format:
```
POSITION: <one sentence conclusion>
ANSWER: <150-250 words>
CONFIDENCE: HIGH / MEDIUM / LOW
```

**Round 2** — Each model reviews the other two's R1 answers, gather again (~5s each)

Each model responds with:
```
AGREE_ON: <common ground>
DISAGREE_ON: <disagreements + why>
REFINED_POSITION: <updated stance>
CHANGE_FROM_R1: MAJOR / MINOR / NONE
```

**Round 3** — Nemotron synthesises R1 + R2 into one answer, **streamed live**

If experts broadly agree → single unified answer (200–300 words).
If genuinely split → two labelled options (Option A / Option B, 100–150 words each).
Response ends with `[CONSENSUS]` or `[SPLIT]` tag (stripped before sending to user).

Council uses `get_nvidia_client(model)` directly — still advances the key cycle for NVIDIA calls.

### Stream Protocol

Frontend receives a stream of tagged sentinels, then the synthesis text:

```
[COUNCIL:DELIBERATING]
[COUNCIL:PHASE:r1:nemotron:HIGH]<position>\n
[COUNCIL:PHASE:r1:deepseek:MEDIUM]<position>\n
[COUNCIL:PHASE:r1:mistral:HIGH]<position>\n
[COUNCIL:PHASE:r2:nemotron:MINOR]<refined>\n
[COUNCIL:PHASE:r2:deepseek:MAJOR]<refined>\n
[COUNCIL:PHASE:r2:mistral:NONE]<refined>\n
[COUNCIL:SYNTHESIS]\n
...streamed synthesis text...
```

The full debate tree (R1 + R2 + synthesis) is stored in Supabase `venue_council_sessions` as training data.

---

## Replicating for a New Module

### Fast mode (minimum viable)

```python
from routers.providers import next_fast_client
import os

MODEL = os.getenv("NVIDIA_MODEL_CREATIVE", "meta/llama-3.3-70b-instruct")

async def stream_response(system_prompt: str, question: str) -> AsyncGenerator[str, None]:
    pc = next_fast_client(MODEL)
    if not pc:
        yield "[Error: No AI provider configured — set NVIDIA_API_KEY or MISTRAL_API_KEY]"
        return
    stream = await pc.client.chat.completions.create(
        model=pc.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": question},
        ],
        temperature=0.6,
        max_tokens=2000,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

### Council mode

```python
from routers.council import run_council, COUNCIL_DELIBERATING

async for chunk in run_council(venue_id, tab, question, system_prompt):
    yield chunk
```

`run_council` handles all three rounds, streaming, and Supabase logging internally.
No additional configuration needed — the key pool is loaded once at startup and shared across all callers.

---

## Key Facts for New Modules

- **Nothing to configure** — import `next_fast_client` or `run_council` and you're on the shared pool
- **Key pool is module-agnostic** — all routers share the same `itertools.cycle` instance
- **`ProviderClient`** wraps `AsyncOpenAI` + `model` + `name` + `key_hint` — use `pc.client` and `pc.model`
- **Mistral is optional** — if `MISTRAL_API_KEY` is not set, all fast-mode calls stay on NVIDIA
- **Council always uses fixed models** — not affected by fast-mode provider cycle
- **`<think>` blocks are stripped** — DeepSeek R1 and Qwen thinking-mode tokens are removed before any response reaches the user or logs
