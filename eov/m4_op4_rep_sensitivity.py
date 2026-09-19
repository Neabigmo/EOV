"""M4.6 — `OP-4`（策略重复数）的衰减量化：Exp 1 的 ρ 到底被低估了多少？

背景
----
`PHASE1_PROTOCOL.md` §12 登记默认 **`OP-4: n_replicate = 50`**，即每个
`(parent, policy, budget)` 应当跑 50 条**独立策略轨迹**，以对**策略随机性**取期望。
M4 的 Exp 1 每格只跑了 **1 条**轨迹（AMENDMENT-016 §2.1 已登记为偏离）。

后果：`V` 里混入了策略随机性方差 → 跨预算/跨任务的 Spearman ρ 被**衰减**（attenuation）。
本脚本量化这个衰减，给出：
  · 单轨迹 ρ（= Exp 1 的值，可复现）
  · `n_rep` 条轨迹**先平均再算**的 ρ（对策略随机性取期望后的值）
  · 二者之差 = **OP-4 偏离造成的低估量**

范围（有意收窄）
----------------
只做 **`greedy_ssm`**：它是唯一在 §3.3 意义上让 `V` 具有起点特异内容的策略，
也是生死问题 #1/#2 的唯一支撑。`random` / `mlde_ridge` 的 ρ ≈ 0 是**结构性**的
（起点身份传不到终点），策略重复不会改变这一点。

⚠️ 本脚本**不修改** OP-4 的登记默认，也**不替换** Exp 1 的主结果；只新增一份敏感性。
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
from search_sim import BUDGETS, Scratch, make_context, simulate_search, utility_from_values  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
OUT = os.path.join(ROOT, "data_registry", "M4_OP4_REP_SENSITIVITY.csv")

DS = "Phillips2023_HA_CH65"
TASKS = ["MA90", "SI06", "G189E"]
POLICY = "greedy_ssm"
N_BITS = 16
N_PARENTS = 1000
N_REP = 20                      # 敏感性用；远小于 OP-4 默认的 50，故仍偏保守
SEED = 20260919


def spearman(a, b):
    if np.all(a == a[0]) or np.all(b == b[0]):
        return float("nan")
    ra = pd.Series(a).rank().values
    rb = pd.Series(b).rank().values
    ra = ra - ra.mean(); rb = rb - rb.mean()
    d = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
    return float((ra * rb).sum() / d) if d > 0 else float("nan")


def main() -> int:
    t0 = time.time()
    df = pd.read_parquet(MEAS)[lambda d: d.dataset_id == DS]
    raw = {}
    for t in TASKS:
        s = df[df.task_id == t]
        nun = s.groupby(["genotype_id", "condition_id"]).value_group.nunique(dropna=False)
        assert int((nun > 1).sum()) == 0
        v = np.full(1 << N_BITS, np.nan)
        gi = np.array([int(x, 2) for x in s.genotype_id.astype(str)], dtype=np.int64)
        ok = s.informative.astype(bool).values
        v[gi[ok]] = pd.to_numeric(s.value_group, errors="coerce").values[ok]
        raw[t] = v
    space = MixedAlphabetSpace.from_masked_profiles(
        [format(i, "0%db" % N_BITS) for i in range(1 << N_BITS)])
    ctx = make_context(space)
    scratch = Scratch(1 << N_BITS)

    us = {}
    for t in TASKS:
        us[t], q05, q95 = utility_from_values(raw[t], scale="q05q95")

    cand = np.flatnonzero(~np.isnan(raw[TASKS[0]]))
    parents = np.sort(np.random.default_rng(SEED).choice(
        cand, size=min(N_PARENTS, len(cand)), replace=False))
    print("parents=%d  n_rep=%d  policy=%s" % (len(parents), N_REP, POLICY), flush=True)

    cand_t = {t: np.flatnonzero(~np.isnan(raw[t])) for t in TASKS}
    # V[task, budget, parent, rep]
    V = np.full((len(TASKS), len(BUDGETS), len(parents), N_REP), np.nan)
    rng = np.random.default_rng(SEED + 3)
    for ti, t in enumerate(TASKS):
        for bi, B in enumerate(BUDGETS):
            for pi, x in enumerate(parents):
                for rep in range(N_REP):
                    r = simulate_search(ctx, int(x), raw[t], cand_t[t], POLICY, B, rng, scratch)
                    if not np.isnan(r):
                        V[ti, bi, pi, rep] = us[t](r)
        print("  %-6s done (%.0f s)" % (t, time.time() - t0), flush=True)

    rows = []
    for ti, t in enumerate(TASKS):
        for bi in range(len(BUDGETS)):
            for bj in range(bi + 1, len(BUDGETS)):
                a1, b1 = V[ti, bi, :, 0], V[ti, bj, :, 0]
                m = ~np.isnan(a1) & ~np.isnan(b1)
                r_single = spearman(a1[m], b1[m]) if m.sum() >= 50 else float("nan")
                a2 = np.nanmean(V[ti, bi], axis=1)
                b2 = np.nanmean(V[ti, bj], axis=1)
                m2 = ~np.isnan(a2) & ~np.isnan(b2)
                r_avg = spearman(a2[m2], b2[m2]) if m2.sum() >= 50 else float("nan")
                # 该 (task,budget) 格内 V 的策略随机性 sd（相对 parent 间 sd）
                sd_within = float(np.nanmean(np.nanstd(V[ti, bi], axis=1)))
                sd_between = float(np.nanstd(a2))
                rows.append(dict(kind="cross_budget", task=t, budget_a=BUDGETS[bi],
                                 budget_b=BUDGETS[bj], n=int(m2.sum()),
                                 rho_single_rep=round(r_single, 4),
                                 rho_rep_averaged=round(r_avg, 4),
                                 delta=round(r_avg - r_single, 4),
                                 sd_within_parent_over_reps=round(sd_within, 5),
                                 sd_between_parents=round(sd_between, 5)))
    for bi, B in enumerate(BUDGETS):
        for ti in range(len(TASKS)):
            for tj in range(ti + 1, len(TASKS)):
                a1, b1 = V[ti, bi, :, 0], V[tj, bi, :, 0]
                m = ~np.isnan(a1) & ~np.isnan(b1)
                r_single = spearman(a1[m], b1[m]) if m.sum() >= 50 else float("nan")
                a2 = np.nanmean(V[ti, bi], axis=1)
                b2 = np.nanmean(V[tj, bi], axis=1)
                m2 = ~np.isnan(a2) & ~np.isnan(b2)
                r_avg = spearman(a2[m2], b2[m2]) if m2.sum() >= 50 else float("nan")
                rows.append(dict(kind="cross_task", task="%s~%s" % (TASKS[ti], TASKS[tj]),
                                 budget_a=B, budget_b="", n=int(m2.sum()),
                                 rho_single_rep=round(r_single, 4),
                                 rho_rep_averaged=round(r_avg, 4),
                                 delta=round(r_avg - r_single, 4),
                                 sd_within_parent_over_reps="", sd_between_parents=""))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    R = pd.DataFrame(rows)
    print("\nWROTE", OUT, len(rows), "rows\n")
    for kind in ("cross_budget", "cross_task"):
        z = R[R.kind == kind]
        print("=== %s ===" % kind)
        print(z[["task", "budget_a", "budget_b", "n", "rho_single_rep",
                 "rho_rep_averaged", "delta"]].to_string(index=False))
        print("  single: median %.3f  min %.3f  max %.3f" % (
            z.rho_single_rep.median(), z.rho_single_rep.min(), z.rho_single_rep.max()))
        print("  n_rep : median %.3f  min %.3f  max %.3f" % (
            z.rho_rep_averaged.median(), z.rho_rep_averaged.min(), z.rho_rep_averaged.max()))
        print()
    w = R[(R.kind == "cross_budget") & R.sd_within_parent_over_reps.notna()]
    if len(w):
        print("策略随机性 sd（格内，逐 parent 跨 %d 条轨迹）vs parent 间 sd：" % N_REP)
        print("  median within = %.5f   median between = %.5f   ratio = %.4f" % (
            w.sd_within_parent_over_reps.median(), w.sd_between_parents.median(),
            (w.sd_within_parent_over_reps / w.sd_between_parents).median()))
    print("total %.0f s" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
