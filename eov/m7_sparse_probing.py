"""M7 — Sparse future-task probing（`AMENDMENT-020`）。

问题：用 m 个 shared genotypes 估出的 f̂₁，还能不能预测 ρ_rank？
  m ∈ {4,8,16,32,64,128} + full；每 (pair,m) 独立重复 R=200；均匀无放回抽样。

纪律：只用 f1；ρ_rank 用已冻结值；pair 集固定于 N>=128；不改 m 网格。
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

from m5_transfer_map import load_values                       # noqa: E402

M5MAP = os.path.join(ROOT, "results", "tables", "M5_TRANSFER_MAP.csv")
M6RES = os.path.join(ROOT, "data", "manifests", "M6_WU2020_RESULT.json")
M6NPZ = os.path.join(ROOT, "data", "processed", "M6_WU2020_R.npz")
OUT_JSON = os.path.join(ROOT, "data", "manifests", "M7_SPARSE_RESULT.json")
OUT_CSV = os.path.join(ROOT, "results", "tables", "M7_SPARSE_CURVE.csv")

M_GRID = (4, 8, 16, 32, 64, 128)
M_STAR = 16
N_REP = 200
THRESH = 0.45
MIN_N = 128
SEED_SUB = 20260919 + 101
SEED_BOOT = 20260919 + 107
N_BOOT = 2000


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


# ------------------------------------------------------------------ 组装
def assemble():
    """返回 pairs: list of dict(dataset, A, B, va, vb, rho_full, rho_rank, N)."""
    vals, meta = load_values()

    # --- M5 的 21 对（pair 级 = 逐格均值，与 M5 报告口径一致） ---
    m5 = pd.read_csv(M5MAP)
    m5p = (m5.groupby(["dataset", "task_A", "task_B"], as_index=False)
             .agg(rho_rank=("rho_rank", "mean"), n_cells=("rho_rank", "size")))
    pairs = []
    missing = []
    for r in m5p.itertuples():
        ka = (r.dataset, r.task_A); kb = (r.dataset, r.task_B)
        if ka not in vals or kb not in vals:
            missing.append((r.dataset, r.task_A, r.task_B))
            continue
        va, vb = vals[ka], vals[kb]
        m = ~np.isnan(va) & ~np.isnan(vb)
        N = int(m.sum())
        pairs.append(dict(dataset=r.dataset, A=r.task_A, B=r.task_B,
                          va=va[m], vb=vb[m], N=N, rho_rank=float(r.rho_rank),
                          n_cells=int(r.n_cells)))
    if missing:
        print("  !! M5 有 %d 对在 load_values() 中找不到键：" % len(missing))
        for x in missing[:5]:
            print("     ", x)
        print("     available keys sample:", sorted(vals)[:8])

    # --- Wu2020 的 15 对 ---
    d = np.load(M6NPZ, allow_pickle=True)
    res = json.loads(open(M6RES, encoding="utf-8").read())
    tasks = [str(x) for x in d["tasks"]]
    wv = {t: d["vals_" + t] for t in tasks}
    for i in range(len(tasks)):
        for j in range(i + 1, len(tasks)):
            A, B = tasks[i], tasks[j]
            va, vb = wv[A], wv[B]
            m = ~np.isnan(va) & ~np.isnan(vb)
            key = "%s~%s" % (A, B)
            pairs.append(dict(dataset="Wu2020_H3N2_siteB", A=A, B=B,
                              va=va[m], vb=vb[m], N=int(m.sum()),
                              rho_rank=float(res["rho_pair_level"][key]),
                              n_cells=5))
    return pairs


# ------------------------------------------------------------------ 主
def main() -> int:
    print("=" * 78); print("M7 S2  assemble pairs")
    t0 = time.time()
    pairs = assemble()
    print("  pairs found: %d   (%.1fs)" % (len(pairs), time.time() - t0))
    for p in pairs:
        pass
    by_ds = {}
    for p in pairs:
        by_ds.setdefault(p["dataset"], []).append(p)
    for ds, ps in by_ds.items():
        print("  %-22s pairs=%2d  N min/median/max = %d / %d / %d"
              % (ds, len(ps), min(x["N"] for x in ps),
                 int(np.median([x["N"] for x in ps])), max(x["N"] for x in ps)))

    keep = [p for p in pairs if p["N"] >= MIN_N]
    drop = [p for p in pairs if p["N"] < MIN_N]
    print("  N >= %d : kept %d, dropped %d" % (MIN_N, len(keep), len(drop)))
    for p in drop:
        print("     DROP %-22s %s~%s N=%d" % (p["dataset"], p["A"], p["B"], p["N"]))

    print("=" * 78); print("M7 S3  sparse subsampling (%d pairs x %d m x %d reps)"
                          % (len(keep), len(M_GRID) + 1, N_REP))
    rng = np.random.default_rng(SEED_SUB)
    n = len(keep)
    fbar = {m: np.full(n, np.nan) for m in list(M_GRID) + ["full"]}
    draws = {m: np.full((n, N_REP), np.nan) for m in list(M_GRID) + ["full"]}
    for i, p in enumerate(keep):
        va, vb, N = p["va"], p["vb"], p["N"]
        fbar["full"][i] = spearman(va, vb)
        draws["full"][i, :] = fbar["full"][i]
        for m in M_GRID:
            if m > N:
                continue
            r = np.empty(N_REP)
            for t in range(N_REP):
                s = rng.choice(N, size=m, replace=False)
                r[t] = spearman(va[s], vb[s])
            draws[m][i] = r
            fbar[m][i] = float(np.nanmean(r))
        if (i + 1) % 6 == 0:
            print("    %2d/%2d  %.1fs" % (i + 1, n, time.time() - t0), flush=True)
    np.savez_compressed(os.path.join(ROOT, "data", "processed", "M7_SPARSE.npz"),
                        **{"fbar_" + str(m): fbar[m] for m in fbar},
                        **{"draws_" + str(m): draws[m] for m in draws},
                        rho_rank=np.array([p["rho_rank"] for p in keep]),
                        N=np.array([p["N"] for p in keep]),
                        labels=np.array(["%s|%s|%s" % (p["dataset"], p["A"], p["B"])
                                         for p in keep]))
    print("  checkpoint saved")

    print("=" * 78); print("M7 S4  rho_hat(m) + CI")
    rr = np.array([p["rho_rank"] for p in keep])
    brng = np.random.default_rng(SEED_BOOT)
    rows, out = [], {}
    print("  %-6s %10s %20s %10s %10s" % ("m", "rho_hat", "95% CI", "retention", "draw_q05"))
    full = spearman(fbar["full"], rr)
    for m in list(M_GRID) + ["full"]:
        st = spearman(fbar[m], rr)
        boot = np.array([spearman(fbar[m][s], rr[s])
                         for s in (brng.integers(0, n, n) for _ in range(N_BOOT))])
        lo, hi = np.nanpercentile(boot, [2.5, 97.5])
        dq05 = float(np.nanpercentile([spearman(draws[m][:, t], rr)
                                       for t in range(N_REP)], 5))
        dmed = float(np.nanmedian([spearman(draws[m][:, t], rr)
                                   for t in range(N_REP)]))
        dq95 = float(np.nanpercentile([spearman(draws[m][:, t], rr)
                                       for t in range(N_REP)], 95))
        rows.append(dict(m=m, rho_hat=round(st, 6), ci_lo=round(lo, 6),
                         ci_hi=round(hi, 6), retention=round(st / full, 4),
                         draw_q05=round(dq05, 4), draw_median=round(dmed, 4),
                         draw_q95=round(dq95, 4)))
        out[str(m)] = rows[-1]
        print("  %-6s %+10.4f %20s %10.4f %10.4f"
              % (m, st, "[%+.4f, %+.4f]" % (lo, hi), st / full, dq05))

    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    print("=" * 78); print("M7 S4b per-dataset at m*=16 and full")
    for ds in sorted(by_ds):
        idx = [i for i, p in enumerate(keep) if p["dataset"] == ds]
        if len(idx) < 4:
            print("  %-22s n=%d  (too few for a correlation)" % (ds, len(idx)))
            continue
        i16 = np.array(idx)
        print("  %-22s n=%2d  rho_hat(16)=%+.4f  rho_hat(full)=%+.4f"
              % (ds, len(i16), spearman(fbar[16][i16], rr[i16]),
                 spearman(fbar["full"][i16], rr[i16])))

    print("=" * 78); print("M7 S4c decision utility at m*=16 (terciles, no invented threshold)")
    q = np.quantile(fbar[M_STAR], [1 / 3, 2 / 3])
    lab = np.where(fbar[M_STAR] <= q[0], "low", np.where(fbar[M_STAR] <= q[1], "mid", "high"))
    terc = {}
    for g in ("low", "mid", "high"):
        s = rr[lab == g]
        terc[g] = dict(n=int(len(s)), f1_range=[round(float(fbar[M_STAR][lab == g].min()), 4),
                                                round(float(fbar[M_STAR][lab == g].max()), 4)],
                       rho_median=round(float(np.median(s)), 4),
                       rho_mean=round(float(np.mean(s)), 4),
                       rho_max=round(float(np.max(s)), 4))
        print("  %-5s n=%2d  f1 in [%+.3f, %+.3f]   rho_rank median=%+.4f mean=%+.4f max=%+.4f"
              % (g, terc[g]["n"], terc[g]["f1_range"][0], terc[g]["f1_range"][1],
                 terc[g]["rho_median"], terc[g]["rho_mean"], terc[g]["rho_max"]))

    st16 = out[str(M_STAR)]
    ok = bool(st16["rho_hat"] >= THRESH and st16["ci_lo"] > 0)
    print("=" * 78); print("M7 S5  VERDICT (AMENDMENT-020 §4)")
    print("  m*=%d : rho_hat=%+.4f  CI=[%+.4f, %+.4f]  threshold >= %.2f  -> %s"
          % (M_STAR, st16["rho_hat"], st16["ci_lo"], st16["ci_hi"], THRESH,
             "PASS" if ok else "FAIL"))
    print("  NOTE: M7 is EXPLORATORY simulation, not a confirmation (AMENDMENT-020 §5.6/§6)")

    json.dump({"n_pairs_total": len(pairs), "n_pairs_used": len(keep),
               "dropped": ["%s|%s|%s|N=%d" % (p["dataset"], p["A"], p["B"], p["N"])
                           for p in drop],
               "m_grid": list(M_GRID), "m_star": M_STAR, "n_rep": N_REP,
               "threshold": THRESH, "curve": out, "full_rho_hat": full,
               "terciles_m16": terc, "verdict": "PASS" if ok else "FAIL",
               "seeds": {"subsample": SEED_SUB, "bootstrap": SEED_BOOT},
               "label": "exploratory/design characterisation (NOT a confirmation)"},
              open(OUT_JSON, "w", encoding="utf-8"), indent=2)
    print("  ->", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
