"""
run_pipeline.py
Master runner — executes all loaders in dependency order.

Usage:
    # Set env vars first (see .env.example), then:
    python run_pipeline.py            # run everything
    python run_pipeline.py --from 4   # resume from script 004
    python run_pipeline.py --only 2   # run only 002
"""

import argparse
import importlib.util
import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

SCRIPTS_DIR = os.path.dirname(__file__)

# Ordered list: (script_number, filename, description)
# ── Google Places pipeline ──────────────────────────────────────────────────
PIPELINE = [
    (2,  '002_load_venues.py',               'Venues'),
    (10, '010_load_primitives.py',           'Google primitives (54 signals)'),
    (3,  '003_load_patterns.py',             'Google behavioral patterns + venue links'),
    (19, '019_load_google_step4_clusters.py','Google step4 clusters → raw_venue_data'),
    (7,  '007_load_governance.py',           'Google data quality + drift signals'),
    (6,  '006_load_pattern_scores.py',       'Google pattern scores'),
    (4,  '004_load_scores.py',              'Google fitness scores'),
    (5,  '005_load_similarity.py',           'Google venue vectors + similarity pairs'),
    (20, '020_load_google_step6.py',         'Google step6 → raw_venue_data'),

# ── MagicPin upper pipeline ─────────────────────────────────────────────────
    (21, '021_load_magicpin_step3.py',       'MagicPin primitives'),
    (22, '022_load_magicpin_step4.py',       'MagicPin patterns + clusters'),
    (23, '023_load_magicpin_step4b.py',      'MagicPin governance'),
    (24, '024_load_magicpin_step5_scores.py','MagicPin pattern scores'),
    (25, '025_load_magicpin_step5b.py',      'MagicPin vectors + similarity'),
    (26, '026_load_magicpin_step6_fitness.py','MagicPin fitness + interventions'),

# ── Blend ───────────────────────────────────────────────────────────────────
    (27, '027_blend_fitness.py',             'Blend all sources → source=blended'),

# ── Static / reference data (run once) ─────────────────────────────────────
    (8,  '008_load_surveys.py',              'Survey responses + archetypes'),
    (9,  '009_load_marketing_engine.py',     'Marketing engine lookup tables'),
    (11, '011_load_demographics.py',         'Demographic segments & archetype mappings'),

# ── Compute (run after all sources loaded) ──────────────────────────────────
    (12, '012_compute_venue_demographics.py','Venue→segment scores + similarity rank'),
    (13, '013_compute_fitness_deltas.py',    'Delta rules + pre-computed similarity deltas'),
]


def load_and_run(filename: str) -> None:
    path = os.path.join(SCRIPTS_DIR, filename)
    spec = importlib.util.spec_from_file_location('module', path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()


def check_env() -> bool:
    missing = [k for k in ('PG_HOST', 'PG_DB', 'PG_USER', 'PG_PASSWORD')
               if not os.getenv(k)]
    if missing:
        print(f"\n[ERROR] Missing environment variables: {', '.join(missing)}")
        print("  Set them or copy .env.example → .env and load it first.\n")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description='Polynovea Module 2 — Data Pipeline Runner')
    parser.add_argument('--from',  dest='from_step', type=int, default=None,
                        help='Resume from this script number (e.g. 4 = 004_load_scores.py)')
    parser.add_argument('--only',  dest='only_step', type=int, default=None,
                        help='Run only this script number (e.g. 7)')
    args = parser.parse_args()

    if not check_env():
        sys.exit(1)

    steps = PIPELINE
    if args.only_step:
        steps = [(n, f, d) for n, f, d in PIPELINE if n == args.only_step]
        if not steps:
            print(f"[ERROR] No script with number {args.only_step}")
            sys.exit(1)
    elif args.from_step:
        steps = [(n, f, d) for n, f, d in PIPELINE if n >= args.from_step]

    total_start = time.time()
    print("\n" + "="*60)
    print("  POLYNOVEA MODULE 2 — DATA PIPELINE")
    print(f"  Running {len(steps)} script(s)")
    print("="*60)

    for i, (num, filename, desc) in enumerate(steps, 1):
        print(f"\n[{i}/{len(steps)}] {filename}  ({desc})")
        print("-" * 60)
        step_start = time.time()
        try:
            load_and_run(filename)
        except Exception as e:
            print(f"\n[PIPELINE ERROR] {filename} failed: {e}")
            print("Stopping pipeline. Fix the error and resume with:")
            print(f"  python run_pipeline.py --from {num}\n")
            sys.exit(1)
        elapsed = round(time.time() - step_start, 1)
        print(f"  Done in {elapsed}s")

    total = round(time.time() - total_start, 1)
    print("\n" + "="*60)
    print(f"  ALL SCRIPTS COMPLETE  ({total}s total)")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
