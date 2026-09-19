"""M4.2 — 为什么 §3.1 的 WT/dead 锚点尺度**不能**用于比较 `R_{B,pi}`（AMENDMENT-014 的证据）。

论点是**类错误（category error）**，不是噪声问题：

    `u_anchor` 把"单个变体的 fitness"表达为相对 WT 的倍数（死=0，WT=1）。
    它被设计用来**比较单个变体**。
    而 `R_{B,pi}(x,τ)` 是**定向进化后的终点**——它系统性地超过 WT。
    → `clip(...,0,1)` 把超过 WT 的**整段区间**压成常数 1，分辨率归零。

本脚本对每个条件输出：
    frac_u_gt_1  = P(单个 informative 基因型的 u_anchor > 1)
    sat_random_B = P(在 B 次均匀抽样中至少命中一个 u>1 的基因型) = 1 - (1-frac)^B
后者是**任何**搜索策略下饱和概率的下界（random 是最弱的策略；greedy/MLDE 只会更容易命中）。
"""
from __future__ import annotations

import csv
import os
import re

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
OUT = os.path.join(ROOT, "data_registry", "M4_ANCHOR_SATURATION.csv")
BUDGETS = (24, 96, 384)


def main() -> int:
    df = pd.read_parquet(MEAS)
    rows = []
    for ds in sorted(df.dataset_id.unique()):
        t = df[df.dataset_id == ds]
        for (tid, cid), s in t.groupby(["task_id", "condition_id"], sort=True):
            gi = np.asarray(s.genotype_id.astype(str))
            g = s.groupby(gi).value_group.median()
            inf = s.groupby(gi).informative.max().astype(bool)
            keep = inf[inf].index
            g = g.loc[keep]
            wt = g.get("." * 13, np.nan)
            dead = g.get("X" * 13, np.nan)
            if not (wt == wt and dead == dead) or wt == dead:
                rows.append(dict(dataset_id=ds, task_id=tid, condition_id=cid,
                                 n=len(g), F_WT="", F_dead="", frac_u_gt_1="",
                                 **{"sat_random_B%d" % B: "" for B in BUDGETS},
                                 saturated_any=""))
                continue
            u = (g.values - dead) / (wt - dead)
            f = float((u > 1).mean())
            row = dict(dataset_id=ds, task_id=tid, condition_id=cid, n=int(len(g)),
                       F_WT=round(float(wt), 4), F_dead=round(float(dead), 4),
                       frac_u_gt_1=round(f, 5))
            for B in BUDGETS:
                row["sat_random_B%d" % B] = round(1.0 - (1.0 - f) ** B, 5)
            row["saturated_any"] = bool(f > 0.01)
            rows.append(row)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("WROTE", OUT, "rows=%d" % len(rows))
    print("%-16s %-8s %9s %9s %9s" % ("task@cond", "frac>1", "sat B24", "sat B96", "sat B384"))
    for r in rows:
        if r["dataset_id"] != "TEM-1CML":
            continue
        print("%-16s %9s %9s %9s %9s" % (
            "%s@%s" % (r["task_id"], r["condition_id"]), r["frac_u_gt_1"],
            r.get("sat_random_B24"), r.get("sat_random_B96"), r.get("sat_random_B384")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
