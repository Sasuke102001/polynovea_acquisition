"""
enrich_step5b.py
Adds place_id to step_5b_similarity.json for ALL sources so DB loaders
can join on place_id (unique) instead of venue_name (fragile text).

Sources handled:
  google         — lookup built from step_1_venues_refined.json (has place_id)
  magicpin_upper — lookup built from step_3_signals_extracted.json (has place_id)

Run before:
  005_load_similarity.py          (google)
  025_load_magicpin_step5b.py     (magicpin_upper)

Output per city/region:
  step_5b_similarity_enriched.json
  data/processed/name_mismatch_report.json  (combined across all sources)
"""

import json
import os
import re
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

SCRIPTS_DIR    = os.path.dirname(__file__)
PROCESSED_PATH = os.path.join(SCRIPTS_DIR, '..', '..', 'data', 'processed')

# -----------------------------------------------------------------------
# Source configuration
# Each entry defines:
#   base_path   — root folder containing region/city subdirectories
#   regions     — list of subdirectory names
#   lookup_file — file to build name→place_id lookup from
#   lookup_key  — top-level key in that file containing the venue list
#   name_field  — field name for venue name inside each venue object
#   id_field    — field name for place_id inside each venue object
# -----------------------------------------------------------------------
SOURCES = [
    {
        'name':        'google',
        'base_path':   os.path.join(SCRIPTS_DIR, '..', '..', 'data', 'raw', 'google_places'),
        'regions':     ['navi-mumbai', 'mumbai-sobo', 'mumbai-main', 'thane'],
        'lookup_file': 'step_1_venues_refined.json',
        'lookup_key':  None,        # file IS the list at top level
        'name_field':  'name',
        'id_field':    'place_id',
    },
    {
        'name':        'magicpin_upper',
        'base_path':   os.path.join(SCRIPTS_DIR, '..', '..', 'data', 'raw', 'magicpin'),
        'regions':     ['mumbai', 'navi-mumbai', 'sobo', 'thane'],
        'lookup_file': 'step_3_signals_extracted.json',
        'lookup_key':  'venues',    # file has {"venues": [...]}
        'name_field':  'name',      # step_3 uses 'name', not 'venue_name'
        'id_field':    'place_id',
    },
]


def normalize(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'[–—]', '-', name)
    return name


def build_lookup(lookup_path: str, lookup_key, name_field: str, id_field: str) -> dict:
    with open(lookup_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    venues = data[lookup_key] if lookup_key else data
    lookup = {}
    for v in venues:
        key = normalize(v.get(name_field, ''))
        if key and key not in lookup:
            lookup[key] = v.get(id_field)
    return lookup


def enrich_entry(entry: dict, lookup: dict, mismatches: list, context: str) -> dict:
    name  = entry.get('venue_name', '')
    key   = normalize(name)
    pid   = lookup.get(key)
    entry['place_id'] = pid
    if not pid:
        mismatches.append({'venue_name': name, 'context': context})
    return entry


def enrich_region(source_cfg: dict, region: str) -> dict:
    base      = os.path.join(source_cfg['base_path'], region)
    step5b    = os.path.join(base, 'step_5b_similarity.json')
    lkp_file  = os.path.join(base, source_cfg['lookup_file'])
    out_path  = os.path.join(base, 'step_5b_similarity_enriched.json')

    if not os.path.exists(step5b):
        print(f"    [SKIP] step_5b_similarity.json not found: {step5b}")
        return {'region': region, 'total': 0, 'enriched': 0, 'pool_enriched': 0, 'mismatches': []}

    if not os.path.exists(lkp_file):
        print(f"    [SKIP] lookup file not found: {lkp_file}")
        return {'region': region, 'total': 0, 'enriched': 0, 'pool_enriched': 0, 'mismatches': []}

    lookup = build_lookup(
        lkp_file,
        source_cfg['lookup_key'],
        source_cfg['name_field'],
        source_cfg['id_field'],
    )

    with open(step5b, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mismatches    = []
    enriched      = 0
    pool_enriched = 0

    for entry in data.get('venue_similarity', []):
        enrich_entry(entry, lookup, mismatches, context='primary_venue')
        if entry.get('place_id'):
            enriched += 1

        for similar in entry.get('similar_venues_pool', []):
            enrich_entry(
                similar, lookup, mismatches,
                context=f"similar_of:{entry.get('venue_name', '?')}"
            )
            if similar.get('place_id'):
                pool_enriched += 1

    data['enriched_at']     = datetime.utcnow().isoformat()
    data['enriched_by']     = 'enrich_step5b.py'
    data['enriched_source'] = source_cfg['name']
    data['join_key']        = 'place_id'

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    total = len(data.get('venue_similarity', []))
    primary_miss = len([m for m in mismatches if m['context'] == 'primary_venue'])
    print(f"    {region:<15}  {enriched}/{total} primary  |  {pool_enriched} pool  |  {primary_miss} mismatches")

    return {
        'region':       region,
        'total':        total,
        'enriched':     enriched,
        'pool_enriched': pool_enriched,
        'mismatches':   mismatches,
    }


def run_source(source_cfg: dict) -> list:
    name = source_cfg['name']
    print(f"\n  Source: {name}")
    print(f"  {'─'*50}")

    results = []
    for region in source_cfg['regions']:
        result = enrich_region(source_cfg, region)
        results.append(result)

    total    = sum(r['total']    for r in results)
    enriched = sum(r['enriched'] for r in results)
    misses   = sum(len(r['mismatches']) for r in results if r['mismatches'])
    print(f"  → {enriched}/{total} enriched  |  {misses} total mismatches")
    return results


def main():
    os.makedirs(PROCESSED_PATH, exist_ok=True)
    print("\nenrich_step5b.py — Adding place_id to step_5b_similarity for all sources\n")

    all_mismatches = []
    report_summary = []

    for source_cfg in SOURCES:
        results = run_source(source_cfg)
        for r in results:
            all_mismatches.extend([
                {**m, 'source': source_cfg['name']}
                for m in r.get('mismatches', [])
            ])
            report_summary.append({
                'source':       source_cfg['name'],
                'region':       r['region'],
                'total':        r['total'],
                'enriched':     r['enriched'],
                'pool_enriched': r['pool_enriched'],
                'mismatches':   len(r.get('mismatches', [])),
            })

    report = {
        'generated_at':     datetime.utcnow().isoformat(),
        'total_mismatches': len(all_mismatches),
        'summary':          report_summary,
        'mismatches':       all_mismatches,
    }

    report_path = os.path.join(PROCESSED_PATH, 'name_mismatch_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*55}")
    print(f"  COMPLETE")
    print(f"  Total mismatches : {len(all_mismatches)}")
    print(f"  Report saved     : data/processed/name_mismatch_report.json")
    print(f"{'='*55}\n")

    if all_mismatches:
        print("[WARN] Mismatched venues will fall back to name-based join in DB loaders.")
        print("       Review name_mismatch_report.json if coverage is unexpectedly low.\n")
    else:
        print("[OK] Zero mismatches across all sources.\n")


if __name__ == '__main__':
    main()
