#!/usr/bin/env python
"""Release self-check: privacy / large files / license-adjacent / structure.

Runs offline and needs no third-party data, so it works in a clean clone.

    python scripts/verify_release.py [--root .] [--json RELEASE_CHECK.json]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TEXT_EXT = {".py", ".md", ".csv", ".json", ".yaml", ".yml", ".txt", ".toml",
            ".cfg", ".ini", ".cff", ".sha256"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".ipynb_checkpoints",
             ".venv", "venv", "build", "dist"}

# This scanner necessarily contains its own patterns — exclude it.
SELF = {"scripts/verify_release.py"}

PATTERNS = [
    ("windows_drive_abs", re.compile(r"\b[A-Z]:[\\/](?!\.\.)[^\s\"'`)\]},;]*")),
    ("posix_home_path", re.compile(r"(?:/Users/|/home/)[A-Za-z0-9._\-]+")),
    ("conda_path", re.compile(r"(?i)(?:anaconda3|miniconda3|/opt/conda)")),
    ("email_addr", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")),
    ("ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("token_like", re.compile(r"(?i)\b(?:ghp_|github_pat_|sk-[A-Za-z0-9]{16,}|"
                              r"xox[baprs]-|AKIA[0-9A-Z]{16})")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

# Absolute-looking strings that are NOT local-machine leaks.
ALLOW_SUBSTR = ("http://", "https://", "example.invalid", "C:/Windows")

# LaTeX control sequences read as "X:\word" by the drive-letter regex
# (e.g. a formula containing an inline `\quad` right after a capital letter).
# These are typography, not paths.
LATEX_CMDS = (
    "quad", "qquad", "cdot", "cdots", "ldots", "dots", "times", "approx",
    "sim", "simeq", "leq", "geq", "le", "ge", "to", "mapsto", "rightarrow",
    "leftarrow", "Longrightarrow", "longrightarrow", "uparrow", "downarrow",
    "text", "mathrm", "mathbf", "mathcal", "frac", "sqrt", "sum", "prod",
    "int", "partial", "nabla", "alpha", "beta", "gamma", "delta", "epsilon",
    "theta", "kappa", "lambda", "mu", "nu", "xi", "pi", "rho", "sigma",
    "tau", "phi", "chi", "psi", "omega", "in", "notin", "subset", "forall",
    "exists", "pm", "mp", "star", "circ", "bullet", "oplus", "otimes",
)
LATEX_RX = re.compile(r"^[A-Za-z]:\\(%s)\b" % "|".join(LATEX_CMDS))

FORBIDDEN_TRACKED = [
    (re.compile(r"^data/external/"), "raw third-party data must not be committed"),
    (re.compile(r"\.parquet$"), "large parquet must not be committed"),
    (re.compile(r"\.npz$|\.npy$"), "search matrices / intermediates must not be committed"),
    (re.compile(r"\.rda$|\.xlsx$|\.zip$|\.tar|\.gz$"), "raw data formats must not be committed"),
    (re.compile(r"\.log$"), "run logs must not be committed"),
    (re.compile(r"__pycache__|\.pytest_cache"), "caches must not be committed"),
]

# Files shipped VERBATIM on purpose (hash-asserted by tests / freeze ledger).
KNOWN_VERBATIM = ("tests/test_tem1_topology.py", "tests/test_schema_v1_2.py",
                  "tests/test_schema_v1_4.py", "prereg/M1_SCHEMA_SPEC.md")

LIMITS = [(10, "warn"), (25, "fail"), (50, "critical")]


def tracked(root: Path) -> list[str]:
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files"],
                             capture_output=True, text=True, check=True)
        files = [l.strip() for l in out.stdout.splitlines() if l.strip()]
        if files:
            return files
    except Exception:
        pass
    return [p.relative_to(root).as_posix() for p in root.rglob("*")
            if p.is_file() and not any(s in p.parts for s in SKIP_DIRS)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    root = Path(a.root).resolve()
    files = tracked(root)

    res: dict = {"root": str(root), "n_files": len(files), "privacy": {},
                 "large_files": [], "forbidden": [], "known_verbatim_hits": []}

    hits = {k: [] for k, _ in PATTERNS}
    for rel in files:
        p = root / rel
        if p.suffix.lower() not in TEXT_EXT or rel in SELF:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(txt.splitlines(), 1):
            for name, rx in PATTERNS:
                for m in rx.finditer(line):
                    s = m.group(0)
                    if any(k in s for k in ALLOW_SUBSTR):
                        continue
                    if LATEX_RX.match(s):
                        continue
                    rec = {"file": rel, "line": i, "match": s[:100]}
                    (res["known_verbatim_hits"] if rel in KNOWN_VERBATIM
                     else hits[name]).append(rec)
    res["privacy"] = {k: {"n": len(v), "examples": v[:6]} for k, v in hits.items()}

    for rel in files:
        p = root / rel
        if not p.exists():
            continue
        mb = p.stat().st_size / 1e6
        if mb >= LIMITS[0][0]:
            lvl = "warn" if mb < 25 else "fail" if mb < 50 else "critical"
            res["large_files"].append({"file": rel, "MB": round(mb, 3), "level": lvl})
    res["large_files"].sort(key=lambda r: -r["MB"])

    for rel in files:
        for rx, why in FORBIDDEN_TRACKED:
            if rx.search(rel):
                res["forbidden"].append({"file": rel, "reason": why})

    need = ["README.md", "LICENSE", "CITATION.cff", ".gitignore",
            "pyproject.toml", "eov", "tests", "prereg", "data_registry",
            "results", "scripts", "docs", "configs", "figures"]
    missing = [n for n in need if not (root / n).exists()]
    res["missing_top_level"] = missing

    blocking = []
    for k, v in res["privacy"].items():
        if v["n"]:
            blocking.append("privacy:%s=%d" % (k, v["n"]))
    if res["forbidden"]:
        blocking.append("forbidden_files=%d" % len(res["forbidden"]))
    for lf in res["large_files"]:
        if lf["level"] in ("fail", "critical"):
            blocking.append("large_file:%s=%.1fMB" % (lf["file"], lf["MB"]))
    if missing:
        blocking.append("missing_top_level=%s" % ",".join(missing))
    res["verdict"] = "PASS" if not blocking else "FAIL"
    res["blocking"] = blocking

    print("=" * 74)
    print("EOV RELEASE SELF-CHECK     root = %s" % root)
    print("=" * 74)
    print("files considered : %d" % len(files))
    print("\n-- privacy (excluding files shipped verbatim on purpose) --")
    any_hit = False
    for k, v in res["privacy"].items():
        if v["n"]:
            any_hit = True
        print("   %-20s %d" % (k, v["n"]))
        for e in v["examples"][:3]:
            print("        %s:%d  %s" % (e["file"], e["line"], e["match"]))
    if not any_hit:
        print("   (clean)")
    if res["known_verbatim_hits"]:
        print("\n-- verbatim files (documented exception, not blocking) --")
        seen = {}
        for e in res["known_verbatim_hits"]:
            seen.setdefault(e["file"], 0)
            seen[e["file"]] += 1
        for f, c in sorted(seen.items()):
            print("   %-40s %d occurrence(s)" % (f, c))
    print("\n-- large files (>= 10 MB) --")
    if not res["large_files"]:
        print("   none")
    for lf in res["large_files"][:12]:
        print("   %8.2f MB  [%s]  %s" % (lf["MB"], lf["level"], lf["file"]))
    print("\n-- forbidden tracked types --")
    if not res["forbidden"]:
        print("   none")
    for f in res["forbidden"][:12]:
        print("   %s   (%s)" % (f["file"], f["reason"]))
    print("\n-- structure --")
    print("   ok" if not missing else "   MISSING: %s" % missing)
    print("\nVERDICT: %s" % res["verdict"])
    for b in blocking:
        print("   BLOCKING: %s" % b)
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=2), encoding="utf-8")
        print("\n-> %s" % a.json)
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
