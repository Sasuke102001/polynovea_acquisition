import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from llm_client import call_llm, extract_json

_SYSTEM = """You are detecting contradictions in marketing research claims about Indian F&B venues.

Given claims about the same customer segment and marketing channel from different research files,
identify if any claims genuinely contradict each other.

A real contradiction means:
- One claim says a channel is effective for a segment; another says it is not
- Claims give conflicting specific guidance (e.g. "send at 11 AM" vs "send at 6 PM")
- india_verdict is "CONFIRMED" in one file and "UNCONFIRMED" or "ADJUST" in another
- One claim warns against something that another explicitly recommends

Do NOT flag as contradiction:
- Claims that are about different aspects of the same channel (complementary, not conflicting)
- Minor wording differences that mean the same thing
- One claim being more specific than another

Return a JSON object with exactly these fields:
- has_contradiction: true or false
- conflict_type: "effectiveness_disagreement" | "timing_conflict" | "audience_mismatch" | "verdict_conflict" | "guidance_conflict" | null
- summary: 1-2 sentence description of the specific conflict (null if no contradiction)
- resolution: null (always null — human reviews fill this in)

Return only the JSON object."""


def detect_contradictions(all_claims: list[dict], client, model: str) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for claim in all_claims:
        key = (claim["segment"], claim["channel"])
        groups[key].append(claim)

    contradictions: list[dict] = []

    pairs = [(k, v) for k, v in groups.items() if len({c["source_file"] for c in v}) >= 2]
    print(f"  checking {len(pairs)} segment×channel pairs with multi-file claims...")

    for i, ((segment, channel), claims) in enumerate(pairs):
        claims_text = "\n".join(
            f"[{c['source_file']}] verdict={c['india_verdict']} conf={c['confidence']:.2f}: {c['claim']}"
            for c in claims
        )
        user_msg = f"Segment: {segment}\nChannel: {channel}\n\nClaims from different research files:\n{claims_text}"

        try:
            raw = call_llm(client, model, _SYSTEM, user_msg)
            result = extract_json(raw)
            if isinstance(result, dict) and result.get("has_contradiction"):
                contradictions.append({
                    "segment":      segment,
                    "channel":      channel,
                    "claims":       [
                        {
                            "claim":         c["claim"],
                            "source":        c["source_file"],
                            "confidence":    c["confidence"],
                            "india_verdict": c["india_verdict"],
                        }
                        for c in claims
                    ],
                    "conflict_type": result.get("conflict_type"),
                    "summary":       result.get("summary"),
                    "resolution":    None,
                })
            if i < len(pairs) - 1:
                time.sleep(0.3)
        except Exception as e:
            print(f"    [warn] contradiction check failed for {segment}×{channel}: {e}")

    return contradictions
