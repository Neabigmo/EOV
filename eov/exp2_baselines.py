"""M4 / Exp 2 —— Day-0 baseline ladder，主指标 = future-task parent-selection regret。

系统：TEM-1CML（M4.0 门控：TEM-1 是唯一拥有合法 (today, future) 对的系统 ——
48 个跨药条件对、CL-5 rho <= 0.38、双方 ~100% informative；Phillips2023 在冻结门控下
**不存在**合法对，故 Exp 1 只做跨预算/跨任务一致性，selection regret 在 TEM-1 上做）。

任务划分（leave-one-task-out 的最强形式）
----------------------------------------
τ_today  = AMP 全浓度族（Day-0 已知；特征、选择器一律只用它）
τ_future = **AZT@0.44**（主；AMENDMENT-013 §4 + AMENDMENT-014 §4）
           AZT@36.0（**强制复现**，不得只报其一）
future 的任何测量**不进入**特征构造、选择器拟合或排序。这是 LOTO 的严格形式。

尺度（AMENDMENT-013 §1 + AMENDMENT-014 §3，**在看任何结果之前冻结**）
------------------------------------------------------------------
TEM-1 全栈统一使用 PROTOCOL §3.3 的 OP-12，**无 clip**：
    u_τ(z) = (z − q05_τ) / (q95_τ − q05_τ)
理由：(i) §3.1 锚点在 TEM-1 的**全部 14 个条件**上都无法通过准入 —— 噪声可分辨性
(013 §2) 与值域饱和 (014 §2) 两条判据，其中饱和判据 **零条件通过**；
(ii) `AdaptationPremium` 把 `R_0`（单变体量）与 `R_{B,π}`（终点量）相减，二者**必须同尺度**。
**尺度不变性**：OP-12 与 `scale2max` 都是 `value` 的**仿射**变换 → Spearman 与 NR **恒等不变**；
§3.2 的经验分位尺度是非线性的 → 作为**真敏感性**单独报告（仅主条件）。

主指标（PHASE1_DECISION.md §2.5，冻结）
-------------------------------------
Regret_{B,pi} = V_{B,pi}(x_oracle, τ_future) - V_{B,pi}(x_selected, τ_future)
NR_{B,pi}     = Regret / ( V(x_oracle) - V(x_robust-worst) )
x_robust-worst = eligible parents 的 V 的 5% 分位（不用 raw min）
任何 NR 必须同时报 absolute V。

噪声（DECISION §2.4 不变量 5）
------------------------------
每个 (policy, budget, parent) 在 `N_NOISE_REPS` 个独立扰动值场上重复，逐 genotype 用
`value_sem` 加性高斯扰动；**censored / at_inferred_floor 的组不扰动**（真值只在 floor 以下）。
V 取重复均值；`V_clean`（干净值场）单独报为敏感性。
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landscape import MixedAlphabetSpace  # noqa: E402
from search_sim import (BUDGETS, POLICIES, Scratch, make_context,  # noqa: E402
                        simulate_search)
from tis import TIS  # noqa: E402  （L39：特征只由 TIS 产出）

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
OUT_LADDER = os.path.join(ROOT, "results", "tables", "M4_EXP2_LADDER.csv")
OUT_FEAT = os.path.join(ROOT, "results", "tables", "M4_EXP2_FEATURES.csv")
OUT_SENS = os.path.join(ROOT, "data_registry", "M4_EXP2_SCALE_SENSITIVITY.csv")
OUT_NPZ = os.path.join(ROOT, "data", "processed", "M4_EXP2_V.npz")

DS = "TEM-1CML"
TODAY_CONDITIONS = ["0.0", "3.1", "12.2", "48.8", "195.0", "781.0"]
TODAY_PRIMARY = ("AMP", "781.0")
FUTURE_PRIMARY = ("AZT", "0.44")
FUTURE_REPLICATION = ("AZT", "36.0")
FUTURES = [FUTURE_PRIMARY, FUTURE_REPLICATION]
N_PARENTS = 1000
N_NOISE_REPS = 2          # + 1 干净值场 = 3 个值场
N_BOOT = 2000
SEED = 20260919

SELECTORS = ["random", "current_fitness", "known_family_mean", "known_family_worst",
             "local_robustness", "neighbor_informative_frac", "dist_to_best",
             "n_better_neighbors", "local_ruggedness", "proxy_eov_today", "oracle"]


def load_arrays(df, space, ids):
    out = {}
    for (tid, cid) in ids:
        s = df[(df.dataset_id == DS) & (df.task_id == tid) & (df.condition_id == cid)]
        # 死哨兵 `XXXXXXXXXXXXX` 不属于乘积空间（它不是替换），按 v1.4 语义排除
        s = s[~s.genotype_id.astype(str).str.contains("X", regex=False)]
        nun = s.groupby(["genotype_id"]).value_group.nunique(dropna=False)
        assert int((nun > 1).sum()) == 0, "value_group varies within genotype for %s@%s" % (tid, cid)
        bad = int((s.informative.astype(bool) &
                   (s.at_inferred_floor.astype(bool) |
                    (s.measurement_state.astype(str) != "exact"))).sum())
        assert bad == 0, "%s@%s: %d informative rows violate v1.4" % (tid, cid, bad)
        n = space.space_size()
        v = np.full(n, np.nan)
        m = np.full(n, np.nan)
        pert = np.zeros(n, dtype=bool)
        idx = np.array([space.index_of(tuple(x)) for x in s.genotype_id.astype(str)], dtype=np.int64)
        ok = s.informative.astype(bool).values
        v[idx[ok]] = pd.to_numeric(s.value_group, errors="coerce").values[ok]
        m[idx[ok]] = pd.to_numeric(s.value_sem, errors="coerce").values[ok]
        floorish = (s.measurement_state.astype(str) != "exact").values | \
                   s.at_inferred_floor.astype(bool).values
        pert[idx[ok]] = ~floorish[ok]
        out[(tid, cid)] = (v, m, pert)
    return out


def build_inputs():
    """载入测量表、空间、context、值场与 parent 样本（模拟与报告两条路径共用，保证同源）。"""
    df = pd.read_parquet(MEAS)
    t = df[df.dataset_id == DS]
    ids = sorted(set(t.genotype_id.astype(str).unique()))
    x_ids = [s for s in ids if "X" in s]
    body = [s for s in ids if "X" not in s]
    space = MixedAlphabetSpace.from_masked_profiles(body)
    n = space.space_size()
    assert n == 55296, n
    assert space.degree_topology() == 18, space.degree_topology()
    assert len(set(body)) == n
    ctx = make_context(space)
    all_ids = sorted(set([TODAY_PRIMARY] + [("AMP", c) for c in TODAY_CONDITIONS] + FUTURES))
    arrs = load_arrays(df, space, all_ids)
    return space, ctx, arrs, x_ids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true",
                    help="跳过昂贵的搜索模拟，直接读 M4_EXP2_V.npz 出报告")
    args = ap.parse_args()
    t0 = time.time()
    space, ctx, arrs, x_ids = build_inputs()
    n = space.space_size()
    print("space=%d degree=%d  排除的死哨兵 profile=%s" % (n, space.degree_topology(), x_ids),
          flush=True)
    scratch = Scratch(n)
    rng = np.random.default_rng(SEED)

    def u_fn(key, scale="q05q95"):
        v = arrs[key][0]
        vv = v[~np.isnan(v)]
        q05, q95 = float(np.percentile(vv, 5)), float(np.percentile(vv, 95))
        vmax = float(vv.max())
        if scale == "q05q95":
            return (lambda z: float((z - q05) / (q95 - q05))), q05, q95
        if scale == "scale2max":
            return (lambda z: float(z / vmax)), q05, q95
        raise ValueError(scale)

    us, qs = {}, {}
    for k in sorted(arrs):
        us[k], q05, q95 = u_fn(k)
        qs[k] = (q05, q95)
        print("  %-12s informative=%5d q05=%.4f q95=%.4f span=%.4f" % (
            "%s@%s" % k, int((~np.isnan(arrs[k][0])).sum()), q05, q95, q95 - q05), flush=True)

    if args.report_only:
        d = np.load(OUT_NPZ)
        parents = d["parents"]
        R = {}
        for key in FUTURES + [TODAY_PRIMARY]:
            nm = "R_%s_%s" % key
            assert nm in d.files, "missing %s in %s" % (nm, OUT_NPZ)
            R[key] = d[nm]
        feats = {k[5:]: d[k] for k in d.files if k.startswith("feat_")}
        print("report-only：载入 %d 个 R 场、%d 个特征" % (len(R), len(feats)), flush=True)
    else:
        v_today = arrs[TODAY_PRIMARY][0]
        pool = np.flatnonzero(~np.isnan(v_today))
        print("P0（AMP@781.0 informative，Day-0 定义）= %d" % len(pool), flush=True)
        parents = np.sort(rng.choice(pool, size=min(N_PARENTS, len(pool)), replace=False))
        for (ft, fc) in FUTURES:
            ev = ~np.isnan(arrs[(ft, fc)][0])
            print("  未来条件 %s@%s：parents 可评估 %d / %d（Day-0 池损失 %.3f%%）" % (
                ft, fc, int(ev[parents].sum()), len(parents),
                100.0 * (1 - ev[parents].mean())), flush=True)

        def perturbed(v, m, p, r):
            out = v.copy()
            sel = p & ~np.isnan(m) & (m > 0)
            out[sel] = v[sel] + r.normal(0.0, 1.0, size=int(sel.sum())) * m[sel]
            return out

        R = {}
        for key in FUTURES + [TODAY_PRIMARY]:
            v, m, p = arrs[key]
            vals = [v] + [perturbed(v, m, p, rng) for _ in range(N_NOISE_REPS)]
            cand = np.flatnonzero(~np.isnan(v))
            acc = np.full((len(POLICIES), len(BUDGETS), len(parents), len(vals)), np.nan)
            for si, pol in enumerate(POLICIES):
                for bi, B in enumerate(BUDGETS):
                    for pi, x in enumerate(parents):
                        for rep, vv in enumerate(vals):
                            acc[si, bi, pi, rep] = simulate_search(
                                ctx, int(x), vv, cand, pol, B, rng, scratch)
            R[key] = acc
            print("  R 完成 %-12s (%.0f s)" % ("%s@%s" % key, time.time() - t0), flush=True)

        # ---- Day-0 特征（只用 AMP 族；L39：只走 TIS，调用方无法传入 future 数组）----
        P = parents
        feats = TIS.for_dataset(DS, arrs, ctx, space).features(P, ctx=ctx)
        # ⚠️ 模拟结果**先落盘再出报告**：报告阶段的任何 bug 都不得再吃掉 30 分钟的模拟
        np.savez_compressed(OUT_NPZ, parents=parents,
                            **{"R_%s_%s" % k: v for k, v in R.items()},
                            **{"feat_%s" % k: v for k, v in feats.items()})
        print("  CHECKPOINT 已落盘 %s" % OUT_NPZ, flush=True)

    with open(OUT_FEAT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["selector", "genotype_id", "value"])
        w.writeheader()
        for name, col in feats.items():
            for pi, x in enumerate(parents):
                w.writerow(dict(selector=name,
                                genotype_id=space.node_id(space.node_from_index(int(x))),
                                value="" if np.isnan(col[pi]) else float(col[pi])))
    for name, col in feats.items():
        print("  feat %-26s finite=%d  sd=%.4f" % (
            name, int(np.isfinite(col).sum()), float(np.nanstd(col))), flush=True)

    def V_of(key, si, bi, reps, u):
        """reps: 0 = 干净值场；None = 对全部（干净 + 噪声）实现取均值。"""
        a = R[key][si, bi]
        col = a[:, 0] if reps == 0 else np.nanmean(a, axis=1)
        return np.array([np.nan if np.isnan(z) else u(z) for z in col])

    def spearman(a, b):
        if a.size < 3 or np.all(a == a[0]) or np.all(b == b[0]):
            return float("nan")
        ra = pd.Series(a).rank().values
        rb = pd.Series(b).rank().values
        ra = ra - ra.mean(); rb = rb - rb.mean()
        d = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
        return float((ra * rb).sum() / d) if d > 0 else float("nan")

    rows, sens = [], []
    boot_rng = np.random.default_rng(SEED + 7)
    for (ft, fc) in FUTURES:
        key = (ft, fc)
        u = us[key]
        for si, pol in enumerate(POLICIES):
            for bi, B in enumerate(BUDGETS):
                V = V_of(key, si, bi, None, u)
                Vc = V_of(key, si, bi, 0, u)
                ok = ~np.isnan(V)
                v_oracle = float(np.max(V[ok]))
                v_rw = float(np.percentile(V[ok], 5))
                denom = v_oracle - v_rw
                cand_sel = dict(feats)
                cand_sel["proxy_eov_today"] = V_of(TODAY_PRIMARY, si, bi, None, us[TODAY_PRIMARY])
                cand_sel["oracle"] = V
                for sel in SELECTORS:
                    col = cand_sel.get(sel)
                    pick_i = None
                    if sel == "random":
                        v_sel = float(np.nanmean(V[ok])); v_sel_c = float(np.nanmean(Vc[ok]))
                        rho = float("nan")
                    elif sel == "oracle":
                        v_sel, rho = v_oracle, 1.0
                        v_sel_c = float(np.max(Vc[ok]))
                    else:
                        fin = np.isfinite(col) & ok
                        if fin.sum() < 10:
                            continue
                        pick_i = int(np.flatnonzero(fin)[np.argmax(col[fin])])
                        v_sel = float(V[pick_i])
                        v_sel_c = float(Vc[pick_i]) if not np.isnan(Vc[pick_i]) else float("nan")
                        rho = spearman(col[fin], V[fin])
                    nr = (v_oracle - v_sel) / denom if denom > 0 else float("nan")
                    bs = []
                    for _ in range(N_BOOT):
                        pidx = boot_rng.integers(0, len(V), len(V))
                        Vb = V[pidx]
                        o = ~np.isnan(Vb)
                        if o.sum() < 50:
                            continue
                        vo = float(np.max(Vb[o])); vr = float(np.percentile(Vb[o], 5))
                        dn = vo - vr
                        if dn <= 0:
                            continue
                        if sel == "random":
                            vs = float(np.nanmean(Vb[o]))
                        elif sel == "oracle":
                            vs = vo
                        else:
                            cb = col[pidx]
                            f2 = np.isfinite(cb) & o
                            if f2.sum() < 10:
                                continue
                            vs = float(Vb[f2][np.argmax(cb[f2])])
                        bs.append((vo - vs) / dn)
                    lo, hi = (np.percentile(bs, [2.5, 97.5]) if len(bs) >= 100
                              else (float("nan"), float("nan")))
                    rows.append(dict(
                        future="%s@%s" % (ft, fc), policy=pol, budget=B, selector=sel,
                        v_oracle=round(v_oracle, 4), v_robust_worst=round(v_rw, 4),
                        v_selected=round(v_sel, 4), regret=round(v_oracle - v_sel, 4),
                        NR=round(nr, 4), NR_lo=round(lo, 4), NR_hi=round(hi, 4),
                        spearman=round(rho, 4) if rho == rho else "",
                        v_selected_noisefree=round(v_sel_c, 4), n_boot_used=len(bs),
                        best_selector_in_cell=""))
                print("  %s@%s %-11s B%-4d done (%.0f s)" % (ft, fc, pol, B, time.time() - t0),
                      flush=True)

    # ---- §3.2 经验分位尺度：真非线性敏感性（仅主条件）----
    print()
    print("=== §3.2 empirical-quantile 尺度敏感性（主条件 %s@%s）===" % FUTURE_PRIMARY, flush=True)
    key = FUTURE_PRIMARY
    for si, pol in enumerate(POLICIES):
        for bi, B in enumerate(BUDGETS):
            a = R[key][si, bi]
            rmean = np.nanmean(a, axis=1)
            ok = ~np.isnan(rmean)
            uq = np.full(len(rmean), np.nan)
            rk = pd.Series(rmean[ok]).rank().values
            uq[np.flatnonzero(ok)] = rk / (len(rk) + 1.0)
            vo = float(np.max(uq[ok])); vr = float(np.percentile(uq[ok], 5))
            dn = vo - vr
            for sel in SELECTORS:
                col = (np.nanmean(R[TODAY_PRIMARY][si, bi], axis=1) if sel == "proxy_eov_today"
                       else (uq if sel == "oracle" else feats.get(sel)))
                if sel == "random":
                    vs = float(np.nanmean(uq[ok]))
                elif sel == "oracle":
                    vs = vo
                else:
                    fin = np.isfinite(col) & ok
                    if fin.sum() < 10:
                        continue
                    vs = float(uq[fin][np.argmax(col[fin])])
                sens.append(dict(future="%s@%s" % key, scale="empirical_quantile",
                                 policy=pol, budget=B, selector=sel,
                                 NR=round((vo - vs) / dn, 4) if dn > 0 else ""))
            print("  %-11s B%-4d done (%.0f s)" % (pol, B, time.time() - t0), flush=True)

    with open(OUT_LADDER, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    with open(OUT_SENS, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["future", "scale", "policy", "budget", "selector", "NR"])
        w.writeheader()
        for r in sens:
            w.writerow(r)
    print()
    print("WROTE", OUT_LADDER, len(rows), "rows")
    print("WROTE", OUT_FEAT)
    print("WROTE", OUT_SENS, len(sens), "rows")
    print("NPZ 已在模拟阶段落盘:", OUT_NPZ)
    print("total %.0f s" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
