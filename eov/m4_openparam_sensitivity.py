"""M4.5 — 两个**未签字**开放参数（INT-5 / OP-8）的口径敏感性。

背景（AMENDMENT-016）：`PHASE1_PROTOCOL.md` §12 与 `PHASE1_DECISION.md` §4.2 的整张参数表
全部处于 ⏳ 未签字状态，且两份文件都写明"未签字 = 未冻结，不得据此下任何裁决"。
M4 用了其中三条的**非默认值**。本脚本把两条**纯口径**差异摆出数字，供用户签字时直接取用：

  INT-5  H1 的 uncertainty 定义
         登记默认 = **replicate-level bootstrap SD**
         M4 实际  = `2 × median(value_sd)`（逐基因型重复 SD 的中位数）
         本脚本补算 = `2 × median(value_sem)`（最接近"重复层面的 bootstrap SD"的可用量）

  OP-8   匹配容差 ε
         登记默认 = **1 × pooled replicate SD**
         M4 实际  = `2 × median(σ_u)`
         本脚本补算 = `1 × pooled SD`（pooled = sqrt(mean(value_sd²)) 后换算到 u 尺度）

⛔ 本脚本**不修改**任何登记默认，也**不替换** M4 的主结果；只新增并列口径。
"""
from __future__ import annotations

import csv
import hashlib
import os
import sys
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landscape import MixedAlphabetSpace  # noqa: E402
from search_sim import BUDGETS, POLICIES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
NPZ1 = os.path.join(ROOT, "data", "processed", "M4_EXP1_V.npz")
NPZ2 = os.path.join(ROOT, "data", "processed", "M4_EXP2_V.npz")
OUT_H1 = os.path.join(ROOT, "data_registry", "M4_H1_DENOMINATOR_SENSITIVITY.csv")
OUT_OP8 = os.path.join(ROOT, "data_registry", "M4_EXP4_MATCHED_PAIRS_OP8.csv")

DS_TEM = "TEM-1CML"
DS_PHI = "Phillips2023_HA_CH65"
AMP_CONDITIONS = ["0.0", "3.1", "12.2", "48.8", "195.0", "781.0"]
PROXIES = ["current_fitness", "known_family_mean", "known_family_worst", "local_robustness",
           "neighbor_informative_frac", "dist_to_best", "n_better_neighbors", "local_ruggedness"]
FUTURES = [("AZT", "0.44"), ("AZT", "36.0")]


# ============================================================ INT-5
def h1_denominator():
    d = np.load(NPZ1, allow_pickle=True)
    Rraw = d["Rraw"]
    pol, bud, tk = list(d["policies"]), list(d["budgets"]), list(d["tasks"])
    df = pd.read_parquet(MEAS)[lambda x: x.dataset_id == DS_PHI]
    rows = []
    for ti, t in enumerate(tk):
        s = df[df.task_id == t]
        sd_med = float(np.nanmedian(s.value_sd.values))
        # INT-5 口径的最佳可用近似：逐基因型重复值的标准误（= SD / sqrt(n_rep)）
        n_rep = float(len(s) / s.genotype_id.nunique())
        sem_med = float(np.nanmedian(s.value_sem.values)) if s.value_sem.notna().any() else \
            sd_med / np.sqrt(n_rep)
        for si, p in enumerate(pol):
            for bi, B in enumerate(bud):
                r = Rraw[si, bi, ti]
                r = r[~np.isnan(r)]
                if r.size < 50:
                    continue
                iqr = float(np.percentile(r, 75) - np.percentile(r, 25))
                rows.append(dict(task=t, policy=p, budget=B, n_parents=int(r.size),
                                 iqr_r=round(iqr, 6),
                                 denom_sd=round(2 * sd_med, 6),
                                 denom_sem=round(2 * sem_med, 6),
                                 ratio_sd=round(iqr / (2 * sd_med), 4),
                                 ratio_sem=round(iqr / (2 * sem_med), 4),
                                 pass_sd=bool(iqr >= 2 * sd_med),
                                 pass_sem=bool(iqr >= 2 * sem_med),
                                 n_rep_per_genotype=round(n_rep, 4)))
    with open(OUT_H1, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    R = pd.DataFrame(rows)
    print("WROTE", OUT_H1, len(rows), "rows")
    print("\nINT-5 两种口径下的 H1 通过格数（共 27 格）")
    print("  M4 实际 `2 x median(value_sd)`  :", int(R.pass_sd.sum()))
    print("  INT-5 近似 `2 x median(value_sem)`:", int(R.pass_sem.sum()))
    print("\n逐策略通过格数")
    for p in pol:
        z = R[R.policy == p]
        print("  %-11s sd %d/9   sem %d/9" % (p, int(z.pass_sd.sum()), int(z.pass_sem.sum())))
    print("\n逐 landscape：满足「>=2 策略在 >=2 预算上通过」（严格读法）")
    for t in tk:
        z = R[R.task == t]
        n_sd = sum(1 for p in pol if sum(z[(z.policy == p)].pass_sd) >= 2)
        n_sem = sum(1 for p in pol if sum(z[(z.policy == p)].pass_sem) >= 2)
        print("  %-6s sd %d 个策略   sem %d 个策略" % (t, n_sd, n_sem))
    print("\n0.72 倍假设的实测值：n_rep per genotype =",
          dict(R.groupby('task').n_rep_per_genotype.first().round(3)))
    return R


# ============================================================ OP-8
def split_of(gid):
    return "discovery" if int(hashlib.sha256(("eov-m4-split|" + gid).encode()).hexdigest()[:8], 16) % 2 == 0 \
        else "confirmation"


def op8():
    if not os.path.exists(NPZ2):
        print("跳过 OP-8：缺", NPZ2)
        return None
    d2 = np.load(NPZ2)
    parents = d2["parents"]
    feats = {k[5:]: d2[k] for k in d2.files if k.startswith("feat_")}
    t = pd.read_parquet(MEAS)
    t = t[t.dataset_id == DS_TEM]
    ids = sorted(set(t.genotype_id.astype(str).unique()))
    space = MixedAlphabetSpace.from_masked_profiles([s for s in ids if "X" not in s])
    n = space.space_size()

    def load(tid, cid):
        s = t[(t.task_id == tid) & (t.condition_id == cid)]
        s = s[~s.genotype_id.astype(str).str.contains("X", regex=False)].drop_duplicates("genotype_id")
        v = np.full(n, np.nan); sem = np.full(n, np.nan)
        idx = np.array([space.index_of(tuple(x)) for x in s.genotype_id.astype(str)], dtype=np.int64)
        ok = s.informative.astype(bool).values
        v[idx[ok]] = pd.to_numeric(s.value_group, errors="coerce").values[ok]
        sem[idx[ok]] = pd.to_numeric(s.value_sem, errors="coerce").values[ok]
        return v, sem

    v_t, sem_t = load("AMP", "781.0")
    vv = v_t[~np.isnan(v_t)]
    q05t, q95t = float(np.percentile(vv, 5)), float(np.percentile(vv, 95))
    span = q95t - q05t
    # OP-8 登记默认：1 x pooled replicate SD（pooled = sqrt(mean(value_sd^2)) over informative）
    s_t = t[(t.task_id == "AMP") & (t.condition_id == "781.0")]
    s_t = s_t[~s_t.genotype_id.astype(str).str.contains("X", regex=False)]
    s_t = s_t[s_t.informative.astype(bool)]
    pooled_sd = float(np.sqrt(np.nanmean(pd.to_numeric(s_t.value_sd, errors="coerce").values ** 2)))
    eps = 1.0 * pooled_sd / span
    print("\nOP-8：pooled replicate SD = %.6f  ->  1 x pooled SD 在 u 尺度上 eps = %.6f" % (
        pooled_sd, eps))
    print("     （M4 主表用的是 2 x median(sigma_u) = 0.152235，见 Exp 4 日志）")

    gids = [space.node_id(space.node_from_index(int(x))) for x in parents]
    half = np.array([split_of(g) for g in gids])
    conf = np.flatnonzero(half == "confirmation")
    TOL = {"known_family_mean": eps, "known_family_worst": eps, "current_fitness": eps,
           "local_robustness": eps, "proxy_eov_today": eps, "local_ruggedness": eps,
           "neighbor_informative_frac": 0.0, "dist_to_best": 0.0, "n_better_neighbors": 0.0}
    rows = []
    for key in FUTURES:
        v_f = load(*key)[0]
        vf = v_f[~np.isnan(v_f)]
        q05f, q95f = float(np.percentile(vf, 5)), float(np.percentile(vf, 95))
        u_f = lambda z: (z - q05f) / (q95f - q05f)          # noqa: E731
        u_t = lambda z: (z - q05t) / span                    # noqa: E731
        name = "%s@%s" % key
        for si, pol in enumerate(POLICIES):
            for bi, B in enumerate(BUDGETS):
                V = np.array([np.nan if np.isnan(z) else u_f(z)
                              for z in np.nanmean(d2["R_%s_%s" % key][si, bi], axis=1)])
                proxy_today = np.array([np.nan if np.isnan(z) else u_t(z)
                                        for z in np.nanmean(d2["R_AMP_781.0"][si, bi], axis=1)])
                cols = [("known_family_mean", feats["known_family_mean"])]
                cols += [(p, feats[p]) for p in PROXIES if p != "known_family_mean" and p in feats]
                cols += [("proxy_eov_today", proxy_today)]
                M = np.column_stack([c for _, c in cols])
                tol = np.array([TOL[nm] for nm, _ in cols])
                good = np.isfinite(M).all(axis=1) & ~np.isnan(V)
                cand = [i for i in conf if good[i]]
                pairs = [(i, j) for i, j in combinations(cand, 2)
                         if np.all(np.abs(M[i] - M[j]) <= tol)]
                if len(pairs) < 20:
                    rows.append(dict(future=name, policy=pol, budget=B, n_pairs=len(pairs),
                                     sd_ratio="", var_explained="", Readiness_dir="",
                                     Readiness_p="", verdict="INSUFFICIENT_PAIRS"))
                    continue
                dv = np.array([V[i] - V[j] for i, j in pairs])
                rng = np.random.default_rng(20260919)
                sd_m = float(np.std(dv, ddof=1))
                null = []
                pc = np.array(cand)
                for _ in range(200):
                    pm = rng.permutation(pc)
                    a, b = pm[:len(pm) // 2], pm[len(pm) // 2:2 * (len(pm) // 2)]
                    null.append(float(np.std(V[a] - V[b], ddof=1)))
                ns = float(np.mean(null))
                ratio = sd_m / ns if ns > 0 else float("nan")
                P = feats["known_family_mean"]
                sg = np.array([np.sign(P[i] - P[j]) * (V[i] - V[j]) for i, j in pairs])
                nz = sg[sg != 0]
                hit = int((nz > 0).sum())
                rate = hit / len(nz) if len(nz) else float("nan")
                pv = (float(stats.binomtest(hit, len(nz), 0.5, alternative="two-sided").pvalue)
                      if len(nz) else 1.0)
                rows.append(dict(future=name, policy=pol, budget=B, n_pairs=len(pairs),
                                 sd_ratio=round(ratio, 4),
                                 var_explained=round(1 - ratio ** 2, 4) if ratio == ratio else "",
                                 Readiness_dir=round(rate, 4), Readiness_p=round(pv, 6),
                                 verdict=("PASS" if (len(pairs) >= 20 and pv < 0.05) else "FAIL")))
    with open(OUT_OP8, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    R = pd.DataFrame(rows)
    print("WROTE", OUT_OP8, len(rows), "rows")
    print("\nOP-8 口径下（eps = 1 x pooled SD）与主表（2 x median sigma_u）的对照")
    print(R.to_string(index=False))
    return R


if __name__ == "__main__":
    h1_denominator()
    op8()
