"""M4.10 — Exp 3 的**决策规则敏感性**：argmax → top-k（`OP-25` 主动披露）。

动机（**必须与改判据严格区分**）
------------------------------
Exp 3 的冻结判据在 **0/180** 个单元上不通过。但 `NR` 用 `argmax` 选起点：

    x_selected = argmax_x feature(x)

`argmax` 是**单个点**，其 bootstrap 分布极宽（§5.3 已述）。本脚本问一个**不同的问题**：

    如果决策规则是"取该选择器排名前 k 的 parent、看它们的**平均**可达值"，结论会变吗？

这在实践上也更接近真实决策（实验室通常一次带走一小组起点，而不是一个）。

⛔ **这不是判据替换**。冻结判据（相对最强 heuristic 的 NR 降低 >= 20% 且 CI 排除 0）
   的结果 **0/180 仍是主结论**，`M4_EXP3_TOMORROW.csv` 一字不改。
   本脚本只新增一列**已披露的敏感性**，供用户决定是否把决策规则正式改为 top-k（`M4_SIGNATURE_REQUEST` D2）。

⚠️ **新增构念披露（OP-25）**：`top-k 决策规则` 是**本脚本引入**的，本项目从未登记过它。
   它与 `scale2max`、`sd_ratio` 一样，**只作并列证据，不替换任何冻结判据**。
"""
from __future__ import annotations

import csv
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landscape import MixedAlphabetSpace  # noqa: E402
from search_sim import BUDGETS, POLICIES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
NPZ2 = os.path.join(ROOT, "data", "processed", "M4_EXP2_V.npz")
OUT_FREEZE3 = os.path.join(ROOT, "data_registry", "M4_EXP3_FROZEN_SELECTOR.md")
OUT = os.path.join(ROOT, "results", "tables", "M4_EXP3_TOPK_SENSITIVITY.csv")

DS = "TEM-1CML"
TODAY_PRIMARY = ("AMP", "781.0")
FUTURES = [("AZT", "0.44"), ("AZT", "36.0")]
KS = [1, 5, 20]
N_BOOT = 2000
BOOT_SEED = 20260919 + 11

# 与 Exp 3 完全一致的选择器集合（含 S1 胜出者与 S1 口径下的最强 heuristic）
CANDIDATES = ["current_fitness", "known_family_mean", "known_family_worst",
              "local_robustness", "neighbor_informative_frac", "dist_to_best",
              "n_better_neighbors", "local_ruggedness", "proxy_eov_today"]


def nr_topk(V, col, k, denom_pct=5.0):
    """用「按 col 排名前 k 的 parent 的 V 均值」作为被选中的值。col=None → random（全体均值）。"""
    ok = ~np.isnan(V)
    vo = float(np.max(V[ok])); vr = float(np.percentile(V[ok], denom_pct))
    dn = vo - vr
    if dn <= 0:
        return None
    if col is None:
        vs = float(np.nanmean(V[ok]))
    else:
        fin = np.isfinite(col) & ok
        if fin.sum() < k:
            return None
        idx = np.flatnonzero(fin)
        top = idx[np.argsort(-col[idx])[:k]]
        vs = float(np.mean(V[top]))
    return (vo - vs) / dn


def main() -> int:
    d2 = np.load(NPZ2)
    parents = d2["parents"]
    feats = {k[5:]: d2[k] for k in d2.files if k.startswith("feat_")}
    t = pd.read_parquet(MEAS)
    t = t[t.dataset_id == DS]
    ids = sorted(set(t.genotype_id.astype(str).unique()))
    space = MixedAlphabetSpace.from_masked_profiles([s for s in ids if "X" not in s])
    n = space.space_size()

    def load(tid, cid):
        s = t[(t.task_id == tid) & (t.condition_id == cid)]
        s = s[~s.genotype_id.astype(str).str.contains("X", regex=False)].drop_duplicates("genotype_id")
        v = np.full(n, np.nan)
        idx = np.array([space.index_of(tuple(x)) for x in s.genotype_id.astype(str)], dtype=np.int64)
        ok = s.informative.astype(bool).values
        v[idx[ok]] = pd.to_numeric(s.value_group, errors="coerce").values[ok]
        vv = v[~np.isnan(v)]
        q05, q95 = float(np.percentile(vv, 5)), float(np.percentile(vv, 95))
        return lambda z: (z - q05) / (q95 - q05)

    u_today = load(*TODAY_PRIMARY)
    frozen = None
    with open(OUT_FREEZE3, encoding="utf-8") as f:
        for line in f:
            if "冻结的 Phase-I selector" in line and "`" in line:
                frozen = line.split("`")[1]
    assert frozen, "无法从 %s 解析冻结的 selector" % OUT_FREEZE3
    print("从 S2 冻结记录读到 frozen selector =", frozen, flush=True)

    rows = []
    boot_rng = np.random.default_rng(BOOT_SEED)
    for key in FUTURES:
        u_f = load(*key)
        name = "%s@%s" % key
        for si, pol in enumerate(POLICIES):
            for bi, B in enumerate(BUDGETS):
                V = np.array([np.nan if np.isnan(z) else u_f(z)
                              for z in np.nanmean(d2["R_%s_%s" % key][si, bi], axis=1)])
                F = dict(feats)
                F["proxy_eov_today"] = np.array([
                    np.nan if np.isnan(z) else u_today(z)
                    for z in np.nanmean(d2["R_AMP_781.0"][si, bi], axis=1)])
                ok = ~np.isnan(V)
                for k in KS:
                    nrf = nr_topk(V, F[frozen], k)
                    if nrf is None:
                        continue
                    for sel in CANDIDATES + ["random"]:
                        col = None if sel == "random" else F[sel]
                        nro = nr_topk(V, col, k)
                        if nro is None:
                            continue
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

                            def nr_b(c):
                                if c is None:
                                    return (vo - float(np.nanmean(Vb[o]))) / dn
                                fin = np.isfinite(c) & o
                                if fin.sum() < k:
                                    return None
                                ii = np.flatnonzero(fin)
                                tp = ii[np.argsort(-c[ii])[:k]]
                                return (vo - float(np.mean(Vb[tp]))) / dn

                            a = nr_b(F[frozen][pidx] if sel != "random" else F[frozen][pidx])
                            b = nr_b(None if sel == "random" else F[sel][pidx])
                            if a is None or b is None:
                                continue
                            bs.append(b - a)
                        lo, hi = (np.percentile(bs, [2.5, 97.5]) if len(bs) >= 100
                                  else (float("nan"), float("nan")))
                        rows.append(dict(
                            future=name, policy=pol, budget=B, k=k,
                            frozen_selector=frozen, opponent=sel,
                            NR_frozen=round(nrf, 4), NR_opponent=round(nro, 4),
                            NR_diff=round(nro - nrf, 4),
                            reduction_pct=(round(100.0 * (nro - nrf) / nro, 2) if nro else ""),
                            CI_lo=round(lo, 4), CI_hi=round(hi, 4),
                            CI_excludes_0=bool(lo == lo and (lo > 0 or hi < 0)),
                            meets_20pct_and_CI=bool(nro < nrf * 0.8 and lo == lo and lo > 0)))
                print("  %s %-11s B%-4d done" % (name, pol, B), flush=True)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    R = pd.DataFrame(rows)
    print("\nWROTE", OUT, len(rows), "rows")
    print("\n=== 决策规则敏感性：k 越大，CI 越窄、但名义降幅也越小 ===")
    g = R[(R.future == "AZT@0.44") & (R.policy == "greedy_ssm")]
    for k in KS:
        z = g[(g.k == k) & (g.opponent != "random")]
        zr = g[(g.k == k) & (g.opponent == "random")]
        print("  k=%-3d  vs 非随机 heuristic: 名义降幅 %.1f-%.1f%%, CI 排除 0 的格数 %d/%d, 满足 20%%+CI 的格数 %d" % (
            k, z.reduction_pct.min(), z.reduction_pct.max(),
            int(z.CI_excludes_0.sum()), len(z), int(z.meets_20pct_and_CI.sum())))
        print("         vs random: 降幅 %.1f-%.1f%%, CI 排除 0 的格数 %d/%d" % (
            zr.reduction_pct.min(), zr.reduction_pct.max(),
            int(zr.CI_excludes_0.sum()), len(zr)))
    print("\n=== 全表：满足 20%+CI 的格数（任何条件任何对手）===")
    for k in KS:
        z = R[R.k == k]
        print("  k=%-3d  %d / %d" % (k, int(z.meets_20pct_and_CI.sum()), len(z)))
    print("\n=== CI 排除 0 的格数（全表）===")
    for k in KS:
        z = R[R.k == k]
        print("  k=%-3d  %d / %d" % (k, int(z.CI_excludes_0.sum()), len(z)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
