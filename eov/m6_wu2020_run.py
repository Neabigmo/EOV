"""M6 step S3 — Wu2020 确认检验（`AMENDMENT-017` §3/§4 + `AMENDMENT-018`）。

流程：
  S3.1 建统一测量表（期刊 Source Data，6 task × 576 genotype）
  S3.2 建空间与图，核验 E3/E4
  S3.3 预指定不变式核验（`Preference` vs `Fitness`，见 AMENDMENT-018 §5.1）
  S3.4 跑 576 × 6 × 3 × 2 = 20,736 次搜索 -> R_{B,pi}(x,tau)
  S3.5 **先落盘 checkpoint**，再出报告（项目铁律）
  S3.6 算 f1（15 对）、pair 级 rho_rank、Spearman + bootstrap CI
  S3.7 按 §8 判定
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "eov"))

from landscape import MixedAlphabetSpace                     # noqa: E402
from search_sim import (POLICIES, Scratch, make_context,      # noqa: E402
                        simulate_search, utility_from_values)  # noqa: E402

SRC = os.path.join(ROOT, "data", "external", "Wu2020_RBS_epistasis", "raw",
                   "41467_2020_15102_MOESM6_ESM.xlsx")
OUT_R = os.path.join(ROOT, "data", "processed", "M6_WU2020_R.npz")
OUT_JSON = os.path.join(ROOT, "data", "manifests", "M6_WU2020_RESULT.json")
OUT_MAP = os.path.join(ROOT, "results", "tables", "M6_WU2020_TRANSFER_MAP.csv")

SEED = 20260919          # 与 exp2 同（项目统一 shared_seed）
BOOT_SEED = SEED + 7
N_BOOT = 2000
BUDGETS = (24, 96)       # OP-21 剔除 384（AMENDMENT-018 §4 E6）


def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ok = ~np.isnan(a) & ~np.isnan(b)
    if ok.sum() < 3:
        return float("nan")
    ra = pd.Series(a[ok]).rank().to_numpy()
    rb = pd.Series(b[ok]).rank().to_numpy()
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


# --------------------------------------------------------------------- S3.1
def build_table():
    df = pd.read_excel(SRC, sheet_name="Fitness and preference")
    df.columns = [str(c).strip() for c in df.columns]
    tasks = sorted(df["Genetic Background"].unique().tolist())
    variants = sorted(df["Variant"].unique().tolist())
    tab = df.pivot(index="Variant", columns="Genetic Background",
                   values="Fitness").loc[variants, tasks]
    assert not tab.isna().to_numpy().any(), "缺失值存在"
    assert len(variants) == 576, len(variants)
    assert len(tasks) == 6, len(tasks)
    assert df.shape[0] == 3456, df.shape
    return df, tab, tasks, variants


# --------------------------------------------------------------------- S3.2
def build_space(variants):
    npos = len(variants[0])
    alleles = [sorted({v[p] for v in variants}) for p in range(npos)]
    sp = MixedAlphabetSpace(alleles)
    assert sp.space_size() == 576, sp.space_size()
    assert sp.is_complete_product(), "非完整乘积空间"
    assert sp.degree_topology() == sum(len(a) - 1 for a in alleles)
    idx = np.array([sp.index_of(tuple(v)) for v in variants], dtype=np.int64)
    assert len(set(idx.tolist())) == 576 and idx.max() == 575
    return sp, idx, [len(a) for a in alleles]


# --------------------------------------------------------------------- S3.3
def affine_invariance(df, tasks, variants):
    """AMENDMENT-018 §5.1：Preference 是否为 Fitness 的逐 task 仿射变换。"""
    out = {}
    for t in tasks:
        sub = df[df["Genetic Background"] == t].set_index("Variant").loc[variants]
        x = sub["Fitness"].to_numpy(float); y = sub["Preference"].to_numpy(float)
        A = np.vstack([x, np.ones_like(x)]).T
        coef, res, *_ = np.linalg.lstsq(A, y, rcond=None)
        pred = A @ coef
        out[t] = {"slope": float(coef[0]), "intercept": float(coef[1]),
                  "max_abs_resid": float(np.max(np.abs(y - pred))),
                  "r2": float(1 - np.sum((y - pred) ** 2) /
                              np.sum((y - y.mean()) ** 2))}
    return out


# --------------------------------------------------------------------- S3.4
def run_searches(sp, idx, tab, tasks, variants):
    ctx = make_context(sp)
    n = sp.space_size()
    vals = {}
    for t in tasks:
        v = np.full(n, np.nan)
        v[idx] = tab[t].to_numpy(float)
        vals[t] = v
    R = np.full((len(POLICIES), len(BUDGETS), len(tasks), n), np.nan)
    rng = np.random.default_rng(SEED)
    scratch = Scratch(n)
    cand = np.arange(n, dtype=np.int64)      # 全部 576 均可测（informative=1.0）
    t0 = time.time(); done = 0
    total = len(POLICIES) * len(BUDGETS) * len(tasks) * n
    for ti, t in enumerate(tasks):
        for si, pol in enumerate(POLICIES):
            for bi, B in enumerate(BUDGETS):
                col = R[si, bi, ti]
                for x in range(n):
                    col[x] = simulate_search(ctx, x, vals[t], cand, pol, B,
                                             rng, scratch)
                done += n
                print("    task=%-7s pol=%-11s B=%-4d  %6.1fs  (%.0f%%)"
                      % (t, pol, B, time.time() - t0, 100 * done / total),
                      flush=True)
    return vals, R, ctx


# --------------------------------------------------------------------- S3.6
def cell_stats(r):
    v = r[~np.isnan(r)]
    q05, q95 = float(np.percentile(v, 5)), float(np.percentile(v, 95))
    return dict(n_uniq=int(len(np.unique(v))), q05=q05, q95=q95, span=q95 - q05)


def analyse(vals, R, tasks, ctx):
    """按 AMENDMENT-019 §2：退化格（q95 <= q05）-> rho = NaN，聚合仍用 nanmean。"""
    keys = list(tasks)
    f1s, rho_cells, pair_rows, cell_diag = {}, {}, [], []
    n_deg = n_cells = 0
    for ti, t in enumerate(keys):
        for si, pol in enumerate(POLICIES):
            for bi, B in enumerate(BUDGETS):
                st = cell_stats(R[si, bi, ti])
                cell_diag.append(dict(task=t, policy=pol, budget=B, **st))
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            A, Bt = keys[i], keys[j]
            va, vb = vals[A], vals[Bt]
            m = ~np.isnan(va) & ~np.isnan(vb)
            f1 = spearman(va[m], vb[m])            # = M5 pair_features 的 f1
            f1s[(A, Bt)] = f1
            cells, used = [], 0
            for si, pol in enumerate(POLICIES):
                for bi, B in enumerate(BUDGETS):
                    n_cells += 1
                    ra = R[si, bi, tasks.index(A)]
                    rb = R[si, bi, tasks.index(Bt)]
                    mm = ~np.isnan(ra) & ~np.isnan(rb)
                    if mm.sum() < 50:
                        pair_rows.append(dict(task_A=A, task_B=Bt, policy=pol,
                                              budget=B, n=int(mm.sum()),
                                              rho_rank="", degenerate="too_few"))
                        continue
                    sa, sb = cell_stats(ra[mm]), cell_stats(rb[mm])
                    if sa["span"] <= 0 or sb["span"] <= 0:
                        n_deg += 1
                        pair_rows.append(dict(task_A=A, task_B=Bt, policy=pol,
                                              budget=B, n=int(mm.sum()), rho_rank="",
                                              degenerate="scale:%s%s"
                                              % ("A" if sa["span"] <= 0 else "",
                                                 "B" if sb["span"] <= 0 else "")))
                        continue
                    ua = np.array([utility_from_values(ra[mm])[0](z) for z in ra[mm]])
                    ub = np.array([utility_from_values(rb[mm])[0](z) for z in rb[mm]])
                    rho = spearman(ua, ub)
                    cells.append(rho); used += 1
                    pair_rows.append(dict(task_A=A, task_B=Bt, policy=pol,
                                          budget=B, n=int(mm.sum()),
                                          rho_rank=round(rho, 6), degenerate=""))
            rho_cells[(A, Bt)] = float(np.nanmean(cells)) if cells else float("nan")
            pair_rows.append(dict(task_A=A, task_B=Bt, policy="<pair-level mean>",
                                  budget="", n=used,
                                  rho_rank=(round(rho_cells[(A, Bt)], 6)
                                            if cells else ""), degenerate=""))
    return f1s, rho_cells, pd.DataFrame(pair_rows), pd.DataFrame(cell_diag), n_deg, n_cells


def main() -> int:
    print("=" * 78); print("S3.1  unified measurement table")
    df, tab, tasks, variants = build_table()
    print("  rows=%d  tasks=%d  variants=%d  missing=%d"
          % (df.shape[0], len(tasks), len(variants),
             int(df[["Fitness", "Preference"]].isna().sum().sum())))
    print("  tasks:", tasks)

    print("=" * 78); print("S3.2  space + graph")
    sp, idx, nstates = build_space(variants)
    print("  |space|=%d  complete=%s  degree=%d  states=%s  positions=%d"
          % (sp.space_size(), sp.is_complete_product(), sp.degree_topology(),
             nstates, sp.n_positions))

    print("=" * 78); print("S3.3  pre-specified invariance check (Preference ~ Fitness)")
    inv = affine_invariance(df, tasks, variants)
    for t, d in inv.items():
        print("  %-7s slope=%+.6f  intercept=%+.6f  max|resid|=%.3e  R2=%.8f"
              % (t, d["slope"], d["intercept"], d["max_abs_resid"], d["r2"]))
    inv_ok = all(d["max_abs_resid"] < 1e-6 for d in inv.values())
    print("  -> affine within every task: %s" % inv_ok)

    print("=" * 78); print("S3.4  searches (576 starts x 6 tasks x 3 policies x 2 budgets)")
    if os.path.exists(OUT_R):
        print("  reuse", OUT_R)
        d = np.load(OUT_R, allow_pickle=True)
        R = d["R"]; tasks = [str(x) for x in d["tasks"]]
        vals = {t: d["vals_" + t] for t in tasks}
        _, _, tasks2, variants2 = build_table()
        ctx = make_context(sp)
    else:
        vals, R, ctx = run_searches(sp, idx, tab, tasks, variants)
        print("=" * 78); print("S3.5  CHECKPOINT before reporting")
        np.savez_compressed(OUT_R, R=R, tasks=np.array(tasks),
                            **{"vals_" + t: vals[t] for t in tasks})
        print("  saved", OUT_R)

    print("=" * 78); print("S3.6  f1 / pair-level rho_rank")
    f1s, rho_cells, cells, diag, n_deg, n_cells = analyse(vals, R, tasks, ctx)
    cells.to_csv(OUT_MAP, index=False)
    print("  per-cell R degeneracy (AMENDMENT-019 §2.3):")
    print("    %-9s %-11s %-4s %8s %10s" % ("task", "policy", "B", "n_uniq", "span"))
    for r in diag.itertuples():
        flag = "  <-- DEGENERATE" if r.span <= 0 else ("  (compressed)" if r.span < 0.5 else "")
        print("    %-9s %-11s %-4d %8d %10.5f%s"
              % (r.task, r.policy, r.budget, r.n_uniq, r.span, flag))
    print("  degenerate cells: %d / %d (%.1f%%)"
          % (n_deg, n_cells, 100.0 * n_deg / n_cells))
    pa = np.array([f1s[k] for k in f1s]); pr = np.array([rho_cells[k] for k in f1s])
    rho_stat = spearman(pa, pr)
    print("  n_pairs=%d" % len(pa))
    print("  f1 range        : %.4f .. %.4f (median %.4f)"
          % (np.nanmin(pa), np.nanmax(pa), np.nanmedian(pa)))
    print("  rho_rank range  : %.4f .. %.4f (median %.4f)"
          % (np.nanmin(pr), np.nanmax(pr), np.nanmedian(pr)))
    print("  PRIMARY  Spearman(f1, pair-level rho_rank) = %+.4f" % rho_stat)

    brng = np.random.default_rng(BOOT_SEED)
    n = len(pa); boot = np.empty(N_BOOT)
    for b in range(N_BOOT):
        s = brng.integers(0, n, n)
        boot[b] = spearman(pa[s], pr[s])
    lo, hi = np.nanpercentile(boot, [2.5, 97.5])
    print("  bootstrap 95%% CI (pair resample, %d): [%+.4f, %+.4f]" % (N_BOOT, lo, hi))

    thr = 0.45
    pass_ = bool(rho_stat >= thr and lo > 0)
    print("=" * 78); print("S3.7  VERDICT (AMENDMENT-017 §3/§4)")
    print("  threshold >= %.2f AND CI excludes 0  ->  %s"
          % (thr, "PASS -> CONFIRMED" if pass_ else "FAIL -> STOP EOV MAIN LINE"))

    summary = {
        "dataset": "Wu2020_H3N2_siteB", "n_pairs": int(n),
        "tasks": tasks, "n_variants": 576, "space": 576,
        "degree": sp.degree_topology(), "states_per_position": nstates,
        "budgets": list(BUDGETS), "policies": list(POLICIES),
        "coverage": {str(B): round(B / 576, 4) for B in BUDGETS},
        "affine_invariance": inv, "affine_ok": bool(inv_ok),
        "f1": {("%s~%s" % k): round(v, 6) for k, v in f1s.items()},
        "rho_pair_level": {("%s~%s" % k): round(v, 6) for k, v in rho_cells.items()},
        "cell_diagnostics": diag.to_dict(orient="records"),
        "n_degenerate_cells": int(n_deg), "n_cells_total": int(n_cells),
        "median_f1": float(np.nanmedian(pa)),
        "median_rho_rank_pair_level": float(np.nanmedian(pr)),
        "spearman_f1_vs_rho": round(rho_stat, 6),
        "boot_ci": [round(float(lo), 6), round(float(hi), 6)],
        "threshold": thr, "verdict": "CONFIRMED" if pass_ else "FAIL",
        "seed": SEED, "boot_seed": BOOT_SEED,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print("  ->", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
