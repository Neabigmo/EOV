"""M5 — Task-Transferability Boundary｜Discovery cycle（用户 2026-09-19 指定）。

问题改为：

    **When does starting-point value transfer across tasks?**

只做三件事（用户指令）：
  1. **完整的 task→task transfer map**：每个 pair 同时报 `ρ_rank` / `selector regret` / `magnitude calibration`
  2. **解释 transferability**（不提高 selector）：只用简单可解释的 task-pair 特征
  3. 标为 **discovery**，confirmation 另找独立数据（本轮不做）

⚠️ **本轮是 discovery，不是 confirmatory**。所有结论都必须在报告里这样标注，
否则就变成"看完 M4 结果后重新调指标直到成功"。

数据来源（**零新增计算**，全部复用 M4 已落盘的可达值矩阵）：
  · Phillips2023   `M4_EXP1_V.npz`   `Rraw[policy,budget,task,parent]`（3 任务）
  · TEM-1 AMP 族   `M4_EXP3_S1_R.npz`（6 个浓度）
  · TEM-1 跨药     `M4_EXP2_V.npz`    `R_{AMP@781, AZT@0.44, AZT@36}`（含 3 个噪声值场）
"""
from __future__ import annotations

import csv
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landscape import MixedAlphabetSpace  # noqa: E402
from search_sim import Scratch, make_context, utility_from_values  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
OUT_MAP = os.path.join(ROOT, "results", "tables", "M5_TRANSFER_MAP.csv")
OUT_FEAT = os.path.join(ROOT, "results", "tables", "M5_PAIR_FEATURES.csv")
OUT_CORR = os.path.join(ROOT, "results", "tables", "M5_FEATURE_VS_TRANSFER.csv")

POLICIES = ("random", "greedy_ssm", "mlde_ridge")
BUDGETS = (24, 96, 384)


def spearman(a, b):
    if len(a) < 5 or np.all(a == a[0]) or np.all(b == b[0]):
        return float("nan")
    ra = pd.Series(a).rank().values
    rb = pd.Series(b).rank().values
    ra = ra - ra.mean(); rb = rb - rb.mean()
    d = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
    return float((ra * rb).sum() / d) if d > 0 else float("nan")


def load_values():
    """返回 {(dataset, task): 原始 value 数组}（按各自空间的索引）。"""
    df = pd.read_parquet(MEAS)
    out = {}
    meta = {}
    for ds, nbits in (("Phillips2023_HA_CH65", 16), ("TEM-1CML", None)):
        sub = df[df.dataset_id == ds]
        ids = sorted(set(sub.genotype_id.astype(str).unique()))
        body = [s for s in ids if "X" not in s]
        sp = MixedAlphabetSpace.from_masked_profiles(
            body if nbits is None else [format(i, "0%db" % nbits) for i in range(1 << nbits)])
        meta[ds] = sp
        size = sp.space_size()
        for (tid, cid), s in sub.groupby(["task_id", "condition_id"], sort=True):
            s = s[~s.genotype_id.astype(str).str.contains("X", regex=False)]
            v = np.full(size, np.nan)
            idx = np.array([sp.index_of(tuple(x)) for x in s.genotype_id.astype(str)],
                           dtype=np.int64)
            ok = s.informative.astype(bool).values
            v[idx[ok]] = pd.to_numeric(s.value_group, errors="coerce").values[ok]
            out[(ds, "%s@%s" % (tid, cid))] = v
    return out, meta


# ---------------------------------------------------------------- Part 1
def build_map():
    rows = []
    # --- Phillips：3 任务 × 3 策略 × 3 预算
    d = np.load(os.path.join(ROOT, "data", "processed", "M4_EXP1_V.npz"), allow_pickle=True)
    Rraw = d["Rraw"]; tk = [str(x) for x in d["tasks"]]
    for i in range(3):
        for j in range(i + 1, 3):
            for si, pol in enumerate(POLICIES):
                for bi, B in enumerate(BUDGETS):
                    a, b = Rraw[si, bi, i], Rraw[si, bi, j]
                    rows.append(_pair_row("Phillips2023_HA_CH65", tk[i] + "@default",
                                          tk[j] + "@default", pol, B, a, b))
    # --- TEM-1 AMP 族 6 浓度
    d3 = np.load(os.path.join(ROOT, "data", "processed", "M4_EXP3_S1_R.npz"))
    conds = ["0.0", "3.1", "12.2", "48.8", "195.0", "781.0"]
    for i in range(len(conds)):
        for j in range(i + 1, len(conds)):
            for si, pol in enumerate(POLICIES):
                for bi, B in enumerate(BUDGETS):
                    a = d3["R_AMP_%s" % conds[i]][si, bi]
                    b = d3["R_AMP_%s" % conds[j]][si, bi]
                    rows.append(_pair_row("TEM-1CML", "AMP@" + conds[i],
                                          "AMP@" + conds[j], pol, B, a, b,
                                          group="within_AMP"))
    # --- TEM-1 跨药（3 个条件，含冻结主条件 AMP@781→AZT@36）
    d2 = np.load(os.path.join(ROOT, "data", "processed", "M4_EXP2_V.npz"))
    keys = ["AMP_781.0", "AZT_0.44", "AZT_36.0"]
    lab = {"AMP_781.0": "AMP@781.0", "AZT_0.44": "AZT@0.44", "AZT_36.0": "AZT@36.0"}
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            for si, pol in enumerate(POLICIES):
                for bi, B in enumerate(BUDGETS):
                    a = np.nanmean(d2["R_%s" % keys[i]][si, bi], axis=1)
                    b = np.nanmean(d2["R_%s" % keys[j]][si, bi], axis=1)
                    rows.append(_pair_row("TEM-1CML", lab[keys[i]], lab[keys[j]],
                                          pol, B, a, b, group="cross_drug"))
    M = pd.DataFrame(rows)
    M.to_csv(OUT_MAP, index=False)
    return M


def _pair_row(dataset, A, B, pol, budget, ra, rb, group="within_task"):
    ma = ~np.isnan(ra); mb = ~np.isnan(rb); m = ma & mb
    if m.sum() < 50:
        return dict(dataset=dataset, group=group, task_A=A, task_B=B, policy=pol, budget=budget, n=int(m.sum()))
    ua = np.array([utility_from_values(ra[ma])[0](z) for z in ra[m]])
    ub = np.array([utility_from_values(rb[mb])[0](z) for z in rb[m]])
    rho = spearman(ua, ub)

    def regret(src, dst):
        o = ~np.isnan(dst)
        vo = np.nanmax(dst[o]); vr = np.nanpercentile(dst[o], 5)
        dn = vo - vr
        if dn <= 0:
            return np.nan
        fin = ~np.isnan(src) & o
        if fin.sum() < 10:
            return np.nan
        pick = np.flatnonzero(fin)[np.argmax(src[fin])]
        return (vo - dst[pick]) / dn

    beta = r2 = np.nan
    if np.std(ua) > 0 and np.std(ub) > 0:
        za = (ua - ua.mean()) / ua.std(); zb = (ub - ub.mean()) / ub.std()
        beta = float(np.polyfit(za, zb, 1)[0])
        r2 = float(np.corrcoef(za, zb)[0, 1] ** 2)
    iqr_a = float(np.percentile(ua, 75) - np.percentile(ua, 25))
    iqr_b = float(np.percentile(ub, 75) - np.percentile(ub, 25))
    return dict(dataset=dataset, group=group, task_A=A, task_B=B, policy=pol, budget=budget, n=int(m.sum()),
                rho_rank=round(rho, 4),
                regret_A_to_B=round(regret(ra, rb), 4),
                regret_B_to_A=round(regret(rb, ra), 4),
                beta=round(beta, 4) if beta == beta else "",
                r2=round(r2, 4) if r2 == r2 else "",
                iqr_ratio=round(iqr_b / iqr_a, 4) if iqr_a > 0 else "")


# ---------------------------------------------------------------- Part 2
_ROB_CACHE = {}


def _rob(v, ctx):
    """Hamming-1 邻域均值（向量化）。按 id(v) 缓存，避免每对重算。"""
    k = id(v)
    if k in _ROB_CACHE:
        return _ROB_CACHE[k]
    with np.errstate(invalid="ignore"):
        r = np.nanmean(v[ctx.neighbors], axis=1)
    _ROB_CACHE[k] = r
    return r


def pair_features(vals, meta):
    """只用简单、可解释的 task-pair 特征（用户指定的六类）。"""
    ctxs = {ds: make_context(sp) for ds, sp in meta.items()}
    keys = sorted(vals)
    rows = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            dsA, tA = keys[i]; dsB, tB = keys[j]
            if dsA != dsB:
                continue                      # 只做同数据集内的 pair（空间必须可比）
            sp = meta[dsA]
            va, vb = vals[keys[i]], vals[keys[j]]
            m = ~np.isnan(va) & ~np.isnan(vb)
            if m.sum() < 100:
                continue
            # f1 landscape rank correlation（= CL-5 那一类量）
            f1 = spearman(va[m], vb[m])
            # f4 local-neighborhood agreement：对每个可测基因型，比较每个邻居的升降号
            # 同样向量化：对全部节点算 (邻居值 - 自身值) 的符号，再比两任务的符号是否一致
            CX = ctxs[dsA]
            NB = CX.neighbors
            ok = m[:, None] & m[NB]
            sa = np.sign(va[NB] - va[:, None]); sb = np.sign(vb[NB] - vb[:, None])
            agree = int(((sa == sb) & ok).sum()); tot = int(ok.sum())
            f4 = agree / tot if tot else np.nan
            # f2 beneficial-mutation overlap（以全 WT 背景为准）
            wt = tuple(sp.alleles_at(p)[0] for p in range(sp.n_positions))

            def benset(v):
                base = v[sp.index_of(wt)]
                s = set()
                if np.isnan(base):
                    return s
                for p in range(sp.n_positions):
                    for a in sp.alleles_at(p)[1:]:
                        y = sp.index_of(tuple(wt[:p]) + (a,) + tuple(wt[p + 1:]))
                        if not np.isnan(v[y]) and v[y] > base:
                            s.add((p, a))
                return s
            ba, bb = benset(va), benset(vb)
            f2 = len(ba & bb) / len(ba | bb) if (ba | bb) else np.nan
            # f3 sign-epistasis overlap：双突变相对 WT 的 epistasis 符号
            def epsigns(v):
                base = v[sp.index_of(wt)]
                out = {}
                if np.isnan(base):
                    return out
                subs = []
                for p in range(sp.n_positions):
                    for a in sp.alleles_at(p)[1:]:
                        subs.append((p, a))
                for ii in range(len(subs)):
                    for jj in range(ii + 1, len(subs)):
                        (p1, a1), (p2, a2) = subs[ii], subs[jj]
                        if p1 == p2:
                            continue
                        s1 = list(wt); s1[p1] = a1
                        s2 = list(wt); s2[p2] = a2
                        s12 = list(wt); s12[p1] = a1; s12[p2] = a2
                        v1, v2, v12 = v[sp.index_of(tuple(s1))], v[sp.index_of(tuple(s2))], \
                            v[sp.index_of(tuple(s12))]
                        if np.isnan(v1) or np.isnan(v2) or np.isnan(v12):
                            continue
                        e = (v12 - base) - ((v1 - base) + (v2 - base))
                        out[(p1, a1, p2, a2)] = np.sign(e)
                return out
            ea, eb = epsigns(va), epsigns(vb)
            common = set(ea) & set(eb)
            f3 = (np.mean([ea[k] == eb[k] for k in common]) if common else np.nan)
            # f6 parent-level robustness consistency（Hamming-1 邻域均值）
            # 用 M4 已构建的 ctx.neighbors 邻居表**向量化**（原实现逐节点枚举，慢 ~1000x）
            ra_, rb_ = _rob(va, ctxs[dsA]), _rob(vb, ctxs[dsA])
            mm = ~np.isnan(ra_) & ~np.isnan(rb_)
            f6 = spearman(ra_[mm], rb_[mm]) if mm.sum() > 100 else np.nan
            # f5 task distance：1 - landscape rho（并用浓度比作为 TEM-1 的辅助距离）
            f5 = 1 - f1 if f1 == f1 else np.nan
            rows.append(dict(dataset=dsA, task_A=tA, task_B=tB,
                             f1_landscape_rho=round(f1, 4),
                             f2_beneficial_overlap=round(f2, 4) if f2 == f2 else "",
                             f3_sign_epistasis_agree=round(f3, 4) if f3 == f3 else "",
                             f4_neighborhood_agree=round(f4, 4) if f4 == f4 else "",
                             f5_task_distance=round(f5, 4) if f5 == f5 else "",
                             f6_robustness_consistency=round(f6, 4) if f6 == f6 else "",
                             n_common=int(m.sum()), n_epistasis_common=len(common)))
    F = pd.DataFrame(rows)
    F.to_csv(OUT_FEAT, index=False)
    return F


def main() -> int:
    print("=== Part 1: transfer map ===", flush=True)
    M = build_map()
    print("  rows=%d  pairs=%d" % (len(M), M.groupby(["dataset", "task_A", "task_B"]).ngroups))
    print("WROTE", OUT_MAP)
    print("\n=== Part 2: pair features ===", flush=True)
    vals, meta = load_values()
    print("  loaded %d task-value arrays" % len(vals))
    F = pair_features(vals, meta)
    print("  rows=%d" % len(F))
    print("WROTE", OUT_FEAT)
    print("\n=== Part 3: feature vs transferability ===", flush=True)
    Mv = M.dropna(subset=["rho_rank"])
    agg = (Mv.groupby(["dataset", "task_A", "task_B"])
           .agg(rho_rank_mean=("rho_rank", "mean"),
                regret_A_to_B_mean=("regret_A_to_B", "mean"),
                regret_B_to_A_mean=("regret_B_to_A", "mean"),
                beta_mean=("beta", "mean"), r2_mean=("r2", "mean"),
                n_cells=("rho_rank", "size")).reset_index())
    for _df in (agg, F):
        _df["pk"] = [ "|".join(sorted([a, b])) for a, b in zip(_df.task_A, _df.task_B) ]
    J = agg.merge(F, on=["dataset", "pk"], how="inner", suffixes=("", "_f"))
    print("  merged pairs=%d" % len(J))
    if len(J) >= 5:
        cand = ["f1_landscape_rho", "f2_beneficial_overlap", "f3_sign_epistasis_agree",
                "f4_neighborhood_agree", "f5_task_distance", "f6_robustness_consistency"]
        rows = []
        for y in ("rho_rank_mean", "regret_A_to_B_mean", "beta_mean"):
            for c in cand:
                z = J[[c, y]].apply(pd.to_numeric, errors="coerce").dropna()
                if len(z) < 5:
                    continue
                r = spearman(z[c].values, z[y].values)
                rows.append(dict(outcome=y, feature=c, n=len(z), spearman=round(r, 4)))
        C = pd.DataFrame(rows)
        C.to_csv(OUT_CORR, index=False)
        print("WROTE", OUT_CORR)
        pd.set_option("display.width", 200)
        print(C.pivot(index="feature", columns="outcome", values="spearman").to_string())
    J.to_csv(os.path.join(ROOT, "results", "tables", "M5_PAIR_LEVEL.csv"), index=False)
    print("\nWROTE M5_PAIR_LEVEL.csv  pairs=%d" % len(J))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
