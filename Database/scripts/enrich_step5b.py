"""
enrich_step5b.py
Enriches step_5b_similarity.json with place_id from step_1_venues_refined.json
so the DB load can join on place_id (unique) instead of venue_name (fragile text).

Run before any SQL load scripts.
Output: step_5b_similarity_enriched.json per city + name_mismatch_report.json
"""

import json
import os
import re
import sys
from datetime import datetime

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'google_places')
PROCESSED_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')

CITIES = ['navi-mumbai', 'mumbai-sobo', 'mumbai-main', 'thane']


def normalize(name: str) -> str:
    """Lowercase, strip whitespace, collapse spaces, normalize dashes."""
    name = name.lower().strip()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'[–—]', '-', name)
    return name


def build_lookup(step1_path: str) -> dict:
    """Build normalized_name -> place_id lookup from step_1_venues_refined.json."""
    with open(step1_path, 'r', encoding='utf-8') as f:
        venues = json.load(f)

    lookup = {}
    for v in venues:
        key = normalize(v['name'])
        if key in lookup:
            print(f"  [WARN] Duplicate name in step_1: '{v['name']}'")
        lookup[key] = {
            'place_id': v['place_id'],
            'name':     v['name'],
        }
    return lookup


def enrich_venue_entry(entry: dict, lookup: dict, mismatches: list, context: str) -> dict:
    """Add place_id to a venue dict. Records mismatch if not found."""
    name = entry.get('venue_name', '')
    key  = normalize(name)
    match = lookup.get(key)

    if match:
        entry['place_id'] = match['place_id']
    else:
        entry['place_id'] = None
        mismatches.append({'venue_name': name, 'context': context})

    return entry


def enrich_city(city: str) -> dict:
    """Enrich step_5b for one city. Returns mismatch summary."""
    city_path   = os.path.join(BASE_PATH, city)
    step1_path  = os.path.join(city_path, 'step_1_venues_refined.json')
    step5b_path = os.path.join(city_path, 'step_5b_similarity.json')
    out_path    = os.path.join(city_path, 'step_5b_similarity_enriched.json')

    print(f"\n{'='*55}")
    print(f"  City: {city}")
    print(f"{'='*55}")

    lookup = build_lookup(step1_path)
    print(f"  step_1 lookup built: {len(lookup)} venues")

    with open(step5b_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mismatches    = []
    enriched      = 0
    pool_enriched = 0
    pool_miss     = 0

    for venue_entry in data.get('venue_similarity', []):
        before = len(mismatches)
        enrich_venue_entry(venue_entry, lookup, mismatches, context='primary_venue')
        if venue_entry.get('place_id'):
            enriched += 1

        for similar in venue_entry.get('similar_venues_pool', []):
            pool_before = len(mismatches)
            enrich_venue_entry(
                similar, lookup, mismatches,
                context=f"similar_of:{venue_entry.get('venue_name','?')}"
            )
            if similar.get('place_id'):
                pool_enriched += 1
            elif len(mismatches) > pool_before:
                pool_miss += 1

    data['enriched_at'] = datetime.utcnow().isoformat()
    data['enriched_by'] = 'enrich_step5b.py'
    data['join_key']    = 'place_id'

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    primary_miss = len([m for m in mismatches if m['context'] == 'primary_venue'])
    total_venues = len(data.get('venue_similarity', []))

    print(f"  Primary venues  : {enriched}/{total_venues} enriched ({primary_miss} mismatches)")
    print(f"  Pool entries    : {pool_enriched} enriched ({pool_miss} mismatches)")
    print(f"  Output          : step_5b_similarity_enriched.json")

    return {
        'city':             city,
        'total_venues':     total_venues,
        'primary_enriched': enriched,
        'pool_enriched':    pool_enriched,
        'mismatches':       mismatches,
    }


def main():
    os.makedirs(PROCESSED_PATH, exist_ok=True)

    print("\nenrich_step5b.py -- Adding place_id to step_5b_similarity\n")

    all_mismatches = []
    summary        = []

    for city in CITIES:
        result = enrich_city(city)
        summary.append(result)
        all_mismatches.extend(result['mismatches'])

    report = {
        'generated_at':     datetime.utcnow().isoformat(),
        'total_mismatches': len(all_mismatches),
        'mismatches':       all_mismatches,
        'summary_by_city': [
            {
                'city':             r['city'],
                'total_venues':     r['total_venues'],
                'primary_enriched': r['primary_enriched'],
                'pool_enriched':    r['pool_enriched'],
                'mismatch_count':   len(r['mismatches']),
            }
            for r in summary
        ]
    }

    report_path = os.path.join(PROCESSED_PATH, 'name_mismatch_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    total_venues   = sum(r['total_venues']     for r in summary)
    total_enriched = sum(r['primary_enriched'] for r in summary)

    print(f"\n{'='*55}")
    print(f"  COMPLETE")
    print(f"  Total venues    : {total_venues}")
    print(f"  Enriched        : {total_enriched}")
    print(f"  Mismatches      : {len(all_mismatches)}")
    print(f"  Report saved    : data/processed/name_mismatch_report.json")
    print(f"{'='*55}\n")

    if all_mismatches:
        print("[WARN] Mismatched venues will have place_id = NULL in DB.")
        print("       Review name_mismatch_report.json before loading SQL.\n")
    else:
        print("[OK] Zero mismatches -- safe to run SQL load scripts.\n")


if __name__ == '__main__':
    main()
