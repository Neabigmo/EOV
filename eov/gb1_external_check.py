"""GB1 —— **第二个**外部校验景观（TrpB 复现的延伸，非用户规格要求）。

为什么做：`eov/search_sim.py` 的外部校验在 TrpB4 上只有**一个**景观。
原文的 `run_all_simulations` 同时跑 **TrpB 与 GB1**，而 GB1 的数据就在同一个 `data.zip` 里。
→ 多一个独立景观，就多一个"我的模拟器没坏"的证据点。

⚠️ **边界**：用户 M4 规格只要求 TrpB（"TrpB = published baseline reproduction only"）。
本脚本是**延伸**，明确登记为"超出规格的外部校验"，**不产生任何新的科学主张与图**。

⚠️ **GB1 的 `active` 与 TrpB 的规则不同**（必须逐字复刻，否则不是复现）：
    原文 notebook 对 GB1 **没有** `active` 列，而是**当场定义**：

        GB1_fit_min = 0.01
        active = (Fitness > 0.01) & (imputed == False)

    即"实测的、且 fitness 高于 0.01"的变体才能当起点。TrpB 则直接用数据文件里的 `active` 列。
    两者的差异本身就是一个**必须如实标注**的复现细节。
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
from trpb_baseline import (AA20, DATA, N_SITES,  # noqa: E402
                           characteristics, sample_SSM_test_top_N,
                           simulate_simple_SSM_recomb_DE, simulate_single_step_DE)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data_registry", "M4_GB1_BASELINE_AND_EXTERNAL.csv")
GB1_FIT_MIN = 0.01          # 原文 notebook 的常数
N_START = 400
BUDGETS = [24, 96, 384, 1920]
SEED = 20260919


def load_gb1():
    """**逐字复刻**原文 notebook cell 4 的 GB1 装载。"""
    g = os.path.join(DATA, "figure_data", "GB1_data")
    mea = pd.read_csv(os.path.join(g, "GB1_Fitness.csv")).rename(
        columns={"AAString": "AAs"}).drop(columns=["Mutations"])
    mea["imputed"] = False
    imp = pd.read_excel(os.path.join(g, "GB1_missing_data.xlsx")).rename(
        columns={"Variants": "AAs", "Imputed fitness": "Fitness"})
    imp["imputed"] = True
    df = pd.concat([mea, imp], ignore_index=True).sort_values("AAs").reset_index(drop=True)
    for i in range(4):
        df.insert(i + 1, "AA%d" % (i + 1), df["AAs"].apply(lambda x: x[i]))
    df["Fitness/max"] = df["Fitness"] / df["Fitness"].max()
    # 原文：`active` 当场定义（GB1 数据文件里没有这一列）
    #   GB1_data['active'] = GB1_data.apply(lambda x: (x['Fitness'] > GB1_fit_min) & (x['imputed'] == False), axis=1)
    df["active"] = (df["Fitness"] > GB1_FIT_MIN) & (~df["imputed"].astype(bool))
    return df


def main() -> int:
    t0 = time.time()
    if not os.path.isdir(DATA):
        print("缺少", DATA)
        return 1
    df = load_gb1()
    print("GB1_data rows=%d  imputed=%d  active=%d" % (
        len(df), int(df["imputed"].sum()), int(df["active"].sum())), flush=True)
    print("  Fitness/max: min=%.5f median=%.5f max=%.5f" % (
        df["Fitness/max"].min(), df["Fitness/max"].median(), df["Fitness/max"].max()), flush=True)

    rows = []
    for name, fn in [("single_step_DE", simulate_single_step_DE),
                     ("SSM_recomb_DE", simulate_simple_SSM_recomb_DE),
                     ("SSM_top96", sample_SSM_test_top_N)]:
        print("  running %s ..." % name, flush=True)
        out = fn(df, "AAs", "Fitness/max")
        c = characteristics(out)
        rows.append(dict(kind="reproduction", method=name, protein="GB1", budget="", **c))
        print("    -> n=%d mean=%.4f median=%.4f frac_max=%.4f" % (
            c["n"], c["mean"], c["median"], c["frac_reaching_max"]), flush=True)

    # ---- 外部校验：我的 greedy_ssm vs 原文 single_step_DE
    space = MixedAlphabetSpace([AA20] * N_SITES)
    n = space.space_size()
    ctx = make_context(space)
    scratch = Scratch(n)
    val = np.zeros(n, dtype=float)
    idx = np.array([space.index_of(tuple(s)) for s in df["AAs"]], dtype=np.int64)
    val[idx] = df["Fitness/max"].values
    cand = np.arange(n, dtype=np.int64)
    act = df[df["active"]]["AAs"].values
    pick = np.linspace(0, len(act) - 1, min(N_START, len(act))).astype(int)
    sample = act[pick]
    theirs = simulate_single_step_DE(df, "AAs", "Fitness/max", verbose=False, starts=sample)
    per = theirs.groupby("start_seq").final_fitness.max()
    rng = np.random.default_rng(SEED)
    for B in BUDGETS:
        m = np.array([simulate_search(ctx, int(space.index_of(tuple(s))), val, cand,
                                      "greedy_ssm", B, rng, scratch) for s in sample])
        tv = per.loc[sample].values.astype(float)
        rows.append(dict(kind="external_check", method="greedy_ssm", protein="GB1",
                         budget=B, n=len(sample),
                         mean=round(float(np.mean(m)), 6),
                         median=round(float(np.median(m)), 6),
                         frac_reaching_max="",
                         ratio=round(float(np.mean(m) / np.mean(tv)), 6),
                         exact_equal=round(float(np.mean(np.isclose(m, tv))), 4),
                         mine_ge_theirs=round(float(np.mean(m >= tv - 1e-12)), 4)))
        print("  B=%-5d mine=%.5f theirs=%.5f ratio=%.4f exact=%.3f mine>=theirs=%.3f" % (
            B, np.mean(m), np.mean(tv), np.mean(m) / np.mean(tv),
            np.mean(np.isclose(m, tv)), np.mean(m >= tv - 1e-12)), flush=True)

    keys = ["kind", "method", "protein", "budget", "n", "mean", "median",
            "frac_reaching_max", "ratio", "exact_equal", "mine_ge_theirs"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in keys})
    print("\nWROTE", OUT, len(rows), "rows")
    print("total %.0f s" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
