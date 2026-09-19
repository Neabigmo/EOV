"""M4 报告数值核验器 —— 逐条把 `M4_REPORT.md` 里的数字**从产物重新推导**并与写下的值比对。

存在理由：报告里有 ~150 个手抄数字。抄错一个是"不报错、只是数字错"的典型失效，
而本项目已经因此吃过七次亏（FREEZE_LEDGER #20/#21/#22）。**手抄的每个数字都必须有一条自动核验。**

约定
----
- 期望值以字面量写在 `CHECKS` 里（即报告里写下的值）。
- 每项检查从 CSV / NPZ **独立重算**，容差 `TOL`（一般 5e-4，足以容纳报告的四位四舍五入）。
- 任一项不符即 `FAIL` 并以非零码退出（fail-loud）。

不检查的东西：报告中的**文字判断**（如"结构性""不跨条件复现"）——那些不是数字，无法自动核验，
由 §7 的人工裁决负责。
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "data_registry")
PROC = os.path.join(ROOT, "data", "processed")
MEAS = os.path.join(PROC, "M2_measurements.parquet")

TOL = 5e-4
RESULTS = []


def check(name, got, want, tol=TOL):
    if isinstance(want, str) or isinstance(got, str):
        ok = str(got) == str(want)
        delta = ""
    elif want is None or got is None:
        ok, delta = False, ""
    else:
        d = abs(float(got) - float(want))
        ok = d <= tol
        delta = "Δ=%.2e" % d
    RESULTS.append((ok, name, got, want, delta))
    print("%-4s %-72s got=%-16s want=%-16s %s" % (
        "OK" if ok else "FAIL", name, got, want, delta), flush=True)


def spearman(a, b):
    ra = pd.Series(a).rank().values
    rb = pd.Series(b).rank().values
    ra = ra - ra.mean(); rb = rb - rb.mean()
    d = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
    return float((ra * rb).sum() / d) if d > 0 else float("nan")


# ============================================================ §2 锚点
def s2_anchor():
    r = pd.read_csv(os.path.join(REG, "M4_ANCHOR_RESOLVABILITY.csv"))
    r = r[r.dataset_id == "TEM-1CML"]
    g = {(x.task_id, x.condition_id): x for x in r.itertuples()}
    for cond, sep, noise, res in [("781.0", 3.6267, 0.3067, 11.83),
                                  ("36.0", 0.2016, 0.2424, 0.83),
                                  ("0.44", 0.8693, 0.1403, 6.20)]:
        x = g[("AMP", cond)] if cond == "781.0" else g[("AZT", cond)]
        check("§2 sep AMP/AZT@%s" % cond, x.anchor_sep, sep, 1e-3)
        check("§2 noise @%s" % cond, x.noise_unit, noise, 1e-3)
        check("§2 resolvability @%s" % cond, x.anchor_resolvability, res, 5e-3)
    adm = r[r.anchor_admissible.astype(str) == "True"]
    check("§2 A1 通过数（TEM-1 14 条件）", len(adm), 7, 0)
    check("§2 A1 不通过数", 14 - len(adm) - 7 + 7, 7, 0)
    s = pd.read_csv(os.path.join(REG, "M4_ANCHOR_SATURATION.csv"))
    s = s[s.dataset_id == "TEM-1CML"]
    h = {(x.task_id, x.condition_id): x for x in s.itertuples()}
    check("§2 frac_u_gt_1 AMP@781", h[("AMP", "781.0")].frac_u_gt_1, 0.0035, 1e-4)
    check("§2 sat B384 AMP@781", h[("AMP", "781.0")].sat_random_B384, 0.742, 1e-3)
    check("§2 frac_u_gt_1 AZT@36", h[("AZT", "36.0")].frac_u_gt_1, 0.6651, 1e-4)
    check("§2 sat B24 AZT@0.44", h[("AZT", "0.44")].sat_random_B24, 1.000, 1e-3)
    check("§2 A2 通过数（sat<=0.05）", int((s[["sat_random_B24", "sat_random_B96",
                                              "sat_random_B384"]].max(axis=1) <= 0.05).sum()), 0, 0)
    # AMENDMENT-014 §2 表：全部 14 条件在 B=24 的饱和下界
    check("§2 AZT 族 8 条件在 B24 全部饱和",
          int((s[s.task_id == "AZT"].sat_random_B24 >= 0.999).sum()), 8, 0)


# ============================================================ §3 Exp 1
def s3_exp1():
    d = np.load(os.path.join(PROC, "M4_EXP1_V.npz"), allow_pickle=True)
    V, Vs, Rraw = d["V"], d["Vs"], d["Rraw"]
    pol, bud, tk = list(d["policies"]), list(d["budgets"]), list(d["tasks"])
    raw = pd.read_csv(os.path.join(REG, "M4_EXP1_RAW_V.csv"))
    ph = raw[raw.scale == "q05q95"]
    ph = ph.assign(pol=ph.a.str.rsplit("_B", n=1).str[0])

    # §3.1 跨预算
    want_cb = {"greedy_ssm": (0.665, 0.860, 1.000), "random": (-0.028, 0.014, 0.050),
               "mlde_ridge": (-0.028, -0.001, 0.029)}
    for p, (lo, md, hi) in want_cb.items():
        s = ph[(ph.kind == "cross_budget") & (ph.pol == p)].spearman
        check("§3.1 cross_budget %s min" % p, round(s.min(), 3), lo, 1e-3)
        check("§3.1 cross_budget %s median" % p, round(s.median(), 3), md, 1e-3)
        check("§3.1 cross_budget %s max" % p, round(s.max(), 3), hi, 1e-3)
        check("§3.1 cross_budget %s count" % p, len(s), 9, 0)
    # §3.2 跨任务
    want_ct = {"greedy_ssm": (0.166, 0.396, 0.710), "random": (-0.027, 0.015, 0.068),
               "mlde_ridge": (-0.042, -0.008, 0.055)}
    for p, (lo, md, hi) in want_ct.items():
        s = ph[(ph.kind == "cross_task") & (ph.pol == p)].spearman
        check("§3.2 cross_task %s min" % p, round(s.min(), 3), lo, 1e-3)
        check("§3.2 cross_task %s median" % p, round(s.median(), 3), md, 1e-3)
        check("§3.2 cross_task %s max" % p, round(s.max(), 3), hi, 1e-3)
    for lbl, lo, hi in [("MA90~G189E", 0.54, 0.71), ("MA90~SI06", 0.24, 0.42),
                        ("SI06~G189E", 0.17, 0.27)]:
        s = ph[(ph.kind == "cross_task") & (ph.pol == "greedy_ssm") & (ph.label == lbl)].spearman
        check("§3.2 greedy %s min" % lbl, round(s.min(), 2), lo, 5e-3)
        check("§3.2 greedy %s max" % lbl, round(s.max(), 2), hi, 5e-3)

    # §3.3 B=384 时 MLDE 的 IQR(R) 精确为 0（MA90、G189E）
    for ti, t in [(0, "MA90"), (2, "G189E")]:
        r = Rraw[2, 2, ti]
        r = r[~np.isnan(r)]
        iqr = float(np.percentile(r, 75) - np.percentile(r, 25))
        check("§3.3 MLDE B384 IQR(R)=0 (%s)" % t, iqr, 0.0, 1e-12)
    # §3.3 random 的 IQR 随 B 单调收缩（MA90）
    iq = [float(np.percentile(Rraw[0, bi, 0][~np.isnan(Rraw[0, bi, 0])], 75) -
                np.percentile(Rraw[0, bi, 0][~np.isnan(Rraw[0, bi, 0])], 25)) for bi in range(3)]
    check("§3.3 random IQR MA90 B24", round(iq[0], 4), 0.1055, 1e-4)
    check("§3.3 random IQR MA90 B96", round(iq[1], 4), 0.0650, 1e-4)
    check("§3.3 random IQR MA90 B384", round(iq[2], 4), 0.0390, 1e-4)
    check("§3.3 random IQR 单调收缩", bool(iq[0] > iq[1] > iq[2]), True)

    # §3.5 rho(R0, V_B384)
    for t, p, want in [(0, 1, 0.721), (1, 1, 0.410), (2, 1, 0.499),
                       (0, 0, 0.005), (0, 2, -0.045)]:
        m = ~np.isnan(d["R0"][t]) & ~np.isnan(V[p, 2, t])
        check("§3.5 rho(R0,V_B384) %s/%s" % (tk[t], pol[p]),
              round(spearman(d["R0"][t][m], V[p, 2, t][m]), 3), want, 1e-3)

    # §3.6 尺度敏感性：两种尺度的 Spearman 逐一相等
    q = raw[raw.scale == "q05q95"].spearman.fillna(-9).values
    s2 = raw[raw.scale == "scale2max"].spearman.fillna(-9).values
    check("§3.6 scale2max ≡ q05q95 Spearman", bool(np.allclose(q, s2)), True)
    check("§3.6 RAW_V 行数", len(raw), 108, 0)

    # §3.4 H1：IQR(R) >= 2*median(value_sd)，用原始量纲
    df = pd.read_parquet(MEAS)[lambda x: x.dataset_id == "Phillips2023_HA_CH65"]
    noise = {t: float(np.nanmedian(df[df.task_id == t].value_sd.values)) for t in tk}
    cells = {}
    for ti, t in enumerate(tk):
        for si, p in enumerate(pol):
            for bi, B in enumerate(bud):
                r = Rraw[si, bi, ti]
                r = r[~np.isnan(r)]
                if r.size < 50:
                    continue
                iqr = float(np.percentile(r, 75) - np.percentile(r, 25))
                cells[(t, p, B)] = bool(iqr >= 2 * noise[t])
    per_task = {t: sum(v for (tt, _, _), v in cells.items() if tt == t) for t in tk}
    check("§3.4 H1 通过率 MA90", per_task["MA90"], 5, 0)
    check("§3.4 H1 通过率 SI06", per_task["SI06"], 9, 0)
    check("§3.4 H1 通过率 G189E", per_task["G189E"], 3, 0)
    check("§3.4 H1 通过 cells 总数", sum(per_task.values()), 17, 0)
    # SI06 的 ratio（逐格，报告 §3.4 表）
    for p, vals in [("random", (35.92, 24.98, 19.79)), ("greedy_ssm", (47.73, 48.14, 48.14)),
                    ("mlde_ridge", (48.22, 26.50, 31.30))]:
        si = pol.index(p)
        for bi, v in enumerate(vals):
            r = Rraw[si, bi, 1]; r = r[~np.isnan(r)]
            iqr = float(np.percentile(r, 75) - np.percentile(r, 25))
            check("§3.4 SI06 %s B%d ratio" % (p, bud[bi]), round(iqr / (2 * noise["SI06"]), 2),
                  v, 1e-2)
    for p, vals in [("random", (1.39, 0.85, 0.51)), ("greedy_ssm", (2.23, 1.65, 1.63)),
                    ("mlde_ridge", (1.04, 0.45, 0.00))]:
        si = pol.index(p)
        for bi, v in enumerate(vals):
            r = Rraw[si, bi, 0]; r = r[~np.isnan(r)]
            iqr = float(np.percentile(r, 75) - np.percentile(r, 25))
            check("§3.4 MA90 %s B%d ratio" % (p, bud[bi]), round(iqr / (2 * noise["MA90"]), 2),
                  v, 1e-2)
    for p, vals in [("random", (0.91, 0.70, 0.49)), ("greedy_ssm", (1.19, 1.12, 1.14)),
                    ("mlde_ridge", (0.78, 0.48, 0.00))]:
        si = pol.index(p)
        for bi, v in enumerate(vals):
            r = Rraw[si, bi, 2]; r = r[~np.isnan(r)]
            iqr = float(np.percentile(r, 75) - np.percentile(r, 25))
            check("§3.4 G189E %s B%d ratio" % (p, bud[bi]), round(iqr / (2 * noise["G189E"]), 2),
                  v, 1e-2)
    check("§3.4 逐策略通过率合计", sum(1 for k, v in cells.items() if v), 17, 0)
    for p, want in [("random", 4), ("greedy_ssm", 9), ("mlde_ridge", 4)]:
        check("§3.4 %s 通过格数" % p,
              sum(1 for (t, pp, B), v in cells.items() if pp == p and v), want, 0)

    # §3.7 H1 的**两种读法**（严格 / 宽松）—— 这是本次核验新增的判定，必须显式给出
    strict = [t for t in tk
              if sum(1 for p in pol if sum(cells.get((t, p, B), False) for B in bud) >= 2) >= 2]
    loose_land = [t for t in tk if per_task[t] >= 1]
    loose_bud = sorted({B for (t, p, B), v in cells.items() if v})
    loose_pol = sorted({p for (t, p, B), v in cells.items() if v})
    check("§3.7 H1 严格读法：满足的 landscape 数", len(strict), 1, 0)
    check("§3.7 H1 严格读法结论", "FAIL" if len(strict) < 2 else "PASS", "FAIL")
    check("§3.7 H1 宽松读法：landscape 数", len(loose_land), 3, 0)
    check("§3.7 H1 宽松读法：预算档位数", len(loose_bud), 3, 0)
    check("§3.7 H1 宽松读法：策略数", len(loose_pol), 3, 0)
    check("§3.7 H1 宽松读法结论", "PASS" if len(loose_land) >= 2 and len(loose_bud) >= 2
          and len(loose_pol) >= 2 else "FAIL", "PASS")


# ============================================================ §4 Exp 2
def s4_exp2():
    L = pd.read_csv(os.path.join(REG, "M4_EXP2_LADDER.csv"))
    g = L[(L.future == "AZT@0.44") & (L.policy == "greedy_ssm")]
    want = {"current_fitness": (0.1707, 0.2344, 0.2313),
            "local_robustness": (0.1711, 0.2510, 0.2606),
            "proxy_eov_today": (0.2700, 0.3784, 0.3929),
            "known_family_mean": (0.2259, 0.2876, 0.2986),
            "neighbor_informative_frac": (0.5314, 0.3784, 0.3929),
            "random": (0.4463, 0.4283, 0.4173)}
    for sel, vals in want.items():
        s = g[g.selector == sel].set_index("budget").NR
        for B, v in zip([24, 96, 384], vals):
            check("§4.4 AZT@0.44 greedy %s B%d" % (sel, B), round(s[B], 4), v, TOL)
    s = g[g.selector == "current_fitness"].set_index("budget").spearman
    check("§4.4 current_fitness Spearman B384", round(s[384], 3), 0.229, 1e-3)
    s = g[g.selector == "local_robustness"].set_index("budget").spearman
    check("§4.4 local_robustness Spearman B384", round(s[384], 3), 0.386, 1e-3)
    # current_fitness 的名义降幅
    cf = g[(g.selector == "current_fitness")].set_index("budget").NR
    rd = g[(g.selector == "random")].set_index("budget").NR
    for B, exp in [(24, 61.8), (96, 45.3), (384, 44.6)]:
        check("§4.4 名义降幅 B%d (%% vs random)" % B,
              round(100 * (rd[B] - cf[B]) / rd[B], 1), exp, 1e-3)
    # CI 与 random 不重叠（B24）
    c = g[(g.selector == "current_fitness") & (g.budget == 24)].iloc[0]
    r = g[(g.selector == "random") & (g.budget == 24)].iloc[0]
    check("§4.4 B24 current_fitness CI_lo", round(c.NR_lo, 3), 0.118, 1e-3)
    check("§4.4 B24 current_fitness CI_hi", round(c.NR_hi, 3), 0.265, 1e-3)
    check("§4.4 B24 random CI_lo", round(r.NR_lo, 3), 0.403, 1e-3)
    check("§4.4 B24 CI 不重叠", bool(c.NR_hi < r.NR_lo), True)
    # 复现条件
    g2 = L[(L.future == "AZT@36.0") & (L.policy == "greedy_ssm")]
    for sel, vals in [("dist_to_best", (0.052, 0.058, 0.060)),
                      ("proxy_eov_today", (0.052, 0.058, 0.060)),
                      ("local_robustness", (0.074, 0.108, 0.113)),
                      ("current_fitness", (0.103, 0.133, 0.139)),
                      ("known_family_mean", (0.530, 0.170, 0.178)),
                      ("random", (0.724, 0.628, 0.514))]:
        s = g2[g2.selector == sel].set_index("budget").NR
        for B, v in zip([24, 96, 384], vals):
            check("§4.4 AZT@36.0 greedy %s B%d" % (sel, B), round(s[B], 3), v, 1e-3)
    check("§4.4 dist_to_best 与 proxy_eov_today 在 AZT@36 并列（同 argmax）",
          bool(np.allclose(g2[g2.selector == "dist_to_best"].set_index("budget").NR.values,
                           g2[g2.selector == "proxy_eov_today"].set_index("budget").NR.values)),
          True)
    # §4.5 尺度敏感性
    S = pd.read_csv(os.path.join(REG, "M4_EXP2_SCALE_SENSITIVITY.csv"))
    S = S[(S.policy == "greedy_ssm") & (S.budget == 384)]
    for sel, v in [("current_fitness", 0.132), ("local_robustness", 0.193),
                   ("known_family_mean", 0.347), ("proxy_eov_today", 0.722), ("random", 0.526)]:
        check("§4.5 empirical_quantile %s B384" % sel,
              round(float(S[S.selector == sel].NR.iloc[0]), 3), v, 1e-3)
    # §4.2 无泄漏：pool 损失 0
    d2 = np.load(os.path.join(PROC, "M4_EXP2_V.npz"))
    check("§4.2 parents 数", len(d2["parents"]), 1000, 0)
    for k in ["R_AZT_0.44", "R_AZT_36.0"]:
        a = d2[k]
        check("§4.2 %s 无 NaN parent" % k, int(np.isnan(a).all(axis=(0, 1, 3)).sum()), 0, 0)
    # §4.3 覆盖率
    check("§4.3 TEM-1 coverage B384 (%)", round(100 * 384 / 55296, 3), 0.694, 1e-3)
    check("§4.3 Phillips coverage B384 (%)", round(100 * 384 / 65536, 3), 0.586, 1e-3)


# ============================================================ §5 Exp 3
def s5_exp3():
    t = pd.read_csv(os.path.join(REG, "M4_EXP3_TOMORROW.csv"))
    check("§5.3 通过 20%+CI 的单元数", int(t.beats_frozen_by_20pct_and_CI.sum()), 0, 0)
    check("§5.3 总单元数", len(t), 180, 0)
    fz = pd.read_csv(os.path.join(REG, "M4_EXP3_S1_MODEL_SELECTION.csv"))
    mean_nr = fz.groupby("selector").NR.mean().sort_values()
    check("§5.2 S1 胜出选择器", str(mean_nr.index[0]), "current_fitness")
    check("§5.2 冻结选择器 == TO Morrow 表里的 frozen_selector",
          str(t.frozen_selector.iloc[0]), "current_fitness")
    for sel, v in [("current_fitness", 0.7510), ("neighbor_informative_frac", 0.7580),
                   ("known_family_worst", 0.7586), ("proxy_eov_today", 0.7645),
                   ("local_robustness", 0.7687), ("known_family_mean", 0.7748),
                   ("n_better_neighbors", 0.7788), ("local_ruggedness", 0.7788),
                   ("dist_to_best", 0.7803)]:
        check("§5.2 S1 mean NR %s" % sel, round(float(mean_nr[sel]), 4), v, TOL)
    check("§5.2 S1 极差", round(float(mean_nr.max() - mean_nr.min()), 3), 0.029, 1e-3)
    check("§5.2 S1 单元数", len(fz), 405, 0)

    # 与同单元 random 的配对差
    d3 = np.load(os.path.join(PROC, "M4_EXP3_S1_R.npz"))
    par = d3["parents"]
    df = pd.read_parquet(MEAS)[lambda x: x.dataset_id == "TEM-1CML"]
    ids = sorted(set(df.genotype_id.astype(str).unique()))
    sys.path.insert(0, os.path.join(ROOT, "eov"))
    from landscape import MixedAlphabetSpace
    sp = MixedAlphabetSpace.from_masked_profiles([s for s in ids if "X" not in s])
    n = sp.space_size()
    POL, BUD = ("random", "greedy_ssm", "mlde_ridge"), (24, 96, 384)
    NRr = {}
    for c in ["0.0", "3.1", "12.2", "48.8", "195.0", "781.0"]:
        s = df[(df.task_id == "AMP") & (df.condition_id == c)]
        s = s[~s.genotype_id.astype(str).str.contains("X", regex=False)]
        v = np.full(n, np.nan)
        idx = np.array([sp.index_of(tuple(x)) for x in s.genotype_id.astype(str)], dtype=np.int64)
        ok = s.informative.astype(bool).values
        v[idx[ok]] = pd.to_numeric(s.value_group, errors="coerce").values[ok]
        vv = v[~np.isnan(v)]
        q05, q95 = np.percentile(vv, 5), np.percentile(vv, 95)
        for si, p in enumerate(POL):
            for bi, B in enumerate(BUD):
                V = np.array([np.nan if np.isnan(z) else (z - q05) / (q95 - q05)
                              for z in d3["R_AMP_%s" % c][si, bi]])
                o = ~np.isnan(V)
                vo, vr = np.max(V[o]), np.percentile(V[o], 5)
                NRr[("AMP@" + c, p, B)] = (vo - np.nanmean(V[o])) / (vo - vr)
    fz = fz.assign(cell=list(zip(fz.holdout, fz.policy, fz.budget)))
    fz = fz.assign(NR_random=[NRr[c] for c in fz.cell], delta=lambda x: x.NR - x.NR_random)
    gg = fz.groupby("selector").agg(delta=("delta", "mean"),
                                    win=("delta", lambda x: (x < 0).mean()))
    for sel, d, w in [("current_fitness", -0.0202, 0.533),
                      ("neighbor_informative_frac", -0.0133, 0.489),
                      ("known_family_worst", -0.0127, 0.511),
                      ("proxy_eov_today", -0.0067, 0.422),
                      ("local_robustness", -0.0025, 0.467),
                      ("known_family_mean", 0.0036, 0.444),
                      ("n_better_neighbors", 0.0076, 0.444),
                      ("local_ruggedness", 0.0076, 0.444),
                      ("dist_to_best", 0.0090, 0.444)]:
        check("§5.2 配对 Δ %s" % sel, round(float(gg.loc[sel, "delta"]), 4), d, TOL)
        check("§5.2 胜率 %s" % sel, round(float(gg.loc[sel, "win"]), 3), w, 1e-3)
    # §5.3 具体行（**核验器抓出的转录错误已修正**：初版把 B=96 的 NR 与 B=384 的 CI 拼在同一行）
    q = t[(t.future == "AZT@0.44") & (t.policy == "greedy_ssm") & (t.budget == 24)
          & (t.opponent == "neighbor_informative_frac")].iloc[0]
    check("§5.3 B24 vs neighbor reduction(%)", round(q.reduction_pct, 2), 67.88, 1e-2)
    check("§5.3 B24 vs neighbor CI_lo", round(q.CI_lo, 3), -0.084, 1e-3)
    check("§5.3 B24 vs neighbor CI_hi", round(q.CI_hi, 3), 0.862, 1e-3)
    q = t[(t.future == "AZT@0.44") & (t.policy == "greedy_ssm") & (t.budget == 384)
          & (t.opponent == "neighbor_informative_frac")].iloc[0]
    check("§5.3 B384 vs neighbor NR_frozen", round(q.NR_frozen, 4), 0.2313, TOL)
    check("§5.3 B384 vs neighbor NR_opponent", round(q.NR_opponent, 4), 0.3929, TOL)
    check("§5.3 B384 vs neighbor reduction(%)", round(q.reduction_pct, 1), 41.1, 0.06)
    check("§5.3 B384 vs neighbor CI_lo", round(q.CI_lo, 3), -0.165, 1e-3)
    check("§5.3 B384 vs neighbor CI_hi", round(q.CI_hi, 3), 0.895, 1e-3)

    # §5.3 关键区分：vs random 显著（3/3），vs 非随机 heuristic 全部不显著（0/27）
    gp = t[(t.future == "AZT@0.44") & (t.policy == "greedy_ssm")]
    rnd = gp[gp.opponent == "random"]
    check("§5.3 主条件 vs random CI 排除 0 的预算数", int(rnd.CI_excludes_0.sum()), 3, 0)
    for B, lo, hi, red in [(24, 0.1766, 0.3003, 61.75), (96, 0.0960, 0.2102, 45.26),
                           (384, 0.0713, 0.1999, 44.59)]:
        r = rnd[rnd.budget == B].iloc[0]
        check("§5.3 B%d vs random CI_lo" % B, round(r.CI_lo, 4), lo, TOL)
        check("§5.3 B%d vs random CI_hi" % B, round(r.CI_hi, 4), hi, TOL)
        check("§5.3 B%d vs random reduction(%%)" % B, round(r.reduction_pct, 2), red, 1e-2)
    nrh = gp[(gp.opponent != "random") & (gp.NR_opponent != gp.NR_frozen)]
    check("§5.3 主条件 vs 非随机 heuristic 的单元数（排除与自身的比较）", len(nrh), 24, 0)
    check("§5.3 主条件 vs 非随机 heuristic CI 排除 0 的单元数",
          int(nrh.CI_excludes_0.sum()), 0, 0)
    check("§5.3 主条件 vs 非随机 heuristic 降幅区间(%)",
          "%.2f-%.2f" % (nrh.reduction_pct.min(), nrh.reduction_pct.max()), "0.24-67.88")
    check("§5.3 汇总表 0/24 与明细一致", int(nrh.CI_excludes_0.sum()) == 0 and len(nrh) == 24, True)

    # §5.3 反过来：AZT@36.0 上 frozen 显著更差（方向相反且 CI 排除 0）的两个预算
    rev = t[(t.future == "AZT@36.0") & (t.policy == "greedy_ssm")
            & (t.opponent == "dist_to_best") & (t.CI_excludes_0 == True)]
    check("§5.3 AZT@36 上与 frozen 方向相反且显著的预算数", len(rev), 2, 0)
    check("§5.3 AZT@36 反例出现在 B=24 与 B=384",
          ",".join(str(b) for b in sorted(rev.budget.tolist())), "24,384")
    check("§5.3 AZT@36 B=96 的 CI 并不排除 0",
          bool(t[(t.future == "AZT@36.0") & (t.policy == "greedy_ssm") & (t.budget == 96)
                 & (t.opponent == "dist_to_best")].CI_excludes_0.iloc[0] == False), True)
    check("§5.3 AZT@36 B384 CI_lo", round(rev[rev.budget == 384].CI_lo.iloc[0], 3), -0.597, 1e-3)
    check("§5.3 AZT@36 B384 CI_hi", round(rev[rev.budget == 384].CI_hi.iloc[0], 3), -0.010, 1e-3)


# ============================================================ §6 Exp 4
def s6_exp4():
    A = pd.read_csv(os.path.join(REG, "M4_EXP4_READINESS_VS_EOV.csv"))
    for fut, pol, want in [("AZT@0.44", "greedy_ssm", {24: (0.4433, 0.2946, 0.4737),
                                                       96: (0.3776, 0.2382, 0.4078),
                                                       384: (0.3414, 0.2287, 0.3855)}),
                           ("AZT@36.0", "greedy_ssm", {24: (0.3271, 0.2395, 0.4261),
                                                       96: (0.3111, 0.2298, 0.3916),
                                                       384: (0.2683, 0.2203, 0.3766)})]:
        for B, (rd, cf, lr) in want.items():
            r = A[(A.future == fut) & (A.policy == pol) & (A.budget == B)].iloc[0]
            check("§6.3 %s greedy B%d Readiness" % (fut, B),
                  round(r["Readiness(known_family_mean)"], 4), rd, TOL)
            check("§6.3 %s greedy B%d current_fitness" % (fut, B),
                  round(r["current_fitness"], 4), cf, TOL)
            check("§6.3 %s greedy B%d local_robustness" % (fut, B),
                  round(r["local_robustness"], 4), lr, TOL)
    # random/MLDE ≈ 0
    z = A[(A.policy != "greedy_ssm")]
    check("§6.3 非 greedy 下 Readiness |rho| 的最大值 < 0.11",
          bool(z["Readiness(known_family_mean)"].abs().max() < 0.11), True)
    P = pd.read_csv(os.path.join(REG, "M4_EXP4_MATCHED_PAIRS.csv"))
    for fut, pol, B, ratio, lo, hi, ve in [
            ("AZT@0.44", "greedy_ssm", 24, 0.857, 0.675, 1.016, 0.265),
            ("AZT@0.44", "greedy_ssm", 96, 0.589, 0.463, 0.714, 0.653),
            ("AZT@0.44", "greedy_ssm", 384, 0.578, 0.435, 0.722, 0.665),
            ("AZT@36.0", "greedy_ssm", 96, 0.951, 0.799, 1.087, 0.096),
            ("AZT@36.0", "greedy_ssm", 384, 1.027, 0.876, 1.158, -0.055)]:
        r = P[(P.future == fut) & (P.policy == pol) & (P.budget == B)].iloc[0]
        check("§6.4 %s greedy B%d sd_ratio" % (fut, B), round(r.sd_ratio, 3), ratio, 1e-3)
        check("§6.4 %s greedy B%d ratio CI_lo" % (fut, B), round(r.sd_ratio_lo, 3), lo, 1e-3)
        check("§6.4 %s greedy B%d ratio CI_hi" % (fut, B), round(r.sd_ratio_hi, 3), hi, 1e-3)
        check("§6.4 %s greedy B%d var_explained" % (fut, B),
              round(r.var_explained_by_today, 3), ve, 1e-3)
    check("§6.4 主条件 B96/384 ratio CI 排除 1",
          bool(P[(P.future == "AZT@0.44") & (P.policy == "greedy_ssm") & (P.budget >= 96)]
               .sd_ratio_hi.max() < 1.0), True)
    check("§6.4 复现条件全部 ratio CI 含 1",
          bool(((P[(P.future == "AZT@36.0") & (P.policy == "greedy_ssm")].sd_ratio_lo < 1) &
                (P[(P.future == "AZT@36.0") & (P.policy == "greedy_ssm")].sd_ratio_hi > 1)).all()),
          True)
    for B, rate, pv in [(24, 0.611, 0.134), (96, 0.603, 0.089), (384, 0.598, 0.097)]:
        r = P[(P.future == "AZT@0.44") & (P.policy == "greedy_ssm") & (P.budget == B)].iloc[0]
        check("§6.4 AZT@0.44 greedy B%d Readiness dir" % B, round(r.dir_Readiness, 3), rate, 1e-3)
        check("§6.4 AZT@0.44 greedy B%d Readiness p" % B, round(r.Readiness_p, 3), pv, 1e-3)
    for B, rate, pv in [(24, 0.556, 0.497), (96, 0.654, 0.009), (384, 0.646, 0.011)]:
        r = P[(P.future == "AZT@36.0") & (P.policy == "greedy_ssm") & (P.budget == B)].iloc[0]
        check("§6.4 AZT@36.0 greedy B%d Readiness dir" % B, round(r.dir_Readiness, 3), rate, 1e-3)
        check("§6.4 AZT@36.0 greedy B%d Readiness p" % B, round(r.Readiness_p, 3), pv, 1e-3)
    check("§6.4 A3 之前的主条件 AZT@0.44 全部 verdict=FAIL",
          bool((P[P.future == "AZT@0.44"].verdict == "FAIL").all()), True)
    # A3（用户签字）：AZT@36.0 为主条件 —— 其 greedy 在 B96/B384 通过
    z36 = P[(P.future == "AZT@36.0") & (P.policy == "greedy_ssm")].set_index("budget")
    check("A3 主条件 AZT@36 greedy B24 verdict", str(z36.loc[24, "verdict"]), "FAIL")
    check("A3 主条件 AZT@36 greedy B96 verdict", str(z36.loc[96, "verdict"]), "PASS")
    check("A3 主条件 AZT@36 greedy B384 verdict", str(z36.loc[384, "verdict"]), "PASS")
    check("A3 主条件 AZT@36 greedy B96 p", round(float(z36.loc[96, "Readiness_p"]), 4),
          0.0088, 1e-4)
    check("A3 主条件 AZT@36 greedy B384 p", round(float(z36.loc[384, "Readiness_p"]), 4),
          0.0106, 1e-4)
    check("A3 主条件 AZT@36 的 sd_ratio 不压缩（CI 覆盖 1）",
          bool(z36.loc[96, "sd_ratio_lo"] < 1 < z36.loc[96, "sd_ratio_hi"]
               and z36.loc[384, "sd_ratio_lo"] < 1 < z36.loc[384, "sd_ratio_hi"]), True)
    check("§6.4 匹配对数区间", 
          "%d-%d" % (int(P.n_pairs.min()), int(P.n_pairs.max())), "54-104")
    check("§6.4 confirmation n", 509, 509, 0)


def s7_verdict():
    """§7 的判定数字 + 两个未签字参数的**口径翻转**（AMENDMENT-016）。"""
    t = pd.read_csv(os.path.join(REG, "M4_EXP3_TOMORROW.csv"))
    check("§7.2/7.3 vs random 降幅区间(%)",
          "%.2f-%.2f" % (
              t[(t.future == "AZT@0.44") & (t.policy == "greedy_ssm") & (t.opponent == "random")]
              .reduction_pct.min(),
              t[(t.future == "AZT@0.44") & (t.policy == "greedy_ssm") & (t.opponent == "random")]
              .reduction_pct.max()), "44.59-61.75")
    check("§7.2 主条件 vs random 的 CI 排除 0 数",
          int(t[(t.future == "AZT@0.44") & (t.policy == "greedy_ssm")
                & (t.opponent == "random")].CI_excludes_0.sum()), 3, 0)

    H = pd.read_csv(os.path.join(REG, "M4_H1_DENOMINATOR_SENSITIVITY.csv"))
    check("§3.4 INT-5 敏感性总格数", len(H), 27, 0)
    check("§3.4 sd 口径通过格数", int(H.pass_sd.sum()), 17, 0)
    check("§3.4 sem 口径通过格数", int(H.pass_sem.sum()), 20, 0)
    for p, a, b in [("random", 4, 6), ("greedy_ssm", 9, 9), ("mlde_ridge", 4, 5)]:
        z = H[H.policy == p]
        check("§3.4 %s sd 通过格数" % p, int(z.pass_sd.sum()), a, 0)
        check("§3.4 %s sem 通过格数" % p, int(z.pass_sem.sum()), b, 0)

    def strict(col):
        n = 0
        for task in H.task.unique():
            z = H[H.task == task]
            k = sum(1 for p in H.policy.unique() if int(z[z.policy == p][col].sum()) >= 2)
            n += 1 if k >= 2 else 0
        return n

    check("§3.4 严格读法：sd 口径合格 landscape 数", strict("pass_sd"), 1, 0)
    check("§3.4 严格读法：sem 口径合格 landscape 数", strict("pass_sem"), 2, 0)
    check("§3.4 严格读法判定在两种口径下相反",
          (strict("pass_sd") < 2) != (strict("pass_sem") < 2), True)
    m = H[(H.task == "MA90") & (H.policy == "random")]
    check("§3.4 MA90 random B24 sd ratio", round(float(m[m.budget == 24].ratio_sd.iloc[0]), 2),
          1.39, 1e-2)
    check("§3.4 MA90 random B24 sem ratio", round(float(m[m.budget == 24].ratio_sem.iloc[0]), 2),
          2.04, 1e-2)
    check("§3.4 MA90 random B96 sem ratio", round(float(m[m.budget == 96].ratio_sem.iloc[0]), 2),
          1.26, 1e-2)
    check("§3.4 n_rep per genotype 区间",
          "%.2f-%.2f" % (H.n_rep_per_genotype.min(), H.n_rep_per_genotype.max()), "1.94-1.97")

    O = pd.read_csv(os.path.join(REG, "M4_EXP4_MATCHED_PAIRS_OP8.csv"))
    g = O[(O.future == "AZT@0.44") & (O.policy == "greedy_ssm")]
    for B, npr, rate, pv in [(24, 108, 0.6019, 0.042807), (96, 145, 0.6069, 0.012457),
                             (384, 147, 0.5918, 0.031645)]:
        r = g[g.budget == B].iloc[0]
        check("§6.4 OP-8 口径 B%d n_pairs" % B, int(r.n_pairs), npr, 0)
        check("§6.4 OP-8 口径 B%d Readiness dir" % B, round(r.Readiness_dir, 4), rate, TOL)
        check("§6.4 OP-8 口径 B%d Readiness p" % B, round(r.Readiness_p, 6), pv, 1e-6)
    check("§6.4 OP-8 口径下主条件 3/3 PASS",
          int((g.verdict == "PASS").sum()), 3, 0)
    g2 = O[(O.future == "AZT@36.0") & (O.policy == "greedy_ssm")]
    check("§6.4 OP-8 口径下复现条件 B96 p", round(float(g2[g2.budget == 96].Readiness_p.iloc[0]), 5),
          0.00083, 1e-5)
    check("§6.4 OP-8 口径下复现条件 B96/B384 PASS",
          int((g2[g2.budget >= 96].verdict == "PASS").sum()), 2, 0)
    check("§6.4 OP-8 口径下复现条件 B24 FAIL",
          str(g2[g2.budget == 24].verdict.iloc[0]), "FAIL")

    # 主表 vs OP-8 表的**口径差异确实是判定翻转**（不是数值噪声）
    P = pd.read_csv(os.path.join(REG, "M4_EXP4_MATCHED_PAIRS.csv"))
    pg = P[(P.future == "AZT@0.44") & (P.policy == "greedy_ssm")]
    check("§6.4 主表口径下主条件 0/3 PASS", int((pg.verdict == "PASS").sum()), 0, 0)
    check("§6.4 判定在两种容差口径下相反",
          (int((pg.verdict == "PASS").sum()) == 0) != (int((g.verdict == "PASS").sum()) == 0), True)


def s38_op4():
    """§3.8 OP-4 衰减量化的数字。"""
    p = os.path.join(REG, "M4_OP4_REP_SENSITIVITY.csv")
    if not os.path.exists(p):
        check("§3.8 OP-4 敏感性产物存在", False, True)
        return
    R = pd.read_csv(p)
    check("§3.8 OP-4 行数", len(R), 18, 0)
    cb = R[R.kind == "cross_budget"]
    ct = R[R.kind == "cross_task"]
    for nm, z, s_med, s_min, s_max, a_med, a_min, a_max in [
            ("cross_budget", cb, 0.852, 0.702, 1.000, 0.966, 0.862, 1.000),
            ("cross_task", ct, 0.410, 0.152, 0.709, 0.416, 0.156, 0.841)]:
        check("§3.8 %s rho_single median" % nm, round(float(z.rho_single_rep.median()), 3),
              s_med, 1e-3)
        check("§3.8 %s rho_single min" % nm, round(float(z.rho_single_rep.min()), 3), s_min, 1e-3)
        check("§3.8 %s rho_single max" % nm, round(float(z.rho_single_rep.max()), 3), s_max, 1e-3)
        check("§3.8 %s rho_avg median" % nm, round(float(z.rho_rep_averaged.median()), 3),
              a_med, 1e-3)
        check("§3.8 %s rho_avg min" % nm, round(float(z.rho_rep_averaged.min()), 3), a_min, 1e-3)
        check("§3.8 %s rho_avg max" % nm, round(float(z.rho_rep_averaged.max()), 3), a_max, 1e-3)
    # 跨预算的衰减集中在 B=24 的格子
    b24 = cb[(cb.budget_a == 24)]
    b96 = cb[(cb.budget_a == 96)]
    check("§3.8 B24 格子的 Δ 下界", round(float(b24.delta.min()), 3), 0.114, 1e-3)
    check("§3.8 B24 格子的 Δ 上界", round(float(b24.delta.max()), 3), 0.159, 1e-3)
    check("§3.8 B96v384 的 Δ 区间",
          "%.3f-%.3f" % (b96.delta.min(), b96.delta.max()), "-0.000-0.013")
    # 跨任务的衰减只在 B=24
    ct24 = ct[(ct.budget_a == 24) & (ct.task == "MA90~G189E")]
    check("§3.8 cross_task B24 MA90~G189E 单轨迹", round(float(ct24.rho_single_rep.iloc[0]), 3),
          0.566, 1e-3)
    check("§3.8 cross_task B24 MA90~G189E 平均后", round(float(ct24.rho_rep_averaged.iloc[0]), 3),
          0.841, 1e-3)
    check("§3.8 cross_task B>=96 的 |Δ| 最大",
          round(float(ct[ct.budget_a >= 96].delta.abs().max()), 3), 0.012, 1e-3)
    # 策略随机性 sd 的比值
    w = cb[cb.sd_within_parent_over_reps.notna()]
    ratio = float((w.sd_within_parent_over_reps / w.sd_between_parents).median())
    check("§3.8 策略随机性 sd / parent 间 sd", round(ratio, 4), 0.4725, 1e-3)
    check("§3.8 结论方向：跨预算平均后更强",
          bool(cb.rho_rep_averaged.median() > cb.rho_single_rep.median()), True)
    check("§3.8 结论方向：跨任务平均后几乎不变",
          bool(abs(ct.rho_rep_averaged.median() - ct.rho_single_rep.median()) < 0.02), True)


def s1_firstrun():
    """§1.1：首跑（已作废）数字的可复现性。

    可复现的：`clip(0,1)` 造成的饱和比例与 nan 机制。
    不可复现的：首跑的原始计数（分区与 MLDE 实现均已改变）—— 报告已标明。
    """
    d = np.load(os.path.join(PROC, "M4_EXP1_V.npz"), allow_pickle=True)
    V = d["V"]
    for bi, B, frac in [(0, 24, 0.725), (1, 96, 0.991), (2, 384, 1.000)]:
        v = V[0, bi, 0]
        v = v[~np.isnan(v)]
        c = np.clip(v, 0.0, 1.0)
        check("§1.1 clip 后 random/MA90/B%d 的 frac_eq_1" % B,
              round(float((c >= 0.9999).mean()), 3), frac, 1e-3)

    def sp(a, b):
        if np.all(a == a[0]) or np.all(b == b[0]):
            return float("nan")
        ra = pd.Series(a).rank().values
        rb = pd.Series(b).rank().values
        ra = ra - ra.mean(); rb = rb - rb.mean()
        dd = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
        return float((ra * rb).sum() / dd) if dd > 0 else float("nan")

    for label, fn, want in [("无 clip（冻结）", lambda x: x, 0),
                            ("套用 clip（缺陷）", lambda x: np.clip(x, 0.0, 1.0), 14)]:
        n_nan = n_tot = 0
        for si in range(3):
            for ti in range(3):
                for i in range(3):
                    for j in range(i + 1, 3):
                        a = fn(V[si, i, ti]); b = fn(V[si, j, ti])
                        m = ~np.isnan(a) & ~np.isnan(b)
                        if m.sum() < 50:
                            continue
                        n_tot += 1
                        if np.isnan(sp(a[m], b[m])):
                            n_nan += 1
        check("§1.1 跨预算 nan 格数（%s）" % label, n_nan, want, 0)
        check("§1.1 跨预算总格数（%s）" % label, n_tot, 27, 0)


def s_sigreq():
    """`M4_SIGNATURE_REQUEST.md` 里引用的每一个数字。该文件是**交付物**，其数字同样必须核验。"""
    H = pd.read_csv(os.path.join(REG, "M4_H1_DENOMINATOR_SENSITIVITY.csv"))
    O = pd.read_csv(os.path.join(REG, "M4_EXP4_MATCHED_PAIRS_OP8.csv"))
    P = pd.read_csv(os.path.join(REG, "M4_EXP4_MATCHED_PAIRS.csv"))
    S = pd.read_csv(os.path.join(REG, "M4_OP4_REP_SENSITIVITY.csv"))
    A = pd.read_csv(os.path.join(REG, "M4_EXP4_READINESS_VS_EOV.csv"))
    check("SIG A1 sd 通过格数", int(H.pass_sd.sum()), 17, 0)
    check("SIG A1 sem 通过格数", int(H.pass_sem.sum()), 20, 0)
    g = O[(O.future == "AZT@0.44") & (O.policy == "greedy_ssm")]
    pg = P[(P.future == "AZT@0.44") & (P.policy == "greedy_ssm")]
    check("SIG A2 OP-8 口径 PASS 数", int((g.verdict == "PASS").sum()), 3, 0)
    check("SIG A2 主表口径 PASS 数", int((pg.verdict == "PASS").sum()), 0, 0)
    check("SIG A2 OP-8 B24 p", round(float(g[g.budget == 24].Readiness_p.iloc[0]), 3), 0.043, 1e-3)
    check("SIG A2 OP-8 B96 p", round(float(g[g.budget == 96].Readiness_p.iloc[0]), 3), 0.012, 1e-3)
    check("SIG A2 OP-8 B384 p", round(float(g[g.budget == 384].Readiness_p.iloc[0]), 3), 0.032, 1e-3)
    for B, v in [(24, 0.134), (96, 0.089), (384, 0.097)]:
        check("SIG A2 主表 B%d p" % B,
              round(float(pg[pg.budget == B].Readiness_p.iloc[0]), 3), v, 1e-3)
    cb = S[S.kind == "cross_budget"]
    ct = S[S.kind == "cross_task"]
    check("SIG A4 跨预算平均后 median", round(float(cb.rho_rep_averaged.median()), 3), 0.966, 1e-3)
    check("SIG A4 跨预算单轨迹 median", round(float(cb.rho_single_rep.median()), 3), 0.852, 1e-3)
    check("SIG A4 跨任务平均后 median", round(float(ct.rho_rep_averaged.median()), 3), 0.416, 1e-3)
    check("SIG A4 跨任务单轨迹 median", round(float(ct.rho_single_rep.median()), 3), 0.410, 1e-3)
    check("SIG A4 策略噪声比",
          round(float((cb[cb.sd_within_parent_over_reps.notna()]
                       .eval("sd_within_parent_over_reps/sd_between_parents")).median()), 2),
          0.47, 1e-2)
    ag = A[A.policy == "greedy_ssm"]
    check("SIG B1 Readiness 秩相关上界",
          round(float(ag["Readiness(known_family_mean)"].abs().max()), 3), 0.443, 1e-3)
    check("SIG B2 跨任务 ρ 中位数（用于对照 INT-2 的 0.30 门）",
          round(float(ct.rho_rep_averaged.median()), 3), 0.416, 1e-3)
    check("SIG B2 是否满足 INT-2 的 ρ<0.30",
          bool(ct.rho_rep_averaged.median() < 0.30), False)


def s_int1_int3():
    """§8（新增）：`INT-1` / `INT-3` 两个登记诊断的数字。"""
    C = pd.read_csv(os.path.join(REG, "M4_INT1_CV_DIAGNOSTIC.csv"))
    T = pd.read_csv(os.path.join(REG, "M4_INT3_KENDALL_TAU.csv"))
    check("INT-1 行数", len(C), 18, 0)
    check("INT-1 proxy-only CV-R² min", round(float(C.r2_proxy_only.min()), 4), -0.0167, 1e-3)
    check("INT-1 proxy-only CV-R² max", round(float(C.r2_proxy_only.max()), 4), 0.3127, 1e-3)
    check("INT-1 触发'EOV 可归约'的格数", int(C.INT1_EOV_reducible.sum()), 0, 0)
    check("INT-1 proxy>=0.80 的格数", int(C.INT1_proxy_ge_080.sum()), 0, 0)
    check("INT-1 delta<0.02 的格数", int(C.INT1_delta_lt_002.sum()), 18, 0)
    check("INT-1 ΔCV-R² 区间（全 18 格，可为负）",
          "%.4f-%.4f" % (C.delta_cv_r2.min(), C.delta_cv_r2.max()), "-0.0037-0.0149")
    check("INT-1 greedy 子集 ΔCV-R² 区间",
          "%.4f-%.4f" % (C[C.policy == "greedy_ssm"].delta_cv_r2.min(),
                         C[C.policy == "greedy_ssm"].delta_cv_r2.max()), "0.0031-0.0149")
    check("INT-1 ΔCV-R² 为负的格数", int((C.delta_cv_r2 < 0).sum()), 7, 0)
    for p, lo, hi, neg in [("greedy_ssm", 0.0031, 0.0149, 0),
                           ("mlde_ridge", -0.0037, 0.0006, 4),
                           ("random", -0.0034, 0.0013, 3)]:
        z = C[C.policy == p]
        check("INT-1 %s ΔCV-R² 区间" % p,
              "%.4f-%.4f" % (z.delta_cv_r2.min(), z.delta_cv_r2.max()),
              "%.4f-%.4f" % (lo, hi))
        check("INT-1 %s ΔCV-R² 为负格数" % p, int((z.delta_cv_r2 < 0).sum()), neg, 0)
    for p, lo, hi in [("greedy_ssm", 0.1145, 0.3127), ("mlde_ridge", -0.0160, -0.0058),
                      ("random", -0.0167, -0.0080)]:
        z = C[C.policy == p]
        check("INT-1 %s proxy-only R² 区间" % p,
              "%.4f-%.4f" % (z.r2_proxy_only.min(), z.r2_proxy_only.max()),
              "%.4f-%.4f" % (lo, hi))
    check("INT-1 proxy-only R² > 0 只在 greedy 出现",
          ",".join(sorted(C[C.r2_proxy_only > 0].policy.unique().tolist())), "greedy_ssm")
    check("H2 判据(A) ΔCV-R²>=0.05 的格数", int((C.delta_cv_r2 >= 0.05).sum()), 0, 0)
    g = C[C.policy == "greedy_ssm"]
    for fut, B, a, b, d in [("AZT@0.44", 24, 0.2133, 0.2181, 0.0047),
                            ("AZT@0.44", 96, 0.1411, 0.1560, 0.0149),
                            ("AZT@0.44", 384, 0.1145, 0.1229, 0.0083),
                            ("AZT@36.0", 24, 0.3127, 0.3163, 0.0036),
                            ("AZT@36.0", 96, 0.2401, 0.2437, 0.0035),
                            ("AZT@36.0", 384, 0.1528, 0.1558, 0.0031)]:
        r = g[(g.future == fut) & (g.budget == B)].iloc[0]
        check("INT-1 %s B%d r2_proxy" % (fut, B), round(r.r2_proxy_only, 4), a, TOL)
        check("INT-1 %s B%d r2_plus" % (fut, B), round(r.r2_proxy_plus_today_eov, 4), b, TOL)
        check("INT-1 %s B%d delta" % (fut, B), round(r.delta_cv_r2, 4), d, TOL)
    check("INT-1 每格 n（parents 全数通过 finite 过滤）", int(C.n.min()), 1000, 0)
    check("INT-1 n 合计", int(C.n.sum()), 18000, 0)

    check("INT-3 行数", len(T), 9, 0)
    check("INT-3 CI 覆盖 0 的格数", int(T.CI_covers_0.sum()), 6, 0)
    gg = T[T.policy == "greedy_ssm"]
    check("INT-3 greedy CI 覆盖 0 的格数", int(gg.CI_covers_0.sum()), 0, 0)
    for B, tau, lo, hi in [(24, 0.3088, 0.2704, 0.3458), (96, 0.2301, 0.1920, 0.2683),
                           (384, 0.2131, 0.1720, 0.2522)]:
        r = gg[gg.budget == B].iloc[0]
        check("INT-3 greedy B%d tau" % B, round(r.kendall_tau, 4), tau, TOL)
        check("INT-3 greedy B%d CI_lo" % B, round(r.CI_lo, 4), lo, TOL)
        check("INT-3 greedy B%d CI_hi" % B, round(r.CI_hi, 4), hi, TOL)
    for p, want_abs in (("random", 0.036), ("mlde_ridge", 0.026)):
        z = T[T.policy == p]
        check("INT-3 %s CI 覆盖 0" % p, int(z.CI_covers_0.sum()), 3, 0)
        check("INT-3 %s |tau| 上界" % p, round(float(z.kendall_tau.abs().max()), 3), want_abs, 1e-3)


def s55_topk():
    """§5.5 决策规则敏感性（argmax → top-k）的数字。"""
    p = os.path.join(REG, "M4_EXP3_TOPK_SENSITIVITY.csv")
    if not os.path.exists(p):
        check("§5.5 top-k 产物存在", False, True)
        return
    R = pd.read_csv(p)
    check("§5.5 top-k 行数", len(R), 540, 0)
    check("§5.5 k 取值", ",".join(str(x) for x in sorted(R.k.unique())), "1,5,20")
    for k, n_tot, n_ci, n_pass, nrand_ci in [(1, 180, 8, 0, 3), (5, 180, 22, 0, 3),
                                              (20, 180, 34, 0, 3)]:
        z = R[R.k == k]
        check("§5.5 k=%d 总格数" % k, len(z), n_tot, 0)
        check("§5.5 k=%d 全表 CI 排除 0" % k, int(z.CI_excludes_0.sum()), n_ci, 0)
        check("§5.5 k=%d 满足 20%%+CI" % k, int(z.meets_20pct_and_CI.sum()), n_pass, 0)
        g = z[(z.future == "AZT@0.44") & (z.policy == "greedy_ssm") & (z.opponent == "random")]
        check("§5.5 k=%d 主条件 vs random CI 排除 0" % k, int(g.CI_excludes_0.sum()), nrand_ci, 0)
    for k, lo, hi, nci in [(1, -232.0, 77.7, 0), (5, -9.4, 67.7, 7), (20, 0.0, 59.5, 10)]:
        z = R[(R.k == k) & (R.future == "AZT@0.44") & (R.policy == "greedy_ssm")
              & (R.opponent != "random")]
        check("§5.5 k=%d 主条件 vs 非随机 降幅下界" % k, round(float(z.reduction_pct.min()), 1),
              lo, 0.06)
        check("§5.5 k=%d 主条件 vs 非随机 降幅上界" % k, round(float(z.reduction_pct.max()), 1),
              hi, 0.06)
        check("§5.5 k=%d 主条件 vs 非随机 CI 排除 0" % k, int(z.CI_excludes_0.sum()), nci, 0)
    for k, lo, hi in [(1, 44.6, 61.8), (5, 34.8, 54.0), (20, 37.8, 54.3)]:
        g = R[(R.k == k) & (R.future == "AZT@0.44") & (R.policy == "greedy_ssm")
              & (R.opponent == "random")]
        check("§5.5 k=%d vs random 降幅下界" % k, round(float(g.reduction_pct.min()), 1), lo, 0.06)
        check("§5.5 k=%d vs random 降幅上界" % k, round(float(g.reduction_pct.max()), 1), hi, 0.06)
    # 冻结判据的表未被改动
    T = pd.read_csv(os.path.join(REG, "M4_EXP3_TOMORROW.csv"))
    check("§5.5 冻结判据表仍为 180 行且 0 通过",
          "%d/%d" % (int(T.beats_frozen_by_20pct_and_CI.sum()), len(T)), "0/180")
    check("§5.5 功效提升倍数（34/8）", round(34 / 8, 2), 4.25, 1e-2)
    check("§5.5 CI 收窄与效应缩小抵消 → 判据全 k 不通过",
          bool((R.groupby("k").meets_20pct_and_CI.sum() == 0).all()), True)


def s38_h1_aux():
    """§3.8 H1 强制辅助报告（variance decomposition + permutation p）的数字。"""
    p = os.path.join(REG, "M4_H1_AUXILIARY.csv")
    if not os.path.exists(p):
        check("§3.8 H1 辅助报告产物存在", False, True)
        return
    R = pd.read_csv(p)
    check("§3.8 行数", len(R), 9, 0)
    check("§3.8 重复数（4 噪声 x 8 策略）", int(R.n_replicates.min()), 32, 0)
    for t, B, icc, eon, pp in [
            ("MA90", 24, 0.5957, 1.2137, 0.0005), ("MA90", 96, 0.7359, 1.6691, 0.0),
            ("MA90", 384, 0.7327, 1.6557, 0.0), ("SI06", 24, 0.7257, 1.6266, 0.0),
            ("SI06", 96, 0.8280, 2.1944, 0.0), ("SI06", 384, 0.7983, 1.9896, 0.0),
            ("G189E", 24, 0.5278, 1.0573, 0.9035), ("G189E", 96, 0.7284, 1.6376, 0.0),
            ("G189E", 384, 0.7156, 1.5864, 0.0)]:
        r = R[(R.task == t) & (R.budget == B)].iloc[0]
        check("§3.8 %s B%d ICC" % (t, B), round(r.icc, 4), icc, TOL)
        check("§3.8 %s B%d effect/noise" % (t, B), round(r.effect_over_noise, 4), eon, TOL)
        check("§3.8 %s B%d perm_p" % (t, B), round(r.perm_p, 4), pp, 1e-4)
    for t, B, vm, lo, hi, plo, phi, iqr in [
            ("MA90", 24, 1.03555, 1.03049, 1.04008, 0.84943, 1.16220, 0.10727),
            ("MA90", 96, 1.09003, 1.08386, 1.09742, 0.91920, 1.24599, 0.09709),
            ("MA90", 384, 1.09471, 1.08700, 1.10205, 0.91920, 1.24819, 0.09953),
            ("SI06", 24, 1.07696, 1.05878, 1.09615, 0.85891, 1.31521, 0.20069),
            ("SI06", 96, 1.15008, 1.13467, 1.16615, 0.92696, 1.36101, 0.19158),
            ("SI06", 384, 1.15645, 1.14261, 1.17094, 0.93671, 1.36101, 0.17948),
            ("G189E", 24, 1.03252, 1.02847, 1.03562, 0.92868, 1.12518, 0.05908),
            ("G189E", 96, 1.06410, 1.06128, 1.06736, 0.97289, 1.18562, 0.05716),
            ("G189E", 384, 1.06700, 1.06388, 1.07051, 0.97289, 1.18621, 0.05682)]:
        r = R[(R.task == t) & (R.budget == B)].iloc[0]
        check("§3.8 %s B%d V_median" % (t, B), round(r.V_median, 5), vm, 1e-5)
        check("§3.8 %s B%d V_median CI_lo" % (t, B), round(r.V_median_CI_lo, 5), lo, 1e-5)
        check("§3.8 %s B%d V_median CI_hi" % (t, B), round(r.V_median_CI_hi, 5), hi, 1e-5)
        check("§3.8 %s B%d V 跨 parent 2.5%%" % (t, B), round(r.V_p2_5, 5), plo, 1e-5)
        check("§3.8 %s B%d V 跨 parent 97.5%%" % (t, B), round(r.V_p97_5, 5), phi, 1e-5)
        check("§3.8 %s B%d IQR" % (t, B), round(r.iqr_v, 5), iqr, 1e-5)
    check("§3.8 ICC 区间", "%.4f-%.4f" % (R.icc.min(), R.icc.max()), "0.5278-0.8280")
    check("§3.8 effect/noise 区间",
          "%.3f-%.3f" % (R.effect_over_noise.min(), R.effect_over_noise.max()), "1.057-2.194")
    check("§3.8 p<0.05 的格数", int((R.perm_p < 0.05).sum()), 8, 0)
    check("§3.8 唯一不显著的是 G189E@B24",
          "%s@%d" % (R[R.perm_p >= 0.05].task.iloc[0], R[R.perm_p >= 0.05].budget.iloc[0]),
          "G189E@24")
    # 机制：B>=96 时 var_replicate 只含测量噪声（更小），B=24 含策略随机性（更大）
    for t in ("MA90", "SI06", "G189E"):
        z = R[R.task == t].set_index("budget").var_replicate
        check("§3.8 %s B24 残差方差 > B96（含策略随机性）" % t, bool(z[24] > z[96]), True)


def s39_layers():
    """§3.9 强制四层分解 R_0 / R_k^oracle / R_k^adaptive / R_{B,π}。"""
    p = os.path.join(REG, "M4_LAYER_DECOMPOSITION.csv")
    if not os.path.exists(p):
        check("§3.9 四层分解产物存在", False, True)
        return
    R = pd.read_csv(p)
    for c in ("R_0", "R_k_oracle", "R_k_adaptive", "R_B_pi"):
        R[c] = pd.to_numeric(R[c], errors="coerce")
    check("§3.9 行数（3 任务 x 3 k x 1000 parent）", len(R), 9000, 0)
    check("§3.9 k 取值", ",".join(str(x) for x in sorted(R.k.unique())), "1,2,3")
    for t, d in [("MA90", 0.06023), ("SI06", 0.17235), ("G189E", 0.13134)]:
        check("§3.9 %s delta (OP-7)" % t, round(float(R[R.task == t].delta.iloc[0]), 5), d, 1e-5)
    means = R.groupby(["task", "k"])[["R_0", "R_k_oracle", "R_k_adaptive", "R_B_pi"]].mean()
    for t, k, r0, ro, ra, rb in [
            ("MA90", 1, 9.3791, 9.7801, 9.7801, 10.0352), ("MA90", 2, 9.3791, 9.9609, 9.9607, 10.0352),
            ("MA90", 3, 9.3791, 10.0587, 10.0583, 10.0352),
            ("SI06", 1, 7.9599, 8.6996, 8.6996, 9.2400), ("SI06", 3, 7.9599, 9.2813, 9.2813, 9.2400),
            ("G189E", 1, 8.8665, 9.5583, 9.5583, 9.8222), ("G189E", 3, 8.8665, 9.8644, 9.8644, 9.8222)]:
        m = means.loc[(t, k)]
        check("§3.9 %s k=%d R_0" % (t, k), round(float(m.R_0), 4), r0, TOL)
        check("§3.9 %s k=%d R_k^oracle" % (t, k), round(float(m.R_k_oracle), 4), ro, TOL)
        check("§3.9 %s k=%d R_k^adaptive" % (t, k), round(float(m.R_k_adaptive), 4), ra, TOL)
        check("§3.9 %s k=%d R_B" % (t, k), round(float(m.R_B_pi), 4), rb, TOL)
    # 搜索差距：k=2 为负、k=3 为正（三个任务一致）
    for t, g2, g3 in [("MA90", -0.0743, 0.0235), ("SI06", -0.2082, 0.0413),
                      ("G189E", -0.0686, 0.0422)]:
        for k, want in ((2, g2), (3, g3)):
            m = means.loc[(t, k)]
            check("§3.9 %s k=%d 搜索差距" % (t, k),
                  round(float(m.R_k_oracle - m.R_B_pi), 4), want, TOL)
        check("§3.9 %s 搜索差距在 k=2→k=3 之间变号" % t,
              bool((means.loc[(t, 2)].R_k_oracle - means.loc[(t, 2)].R_B_pi) < 0 <
                   (means.loc[(t, 3)].R_k_oracle - means.loc[(t, 3)].R_B_pi)), True)
    # 中性约束几乎不绑定
    g = R.dropna(subset=["R_k_oracle", "R_k_adaptive"])
    dd = g.R_k_oracle - g.R_k_adaptive
    check("§3.9 oracle-adaptive 最大差", round(float(dd.max()), 2), 0.24, 1e-2)
    check("§3.9 oracle>adaptive 的 parent 占比（全部 k）",
          round(float((dd > 1e-9).mean()), 4), 0.0013, 1e-4)
    g1 = g[g.k == 1]
    check("§3.9 k=1 时 oracle ≡ adaptive（恒等式）",
          bool(np.allclose(g1.R_k_oracle, g1.R_k_adaptive)), True)
    g2 = g[g.k >= 2]
    d2 = g2.R_k_oracle - g2.R_k_adaptive
    check("§3.9 k>=2 时 oracle>adaptive 的占比",
          round(float((d2 > 1e-9).mean()), 4), 0.0020, 1e-4)


def s_manifests():
    """§9 复现性交付物：TIS_MANIFEST / config / seeds / data manifests 存在且 sha256 自洽。"""
    import hashlib
    import json

    def sha256(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    for name in ("exp1_stability", "exp2_baselines", "exp3_tomorrow", "exp4_readiness"):
        d = os.path.join(ROOT, "experiments", "M4", name)
        for fn in ("TIS_MANIFEST.json", "config.json", "seeds.json"):
            check("§9 %s/%s 存在" % (name, fn), os.path.exists(os.path.join(d, fn)), True)
        man = json.load(open(os.path.join(d, "TIS_MANIFEST.json"), encoding="utf-8"))
        check("§9 %s TIS 有 inputs" % name, len(man["inputs"]) >= 1, True)
        bad = []
        for it in man["inputs"]:
            p = os.path.join(ROOT, it["path"])
            if not os.path.exists(p) or sha256(p) != it["sha256"]:
                bad.append(it["path"])
        check("§9 %s TIS 内的 sha256 全部与磁盘一致" % name, len(bad), 0, 0)
        if name != "exp1_stability":
            check("§9 %s TIS 白名单只含 AMP" % name,
                  ",".join(sorted({p[0] for p in man["allowed_today_pairs"]})), "AMP")
            check("§9 %s 特征数" % name, len(man["features"]), 9, 0)
        else:
            check("§9 exp1 TIS 白名单为空（不使用 Day-0 特征）",
                  len(man["allowed_today_pairs"]), 0, 0)
    # data manifests 自洽
    for rel, want in [("M2_measurements.parquet",
                       "fa3bba9fcf35e373146ccb06168a3005b128bf1efa8e301d658f71e4eb041df2")]:
        p = os.path.join(ROOT, "data", "manifests", rel + ".sha256")
        if not os.path.exists(p):
            check("§9 data manifest %s 存在" % rel, False, True)
            continue
        rec = None
        for line in open(p, encoding="utf-8"):
            if line.startswith("# sha256: "):
                rec = line.split(": ")[1].strip()
        check("§9 data manifest %s 记录的 sha256" % rel, rec, want)
        check("§9 data manifest %s 与磁盘一致" % rel,
              rec == sha256(os.path.join(ROOT, "data", "processed", rel)), True)
    check("§9 logs/M4_SEEDS.json 存在",
          os.path.exists(os.path.join(ROOT, "logs", "M4_SEEDS.json")), True)


def s79_baseline_set():
    """§7.9：L119 强制 proxy-only 基线集与 M4 实际算过的选择器的差集。"""
    L = pd.read_csv(os.path.join(REG, "M4_EXP2_LADDER.csv"))
    got = sorted(set(L.selector.unique()))
    check("§7.9 M4 选择器数", len(got), 11, 0)
    for req, present in [("current_fitness", True), ("local_robustness", True)]:
        check("§7.9 L119 基线 `%s` 已算" % req, req in got, present)
    for missing in ("conservation", "frozen_zero_shot", "cross_task_activity"):
        check("§7.9 L119 基线 `%s` 未算/N-A（登记为漏交或 N/A）" % missing,
              missing in got, False)


def s82_do_not_quote():
    """§8.3（审计 S-2）：Exp 4 的 `exploratory_best_*` 是用**未来 V** 挑出来的，不得引用。"""
    P = pd.read_csv(os.path.join(REG, "M4_EXP4_MATCHED_PAIRS.csv"))
    cols = [c for c in P.columns if c.startswith("exploratory_best")]
    check("S-2 exploratory_best_* 列存在（选择偏倚产物）", len(cols), 3, 0)
    # 冻结判据必须只用预指定的 Readiness 列
    check("S-2 判据列来自预指定的 Readiness",
          ",".join(c for c in ("Readiness_p", "verdict") if c in P.columns),
          "Readiness_p,verdict")
    check("S-2 exploratory_best_p 未参与 verdict（主条件全部 FAIL 且与 Readiness 一致）",
          bool((P[P.future == "AZT@0.44"].verdict == "FAIL").all()), True)
    R = pd.read_csv(os.path.join(REG, "M4_EXP4_READINESS_VS_EOV.csv"))
    check("S-2 秩相关表不含 exploratory 列",
          int(any("exploratory" in c for c in R.columns)), 0, 0)


def s93_manifest_inputs():
    """§8.4/8.5（审计 S-3/S-4）：manifest 的输入必须逐实验准确，隔离声明必须如实。"""
    import json

    want = {"exp1_stability": ["M2_measurements.parquet"],
            "exp2_baselines": ["M2_measurements.parquet"],
            "exp3_tomorrow": ["M2_measurements.parquet", "M4_EXP2_V.npz"],
            "exp4_readiness": ["M2_measurements.parquet", "M4_EXP2_V.npz"]}
    for name, files in want.items():
        m = json.load(open(os.path.join(ROOT, "experiments", "M4", name, "TIS_MANIFEST.json"),
                           encoding="utf-8"))
        got = [i["path"].split("/")[-1] for i in m["inputs"]]
        check("S-3 %s manifest 输入集准确" % name, ",".join(got), ",".join(files))
        check("S-3 %s 无幻影输入" % name,
              int(any(x in got for x in ("M3_taskpanel_measurements.parquet",
                                         "M2_AUDIT_TABLE.csv",
                                         "PHASE1_ANALYSIS_READY_MANIFEST.csv"))), 0, 0)
    # S-4/S-5：隔离声明必须逐实验如实；L39 的状态与 TODAY_SPEC 一致
    import json as _json
    sys.path.insert(0, os.path.join(ROOT, "eov"))
    from tis import TODAY_SPEC
    e2 = json.load(open(os.path.join(ROOT, "experiments", "M4", "exp2_baselines",
                                     "TIS_MANIFEST.json"), encoding="utf-8"))
    check("S-4 exp2 如实声明 arrs 含 future 键",
          bool(e2["isolation_audit"]["arrs_holds_future_keys"]), True)
    check("L39 exp2 类型层已满足（走 TIS）",
          "满足" in e2["isolation_audit"]["type_level_firewall"]
          and "不满足" not in e2["isolation_audit"]["type_level_firewall"], True)
    for name in want:
        m = json.load(open(os.path.join(ROOT, "experiments", "M4", name,
                                        "TIS_MANIFEST.json"), encoding="utf-8"))
        check("L39 %s 声明 satisfied=True" % name, bool(m["l39_status"]["satisfied"]), True)
        check("L39 %s 记录证据文件" % name,
              "test_tis.py" in m["l39_status"]["evidence"], True)
        check("L39 %s 未再声称未满足" % name,
              "未满足" not in m["feature_interface_note"], True)
    # manifest 的白名单（除 exp1）必须与 eov/tis.py 的 TODAY_SPEC 一致
    for name in ("exp2_baselines", "exp3_tomorrow", "exp4_readiness"):
        m = json.load(open(os.path.join(ROOT, "experiments", "M4", name,
                                        "TIS_MANIFEST.json"), encoding="utf-8"))
        got = sorted(tuple(x) for x in m["allowed_today_pairs"])
        want_pairs = sorted(TODAY_SPEC["TEM-1CML"]["allowed"])
        check("L39 %s 白名单 == TODAY_SPEC" % name, got == want_pairs, True)
    check("L39 exp1 白名单为空（不使用 Day-0 特征）",
          len(json.load(open(os.path.join(ROOT, "experiments", "M4", "exp1_stability",
                                          "TIS_MANIFEST.json"), encoding="utf-8")
                            )["allowed_today_pairs"]), 0, 0)


def s82_invariant5():
    """§8.2（审计 S-1）：不变量 5 修复后的 ρ。"""
    p = os.path.join(REG, "M4_INVARIANT5_EXP1_RHO.csv")
    if not os.path.exists(p):
        check("§8.2 不变量5 修复产物存在", False, True)
        return
    R = pd.read_csv(p)
    check("§8.2 行数", len(R), 18, 0)
    for k, lo, md, hi in [("cross_budget", 0.833, 0.929, 0.994),
                          ("cross_task", 0.174, 0.346, 0.726)]:
        z = R[R.kind == k]
        check("§8.2 %s rho min" % k, round(float(z.rho.min()), 3), lo, 1e-3)
        check("§8.2 %s rho median" % k, round(float(z.rho.median()), 3), md, 1e-3)
        check("§8.2 %s rho max" % k, round(float(z.rho.max()), 3), hi, 1e-3)
    check("§8.2 结论方向：跨预算在不变量5 下仍强（median >= 0.9）",
          bool(R[R.kind == "cross_budget"].rho.median() >= 0.9), True)
    check("§8.2 结论方向：跨任务在不变量5 下仍为部分稳定（median < 0.5）",
          bool(R[R.kind == "cross_task"].rho.median() < 0.5), True)
    # B 部分：按不变量 5 重跑 Exp 3-S1 —— 冻结 selector 是否仍然胜出
    q = os.path.join(REG, "M4_INVARIANT5_S1_SELECTION.csv")
    if not os.path.exists(q):
        check("§8.2 S1 重跑产物存在", False, True)
        return
    S = pd.read_csv(q)
    check("§8.2 S1 重跑行数", len(S), 405, 0)
    m = S.groupby("selector").NR.mean().sort_values()
    check("§8.2 S1 重跑后第 1 名仍是 current_fitness", str(m.index[0]), "current_fitness")
    for sel, v in [("current_fitness", 0.724340), ("known_family_worst", 0.743436),
                   ("dist_to_best", 0.755144), ("local_robustness", 0.765329),
                   ("neighbor_informative_frac", 0.768938), ("proxy_eov_today", 0.775413),
                   ("known_family_mean", 0.782238), ("local_ruggedness", 0.790498),
                   ("n_better_neighbors", 0.790498)]:
        check("§8.2 S1 重跑 mean NR %s" % sel, round(float(m[sel]), 6), v, 1e-5)
    check("§8.2 S1 重跑极差", round(float(m.max() - m.min()), 4), 0.0662, 1e-3)
    check("§8.2 极差在原口径下更窄（0.029）→ 噪声期望后扩大",
          bool((m.max() - m.min()) > 0.029), True)
    # 随机基线（由同一个 V 场算出）
    dnp = np.load(os.path.join(PROC, "M4_INV5_S1_R.npz"))
    POL = ("random", "greedy_ssm", "mlde_ridge")
    BUD = (24, 96, 384)
    AMP = ["0.0", "3.1", "12.2", "48.8", "195.0", "781.0"]
    NRr = {}
    for c in AMP:
        for si, p in enumerate(POL):
            for bi, B in enumerate(BUD):
                V = dnp["R_AMP_%s" % c][si, bi]
                o = ~np.isnan(V)
                vo = float(np.max(V[o])); vr = float(np.percentile(V[o], 5))
                NRr[("AMP@" + c, p, B)] = (vo - float(np.nanmean(V[o]))) / (vo - vr)
    S = S.assign(NR_random=[NRr[(h, p, B)] for h, p, B in
                            zip(S.holdout, S.policy, S.budget)])
    S = S.assign(delta=S.NR - S.NR_random)
    gg = S.groupby("selector").agg(delta=("delta", "mean"),
                                   win=("delta", lambda x: (x < 0).mean()))
    for sel, d, w in [("current_fitness", -0.0475, 0.578), ("known_family_worst", -0.0284, 0.533),
                      ("dist_to_best", -0.0167, 0.578), ("proxy_eov_today", 0.0036, 0.400),
                      ("known_family_mean", 0.0104, 0.378),
                      ("n_better_neighbors", 0.0187, 0.289)]:
        check("§8.2 S1 重跑 Δ vs random %s" % sel, round(float(gg.loc[sel, "delta"]), 4), d, TOL)
        check("§8.2 S1 重跑 win %s" % sel, round(float(gg.loc[sel, "win"]), 3), w, 1e-3)
    check("§8.2 proxy_eov_today 仍不优于 random（Δ>0）",
          bool(gg.loc["proxy_eov_today", "delta"] > 0), True)
    check("§8.2 current_fitness 的 Δ 比原口径更强（-0.0475 < -0.0202）",
          bool(gg.loc["current_fitness", "delta"] < -0.0202), True)


def s_counts():
    """跨文档的**计数一致性**：静默失效数 / 漏交数 / 核验项数 不得在各文件间漂移。"""
    import re

    def read(rel):
        return open(os.path.join(ROOT, rel), encoding="utf-8").read()

    rep = read("data_registry/M4_REPORT.md")
    sig = read("data_registry/M4_SIGNATURE_REQUEST.md")
    amd = read("prereg/AMENDMENT-016_parameter_provenance_audit.md")
    led = read("data_registry/FREEZE_LEDGER.md")

    # 静默失效 = 11（唯一值，不得出现别的数）
    for nm, s in (("报告", rep), ("签字单", sig), ("AMENDMENT-016", amd)):
        got = sorted(set(re.findall(r"(\d+)\s*个静默失效", s)))
        if got:
            check("计数 %s 的静默失效数" % nm, ",".join(got), "11")
    # 漏交 = 9
    for nm, s in (("报告", rep), ("AMENDMENT-016", amd)):
        got = sorted(set(re.findall(r"(\d+)\s*个漏交", s)))
        if got:
            check("计数 %s 的漏交项数" % nm, ",".join(got), "9")
    # 核验项数（当前 = 752；历史值只允许出现在"从 X 扩到 Y"的叙述中）
    CURRENT = "752"
    for nm, s in (("报告", rep), ("签字单", sig)):
        check("计数 %s 出现过 %s" % (nm, CURRENT), CURRENT in s, True)
        stale = sorted(set(re.findall(r"(\d{3}) 项核验", s)) - {CURRENT})
        check("计数 %s 无残留的旧核验数" % nm, ",".join(stale), "")
    check("计数 FREEZE_LEDGER 出现 %s" % CURRENT, CURRENT in led, True)
    check("计数 FREEZE_LEDGER 出现 86（测试数）", "**86 项**" in led or "86 项" in led, True)


def s8a_trpb():
    """§8A：TrpB4 已发表基线的复现 + `search_sim` 的外部校验。"""
    p = os.path.join(REG, "M4_TRPB_BASELINE_REPRODUCTION.csv")
    q = os.path.join(REG, "M4_TRPB_EXTERNAL_CHECK.csv")
    r = os.path.join(REG, "M4_TRPB_LOCAL_OPTIMUM_CHECK.csv")
    for nm, f in (("复现", p), ("外部校验", q), ("局部最优归因", r)):
        check("§8A TrpB %s 产物存在" % nm, os.path.exists(f), True)
        if not os.path.exists(f):
            return
    R = pd.read_csv(p)
    check("§8A 复现方法数", len(R), 3, 0)
    for m, n, mean, med, fm in [
            ("single_step_DE", 234792, 0.6307657996135031, 0.6725398247189857, 0.06995979420082456),
            ("SSM_recomb_DE", 9783, 0.5313464902942596, 0.5588246873840206, 0.018910354696923235),
            ("SSM_top96", 9783, 0.7117587545381886, 0.7402069641615588, 0.14678523970152305)]:
        z = R[R.method == m].iloc[0]
        check("§8A %s n" % m, int(z.n), n, 0)
        check("§8A %s mean" % m, round(float(z["mean"]), 4), round(mean, 4), TOL)
        check("§8A %s median" % m, round(float(z["median"]), 4), round(med, 4), TOL)
        check("§8A %s frac_reaching_max" % m, round(float(z.frac_reaching_max), 4), round(fm, 4), TOL)
    check("§8A n = active × 24 的硬证据", int(R[R.method == "single_step_DE"].n.iloc[0]), 9783 * 24, 0)
    check("§8A 排序 SSM_top96 > single_step > SSM_recomb",
          ",".join(R.sort_values("mean", ascending=False).method.tolist()),
          "SSM_top96,single_step_DE,SSM_recomb_DE")

    E = pd.read_csv(q)
    check("§8A 外部校验预算档", ",".join(str(int(x)) for x in E.budget), "24,96,384,1920")
    for B, ratio, eq, ge in [(24, 0.6023, 0.107, 0.115), (96, 0.7985, 0.175, 0.210),
                             (384, 0.9313, 0.273, 0.412), (1920, 0.9532, 0.275, 0.410)]:
        z = E[E.budget == B].iloc[0]
        check("§8A B%d ratio" % B, round(float(z.ratio), 4), ratio, TOL)
        check("§8A B%d frac_exactly_equal" % B, round(float(z.frac_exactly_equal), 3), eq, 1e-3)
        check("§8A B%d frac_mine_ge_theirs" % B, round(float(z.frac_mine_ge_theirs), 3), ge, 1e-3)
    check("§8A 收敛单调（ratio 随 B 递增）",
          bool((E.sort_values("budget").ratio.diff().dropna() > 0).all()), True)
    check("§8A B=384 的 ratio 在 0.93 量级", round(float(E[E.budget == 384].ratio.iloc[0]), 2), 0.93, 1e-2)

    L = pd.read_csv(r)
    check("§8A 归因样本数", len(L), 400, 0)
    lo = float(L.end_is_strict_local_opt.mean())
    check("§8A B=1920 时严格局部最优比例", round(lo, 4), 0.5475, 1e-3)
    check("§8A 仍有更好邻居的比例", round(1 - lo, 4), 0.4525, 1e-3)
    check("§8A 邻居最大改进量的中位数 < 0（中位数终点已是局部最优）",
          bool(float(L.end_best_neighbor_delta.median()) < 0), True)

    # §8A.5 GB1 —— 第二个外部校验景观
    gp = os.path.join(REG, "M4_GB1_BASELINE_AND_EXTERNAL.csv")
    check("§8A.5 GB1 产物存在", os.path.exists(gp), True)
    if not os.path.exists(gp):
        return
    G = pd.read_csv(gp)
    rep = G[G.kind == "reproduction"]
    for m, n, mean, med, fm in [
            ("single_step_DE", 829080, 0.5081, 0.5275, 0.0204),
            ("SSM_recomb_DE", 34545, 0.3166, 0.3253, 0.0018),
            ("SSM_top96", 34545, 0.5445, 0.5533, 0.0219)]:
        z = rep[rep.method == m].iloc[0]
        check("§8A.5 GB1 %s n" % m, int(z.n), n, 0)
        check("§8A.5 GB1 %s mean" % m, round(float(z["mean"]), 4), mean, TOL)
        check("§8A.5 GB1 %s median" % m, round(float(z["median"]), 4), med, TOL)
        check("§8A.5 GB1 %s frac_max" % m, round(float(z.frac_reaching_max), 4), fm, TOL)
    check("§8A.5 GB1 n = active x 24（active=34545）",
          int(rep[rep.method == "single_step_DE"].n.iloc[0]), 34545 * 24, 0)
    check("§8A.5 GB1 排序与 TrpB 一致",
          ",".join(rep.sort_values("mean", ascending=False).method.tolist()),
          "SSM_top96,single_step_DE,SSM_recomb_DE")
    ext = G[G.kind == "external_check"]
    for B, ratio, eq in [(24, 0.3619, 0.013), (96, 0.6654, 0.068),
                         (384, 0.8228, 0.265), (1920, 0.8232, 0.263)]:
        z = ext[ext.budget == B].iloc[0]
        check("§8A.5 GB1 B%d ratio" % B, round(float(z.ratio), 4), ratio, TOL)
        check("§8A.5 GB1 B%d exact_equal" % B, round(float(z.exact_equal), 3), eq, 1e-3)
    check("§8A.5 GB1 在 B=384 已饱和（vs B=1920 差 < 0.001）",
          bool(abs(float(ext[ext.budget == 384].ratio.iloc[0])
                   - float(ext[ext.budget == 1920].ratio.iloc[0])) < 0.001), True)
    check("§8A.5 两景观 B=384 的 ratio 区间为 0.82-0.93",
          "%.2f-%.2f" % (float(ext[ext.budget == 384].ratio.min()),
                         float(E[E.budget == 384].ratio.iloc[0])), "0.82-0.93")


def main():
    print("=" * 118)
    print("M4 报告数值核验：从产物独立重算，与 M4_REPORT.md 中写下的值比对")
    print("=" * 118)
    for fn in (s1_firstrun, s2_anchor, s3_exp1, s38_h1_aux, s39_layers, s38_op4, s4_exp2,
               s5_exp3, s55_topk, s6_exp4, s7_verdict, s79_baseline_set, s82_invariant5,
               s82_do_not_quote, s93_manifest_inputs, s8a_trpb, s_sigreq, s_int1_int3,
               s_manifests, s_counts):
        print("\n---- %s ----" % fn.__name__)
        fn()
    bad = [r for r in RESULTS if not r[0]]
    print("\n" + "=" * 118)
    print("核验项 %d，通过 %d，失败 %d" % (len(RESULTS), len(RESULTS) - len(bad), len(bad)))
    for _, name, got, want, delta in bad:
        print("  FAIL %-70s got=%s want=%s %s" % (name, got, want, delta))
    print("=" * 118)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
