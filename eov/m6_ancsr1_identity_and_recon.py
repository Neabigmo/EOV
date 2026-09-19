"""M6 step S2d — 两个待决问题（均不看 phenotype 数值）：

  A. DT.JOINT 与 DT.11P.CODING 是同一批数据的两种形态，还是两个蛋白背景？
     判据：**缺失模式**（missingness pattern）是否逐行相同 —— 结构性证据。
     相同 -> 同一 background -> 2 个 task；不同 -> 4 个 task。
     （两种情形下 n_pairs 都 < 10，E2 判定不变；此处只为把事实钉死。）

  B. AMENDMENT-017 §7 替代清单的现状侦察：workspace 里已有什么。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "external" / "AncSR1_Starr2017" / "raw"


def load(name: str):
    import rdata
    return list(rdata.conversion.convert(rdata.parser.parse_file(RAW / name)).values())[0]


print("=" * 78)
print("A. missingness-pattern identity: DT.JOINT(RE=E) vs DT.11P.CODING(ERE)")
print("=" * 78)
dj = load("DT.JOINT.rda")
d11 = load("DT.11P.CODING.rda")

strip = lambda s: s[1:] if s and s[0] in "ES" else s
for re_lab, joint_col, p11_col in [("E", "pooled.meanF", "ERE.pooled.meanF"),
                                   ("S", "pooled.meanF", "SRE.pooled.meanF")]:
    sub = dj[dj["RE"] == re_lab].copy()
    sub["k"] = sub["AAseq"].astype(str).map(strip)
    sub = sub.sort_values("k")
    a = sub[joint_col].notna().to_numpy()

    d = d11.copy()
    d["k"] = d["AAseq"].astype(str).map(strip)
    d = d.sort_values("k")
    b = d[p11_col].notna().to_numpy()

    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    same = int((a == b).sum())
    print("  RE=%s : n=%d  identical_missingness=%d (%.4f)  "
          "joint_only=%d  11P_only=%d"
          % (re_lab, n, same, same / n, int((a & ~b).sum()), int((b & ~a).sum())))

# 序列顺序是否一致（进一步的身份证据）
ks_j = sorted({strip(s) for s in dj[dj["RE"] == "E"]["AAseq"].astype(str)})
ks_11 = sorted({strip(s) for s in d11["AAseq"].astype(str)})
print("  sequence sets identical as ordered lists: %s" % (ks_j == ks_11))

print()
print("  class 列缺失模式比较（pooled.class vs 11P 的 ERE.pooled.class）")
sub = dj[dj["RE"] == "E"].copy(); sub["k"] = sub["AAseq"].astype(str).map(strip)
sub = sub.sort_values("k")
d = d11.copy(); d["k"] = d["AAseq"].astype(str).map(strip); d = d.sort_values("k")
a = sub["pooled.class"].notna().to_numpy()
b = d["ERE.pooled.class"].notna().to_numpy()
n = min(len(a), len(b))
print("  identical_class_missingness = %d / %d (%.4f)"
      % (int((a[:n] == b[:n]).sum()), n, (a[:n] == b[:n]).mean()))

print()
print("=" * 78)
print("B. replacement-path reconnaissance (AMENDMENT-017 §7)")
print("=" * 78)
ext = ROOT / "data" / "external"
for d in sorted(ext.iterdir()):
    if not d.is_dir():
        continue
    files = [p for p in d.rglob("*") if p.is_file()]
    tot = sum(p.stat().st_size for p in files)
    print("  %-28s %5d files  %8.1f MB" % (d.name, len(files), tot / 1e6))

print()
led = ROOT / "data_registry" / "PROVENANCE_LEDGER.csv"
df = pd.read_csv(led)
print("  ledger columns:", list(df.columns))
cols = [c for c in ("dataset_id", "protein", "role", "n_observed", "notes")
        if c in df.columns]
print()
print(df[cols].to_string(max_colwidth=70))
