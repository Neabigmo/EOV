"""TrpB4 已发表实现 → **对 `eov/search_sim.py` 的外部校验**。

## 为什么需要这个

M4 的**每一个**结果都建立在 `eov/search_sim.py` 上，而它**从未与任何外部实现比对过** ——
我们只有内部一致性（`tests/` 86 项）。TrpB4 的 `code.zip` 提供了唯一现实的外部参照：
同一张 20⁴ 景观上，一个**已发表**的确定性 DE 实现。

## 这个脚本做的检验（不是新的科学主张）

在同一张 TrpB4 景观、同一批起点上：

    E_theirs(s)      = 原文 `simulate_single_step_DE` 在 24 种位点顺序上的**最优终点**
    E_mine(s, B)     = `search_sim.greedy_ssm` 在预算 B 下的终点

报告：`P(E_mine == E_theirs)`、两者均值之比、以及**达到原文终点所需的预算**。

⚠️ **两处必须如实标注的差异**
  1. **算法不同**：原文是**坐标上升扫描**（固定顺序逐位点取最优），
     `greedy_ssm` 是**最陡上升**（在全部 Hamming-1 邻居里取最优）。
     两者**不保证终点相同** —— 本检验因此是**分布层面的**，不是逐点相等。
  2. **预算档位**：本检验使用 `B ∈ {24, 96, 384, 1920}`。后两档**超出** `OP-2` 登记的 `{24,96,384}`。
     这不违反 OP-2 —— OP-2 约束的是 M4 的**估值设计**，而本检验是**外部一致性检查**，
     不属于估值分析，也不产生任何 M4 结论。此点在此显式披露。
"""
from __future__ import annotations

import csv
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landscape import MixedAlphabetSpace  # noqa: E402
from search_sim import Scratch, make_context, simulate_search  # noqa: E402
from trpb_baseline import (AA20, DATA, N_SITES, load_trpb,  # noqa: E402
                           simulate_single_step_DE)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data_registry", "M4_TRPB_EXTERNAL_CHECK.csv")
BUDGETS = [24, 96, 384, 1920]
N_START = 400
SEED = 20260919
POLICY = "greedy_ssm"


def main() -> int:
    t0 = time.time()
    if not os.path.isdir(DATA):
        print("缺少 %s" % DATA)
        return 1
    df, imp, mea = load_trpb()
    df = df.dropna(subset=["AAs", "fitness (min 0)"]).copy()
    df["AAs"] = df["AAs"].astype(str)

    # ---- 建 20^4 乘积空间（与原文同一张景观）
    space = MixedAlphabetSpace([AA20] * N_SITES)
    n = space.space_size()
    assert n == 160000, n
    print("space=%d  topology_degree=%d" % (n, space.degree_topology()), flush=True)

    # ---- 值数组：**逐字沿用原文的"缺失记 0"约定**
    val = np.zeros(n, dtype=float)
    present = np.zeros(n, dtype=bool)
    idx = np.array([space.index_of(tuple(s)) for s in df["AAs"]], dtype=np.int64)
    val[idx] = df["fitness (min 0)"].values
    present[idx] = True
    print("landscape: rows=%d  covered=%d (%.2f%%)  missing->0 的格数=%d" % (
        len(df), int(present.sum()), 100.0 * present.mean(), int((~present).sum())), flush=True)
    cand = np.arange(n, dtype=np.int64)          # 原文约定下每格都有值
    ctx = make_context(space)
    scratch = Scratch(n)

    # ---- 先定抽样起点（从 active 里等距取），再只对这些起点跑原文方法（d 仍用全表）
    act = df[df["active"]]["AAs"].values
    pick0 = np.linspace(0, len(act) - 1, min(N_START, len(act))).astype(int)
    precut = act[pick0]
    print("running published simulate_single_step_DE on %d sampled starts (full lookup table) ..."
          % len(precut), flush=True)
    theirs = simulate_single_step_DE(df, "AAs", "fitness (min 0)", verbose=False, starts=precut)
    per_start = (theirs.groupby("start_seq", sort=True)
                 .agg(theirs_best=("final_fitness", "max"),
                      theirs_mean=("final_fitness", "mean"),
                      n_orders=("final_fitness", "size")))
    print("  orders per start = %d ; starts = %d" % (
        int(per_start.n_orders.iloc[0]), len(per_start)), flush=True)

    sample = per_start.index.to_numpy()
    print("sampled starts = %d" % len(sample), flush=True)

    rng = np.random.default_rng(SEED)
    rows = []
    mine = {B: np.full(len(sample), np.nan) for B in BUDGETS}
    for bi, s in enumerate(sample):
        x0 = space.index_of(tuple(s))
        for B in BUDGETS:
            r = simulate_search(ctx, int(x0), val, cand, POLICY, B, rng, scratch)
            mine[B][bi] = r
    theirs_vec = per_start.loc[sample, "theirs_best"].values.astype(float)
    for B in BUDGETS:
        m = mine[B]
        eq = float(np.mean(np.isclose(m, theirs_vec)))
        rows.append(dict(policy=POLICY, budget=B, n=len(sample),
                         mine_mean=round(float(np.mean(m)), 6),
                         theirs_mean_best=round(float(np.mean(theirs_vec)), 6),
                         ratio=round(float(np.mean(m) / np.mean(theirs_vec)), 6),
                         frac_exactly_equal=round(eq, 4),
                         mine_median=round(float(np.median(m)), 6),
                         theirs_median=round(float(np.median(theirs_vec)), 6),
                         frac_mine_ge_theirs=round(float(np.mean(m >= theirs_vec - 1e-12)), 4)))
        print("  B=%-5d mine_mean=%.5f theirs=%.5f ratio=%.4f  exact_equal=%.3f  mine>=theirs=%.3f" % (
            B, np.mean(m), np.mean(theirs_vec), np.mean(m) / np.mean(theirs_vec),
            eq, np.mean(m >= theirs_vec - 1e-12)), flush=True)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("\nWROTE", OUT, len(rows), "rows")
    print("total %.0f s" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
