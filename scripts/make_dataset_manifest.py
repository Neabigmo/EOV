#!/usr/bin/env python
"""Derive `configs/dataset_manifest.csv` from `data_registry/PROVENANCE_LEDGER.csv`.

Derived, never hand-copied: change the ledger, re-run this script.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

COLS = ["dataset_id", "protein_or_system", "role", "source_type",
        "official_source", "paper_license", "source_data_license",
        "analysis_allowed", "redistribution_allowed", "redistribution_basis",
        "theoretical_space_size", "complete_product", "observed_genotype_count"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="configs/dataset_manifest.csv")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    src = root / "data_registry" / "PROVENANCE_LEDGER.csv"
    if not src.exists():
        raise SystemExit("missing %s" % src)
    rows = list(csv.DictReader(src.open(encoding="utf-8")))
    out = root / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            r = dict(r)
            r["official_source"] = r.get("original_deposit_url", "")
            w.writerow(r)
    n_redis = sum(1 for r in rows
                  if str(r.get("redistribution_allowed", "")).upper() == "TRUE")
    print("wrote %s  (%d datasets)" % (out, len(rows)))
    print("  redistribution_allowed = TRUE : %d" % n_redis)
    print("  redistribution_allowed = FALSE: %d  (fetch from official source)"
          % (len(rows) - n_redis))
    print("  NOTE: this release redistributes NO dataset, regardless of license.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
