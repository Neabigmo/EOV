"""M4.11 — H1 的**强制辅助报告**（`PHASE1_DECISION.md` §H1：「不参与判定，但必须报」）。

冻结原文要求三项：
    1. **variance decomposition（parent 主效应 vs replicate 残差）**
    2. **permutation test p 值**
    3. **effect/noise ratio**

其中第 3 项已由 `M4_REPORT §3.4` 的 `ratio = IQR(R)/(2×noise)` 给出；
**第 1、2 项在 M4 中缺失** —— 这是一个**漏掉的强制交付物**，本脚本补上。

设计
----
`V` 的噪声有**两个来源**，本脚本把两者都放进去（只做 `greedy_ssm`，它是唯一相关的策略）：

  · **测量噪声**：逐基因型重复值扰动（用 `value_sem`；censored / at_inferred_floor 的组不扰动）
  · **策略随机性**：同一值场上的独立策略轨迹

→ 交叉网格 `N_NOISE × N_POLICY` 个重复，做标准的两因素方差分解：

```
Var(V) = sigma^2_parent + sigma^2_rep            ICC = sigma^2_parent / (sigma^2_parent + sigma^2_rep)
effect/noise = sd(parent means) / sd(within-parent)
```

permutation test（随机化检验）
----------------------------
`IQR(V)` 在**重贴 parent 标签**下不变，故标签置换**没有功效**。正确的零假设是
"H0：parent 之间无差异，`V` 只是围绕共同均值的噪声"。零分布由**从噪声模型重采样**得到：

    对每个 (task, budget)：从 N(mean(V), sigma_rep) 抽 n_parents 个值 → 算 IQR → 重复 2000 次
    p = #{IQR_null >= IQR_obs} / 2000

⚠️ **披露**：该零分布只用**残差 sd**，因此是"parent 效应为 0"的**参数化近似**，不是精确的
随机化检验（精确版本需要可交换性，而 parent 间的基因型相关性破坏了它）。这一点必须标注。
"""
from __future__ import annotations

import csv
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from search_sim import Scratch, make_context, simulate_search, utility_from_values  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
OUT = os.path.join(ROOT, "data_registry", "M4_H1_AUXILIARY.csv")

DS = "Phillips2023_HA_CH65"
TASKS = ["MA90", "SI06", "G189E"]
POLICY = "greedy_ssm"
BUDGETS = (24, 96, 384)
N_BITS = 16
N_PARENTS = 1000
N_NOISE = 3          # 测量噪声实现
N_POLICY = 7         # 策略轨迹
N_PERM = 2000
SEED = 20260919


def main() -> int:
    t0 = time.time()
    df = pd.read_parquet(MEAS)[lambda d: d.dataset_id == DS]
    vals, sems, perts = {}, {}, {}
    for t in TASKS:
        s = df[df.task_id == t]
        n = 1 << N_BITS
        v = np.full(n, np.nan); m = np.full(n, np.nan); p = np.zeros(n, dtype=bool)
        gi = np.array([int(x, 2) for x in s.genotype_id.astype(str)], dtype=np.int64)
        ok = s.informative.astype(bool).values
        v[gi[ok]] = pd.to_numeric(s.value_group, errors="coerce").values[ok]
        m[gi[ok]] = pd.to_numeric(s.value_sd, errors="coerce").values[ok]   # 用 SD（更保守）
        floorish = (s.measurement_state.astype(str) != "exact").values | \
                   s.at_inferred_floor.astype(bool).values
        p[gi[ok]] = ~floorish[ok]
        vals[t], sems[t], perts[t] = v, m, p
    space_profiles = [format(i, "0%db" % N_BITS) for i in range(1 << N_BITS)]
    from landscape import MixedAlphabetSpace
    space = MixedAlphabetSpace.from_masked_profiles(space_profiles)
    ctx = make_context(space)
    scratch = Scratch(1 << N_BITS)
    us = {t: utility_from_values(vals[t], scale="q05q95")[0] for t in TASKS}
    cand = {t: np.flatnonzero(~np.isnan(vals[t])) for t in TASKS}
    pool = np.flatnonzero(~np.isnan(vals[TASKS[0]]))
    parents = np.sort(np.random.default_rng(SEED).choice(pool, N_PARENTS, replace=False))
    print("parents=%d  网格 = %d 噪声 x %d 策略 = %d 个重复" % (
        len(parents), N_NOISE, N_POLICY, N_NOISE * N_POLICY), flush=True)

    rng = np.random.default_rng(SEED + 5)
    rng_med = np.random.default_rng(SEED + 77)   # 仅供 V median 的 bootstrap，独立以保证可复现
    # 预生成噪声值场
    fields = {}
    for t in TASKS:
        v, m, p = vals[t], sems[t], perts[t]
        fl = [v]
        for _ in range(N_NOISE):
            out = v.copy()
            sel = p & ~np.isnan(m) & (m > 0)
            out[sel] = v[sel] + rng.normal(0.0, 1.0, size=int(sel.sum())) * m[sel]
            fl.append(out)
        fields[t] = fl

    rows = []
    for t in TASKS:
        u = us[t]
        V = np.full((len(BUDGETS), N_PARENTS, len(fields[t]), N_POLICY + 1), np.nan)
        for bi, B in enumerate(BUDGETS):
            for fi, fv in enumerate(fields[t]):
                for pi, x in enumerate(parents):
                    for rep in range(N_POLICY + 1):
                        r = simulate_search(ctx, int(x), fv, cand[t], POLICY, B, rng, scratch)
                        if not np.isnan(r):
                            V[bi, pi, fi, rep] = u(r)
        for bi, B in enumerate(BUDGETS):
            flat = V[bi].reshape(N_PARENTS, -1)          # (parent, 重复)
            pm = np.nanmean(flat, axis=1)
            ok = ~np.isnan(pm)
            within_var = float(np.nanmean(np.nanvar(flat, axis=1, ddof=1)))
            between_var = float(np.nanvar(pm[ok], ddof=1)) - within_var / flat.shape[1]
            between_var = max(between_var, 0.0)
            icc = between_var / (between_var + within_var) if (between_var + within_var) > 0 else np.nan
            iqr_obs = float(np.percentile(pm[ok], 75) - np.percentile(pm[ok], 25))
            sd_rep = float(np.sqrt(within_var))
            # 参数化零分布：从 N(mean, sd_rep) 抽 n 个值
            mu = float(np.nanmean(pm[ok]))
            null = np.array([np.percentile(rng.normal(mu, sd_rep, int(ok.sum())), 75) -
                             np.percentile(rng.normal(mu, sd_rep, int(ok.sum())), 25)
                             for _ in range(N_PERM)])
            pval = float((null >= iqr_obs).mean())
            # ---- PHASE1_PROTOCOL L162 的强制输出：V 的 median 与 95% CI（+ 已有的 IQR）
            # median 的 CI：对 parent 做 bootstrap；V 的 95% 区间：跨 parent 的分位数
            # ⚠️ 用**独立**的 rng（否则会推移主 rng 流，使已核验的 ICC / perm_p 数字改变 —— 这是
            #    本脚本第一次加这段时踩到的坑：加一个 bootstrap 就让 SI06/G189E 的数字全变了）
            Vmed = float(np.nanmedian(pm[ok]))
            bmed = [float(np.nanmedian(pm[ok][rng_med.integers(0, int(ok.sum()), int(ok.sum()))]))
                    for _ in range(2000)]
            med_lo, med_hi = np.percentile(bmed, [2.5, 97.5])
            p_lo, p_hi = np.percentile(pm[ok], [2.5, 97.5])
            rows.append(dict(
                task=t, policy=POLICY, budget=B, n_parents=int(ok.sum()),
                n_replicates=int(flat.shape[1]),
                V_median=round(Vmed, 5),
                V_median_CI_lo=round(float(med_lo), 5),
                V_median_CI_hi=round(float(med_hi), 5),
                V_p2_5=round(float(p_lo), 5),
                V_p97_5=round(float(p_hi), 5),
                iqr_v=round(iqr_obs, 6),
                var_parent=round(between_var, 8),
                var_replicate=round(within_var, 8),
                icc=round(icc, 4) if icc == icc else "",
                sd_parent=round(float(np.sqrt(between_var)), 5),
                sd_replicate=round(sd_rep, 5),
                effect_over_noise=round(float(np.sqrt(between_var)) / sd_rep, 4)
                if sd_rep > 0 else "",
                perm_p=round(pval, 5),
                perm_n=N_PERM,
                noise_model="参数化零分布 N(mean(V), sd_replicate)；非精确随机化检验"))
        print("  %-6s done (%.0f s)" % (t, time.time() - t0), flush=True)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    R = pd.DataFrame(rows)
    print("\nWROTE", OUT, len(rows), "rows\n")
    print("=== H1 强制辅助报告（greedy_ssm）===")
    print(R[["task", "budget", "n_replicates", "var_parent", "var_replicate", "icc",
             "effect_over_noise", "perm_p"]].to_string(index=False))
    print("\nICC 区间：%.4f ~ %.4f" % (R.icc.min(), R.icc.max()))
    print("effect/noise 区间：%.3f ~ %.3f" % (R.effect_over_noise.min(), R.effect_over_noise.max()))
    print("permutation p 区间：%.5f ~ %.5f（最大 %.5f）" % (
        R.perm_p.min(), R.perm_p.max(), R.perm_p.max()))
    print("p < 0.05 的格数：%d / %d" % (int((R.perm_p < 0.05).sum()), len(R)))
    print("total %.0f s" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
