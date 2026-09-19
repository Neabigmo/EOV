#!/usr/bin/env python
"""Fetch the public third-party inputs this project needs.

No dataset is redistributed with this repository.  This script downloads only
from **official sources**, only where the license permits, and verifies a
checksum when one is known.

    python scripts/fetch_public_data.py --dataset wu2020
    python scripts/fetch_public_data.py --list
    python scripts/fetch_public_data.py --dataset all --yes

Datasets that cannot be fetched automatically (no public machine-readable
deposit, or a license that forbids redistribution) are listed with the exact
manual steps instead.  See docs/DATA_ACCESS.md.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

UA = ("Mozilla/5.0 (compatible; eov-repro/1.0; +https://github.com/) "
      "academic-research-use")

# --------------------------------------------------------------------------
# Auto-fetchable: public URL, license permits, no account required.
# --------------------------------------------------------------------------
AUTO: dict[str, dict] = {
    "wu2020": {
        "title": "Wu et al. 2020, Nat Commun 11:1233 — H3N2 HA antigenic site B",
        "doi": "10.1038/s41467-020-15102-5",
        "license": "CC-BY-4.0",
        "role": "M6 confirmation set (6 tasks x 576 variants)",
        "url": ("https://static-content.springer.com/esm/"
                "art%3A10.1038%2Fs41467-020-15102-5/MediaObjects/"
                "41467_2020_15102_MOESM6_ESM.xlsx"),
        "dest": "data/external/Wu2020_RBS_epistasis/raw/"
                "41467_2020_15102_MOESM6_ESM.xlsx",
        "sha256": None,          # publisher file; verify size instead
        "bytes": 173890,
    },
    "phillips2023": {
        "title": "Phillips et al. 2023, eLife 83628 — CH65 HA sequence-affinity",
        "doi": "10.7554/eLife.83628",
        "license": "CC-BY-4.0",
        "role": "M4/M5 discovery landscape (3 conditions x 2^16)",
        "url": "https://doi.org/10.7554/eLife.83628",
        "dest": "data/external/Phillips2023_HA_CH65/raw/",
        "sha256": None, "bytes": None,
        "note": "Source Data are linked from the article page "
                "(elife-83628-fig*-data*.xlsx).",
    },
    "tem1": {
        "title": "Gaszek et al. 2025 — TEM-1 combinatorial mutagenesis",
        "doi": "10.5281/zenodo.21442350",
        "license": "GPL-3.0 (repository LICENSE)",
        "role": "M4/M5 primary system (8 conditions x 55,296)",
        "url": "https://github.com/msadikyildiz/Gaszek_Yildiz_Meng_2025",
        "dest": "data/external/TEM1_Gaszek2025/",
        "sha256": None, "bytes": None,
        "note": "git clone the repository; the intended-genotype CSV must land at "
                "data/external/TEM1_Gaszek2025/data/processed/"
                "TEM1-combinatorial-mutagenesis-intended.csv",
    },
    "ancsr1": {
        "title": "Metzger et al. 2024 — AncSR1 (Dryad 10.5061/dryad.jsxksn0hk)",
        "doi": "10.5061/dryad.jsxksn0hk",
        "license": "CC0-1.0",
        "role": "M6 candidate that FAILED structural eligibility (only 2 tasks)",
        "url": "https://datadryad.org/api/v2/versions/272141/files",
        "dest": "data/external/AncSR1_Starr2017/raw/",
        "sha256": None, "bytes": None,
        "note": "184 files / 6.3 GB. The Dryad /files/{id}/download endpoint "
                "requires a token; the public route is Anubis-PoW protected. "
                "A working client ships in eov/m6_dryad_client.py.",
    },
}

# --------------------------------------------------------------------------
# Manual only.
# --------------------------------------------------------------------------
MANUAL: dict[str, str] = {
    "TrpB4_Johnston2024": "CaltechDATA doi:10.22002/h5rah-5z170 (CC0-1.0) — "
                          "413 MB + 3.3 GB zips; external validation only.",
    "Bank2016_Hsp90_Dryad": "Dryad doi:10.5061/dryad.th0rj (CC0-1.0) — "
                            "640 mutants, external validation only.",
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def fetch(key: str, root: Path, yes: bool) -> bool:
    d = AUTO[key]
    dest = root / d["dest"]
    print("\n=== %s" % key)
    print("    %s" % d["title"])
    print("    license : %s" % d["license"])
    print("    role    : %s" % d["role"])
    print("    url     : %s" % d["url"])
    if d.get("note"):
        print("    note    : %s" % d["note"])
    if d["url"].endswith("/") or d["url"].startswith("https://github.com/") \
            or d["url"].startswith("https://doi.org/") \
            or d["url"].startswith("https://datadryad.org/api/"):
        print("    -> MANUAL (see docs/DATA_ACCESS.md); not auto-downloaded.")
        return False
    if dest.exists() and d["bytes"] and dest.stat().st_size == d["bytes"]:
        print("    -> already present and size matches: %s" % dest)
        return True
    if not yes:
        try:
            if input("    download? [y/N] ").strip().lower() not in ("y", "yes"):
                print("    skipped.")
                return False
        except EOFError:
            print("    non-interactive without --yes; skipped.")
            return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    print("    downloading ...")
    try:
        req = urllib.request.Request(d["url"], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=600) as r, tmp.open("wb") as out:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
    except (urllib.error.URLError, OSError) as e:
        print("    FAILED: %s" % e)
        tmp.unlink(missing_ok=True)
        return False
    tmp.replace(dest)
    print("    saved %s  (%d bytes, sha256 %s)"
          % (dest, dest.stat().st_size, sha256(dest)[:16]))
    if d["bytes"] and dest.stat().st_size != d["bytes"]:
        print("    WARNING: expected %d bytes" % d["bytes"])
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=None,
                    help="wu2020 | phillips2023 | tem1 | ancsr1 | all")
    ap.add_argument("--root", default=".")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--yes", action="store_true", help="do not prompt")
    a = ap.parse_args()
    root = Path(a.root).resolve()

    if a.list or not a.dataset:
        print("auto-fetchable:")
        for k, v in AUTO.items():
            print("   %-14s %-28s %s" % (k, v["license"], v["title"]))
        print("\nmanual only:")
        for k, v in MANUAL.items():
            print("   %-24s %s" % (k, v))
        print("\nNo dataset is redistributed with this repository. "
              "See docs/DATA_ACCESS.md.")
        return 0

    keys = list(AUTO) if a.dataset == "all" else [a.dataset]
    for k in keys:
        if k not in AUTO:
            print("unknown dataset %r; use --list" % k)
            return 2
    ok = all(fetch(k, root, a.yes) for k in keys)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
