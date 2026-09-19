"""M4.15 — **修复 §2.4 不变量 5 的违反**（独立审计 S-1 确认）。

## 违反内容

`PHASE1_DECISION.md` §2.4 逐字：

> **不变量（违反即结果作废）**
> 5. `R_{B,π}` 的期望必须对**测量噪声**取（不得用单次 max 的点估计充数）。

而 M4 首轮：
- `eov/exp1_stability.py:102` —— 每个 (parent, policy, budget) **只调用一次** `simulate_search`，
  用的是**干净值场**（`value_group`），**没有任何测量噪声重复**。
- `eov/exp3_tomorrow_test.py:188` —— 同样，S1 的 5 个 holdout 各只跑一次干净值场。
  **而 S1 决定冻结哪个 Phase-I selector。**

对照（**满足**不变量 5 的）：
- `eov/m4_h1_auxiliary.py`（3 测量噪声 × 7 策略 = 32 重复）
- `eov/exp2_baselines.py`（3 个噪声值场，V 取均值）→ 其产物被 exp3-S3 / exp4 复用
- `h1_auxiliary` 的 §3.8 是为 Exp 1 补的，但 **§3.1/§3.2 的招牌 ρ 与 §3.9 的 OP-4 补算都不含测量噪声**

## 本脚本做什么

按不变量 5 重做两处，并报告**结论是否稳定**：

  A. Exp 1 的 `greedy_ssm`：3 个测量噪声值场 → V 取均值 → 重算跨预算/跨任务 ρ
     （只做 greedy：random/MLDE 的 ρ≈0 是**结构性**的 —— B=384 时 `IQR(R)` 精确为 0 ——
      测量噪声不可能恢复它。这一点在报告里已由 §3.3 论证。）
  B. Exp 3 的 S1：3 个测量噪声值场 → 5 个 AMP holdout 的 R 取均值 → **重做模型选择**，
     看冻结的 selector 是否仍是 `current_fitness`

噪声模型：逐基因型用 `value_sem` 加性高斯扰动；**censored / at_inferred_floor 的组不扰动**
（真值只在 floor 以下）。与 `exp2_baselines.py` 的 `perturbed()` 同一实现口径。
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
from search_sim import (BUDGETS, POLICIES, Scratch, make_context,  # noqa: E402
                        simulate_search, utility_from_values)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
OUT_A = os.path.join(ROOT, "results", "tables", "M4_INVARIANT5_EXP1_RHO.csv")
OUT_B = os.path.join(ROOT, "results", "tables", "M4_INVARIANT5_S1_SELECTION.csv")

N_NOISE = 3
SEED = 20260919


def spearman(a, b):
    if np.all(a == a[0]) or np.all(b == b[0]):
        return float("nan")
    ra = pd.Series(a).rank().values
    rb = pd.Series(b).rank().values
    ra = ra - ra.mean(); rb = rb - rb.mean()
    d = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
    return float((ra * rb).sum() / d) if d > 0 else float("nan")


def perturb(v, m, p, rng):
    out = v.copy()
    sel = p & ~np.isnan(m) & (m > 0)
    out[sel] = v[sel] + rng.normal(0.0, 1.0, size=int(sel.sum())) * m[sel]
    return out


# ============================================================ A. Exp 1
def part_a(rng):
    DS = "Phillips2023_HA_CH65"
    TASKS = ["MA90", "SI06", "G189E"]
    df = pd.read_parquet(MEAS)[lambda d: d.dataset_id == DS]
    v_, s_, p_ = {}, {}, {}
    for t in TASKS:
        s = df[df.task_id == t]
        n = 1 << 16
        v = np.full(n, np.nan); m = np.full(n, np.nan); pf = np.zeros(n, bool)
        gi = np.array([int(x, 2) for x in s.genotype_id.astype(str)], dtype=np.int64)
        ok = s.informative.astype(bool).values
        v[gi[ok]] = pd.to_numeric(s.value_group, errors="coerce").values[ok]
        m[gi[ok]] = pd.to_numeric(s.value_sem, errors="coerce").values[ok]
        floorish = (s.measurement_state.astype(str) != "exact").values | \
                   s.at_inferred_floor.astype(bool).values
        pf[gi[ok]] = ~floorish[ok]
        v_[t], s_[t], p_[t] = v, m, pf
    space = MixedAlphabetSpace.from_masked_profiles([format(i, "016b") for i in range(1 << 16)])
    ctx = make_context(space); scratch = Scratch(1 << 16)
    us = {t: utility_from_values(v_[t], scale="q05q95")[0] for t in TASKS}
    cand = {t: np.flatnonzero(~np.isnan(v_[t])) for t in TASKS}
    parents = np.sort(np.random.default_rng(SEED).choice(
        cand[TASKS[0]], 1000, replace=False))
    V = np.full((len(TASKS), len(BUDGETS), len(parents)), np.nan)
    for ti, t in enumerate(TASKS):
        fields = [v_[t]] + [perturb(v_[t], s_[t], p_[t], rng) for _ in range(N_NOISE)]
        for bi, B in enumerate(BUDGETS):
            for pi, x in enumerate(parents):
                acc = []
                for fv in fields:
                    r = simulate_search(ctx, int(x), fv, cand[t], "greedy_ssm", B, rng, scratch)
                    if not np.isnan(r):
                        acc.append(us[t](r))
                if acc:
                    V[ti, bi, pi] = float(np.mean(acc))
        print("    A: %-6s done (%.0f s)" % (t, time.time()), flush=True)
    rows = []
    for ti, t in enumerate(TASKS):
        for i in range(len(BUDGETS)):
            for j in range(i + 1, len(BUDGETS)):
                a, b = V[ti, i], V[ti, j]
                m = ~np.isnan(a) & ~np.isnan(b)
                rows.append(dict(kind="cross_budget", task=t,
                                 a="B%d" % BUDGETS[i], b="B%d" % BUDGETS[j],
                                 n=int(m.sum()), rho=round(spearman(a[m], b[m]), 4)))
    for bi, B in enumerate(BUDGETS):
        for i in range(len(TASKS)):
            for j in range(i + 1, len(TASKS)):
                a, b = V[i, bi], V[j, bi]
                m = ~np.isnan(a) & ~np.isnan(b)
                rows.append(dict(kind="cross_task", task="%s~%s" % (TASKS[i], TASKS[j]),
                                 a="B%d" % B, b="", n=int(m.sum()),
                                 rho=round(spearman(a[m], b[m]), 4)))
    with open(OUT_A, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["kind", "task", "a", "b", "n", "rho"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    R = pd.DataFrame(rows)
    print("\n  WROTE", OUT_A, len(rows), "rows")
    for k in ("cross_budget", "cross_task"):
        z = R[R.kind == k]
        print("  不变量5 之后 %-13s rho: min=%.3f median=%.3f max=%.3f" % (
            k, z.rho.min(), z.rho.median(), z.rho.max()))
    return R


# ============================================================ B. Exp 3-S1
def part_b(rng):
    DS = "TEM-1CML"
    AMP = ["0.0", "3.1", "12.2", "48.8", "195.0", "781.0"]
    TODAY = ("AMP", "781.0")
    df = pd.read_parquet(MEAS)[lambda d: d.dataset_id == DS]
    ids = sorted(set(df.genotype_id.astype(str).unique()))
    space = MixedAlphabetSpace.from_masked_profiles([s for s in ids if "X" not in s])
    n = space.space_size()
    ctx = make_context(space); scratch = Scratch(n)
    arrs, sems, perts = {}, {}, {}
    for c in AMP:
        s = df[(df.task_id == "AMP") & (df.condition_id == c)]
        s = s[~s.genotype_id.astype(str).str.contains("X", regex=False)]
        v = np.full(n, np.nan); m = np.full(n, np.nan); pf = np.zeros(n, bool)
        idx = np.array([space.index_of(tuple(x)) for x in s.genotype_id.astype(str)], dtype=np.int64)
        ok = s.informative.astype(bool).values
        v[idx[ok]] = pd.to_numeric(s.value_group, errors="coerce").values[ok]
        m[idx[ok]] = pd.to_numeric(s.value_sem, errors="coerce").values[ok]
        floorish = (s.measurement_state.astype(str) != "exact").values | \
                   s.at_inferred_floor.astype(bool).values
        pf[idx[ok]] = ~floorish[ok]
        arrs[("AMP", c)], sems[("AMP", c)], perts[("AMP", c)] = v, m, pf
    us = {}
    for c in AMP:
        us[("AMP", c)] = utility_from_values(arrs[("AMP", c)], scale="q05q95")[0]
    u_today = us[TODAY]
    parents = np.sort(np.random.default_rng(SEED).choice(
        np.flatnonzero(~np.isnan(arrs[TODAY])), 1000, replace=False))
    print("    B: parents=%d  n_noise=%d" % (len(parents), N_NOISE), flush=True)

    R_amp = {}
    for c in AMP:
        key = ("AMP", c)
        v, m, pf = arrs[key], sems[key], perts[key]
        fields = [v] + [perturb(v, m, pf, rng) for _ in range(N_NOISE)]
        cand = np.flatnonzero(~np.isnan(v))
        acc = np.full((len(POLICIES), len(BUDGETS), len(parents)), np.nan)
        for si, pol in enumerate(POLICIES):
            for bi, B in enumerate(BUDGETS):
                for pi, x in enumerate(parents):
                    rr = [simulate_search(ctx, int(x), fv, cand, pol, B, rng, scratch)
                          for fv in fields]
                    rr = [z for z in rr if not np.isnan(z)]
                    if rr:
                        acc[si, bi, pi] = float(np.mean([us[key](z) for z in rr]))
        R_amp[key] = acc
        print("    B: R(%s) done (%.0f s)" % (c, time.time()), flush=True)
    np.savez_compressed(os.path.join(ROOT, "data", "processed", "M4_INV5_S1_R.npz"),
                        parents=parents, **{"R_AMP_%s" % c: R_amp[("AMP", c)] for c in AMP})

    # ---- 重做 S1 模型选择（与 exp3 同口径）
    import warnings

    def feats_for(today_keys, P):
        vp = arrs[TODAY]
        has = ~np.isnan(vp)

        def uv(v, key):
            vv = v[~np.isnan(v)]
            q05, q95 = float(np.percentile(vv, 5)), float(np.percentile(vv, 95))
            return np.where(np.isnan(v), np.nan, (v - q05) / (q95 - q05))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            S = np.vstack([uv(arrs[k], k) for k in today_keys])
            fam_mean = np.nanmean(S, axis=0); fam_worst = np.nanmin(S, axis=0)
        n_inf = np.zeros(n, np.int64); mean_nb = np.full(n, np.nan)
        n_bet = np.zeros(n, np.int64); n_wor = np.zeros(n, np.int64)
        for i in range(n):
            nb = ctx.neighbors[i]; ok = has[nb]; n_inf[i] = int(ok.sum())
            if ok.any():
                vals = vp[nb[ok]]; mean_nb[i] = float(np.mean(vals))
                if not np.isnan(vp[i]):
                    n_bet[i] = int((vals > vp[i]).sum()); n_wor[i] = int((vals < vp[i]).sum())
        pool = np.flatnonzero(has)
        ab = int(pool[np.argmax(vp[pool])])
        db = (ctx.codes != ctx.codes[ab]).sum(axis=1)
        return {"current_fitness": np.array([u_today(vp[x]) for x in P]),
                "known_family_mean": fam_mean[P], "known_family_worst": fam_worst[P],
                "local_robustness": np.array([u_today(mean_nb[x]) if not np.isnan(mean_nb[x])
                                              else np.nan for x in P]),
                "neighbor_informative_frac": n_inf[P] / float(space.degree_topology()),
                "dist_to_best": -db[P].astype(float),
                "n_better_neighbors": -n_bet[P].astype(float),
                "local_ruggedness": np.array([(n_wor[x] / n_inf[x]) if n_inf[x] > 0 else np.nan
                                              for x in P])}

    CAND = ["current_fitness", "known_family_mean", "known_family_worst", "local_robustness",
            "neighbor_informative_frac", "dist_to_best", "n_better_neighbors",
            "local_ruggedness", "proxy_eov_today"]

    def nr(V, col):
        ok = ~np.isnan(V)
        vo = float(np.max(V[ok])); vr = float(np.percentile(V[ok], 5)); dn = vo - vr
        if dn <= 0:
            return None
        fin = np.isfinite(col) & ok
        if fin.sum() < 10:
            return None
        return (vo - float(V[fin][np.argmax(col[fin])])) / dn

    s1 = []
    for hold in AMP:
        if hold == TODAY[1]:
            continue
        F = feats_for([k for k in [("AMP", c) for c in AMP] if k != ("AMP", hold)], parents)
        uh = us[("AMP", hold)]
        for si, pol in enumerate(POLICIES):
            for bi, B in enumerate(BUDGETS):
                V = R_amp[("AMP", hold)][si, bi]
                F["proxy_eov_today"] = R_amp[TODAY][si, bi]
                for sel in CAND:
                    r = nr(V, F[sel])
                    if r is not None:
                        s1.append(dict(holdout="AMP@%s" % hold, policy=pol, budget=B,
                                       selector=sel, NR=round(r, 4)))
        print("    B: S1 holdout %s done (%.0f s)" % (hold, time.time()), flush=True)
    with open(OUT_B, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["holdout", "policy", "budget", "selector", "NR"])
        w.writeheader()
        for r in s1:
            w.writerow(r)
    S = pd.DataFrame(s1)
    mean = S.groupby("selector").NR.mean().sort_values()
    print("\n  WROTE", OUT_B, len(s1), "rows")
    print("  === 不变量5 修正后的 S1 平均 NR（越小越好）===")
    print(mean.to_string())
    print("  → 冻结 selector（原为 current_fitness）= %s" % mean.index[0])
    return S


if __name__ == "__main__":
    t0 = time.time()
    rng = np.random.default_rng(SEED + 101)
    print("=== A. Exp 1（greedy_ssm，%d 个测量噪声值场）===" % N_NOISE, flush=True)
    part_a(rng)
    print("\n=== B. Exp 3-S1（%d 个测量噪声值场）===" % N_NOISE, flush=True)
    part_b(rng)
    print("\ntotal %.0f s" % (time.time() - t0))
