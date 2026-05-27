import sys
import re
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SEGMENTS, CHANNELS, MAX_CHUNK_CHARS, MIN_SECTION_CHARS
from llm_client import call_llm, extract_json

_SYSTEM = f"""You are extracting marketing research claims from Indian F&B venue research documents.

Extract ONLY claims that explicitly relate to a specific customer segment AND a specific marketing channel.

Valid segments: {', '.join(SEGMENTS)}
Valid channels: {', '.join(CHANNELS)}

For each claim return a JSON object with exactly these fields:
- segment: one of the valid segments (exact match)
- channel: one of the valid channels (exact match)
- claim: the specific actionable claim (1-2 sentences, concrete and specific)
- confidence: 0.0-1.0 based on how specific and evidence-backed the claim is
- india_verdict: "CONFIRMED" | "ADJUST" | "UNCONFIRMED" | "NOT_STATED"
- why_it_works: behavioral/psychological mechanism (1 sentence)
- dont: list of strings — what NOT to do for this segment×channel (can be empty list)

Rules:
- Use segment and channel values from the valid lists ONLY — exact match, no variations
- Skip vague claims like "social media works well" — only extract specific, actionable claims
- If a section has no relevant claims, return []
- Return a valid JSON array and nothing else

Example:
[
  {{
    "segment": "office_workers",
    "channel": "whatsapp",
    "claim": "Send lunch broadcasts between 11:30 AM and 12:30 PM — this is the pre-lunch decision window with highest open rates",
    "confidence": 0.90,
    "india_verdict": "CONFIRMED",
    "why_it_works": "Time scarcity drives habitual decision-making; WhatsApp 98% open rate beats all other channels",
    "dont": ["Never send before 9 AM or after 9 PM", "Avoid promotional broadcasts without opt-in"]
  }}
]"""


def _split_sections(text: str) -> list[str]:
    parts = re.split(r'\n(?=#{1,3} )', text)
    chunks = []
    for part in parts:
        part = part.strip()
        if len(part) < MIN_SECTION_CHARS:
            continue
        if len(part) <= MAX_CHUNK_CHARS:
            chunks.append(part)
        else:
            # Slide over large sections with 50-word overlap
            words = part.split()
            buf: list[str] = []
            for word in words:
                buf.append(word)
                if sum(len(w) + 1 for w in buf) >= MAX_CHUNK_CHARS:
                    chunks.append(" ".join(buf))
                    buf = buf[-50:]
            if buf and sum(len(w) + 1 for w in buf) >= MIN_SECTION_CHARS:
                chunks.append(" ".join(buf))
    return chunks


def extract_claims(file_path: Path, client, model: str) -> list[dict]:
    text = file_path.read_text(encoding="utf-8")
    sections = _split_sections(text)
    all_claims: list[dict] = []
    seen: set[tuple] = set()

    for i, section in enumerate(sections):
        try:
            raw = call_llm(client, model, _SYSTEM, section)
            items = extract_json(raw)
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                seg = item.get("segment", "")
                ch = item.get("channel", "")
                if seg not in SEGMENTS or ch not in CHANNELS:
                    continue
                claim_text = item.get("claim", "").strip()
                if not claim_text or len(claim_text) < 20:
                    continue
                key = (seg, ch, claim_text[:80])
                if key in seen:
                    continue
                seen.add(key)
                all_claims.append({
                    "segment":       seg,
                    "channel":       ch,
                    "claim":         claim_text,
                    "confidence":    round(float(item.get("confidence", 0.5)), 2),
                    "india_verdict": item.get("india_verdict", "NOT_STATED"),
                    "why_it_works":  item.get("why_it_works", ""),
                    "dont":          [d for d in item.get("dont", []) if isinstance(d, str)],
                    "source_file":   file_path.name,
                    "extracted_at":  datetime.now(timezone.utc).isoformat(),
                })
            # Delay between sections to stay under rate limits
            if i < len(sections) - 1:
                time.sleep(1.5)
        except Exception as e:
            print(f"    [warn] section {i+1}/{len(sections)} failed: {e}")
            continue

    return all_claims
