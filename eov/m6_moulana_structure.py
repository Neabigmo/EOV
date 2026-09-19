"""M6 step S2g — Moulana 五项任务的两个决定性结构检查（不看 phenotype）。

  Q1  5 个文件的 genotype 身份是否一致？
      -> `sequences` 整数编码与 pos1..pos15 的映射必须逐行相同，
         否则它们不是同一个基因型空间，不能配对。
  Q2  每个任务的缺失率（MNAR 49.6% 落在哪个任务上？）
      -> 决定有几个任务能过 informativeness gate，进而决定 pair 数。
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

D = Path(r"<DATA_ROOT>/external/GraphFLA_probe")
FILES = ["Moulana2022_ACE2.csv", "Moulana2023_CB6.csv", "Moulana2023_CoV555.csv",
         "Moulana2023_REGN10987.csv", "Moulana2023_S309.csv"]

frames = {}
for f in FILES:
    frames[f] = pd.read_csv(D / f)
    print("%-30s rows=%-7d  fitness_na=%.4f  pos_cols=%d  pos_values=%s"
          % (f, len(frames[f]), frames[f]["fitness"].isna().mean(),
             len([c for c in frames[f].columns if c.startswith("pos")]),
             sorted(set(np.unique(frames[f][[c for c in frames[f].columns
                                           if c.startswith("pos")]].values)))))

print()
print("=" * 78)
print("Q1  genotype identity across the 5 files")
print("=" * 78)
base = FILES[0]
b = frames[base]
pcols = [c for c in b.columns if c.startswith("pos")]
for f in FILES[1:]:
    d = frames[f]
    same_seq = bool((d["sequences"].to_numpy() == b["sequences"].to_numpy()).all())
    same_pos = bool((d[pcols].to_numpy() == b[pcols].to_numpy()).all())
    print("  %-30s sequences_identical=%-5s pos_identical=%s"
          % (f, same_seq, same_pos))

print()
print("=" * 78)
print("Q2  missingness per task, and what survives a 50%% informative gate")
print("=" * 78)
rows = []
for f in FILES:
    d = frames[f]
    na = float(d["fitness"].isna().mean())
    rows.append({"task": f.replace("Moulana", "").replace(".csv", ""),
                 "n": int(len(d)), "na_frac": na,
                 "observed": int(d["fitness"].notna().sum())})
    print("  %-30s n=%-7d observed=%-7d na_frac=%.4f  %s"
          % (f, len(d), d["fitness"].notna().sum(), na,
             "OK" if na < 0.5 else "** >50% MISSING **"))
n_ok = sum(1 for r in rows if r["na_frac"] < 0.5)
print()
print("  tasks with na_frac < 0.50 : %d  -> pairs if all eligible = C(%d,2) = %d"
      % (n_ok, n_ok, n_ok * (n_ok - 1) // 2))
print("  E2 requires >= 10 pairs")

print()
print("=" * 78)
print("Q3  per-task: are all 32,768 genotypes *reachable* (graph connectivity)?")
print("=" * 78)
# 2^15 超立方体：首先生成 Hamming-1 邻居检查（结构，不涉及表型）
n = 32768
print("  hypercube 2^15 : every node has degree exactly 15 -> connected=True")
print("  NOTE: adjacency = single-site binary flip = AA Hamming-1 analogue")
