"""
Module 2 Research Extraction Pipeline
======================================
Reads all markdown files in research/ and produces:
  output/claims.json         — structured segment×channel claims
  output/archetypes.json     — archetype marketing briefs
  output/contradictions.json — conflicting claims for human review
  output/rag_chunks.jsonl    — flat chunks ready for vector retrieval

Usage:
  cd research_pipeline
  python extract.py                    # full run
  python extract.py --force            # ignore cache, re-extract everything
  python extract.py --skip-contradictions  # faster run, skip contradiction detection

The existing system (marketing.py, prompts.py) is NOT modified.
"""

import os
import sys
import json
import hashlib
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load .env — check project root, App/backend, then pipeline dir
_HERE = Path(__file__).parent
_ROOT = _HERE.parent
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT / "App" / "backend" / ".env", override=False)
load_dotenv(_HERE / ".env", override=False)

sys.path.insert(0, str(_HERE))

from config import (
    RESEARCH_DIR, OUTPUT_DIR, CACHE_FILE,
    EXTRACT_MODEL_ENV, EXTRACT_MODEL_DEFAULT,
)
from llm_client import get_client
from extractors.claims import extract_claims
from extractors.archetypes import extract_archetypes
from extractors.contradictions import detect_contradictions


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict):
    CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _per_file_cache_path(stem: str, kind: str) -> Path:
    return OUTPUT_DIR / f".{kind}_{stem}.json"


def _build_rag_chunks(claims: list[dict], archetypes: dict) -> list[dict]:
    chunks: list[dict] = []

    for i, c in enumerate(claims):
        donts = "; ".join(c["dont"]) if c["dont"] else "none specified"
        text = (
            f"Marketing claim for {c['segment']} segment on {c['channel']}: "
            f"{c['claim']} "
            f"Why it works: {c['why_it_works']} "
            f"India verdict: {c['india_verdict']}. "
            f"Avoid: {donts}."
        )
        chunks.append({
            "chunk_id":      f"claim_{c['segment']}_{c['channel']}_{i}",
            "type":          "claim",
            "segment":       c["segment"],
            "channel":       c["channel"],
            "text":          text,
            "confidence":    c["confidence"],
            "india_verdict": c["india_verdict"],
            "source_file":   c["source_file"],
        })

    for arch_key, arch in archetypes.items():
        donts = "; ".join(arch.get("dont", [])) or "none specified"
        text = (
            f"Archetype {arch_key}: "
            f"Tone: {arch.get('tone', '')}. "
            f"Emotional driver: {arch.get('emotional_driver', '')}. "
            f"Hook: {arch.get('hook_formula', '')}. "
            f"CTA: {arch.get('cta_style', '')}. "
            f"Visuals: {arch.get('visual_direction', '')}. "
            f"India adjustment: {arch.get('india_adjustment', '')}. "
            f"India verdict: {arch.get('india_verdict', '')}. "
            f"Language: {arch.get('language_rec', '')}. "
            f"Trust first: {arch.get('trust_first', False)}. "
            f"Avoid: {donts}."
        )
        chunks.append({
            "chunk_id":      f"archetype_{arch_key}",
            "type":          "archetype",
            "archetype":     arch_key,
            "text":          text,
            "confidence":    arch.get("confidence", 0.5),
            "india_verdict": arch.get("india_verdict", "NOT_STATED"),
            "source_files":  arch.get("source_files", []),
        })

    return chunks


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Module 2 Research Extraction Pipeline")
    parser.add_argument("--force",                action="store_true", help="Ignore cache, re-extract all files")
    parser.add_argument("--skip-contradictions",  action="store_true", help="Skip contradiction detection (faster)")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    model = os.getenv(EXTRACT_MODEL_ENV, EXTRACT_MODEL_DEFAULT)
    client = get_client()

    print("=" * 55)
    print("Module 2 Research Extraction Pipeline")
    print("=" * 55)
    print(f"Model:        {model}")
    print(f"Research dir: {RESEARCH_DIR}")
    print(f"Output dir:   {OUTPUT_DIR}")
    print(f"Force:        {args.force}")
    print()

    if not RESEARCH_DIR.exists():
        print(f"ERROR: research/ directory not found at {RESEARCH_DIR}")
        sys.exit(1)

    md_files = sorted(RESEARCH_DIR.glob("*.md"))
    if not md_files:
        print("ERROR: No markdown files found in research/")
        sys.exit(1)

    print(f"Found {len(md_files)} research files\n")

    cache = {} if args.force else _load_cache()
    all_claims: list[dict] = []
    archetype_merged: dict[str, dict] = {}

    for f in md_files:
        h = _file_hash(f)
        cache_claims = _per_file_cache_path(f.stem, "claims")
        cache_archs  = _per_file_cache_path(f.stem, "archetypes")

        if not args.force and cache.get(f.name) == h and cache_claims.exists() and cache_archs.exists():
            print(f"  [cache] {f.name}")
            all_claims.extend(json.loads(cache_claims.read_text(encoding="utf-8")))
            for arch in json.loads(cache_archs.read_text(encoding="utf-8")):
                _merge_archetype(archetype_merged, arch)
            continue

        print(f"  [extract] {f.name}")

        # Claims extraction
        try:
            claims = extract_claims(f, client, model)
            print(f"    claims: {len(claims)}")
            all_claims.extend(claims)
            _write_json(cache_claims, claims)
        except Exception as e:
            print(f"    [error] claims extraction failed: {e}")
            claims = []
            _write_json(cache_claims, [])

        time.sleep(2.0)

        # Archetypes extraction
        try:
            archetypes = extract_archetypes(f, client, model)
            print(f"    archetypes: {len(archetypes)}")
            for arch in archetypes:
                _merge_archetype(archetype_merged, arch)
            _write_json(cache_archs, archetypes)
        except Exception as e:
            print(f"    [error] archetypes extraction failed: {e}")
            _write_json(cache_archs, [])

        cache[f.name] = h
        _save_cache(cache)
        time.sleep(2.0)

    # Deduplicate claims (same segment+channel+claim prefix from multiple files)
    seen: set[tuple] = set()
    deduped: list[dict] = []
    for c in all_claims:
        key = (c["segment"], c["channel"], c["claim"][:80])
        if key not in seen:
            seen.add(key)
            deduped.append(c)
    deduped.sort(key=lambda x: (x["segment"], x["channel"]))

    # Contradiction detection
    contradictions: list[dict] = []
    if not args.skip_contradictions and deduped:
        print(f"\nDetecting contradictions across {len(deduped)} claims...")
        try:
            contradictions = detect_contradictions(deduped, client, model)
            print(f"  found: {len(contradictions)}")
        except Exception as e:
            print(f"  [error] contradiction detection failed: {e}")

    # RAG chunks
    rag_chunks = _build_rag_chunks(deduped, archetype_merged)

    # Write final outputs
    _write_json(OUTPUT_DIR / "claims.json",        deduped)
    _write_json(OUTPUT_DIR / "archetypes.json",    archetype_merged)
    _write_json(OUTPUT_DIR / "contradictions.json", contradictions)

    rag_path = OUTPUT_DIR / "rag_chunks.jsonl"
    rag_path.write_text(
        "\n".join(json.dumps(c, ensure_ascii=False) for c in rag_chunks),
        encoding="utf-8",
    )

    summary = {
        "run_at":               datetime.now(timezone.utc).isoformat(),
        "model":                model,
        "research_files":       len(md_files),
        "claims_extracted":     len(deduped),
        "archetypes_extracted": len(archetype_merged),
        "contradictions_found": len(contradictions),
        "rag_chunks":           len(rag_chunks),
    }
    _write_json(OUTPUT_DIR / "run_summary.json", summary)

    print()
    print("=" * 55)
    print(f"Claims extracted:     {len(deduped)}")
    print(f"Archetypes extracted: {len(archetype_merged)}")
    print(f"Contradictions found: {len(contradictions)}")
    print(f"RAG chunks:           {len(rag_chunks)}")
    print(f"Output:               {OUTPUT_DIR}/")
    print("=" * 55)

    if contradictions:
        print(f"\nReview contradictions in: output/contradictions.json")
        print("Fill in the 'resolution' field for each conflict.")


def _merge_archetype(store: dict, arch: dict):
    key = arch.get("archetype", "")
    if not key:
        return
    if key not in store:
        store[key] = arch
    else:
        existing = store[key]
        new_conf = float(arch.get("confidence", 0))
        old_conf = float(existing.get("confidence", 0))
        # Union source files
        existing["source_files"] = list(set(
            existing.get("source_files", []) + arch.get("source_files", [])
        ))
        if new_conf > old_conf:
            arch["source_files"] = existing["source_files"]
            arch["extracted_at"] = existing.get("extracted_at", arch.get("extracted_at"))
            store[key] = arch


if __name__ == "__main__":
    main()
