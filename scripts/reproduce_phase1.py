#!/usr/bin/env python
"""One-click reproduction entry point.

    python scripts/reproduce_phase1.py --stage m7b
    python scripts/reproduce_phase1.py --stage all
    python scripts/reproduce_phase1.py --check          # what is missing?

Every stage prints exactly which input file it needs and where to obtain it.
Nothing ever silently falls back to a developer-machine path.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# stage -> (module path, human description, [required inputs])
STAGES: dict[str, dict] = {
    "m7b": {
        "module": "eov/m7b_zero_measurement_gate.py",
        "desc": "M7-B zero-measurement transferability gate (NO-GO)",
        "needs": ["results/tables/M5_TRANSFER_MAP.csv",
                  "data/manifests/M6_WU2020_RESULT.json"],
        "downloads": [],
    },
    "m6": {
        "module": "eov/m6_wu2020_run.py",
        "desc": "M6 confirmatory test (Wu2020, 576 x 6)",
        "needs": ["data/external/Wu2020_RBS_epistasis/raw/"
                  "41467_2020_15102_MOESM6_ESM.xlsx"],
        "downloads": ["wu2020"],
    },
    "m5": {
        "module": "eov/m5_transfer_map.py",
        "desc": "M5 task-transferability map (discovery)",
        "needs": ["data/processed/M2_measurements.parquet",
                  "data/processed/M4_EXP1_V.npz",
                  "data/processed/M4_EXP2_V.npz",
                  "data/processed/M4_EXP3_S1_R.npz"],
        "downloads": ["tem1", "phillips2023"],
    },
    "m7": {
        "module": "eov/m7_sparse_probing.py",
        "desc": "M7 sparse future-task probing",
        "needs": ["data/processed/M2_measurements.parquet",
                  "data/processed/M6_WU2020_R.npz",
                  "results/tables/M5_TRANSFER_MAP.csv"],
        "downloads": ["tem1", "phillips2023", "wu2020"],
    },
    "m4": {
        "module": "eov/exp1_stability.py",
        "desc": "M4 Exp1 cross-budget stability (long-running)",
        "needs": ["data/processed/M2_measurements.parquet"],
        "downloads": ["tem1", "phillips2023"],
    },
}

ORDER = ["m4", "m5", "m6", "m7", "m7b"]


def report_missing(stage: str) -> list[str]:
    miss = [n for n in STAGES[stage]["needs"] if not (ROOT / n).exists()]
    if miss:
        print("\n  stage %r is missing %d input(s):" % (stage, len(miss)))
        for m in miss:
            print("     - %s" % m)
        dl = STAGES[stage]["downloads"]
        if dl:
            print("  obtain with:")
            for d in dl:
                print("     python scripts/fetch_public_data.py --dataset %s" % d)
        print("  full instructions: docs/DATA_ACCESS.md")
    return miss


def run_one(stage: str, allow_missing: bool) -> bool:
    st = STAGES[stage]
    print("\n" + "=" * 74)
    print("STAGE %-4s  %s" % (stage.upper(), st["desc"]))
    print("=" * 74)
    miss = report_missing(stage)
    if miss and not allow_missing:
        print("  -> SKIPPED (inputs absent)")
        return False
    mod = ROOT / st["module"]
    if not mod.exists():
        print("  !! module not found: %s" % mod)
        return False
    proc = subprocess.run([sys.executable, str(mod)], cwd=str(ROOT))
    ok = proc.returncode == 0
    print("  -> %s" % ("OK" if ok else "FAILED (exit %d)" % proc.returncode))
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default=None,
                    choices=ORDER + ["all", "check"])
    ap.add_argument("--check", action="store_true",
                    help="only report which inputs are present/absent")
    a = ap.parse_args()

    if a.check or a.stage == "check" or a.stage is None:
        print("input availability")
        print("-" * 74)
        for s in ORDER:
            miss = [n for n in STAGES[s]["needs"] if not (ROOT / n).exists()]
            print("  %-5s %-46s %s"
                  % (s, STAGES[s]["desc"][:46],
                     "ready" if not miss else "needs %d input(s)" % len(miss)))
        print("\n  M7-B runs with ZERO downloads (it only needs two small "
              "tracked files).")
        print("  Everything else needs third-party data: docs/DATA_ACCESS.md")
        return 0

    stages = ORDER if a.stage == "all" else [a.stage]
    results = {s: run_one(s, allow_missing=(a.stage == "all")) for s in stages}
    print("\n" + "=" * 74)
    print("SUMMARY")
    print("=" * 74)
    for s, ok in results.items():
        print("  %-5s %s" % (s, "OK" if ok else "skipped/failed"))
    return 0 if any(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
