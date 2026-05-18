"""
run_pipeline.py
Master runner — executes all loaders in dependency order.

Usage (from Database/scripts/):
    # Set env vars first (see .env.example), then:
    python utils/run_pipeline.py            # run everything
    python utils/run_pipeline.py --from 6   # resume from step 6
    python utils/run_pipeline.py --only 3   # run only step 3
"""

import argparse
import importlib.util
import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

# scripts/ directory (one level above this file's utils/ directory)
SCRIPTS_DIR = os.path.dirname(os.path.dirname(__file__))

# Ordered list: (step_number, path_relative_to_scripts_dir, description)
# ── Reference data ──────────────────────────────────────────────────────────
PIPELINE = [
    (1,  'reference/load_venues.py',                                    'Venues'),

# ── Google Places API pipeline ───────────────────────────────────────────────
    (2,  'pipeline/google_places_api/step3_signals_extraction.py',      'Google primitives (54 signals)'),
    (3,  'pipeline/google_places_api/step4_cluster_and_patterns.py',    'Google behavioral clusters + patterns'),
    (4,  'pipeline/google_places_api/step4b_governance.py',             'Google data quality + drift signals'),
    (5,  'pipeline/google_places_api/step4b_pattern_scores.py',         'Google pattern scores'),
    (6,  'pipeline/google_places_api/step5_fitness_scores.py',          'Google fitness scores'),
    (7,  'pipeline/google_places_api/step5b_similarity_enrichment.py',  'Google venue vectors + similarity pairs'),
    (8,  'pipeline/google_places_api/step6_mechanisms_and_interventions.py', 'Google step6 → mechanisms + interventions'),

# ── MagicPin upper pipeline ───────────────────────────────────────────────────
    (9,  'pipeline/magicpin_upper/step3_signals_extraction.py',         'MagicPin primitives'),
    (10, 'pipeline/magicpin_upper/step4_cluster_and_patterns.py',       'MagicPin patterns + clusters'),
    (11, 'pipeline/magicpin_upper/step4b_governance.py',                'MagicPin governance'),
    (12, 'pipeline/magicpin_upper/step4b_pattern_scores.py',            'MagicPin pattern scores'),
    (13, 'pipeline/magicpin_upper/step5b_similarity_enrichment.py',     'MagicPin vectors + similarity'),
    (14, 'pipeline/magicpin_upper/step6_fitness_and_interventions.py',  'MagicPin fitness + interventions'),

# ── Blend ─────────────────────────────────────────────────────────────────────
    (15, 'blend/blend_fitness.py',                                      'Blend all sources → source=blended'),

# ── Static / reference data (run once) ───────────────────────────────────────
    (16, 'reference/load_surveys.py',                                   'Survey responses + archetypes'),
    (17, 'reference/load_marketing_engine.py',                          'Marketing engine lookup tables'),
    (18, 'reference/load_demographics.py',                              'Demographic segments & archetype mappings'),

# ── Compute (run after all sources loaded) ────────────────────────────────────
    (19, 'compute/compute_venue_demographics.py',                       'Venue→segment scores + similarity rank'),
    (20, 'compute/compute_fitness_deltas.py',                           'Delta rules + pre-computed similarity deltas'),
]


def load_and_run(filepath: str) -> None:
    path = os.path.join(SCRIPTS_DIR, filepath)
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
                        help='Resume from this step number (e.g. 6 = step5_fitness_scores)')
    parser.add_argument('--only',  dest='only_step', type=int, default=None,
                        help='Run only this step number (e.g. 8)')
    args = parser.parse_args()

    if not check_env():
        sys.exit(1)

    steps = PIPELINE
    if args.only_step:
        steps = [(n, f, d) for n, f, d in PIPELINE if n == args.only_step]
        if not steps:
            print(f"[ERROR] No step with number {args.only_step}")
            sys.exit(1)
    elif args.from_step:
        steps = [(n, f, d) for n, f, d in PIPELINE if n >= args.from_step]

    total_start = time.time()
    print("\n" + "="*60)
    print("  POLYNOVEA MODULE 2 — DATA PIPELINE")
    print(f"  Running {len(steps)} script(s)")
    print("="*60)

    for i, (num, filepath, desc) in enumerate(steps, 1):
        print(f"\n[{i}/{len(steps)}] {filepath}  ({desc})")
        print("-" * 60)
        step_start = time.time()
        try:
            load_and_run(filepath)
        except Exception as e:
            print(f"\n[PIPELINE ERROR] {filepath} failed: {e}")
            print("Stopping pipeline. Fix the error and resume with:")
            print(f"  python utils/run_pipeline.py --from {num}\n")
            sys.exit(1)
        elapsed = round(time.time() - step_start, 1)
        print(f"  Done in {elapsed}s")

    total = round(time.time() - total_start, 1)
    print("\n" + "="*60)
    print(f"  ALL SCRIPTS COMPLETE  ({total}s total)")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
