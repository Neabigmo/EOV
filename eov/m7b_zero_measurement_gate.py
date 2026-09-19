"""M7-B — Zero-measurement transferability gate（`AMENDMENT-021`）。

S_0 = 零测量可得 descriptor 的相似度；T = 已冻结的 pair 级 rho_rank。
  TEM-1 : S_0 = ECFP4-Tanimoto(药) x exp(-|dlog10 c|)   [c=0 单侧 -> 0]
  Wu2020: S_0 = exp(-|dyear| / 10)
主检验 Spearman(S_0, T)；不确定性 = task-cluster bootstrap + 系统内置换检验。
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M5MAP = os.path.join(ROOT, "results", "tables", "M5_TRANSFER_MAP.csv")
M6RES = os.path.join(ROOT, "data", "manifests", "M6_WU2020_RESULT.json")
OUT_JSON = os.path.join(ROOT, "data", "manifests", "M7B_GATE_RESULT.json")
OUT_CSV = os.path.join(ROOT, "results", "tables", "M7B_GATE_PAIRS.csv")

CHEM_TANIMOTO = {"AMP|AMP": 1.0, "AZT|AZT": 1.0, "AMP|AZT": 0.109756}
YEARS = {"HK68": 1968, "Bk79": 1979, "Bei89": 1989,
         "Mos99": 1999, "Bris07": 2007, "NDako16": 2016}
YEAR_SCALE = 10.0
SEED_CLUSTER = 20260919 + 211
SEED_PERM = 20260919 + 217
N_BOOT = 2000
N_PERM = 20000
GO, COND, NOGO = 0.45, 0.25, 0.25


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


# ------------------------------------------------------------------ S0
def s_chem(d1, d2):
    return CHEM_TANIMOTO["|".join(sorted([d1, d2]))]


def s_conc(c1, c2):
    if c1 == 0 and c2 == 0:
        return 1.0
    if c1 == 0 or c2 == 0:
        return 0.0                      # d_c -> inf 的极限（无自由参数）
    return float(np.exp(-abs(np.log10(c1) - np.log10(c2))))


def parse_dose(label):
    d, c = label.split("@")
    return d, float(c)


def s0_tem1(a, b):
    d1, c1 = parse_dose(a); d2, c2 = parse_dose(b)
    return s_chem(d1, d2) * s_conc(c1, c2)


def s0_wu(a, b):
    return float(np.exp(-abs(YEARS[a] - YEARS[b]) / YEAR_SCALE))


# ------------------------------------------------------------------ 组装
def assemble():
    m5 = pd.read_csv(M5MAP)
    m5p = (m5.groupby(["dataset", "task_A", "task_B"], as_index=False)
             .agg(rho_rank=("rho_rank", "mean")))
    rows = []
    for r in m5p.itertuples():
        if r.dataset != "TEM-1CML":
            continue
        rows.append(dict(system="TEM-1CML", A=r.task_A, B=r.task_B,
                         rho_rank=float(r.rho_rank),
                         S0=s0_tem1(r.task_A, r.task_B)))
    res = json.loads(open(M6RES, encoding="utf-8").read())
    for k, v in res["rho_pair_level"].items():
        A, B = k.split("~")
        rows.append(dict(system="Wu2020_H3N2_siteB", A=A, B=B,
                         rho_rank=float(v), S0=s0_wu(A, B)))
    df = pd.DataFrame(rows)
    df["key"] = df.system + "|" + df.A + "~" + df.B
    return df


def main() -> int:
    print("=" * 78); print("M7-B S2  assemble")
    df = assemble()
    print("  pairs=%d  systems=%s" % (len(df), df.system.value_counts().to_dict()))
    tasks = sorted({(r.system, r.A) for r in df.itertuples()} |
                   {(r.system, r.B) for r in df.itertuples()})
    print("  tasks=%d" % len(tasks))
    print("  S_0 distribution (descriptive, NOT vs T):")
    print("   ", df.S0.describe()[["min", "25%", "50%", "75%", "max"]].round(4).to_dict())
    print("  n pairs at S_0 == 0 exactly:", int((df.S0 == 0).sum()),
          "(all involve the zero-concentration condition)")
    print()
    print(df.sort_values(["system", "S0"]).to_string(index=False))

    Ti = df.rho_rank.to_numpy(); Si = df.S0.to_numpy()
    rho_zero = spearman(Si, Ti)
    print("\n  PRIMARY  rho_zero = Spearman(S_0, T) = %+.4f  (n=%d)" % (rho_zero, len(df)))

    # ---------------- task-cluster bootstrap ----------------
    tidx = {t: i for i, t in enumerate(tasks)}
    pi = np.array([[tidx[(r.system, r.A)], tidx[(r.system, r.B)]]
                   for r in df.itertuples()])
    rng = np.random.default_rng(SEED_CLUSTER)
    nT = len(tasks)
    cl = np.full(N_BOOT, np.nan)
    for b in range(N_BOOT):
        draw = rng.integers(0, nT, nT)
        u = np.unique(draw)
        if len(u) < 4:
            continue
        sel = np.isin(pi[:, 0], u) & np.isin(pi[:, 1], u)
        if sel.sum() < 6:
            continue
        cl[b] = spearman(Si[sel], Ti[sel])
    clo, chi = np.nanpercentile(cl, [2.5, 97.5])
    print("  task-cluster bootstrap 95%% CI : [%+.4f, %+.4f]  (%d/%d usable)"
          % (clo, chi, int(np.isfinite(cl).sum()), N_BOOT))
    print("    mean unique tasks per draw  : %.2f" % np.mean(
        [len(np.unique(rng.integers(0, nT, nT))) for _ in range(2000)]))

    # ---------------- naive pair bootstrap (对照) ----------------
    rng2 = np.random.default_rng(SEED_CLUSTER + 1)
    pb = np.array([spearman(Si[s], Ti[s])
                   for s in (rng2.integers(0, len(df), len(df)) for _ in range(N_BOOT))])
    plo, phi = np.nanpercentile(pb, [2.5, 97.5])
    print("    naive pair bootstrap 95%% CI: [%+.4f, %+.4f]" % (plo, phi))

    # ---------------- within-system permutation ----------------
    prng = np.random.default_rng(SEED_PERM)
    groups = {s: g.index.to_numpy() for s, g in df.groupby("system")}
    # descriptor per pair, recomputed from permuted (task -> descriptor) maps
    task_desc = {}
    for s in groups:
        sub = df[df.system == s]
        labs = sorted(set(sub.A) | set(sub.B))
        task_desc[s] = labs
    null = np.empty(N_PERM)
    for b in range(N_PERM):
        Sperm = np.empty(len(df))
        for s, idxs in groups.items():
            labs = task_desc[s]
            perm = prng.permutation(len(labs))
            remap = {labs[i]: labs[perm[i]] for i in range(len(labs))}
            sub = df.loc[idxs]
            if s == "TEM-1CML":
                Sperm[idxs] = [s0_tem1(remap[a], remap[bb])
                               for a, bb in zip(sub.A, sub.B)]
            else:
                Sperm[idxs] = [s0_wu(remap[a], remap[bb])
                               for a, bb in zip(sub.A, sub.B)]
        null[b] = spearman(Sperm, Ti)
    p_perm = float((np.sum(null >= rho_zero) + 1) / (N_PERM + 1))
    print("  within-system permutation: null median=%+.4f q95=%+.4f q99=%+.4f  p=%.5f"
          % (np.median(null), np.percentile(null, 95),
             np.percentile(null, 99), p_perm))

    # ---------------- verdict（§5 三档，**逐条完整实现**） ----------------
    # 【修正记录】首版漏实现了 Conditional GO 的第三个条件
    # （"bottom tertile 能稳定筛出低-transfer pair"），因而把 NO-GO 误判成 Conditional GO。
    # 该条件的**无阈值操作化**（忠实于用户原话，不引入新常数）：
    #   low_screen = ( median(T | bottom tertile) <= 0 )  AND
    #                ( median(T | bottom tertile) < median(T | top tertile) )
    _q = np.quantile(Si, [1 / 3, 2 / 3])
    _lab = np.where(Si <= _q[0], "low", np.where(Si <= _q[1], "mid", "high"))
    med_low = float(np.median(Ti[_lab == "low"]))
    med_high = float(np.median(Ti[_lab == "high"]))
    low_screen = bool(med_low <= 0.0 and med_low < med_high)
    print("  low-tertile screening: median(T|low)=%+.4f  median(T|high)=%+.4f  -> %s"
          % (med_low, med_high, "HOLDS" if low_screen else "FAILS"))

    if rho_zero >= GO and clo > 0:
        verdict = "Primary GO"
    elif COND <= rho_zero < GO and p_perm < 0.05 and low_screen:
        verdict = "Conditional GO"
    elif rho_zero < NOGO or (clo < 0 < chi):
        verdict = "NO-GO"
    else:
        verdict = "NO-GO"
    print("=" * 78); print("M7-B S5  VERDICT (AMENDMENT-021 §5)")
    print("  rho_zero=%+.4f  cluster CI=[%+.4f, %+.4f]  p_perm=%.5f  low_screen=%s"
          % (rho_zero, clo, chi, p_perm, low_screen))
    print("  档位判定：Primary GO 需 rho>=%.2f 且 CI下界>0 -> %s"
          % (GO, "满足" if (rho_zero >= GO and clo > 0) else "不满足"))
    print("            Conditional GO 需 %.2f<=rho<%.2f 且 p<0.05 且 low_screen -> %s"
          % (COND, GO, "满足" if (COND <= rho_zero < GO and p_perm < 0.05 and low_screen)
             else "不满足"))
    print("  -> %s" % verdict)

    # ---------------- §6 secondaries ----------------
    print("=" * 78); print("M7-B S4  secondaries")
    out_sec = {}
    # 1 tertiles
    q = np.quantile(Si, [1 / 3, 2 / 3])
    lab = np.where(Si <= q[0], "low", np.where(Si <= q[1], "mid", "high"))
    terc = {}
    print("  [1] S_0 tertiles -> T")
    for g in ("low", "mid", "high"):
        s = Ti[lab == g]
        terc[g] = dict(n=int(len(s)), S0_range=[round(float(Si[lab == g].min()), 4),
                                                round(float(Si[lab == g].max()), 4)],
                       T_median=round(float(np.median(s)), 4),
                       T_mean=round(float(np.mean(s)), 4),
                       T_iqr=round(float(np.percentile(s, 75) - np.percentile(s, 25)), 4),
                       T_max=round(float(np.max(s)), 4))
        print("     %-5s n=%2d S0 in [%.4f, %.4f]  T: median=%+.4f mean=%+.4f IQR=%.4f max=%+.4f"
              % (g, terc[g]["n"], terc[g]["S0_range"][0], terc[g]["S0_range"][1],
                 terc[g]["T_median"], terc[g]["T_mean"], terc[g]["T_iqr"], terc[g]["T_max"]))
    out_sec["tertiles"] = terc
    # 2 drop zero-concentration pairs
    keep = df[~((df.system == "TEM-1CML") & (df.S0 == 0))]
    r2 = spearman(keep.S0, keep.rho_rank)
    print("  [2] drop zero-conc pairs  : n=%d  rho_zero=%+.4f" % (len(keep), r2))
    out_sec["drop_zero_conc"] = {"n": int(len(keep)), "rho": round(r2, 4)}
    # 3 within-system rank-normalised S0
    df["S0_rank_in_sys"] = df.groupby("system")["S0"].rank(pct=True)
    r3 = spearman(df.S0_rank_in_sys, df.rho_rank)
    print("  [3] within-system rank-norm S0 : rho_zero=%+.4f" % r3)
    out_sec["within_system_ranknorm"] = round(r3, 4)
    # 4 per system
    per = {}
    for s, g in df.groupby("system"):
        v = spearman(g.S0, g.rho_rank)
        per[s] = {"n": int(len(g)), "rho": round(v, 4) if v == v else None}
        print("  [4] %-22s n=%2d  rho=%s" % (s, len(g), "%+.4f" % v if v == v else "n/a"))
    out_sec["per_system"] = per
    # 5 naive bootstrap already printed
 
    df.to_csv(OUT_CSV, index=False)
    json.dump({"n_pairs": len(df), "n_tasks": len(tasks),
               "systems": sorted(df.system.unique()),
               "excluded_system": "Phillips2023_HA_CH65 (not evaluable this round, AMENDMENT-021 §2.1)",
               "S0_constants": {"chem_tanimoto_AMP_AZT": 0.109756,
                                "conc_scale": "log10, c=0 one-sided -> S_c=0",
                                "year_scale": YEAR_SCALE, "years": YEARS,
                                "form": "S_chem * S_c (product, frozen)"},
               "rho_zero": round(rho_zero, 6),
               "cluster_ci": [round(float(clo), 6), round(float(chi), 6)],
               "naive_pair_ci": [round(float(plo), 6), round(float(phi), 6)],
               "perm": {"p": p_perm, "n": N_PERM, "null_q95": round(float(np.percentile(null, 95)), 4),
                        "null_q99": round(float(np.percentile(null, 99)), 4),
                        "scheme": "within-system descriptor permutation"},
               "verdict": verdict, "thresholds": {"GO": GO, "COND": COND},
               "low_tertile_screening": {
                   "holds": low_screen, "median_T_low": round(med_low, 6),
                   "median_T_high": round(med_high, 6),
                   "operationalisation": "median(T|low)<=0 AND median(T|low)<median(T|high)"},
               "secondaries": out_sec,
               "seeds": {"cluster": SEED_CLUSTER, "perm": SEED_PERM},
               "label": "exploratory/design characterisation (NOT a confirmation)"},
              open(OUT_JSON, "w", encoding="utf-8"), indent=2)
    print("  ->", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
