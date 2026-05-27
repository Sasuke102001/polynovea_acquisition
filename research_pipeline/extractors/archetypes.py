import sys
import re
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ARCHETYPES, MAX_CHUNK_CHARS, MIN_SECTION_CHARS
from llm_client import call_llm, extract_json

_SYSTEM = f"""You are extracting archetype-specific marketing brief data from Indian F&B venue research.

Valid archetypes: {', '.join(ARCHETYPES)}

For each archetype found in the text, return a JSON object with exactly these fields:
- archetype: one of the valid archetypes (exact match)
- tone: creative tone guidance (1-2 sentences)
- emotional_driver: primary psychological mechanism (e.g. "social_proof + fomo")
- hook_formula: how to structure the opening hook (1-2 sentences)
- cta_style: call to action style (1 sentence)
- visual_direction: what visuals or format to use (1-2 sentences)
- india_adjustment: India-specific modification — what changes for the Indian market (1-2 sentences, or null)
- india_verdict: "CONFIRMED" | "ADJUST" | "NOT_STATED"
- dont: list of strings — what NOT to do for this archetype
- language_rec: "Hinglish" | "English-ok" | "Regional" | "NOT_STATED"
- trust_first: true if you must establish trust before any urgency or scarcity, false otherwise
- confidence: 0.0-1.0

Rules:
- Only use archetype values from the valid list — exact match, no variations
- If an archetype appears multiple times, extract the most detailed occurrence
- If no archetypes found in this section, return []
- Return a valid JSON array and nothing else

Example:
[
  {{
    "archetype": "comfort_dweller",
    "tone": "Safety, no surprises — familiar environment is the draw, not the food",
    "emotional_driver": "environmental_expectation + habit_formation",
    "hook_formula": "Environment confidence + consistency. Quiet corner, your usual, nobody rushes you.",
    "cta_style": "Soft, non-pressuring. Your regular table is waiting.",
    "visual_direction": "Quiet corner, soft lighting, consistent plating, clean visible hygiene",
    "india_adjustment": "Post-pandemic 61% prefer familiar environments; safety signal essential especially for women",
    "india_verdict": "CONFIRMED",
    "dont": ["Never FOMO or urgency language", "Avoid crowd or noise visuals", "Never show experimental dishes"],
    "language_rec": "Hinglish",
    "trust_first": true,
    "confidence": 0.88
  }}
]"""


def _split_sections(text: str) -> list[str]:
    parts = re.split(r'\n(?=#{1,3} )', text)
    chunks = []
    for part in parts:
        part = part.strip()
        if len(part) >= MIN_SECTION_CHARS:
            chunks.append(part[:MAX_CHUNK_CHARS])
    return chunks


def extract_archetypes(file_path: Path, client, model: str) -> list[dict]:
    text = file_path.read_text(encoding="utf-8")
    sections = _split_sections(text)
    by_archetype: dict[str, dict] = {}

    for i, section in enumerate(sections):
        try:
            raw = call_llm(client, model, _SYSTEM, section)
            items = extract_json(raw)
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                arch = item.get("archetype", "")
                if arch not in ARCHETYPES:
                    continue
                new_conf = float(item.get("confidence", 0.5))

                if arch not in by_archetype:
                    item["source_files"] = [file_path.name]
                    item["extracted_at"] = datetime.now(timezone.utc).isoformat()
                    item["confidence"] = round(new_conf, 2)
                    by_archetype[arch] = item
                else:
                    existing = by_archetype[arch]
                    old_conf = float(existing.get("confidence", 0))
                    # Union source files
                    if file_path.name not in existing.get("source_files", []):
                        existing["source_files"].append(file_path.name)
                    # Replace with higher-confidence version
                    if new_conf > old_conf:
                        item["source_files"] = existing["source_files"]
                        item["extracted_at"] = existing["extracted_at"]
                        item["confidence"] = round(new_conf, 2)
                        by_archetype[arch] = item

            if i < len(sections) - 1:
                time.sleep(1.5)
        except Exception as e:
            print(f"    [warn] archetype section {i+1}/{len(sections)} failed: {e}")
            continue

    return list(by_archetype.values())
