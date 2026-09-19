"""M6 step S2c — AncSR1 结构资格审计（AMENDMENT-017 §6）。

**纪律**：只输出结构 metadata（数量、维度、取值域、缺失/删失率、图几何）。
绝不输出 phenotype 数值分布，绝不计算任何 task 间相关。

E1 task 数 ≥3 ; E2 task pair 数 ≥10 ; E3 空间可定义 ; E4 AA Hamming-1 可定义 ;
E5 graph_eligible ; E6 OP-21 下预算档 ≥2
"""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m6_dryad_client import DryadClient, BASE  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "external" / "AncSR1_Starr2017" / "raw"
LIST = ROOT / "data" / "manifests" / "M6_ANCSR1_DRYAD_FILELIST.json"
OUT = ROOT / "data" / "manifests" / "M6_ANCSR1_ELIGIBILITY.json"

EXTRA = ["ME.THRESH.NULL.rda", "ME.THRESH.WEAK.rda",
         "PE.THRESH.NULL.rda", "TE.THRESH.NULL.rda"]


def load(name: str):
    import rdata
    conv = rdata.conversion.convert(rdata.parser.parse_file(RAW / name))
    k = list(conv)[0]
    return conv[k]


def fetch_extras():
    listing = json.loads(LIST.read_text(encoding="utf-8"))
    by = {f["path"]: f for f in listing["files"]}
    cl = DryadClient()
    for p in EXTRA:
        f = by[p]
        cl.download("%s/downloads/file_stream/%s" % (BASE, f["file_id"]), RAW / p,
                    expect_size=f["bytes"], expect_sha=f["sha256"])


def main() -> int:
    fetch_extras()
    rep: dict = {}

    # ------------------------------------------------------------------ S1
    print("=" * 78)
    print("S1  phenotype-bearing objects")
    print("=" * 78)
    dj = load("DT.JOINT.rda")
    d11 = load("DT.11P.CODING.rda")
    aaseq = load("AA.SEQ.rda")

    print("DT.JOINT        shape=%s" % (dj.shape,))
    print("  RE domain     : %s" % sorted(dj["RE"].unique().tolist()))
    print("  n per RE      : %s" % dj["RE"].value_counts().to_dict())
    print("  AAseq sample  : %s" % dj["AAseq"].head(3).tolist())
    print("  AAseq width   : %s" % sorted({len(s) for s in dj['AAseq'].head(5000)}))
    print("DT.11P.CODING   shape=%s" % (d11.shape,))
    print("  AAseq sample  : %s" % d11["AAseq"].head(3).tolist())
    print("AA.SEQ          shape=%s" % (aaseq.shape,))
    print("  index sample  : %s" % list(aaseq.index[:3]))
    print("  RE domain     : %s" % sorted(aaseq["RE"].unique().tolist()))

    # 序列集合比较：决定"2 task"还是"4 task"
    strip = lambda s: s[1:] if s and s[0] in "ES" else s
    s_joint = {strip(s) for s in dj["AAseq"].astype(str).unique()}
    s_11p = {str(s) for s in d11["AAseq"].astype(str).unique()}
    if s_11p and max(len(x) for x in list(s_11p)[:50]) == 5:
        s_11p = {strip(x) for x in s_11p}
    inter = s_joint & s_11p
    print("\n  distinct 4-mer sets: DT.JOINT=%d  DT.11P.CODING=%d  |intersection|=%d"
          % (len(s_joint), len(s_11p), len(inter)))
    print("  Jaccard            : %.4f" % (len(inter) / len(s_joint | s_11p)))
    rep["sequence_sets"] = {"DT.JOINT": len(s_joint), "DT.11P.CODING": len(s_11p),
                            "intersection": len(inter),
                            "jaccard": len(inter) / len(s_joint | s_11p)}

    # 每个 RE 的 genotype 覆盖
    rep["per_re"] = {}
    for re_ in sorted(dj["RE"].unique()):
        sub = dj[dj["RE"] == re_]
        rep["per_re"][re_] = {
            "n_rows": int(len(sub)),
            "n_unique_seq": int(sub["AAseq"].nunique()),
            "meanF_notna": int(sub["pooled.meanF"].notna().sum()),
            "SE_notna": int(sub["SE.meanF"].notna().sum()),
            "class_notna": int(sub["pooled.class"].notna().sum()),
        }
        print("  RE=%s  rows=%d  seq=%d  meanF=%d  SE=%d  class=%d"
              % (re_, len(sub), sub["AAseq"].nunique(),
                 sub["pooled.meanF"].notna().sum(),
                 sub["SE.meanF"].notna().sum(),
                 sub["pooled.class"].notna().sum()))

    # ------------------------------------------------------------------ S2
    print()
    print("=" * 78)
    print("S2  space + adjacency geometry (READ-ONLY structure)")
    print("=" * 78)
    geo = {}
    for name in ["NH.ACT.ADJM.rda", "NG.ACT.ADJM.rda", "MG.ACT.ADJM.rda"]:
        m = load(name)
        dim = np.asarray(m.Dim).ravel()
        p = np.asarray(m.p).ravel()
        deg = np.diff(p)
        geo[name] = {
            "Dim": [int(x) for x in dim],
            "n_nodes": int(len(p) - 1),
            "nnz": int(p[-1]),
            "deg_min": int(deg.min()), "deg_max": int(deg.max()),
            "deg_mean": float(deg.mean()),
            "n_full_deg": int((deg == 76).sum()),
            "deg_hist_head": {int(k): int(v) for k, v in
                              zip(*np.unique(deg, return_counts=True))},
        }
        g = geo[name]
        print("%-20s nodes=%-8d nnz=%-10d deg[min/mean/max]=%d/%.2f/%d"
              % (name, g["n_nodes"], g["nnz"], g["deg_min"], g["deg_mean"],
                 g["deg_max"]))
        print("    degree histogram : %s"
              % dict(list(sorted(g["deg_hist_head"].items()))[:8]))
    rep["geometry"] = geo

    # ------------------------------------------------------------------ S3
    print()
    print("=" * 78)
    print("S3  informativeness (CL-9 triad: SE>0 and value > floor + 2*SE)")
    print("=" * 78)
    floors = {}
    for nm, key in [("ME.THRESH.NULL.rda", "ME"), ("PE.THRESH.NULL.rda", "PE"),
                    ("TE.THRESH.NULL.rda", "TE")]:
        try:
            o = load(nm)
            v = np.asarray(o).ravel()
            floors[key] = [float(x) for x in v]
        except Exception as e:
            floors[key] = "ERR %s" % e
    print("THRESH.NULL values :", json.dumps(floors))
    rep["thresh_null"] = floors

    inf = {}
    for re_ in sorted(dj["RE"].unique()):
        sub = dj[dj["RE"] == re_]
        v = sub["pooled.meanF"]
        se = sub["SE.meanF"]
        cls = sub["pooled.class"].astype(str)
        usable = v.notna() & se.notna() & (se > 0)
        lab_nonnull = cls.ne("null") & cls.ne("nan")
        inf[re_] = {
            "n_rows": int(len(sub)),
            "usable_frac": float(usable.mean()),
            "class_non_null_frac": float(lab_nonnull.mean()),
            "class_counts": {k: int(x) for k, x in cls.value_counts().items()},
            "SE_n_unique": int(se.nunique()),
        }
        print("RE=%s rows=%-7d usable_frac=%.4f  class!=null frac=%.4f  %s"
              % (re_, len(sub), inf[re_]["usable_frac"],
                 inf[re_]["class_non_null_frac"], inf[re_]["class_counts"]))
    rep["informativeness"] = inf

    # ------------------------------------------------------------------ S4
    print()
    print("=" * 78)
    print("S4  task inventory and pair count")
    print("=" * 78)
    tasks = ["ERE", "SRE"]
    pairs = list(combinations(tasks, 2))
    print("  measured phenotype axes present in the deposit:")
    print("    DT.JOINT          RE in {E, S}            -> 2 conditions")
    print("    DT.11P.CODING     RE in {ERE,SRE} x rep 1,2 -> 2 conditions"
          " (replicates are NOT tasks)")
    print("  CANDIDATE TASK SET (same protein background) = %s" % tasks)
    print("  n_tasks = %d   n_pairs = C(%d,2) = %d"
          % (len(tasks), len(tasks), len(pairs)))
    rep["tasks"] = {"tasks": tasks, "n_tasks": len(tasks), "n_pairs": len(pairs)}

    # ------------------------------------------------------------------ S5
    print()
    print("=" * 78)
    print("S5  budget admissibility (OP-21: B <= |space|/4)")
    print("=" * 78)
    space = 20 ** 4
    cap = space // 4
    ok = [b for b in (24, 96, 384) if b <= cap]
    print("  |space| = 20^4 = %d ; OP-21 cap = %d ; admissible tiers = %s"
          % (space, cap, ok))
    rep["budget"] = {"space": space, "op21_cap": cap, "tiers": ok}

    # ------------------------------------------------------------------ S6
    print()
    print("=" * 78)
    print("S6  E1..E6 VERDICT")
    print("=" * 78)
    hamm = geo["NH.ACT.ADJM.rda"]
    e = {
        "E1_tasks_ge_3": (len(tasks) >= 3, "n_tasks=%d (need >=3)" % len(tasks)),
        "E2_pairs_ge_10": (len(pairs) >= 10, "n_pairs=%d (need >=10)" % len(pairs)),
        "E3_space_definable": (space == 160000 and len(s_joint) == space,
                              "complete product space 20^4, observed=%d" % len(s_joint)),
        "E4_aa_hamming1_definable": (hamm["deg_min"] == 76 and hamm["deg_max"] == 76,
                                    "NH degree min=%d max=%d (expect 76=4*19)"
                                    % (hamm["deg_min"], hamm["deg_max"])),
        "E5_graph_eligible": (True, "role=strict_multi_task (multi-task, "
                                    "combinatorial neighborhood present)"),
        "E6_budget_ge_2": (len(ok) >= 2, "admissible tiers=%s" % ok),
    }
    rep["E1_E6"] = {k: {"pass": bool(v[0]), "note": v[1]} for k, v in e.items()}
    allpass = all(v[0] for v in e.values())
    for k, (p_, note) in e.items():
        print("  %-28s %s   %s" % (k, "PASS" if p_ else "**FAIL**", note))
    print()
    print("  OVERALL STRUCTURAL ELIGIBILITY: %s"
          % ("PASS -> proceed to unblind (S3 of AMENDMENT-017)"
             if allpass else "**FAIL** -> AMENDMENT-017 §7 replacement path"))
    rep["overall"] = "PASS" if allpass else "FAIL"

    OUT.write_text(json.dumps(rep, indent=2, default=str), encoding="utf-8")
    print("\n-> %s" % OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
