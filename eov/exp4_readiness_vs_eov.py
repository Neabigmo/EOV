"""M4 / Exp 4 —— `Readiness != EOV` 的判别检验。

问题
----
`Readiness(x) = E_τ[u_τ(R_0(x,τ))]` 是**今天就能算**的量（单个变体的即时值）；
`EOV_{B,π}(x) = E_τ[V_{B,π}(x,τ)]` 是**未来揭晓后才能算**的量（预算内适应后的终点值）。
若 `Readiness` 已足以预测 `V_{B,π}`，则 EOV 没有增量 → 项目失败。

两条互补证据
------------
A. **秩相关**：`Spearman(Readiness_today, V_future)`，逐 (policy, budget)。
   同时报全部 Day-0 proxy 的同格 Spearman 作对照 —— 只有**相对**读数才有意义（DECISION §3 H2）。
B. **匹配对（matched pair，"同一个现在、不同的未来"）**，判据逐字取自 DECISION §"Matched-pair confirmation"：
   1. confirmation split 中 >= **20** 对在 `Readiness` 与**全部** proxy 上按**噪声决定的容差**匹配的 parent；
   2. 未来值差异的**方向性成功率**显著高于 0.5（二项检验 p < 0.05）；
   3. aggregate effect 的 **95% bootstrap CI 不跨 0**。

容差**由实验噪声决定，不得人工调 ε**
------------------------------------
`u_τ` 是仿射的，故 `u` 尺度上的噪声 = `value_sem / (q95 − q05)`。取
    `eps = 2 × median_x σ_u(x)`
（2 倍是"两个被匹配的量各自带一份噪声"的传播；预先定死，不随结果调整）。

分割
----
按 `genotype_id` 的稳定哈希分 discovery / confirmation 两半（各 50%）。
匹配对**只在 confirmation 半区**统计（DECISION 原文），discovery 半区用于（可选）选择匹配用的 proxy 集合。

尺度
----
AMENDMENT-014 §3：TEM-1 全栈统一用 PROTOCOL §3.3 OP-12（无 clip）。R 直接读
`M4_EXP2_V.npz`（Exp 2 产出，同源）。
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
NPZ2 = os.path.join(ROOT, "data", "processed", "M4_EXP2_V.npz")
OUT_A = os.path.join(ROOT, "results", "tables", "M4_EXP4_READINESS_VS_EOV.csv")
OUT_B = os.path.join(ROOT, "data_registry", "M4_EXP4_MATCHED_PAIRS.csv")

DS = "TEM-1CML"
AMP_CONDITIONS = ["0.0", "3.1", "12.2", "48.8", "195.0", "781.0"]
TODAY_PRIMARY = ("AMP", "781.0")
FUTURES = [("AZT", "0.44"), ("AZT", "36.0")]
PROXIES = ["current_fitness", "known_family_mean", "known_family_worst", "local_robustness",
           "neighbor_informative_frac", "dist_to_best", "n_better_neighbors", "local_ruggedness"]


def split_of(gid: str) -> str:
    h = hashlib.sha256(("eov-m4-split|" + gid).encode("utf-8")).hexdigest()
    return "discovery" if int(h[:8], 16) % 2 == 0 else "confirmation"


def main() -> int:
    if not os.path.exists(NPZ2):
        print("MISSING %s —— 必须先完成 Exp 2" % NPZ2)
        return 1
    d2 = np.load(NPZ2)
    parents = d2["parents"]
    feats = {k[5:]: d2[k] for k in d2.files if k.startswith("feat_")}
    df = pd.read_parquet(MEAS)
    t = df[df.dataset_id == DS]
    ids = sorted(set(t.genotype_id.astype(str).unique()))
    space = MixedAlphabetSpace.from_masked_profiles([s for s in ids if "X" not in s])
    n = space.space_size()

    def load(tid, cid):
        s = t[(t.task_id == tid) & (t.condition_id == cid)]
        s = s[~s.genotype_id.astype(str).str.contains("X", regex=False)]
        s = s.drop_duplicates("genotype_id")
        v = np.full(n, np.nan)
        idx = np.array([space.index_of(tuple(x)) for x in s.genotype_id.astype(str)], dtype=np.int64)
        ok = s.informative.astype(bool).values
        v[idx[ok]] = pd.to_numeric(s.value_group, errors="coerce").values[ok]
        return s, v, idx, ok

    def scale(key):
        v = load(*key)[1]
        vv = v[~np.isnan(v)]
        q05, q95 = float(np.percentile(vv, 5)), float(np.percentile(vv, 95))
        return (lambda z: (z - q05) / (q95 - q05)), q05, q95

    u_today, q05t, q95t = scale(TODAY_PRIMARY)
    s_t, v_t, idx_t, ok_t = load(*TODAY_PRIMARY)
    sem_t = pd.to_numeric(s_t.value_sem, errors="coerce").values
    sem_map = np.full(n, np.nan)
    sem_map[idx_t] = sem_t
    sigma_u = sem_map[parents] / (q95t - q05t)
    eps = 2.0 * float(np.nanmedian(sigma_u))
    print("噪声决定的匹配容差 eps = 2 x median(sigma_u) = %.6f" % eps, flush=True)

    # ---------- A. 秩相关 ----------
    rows = []
    for key in FUTURES:
        u_f = scale(key)[0]
        name = "%s@%s" % key
        for si, pol in enumerate(POLICIES):
            for bi, B in enumerate(BUDGETS):
                V = np.array([np.nan if np.isnan(z) else u_f(z)
                              for z in np.nanmean(d2["R_%s_%s" % key][si, bi], axis=1)])
                rd = feats["known_family_mean"] if "known_family_mean" in feats else None
                entry = dict(future=name, policy=pol, budget=B)
                m = np.isfinite(rd) & ~np.isnan(V) if rd is not None else None
                for nm, col in [("Readiness(known_family_mean)", rd),
                                ("current_fitness", feats["current_fitness"])] + \
                               [(p, feats[p]) for p in PROXIES if p in feats]:
                    if col is None:
                        continue
                    mm = np.isfinite(col) & ~np.isnan(V)
                    if mm.sum() < 50 or np.all(col[mm] == col[mm][0]):
                        entry[nm] = ""
                        continue
                    entry[nm] = round(float(stats.spearmanr(col[mm], V[mm]).statistic), 4)
                rows.append(entry)
        print("  A 完成 %s" % name, flush=True)
    with open(OUT_A, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # ---------- B. 匹配对（只用 confirmation 半区）----------
    gids = [space.node_id(space.node_from_index(int(x))) for x in parents]
    half = np.array([split_of(g) for g in gids])
    print("split: discovery=%d confirmation=%d" % (int((half == "discovery").sum()),
                                                   int((half == "confirmation").sum())), flush=True)
    conf = np.flatnonzero(half == "confirmation")
    # 逐变量容差：**含测量噪声**的连续量用噪声容差 `eps`（u 尺度）；
    # 离散/几何量（整数或计数比）**没有测量噪声**，故要求精确匹配（tol = 0）。
    # 这样"容差由实验噪声决定"这条才成立 —— 不存在人工调的 ε。
    TOL = {
        "known_family_mean": eps, "known_family_worst": eps,
        "current_fitness": eps, "local_robustness": eps,
        "proxy_eov_today": eps,
        "neighbor_informative_frac": 0.0, "dist_to_best": 0.0,
        "n_better_neighbors": 0.0, "local_ruggedness": eps,
    }
    pair_rows = []
    for key in FUTURES:
        u_f = scale(key)[0]
        name = "%s@%s" % key
        for si, pol in enumerate(POLICIES):
            for bi, B in enumerate(BUDGETS):
                V = np.array([np.nan if np.isnan(z) else u_f(z)
                              for z in np.nanmean(d2["R_%s_%s" % key][si, bi], axis=1)])
                proxy_today = np.array([
                    np.nan if np.isnan(z) else u_today(z)
                    for z in np.nanmean(d2["R_%s_%s" % TODAY_PRIMARY][si, bi], axis=1)])
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
                    pair_rows.append(dict(future=name, policy=pol, budget=B, n_pairs=len(pairs),
                                          n_candidates=len(cand), sd_ratio="", perm_p="",
                                          dir_current_fitness="", dir_local_robustness="",
                                          dir_proxy_eov_today="", dir_Readiness="",
                                          best_dir_rate="", best_dir_p="", verdict="INSUFFICIENT_PAIRS"))
                    continue
                dv = np.array([V[i] - V[j] for i, j in pairs])
                rng = np.random.default_rng(20260919)

                # ---- 统计量 1：匹配对的未来差异 vs 随机配对的未来差异（本项目中心命题的直测）
                # 定义 ratio = sd(dv | 匹配) / sd(dv | 随机配对)，在**同一候选集合**内比较。
                #   ratio -> 1 : "同一个现在、不同的未来"成立（今天的信息不约束未来）
                #   ratio -> 0 : 今天的信息已决定未来（readiness = EOV）
                sd_matched = float(np.std(dv, ddof=1))
                null_sd = []
                pool_c = np.array(cand)
                for _ in range(200):
                    perm = rng.permutation(pool_c)
                    a, b = perm[:len(perm) // 2], perm[len(perm) // 2:2 * (len(perm) // 2)]
                    null_sd.append(float(np.std(V[a] - V[b], ddof=1)))
                null_sd = float(np.mean(null_sd))
                ratio = sd_matched / null_sd if null_sd > 0 else float("nan")
                # bootstrap **比值本身**（分母用固定的置换零分布），原实现误把 CI 算在分子上
                boot = [float(np.std(dv[rng.integers(0, len(dv), len(dv))], ddof=1)) / null_sd
                        for _ in range(2000)]
                r_lo, r_hi = np.percentile(boot, [2.5, 97.5])
                # 解释：Var(dv|匹配)/Var(dv|随机) = ratio^2 → 今天信息已解释的未来方差份额 = 1 - ratio^2
                var_explained = 1.0 - ratio ** 2 if ratio == ratio else float("nan")

                # ---- 统计量 2（冻结判据 2 的正确实现）：
                # 用某条 Day-0 预测器在**每一对内部**预测谁更好，再与观测到的未来差异比方向。
                # 原实现把 (i, j) 按索引序当成有序对，则 P(dv>0)=0.5 恒成立、检验无功效 —— 属方法学错误，
                # 已在 M4_REPORT §6.5 明确披露并改正。
                dirs = {}
                for pname in ["current_fitness", "local_robustness", "proxy_eov_today",
                              "known_family_mean"]:
                    P = feats[pname] if pname != "proxy_eov_today" else proxy_today
                    signed = np.array([np.sign(P[i] - P[j]) * (V[i] - V[j]) for i, j in pairs])
                    nz = signed[signed != 0]
                    hit = int((nz > 0).sum())
                    rate = hit / len(nz) if len(nz) else float("nan")
                    pv = (float(stats.binomtest(hit, len(nz), 0.5, alternative="two-sided").pvalue)
                          if len(nz) else 1.0)
                    bb = [float(np.mean(signed[rng.integers(0, len(signed), len(signed))]))
                          for _ in range(2000)]
                    dirs[pname] = (rate, pv, float(np.mean(signed)),
                                   float(np.percentile(bb, 2.5)), float(np.percentile(bb, 97.5)))
                best = min(dirs.items(), key=lambda kv: kv[1][1])
                # 判据 2 的**预指定**预测器 = `Readiness`（被检验的假设就是 "Readiness != EOV"）。
                # `best_dir_*`（4 个预测器里取最小 p）只作探索性报告，并须按 4 重比较降权。
                rd = dirs["known_family_mean"]
                pair_rows.append(dict(
                    future=name, policy=pol, budget=B, n_pairs=len(pairs), n_candidates=len(cand),
                    sd_ratio=round(ratio, 4), sd_ratio_lo=round(float(r_lo), 4),
                    sd_ratio_hi=round(float(r_hi), 4),
                    var_explained_by_today=round(var_explained, 4),
                    dir_current_fitness=round(dirs["current_fitness"][0], 4),
                    dir_local_robustness=round(dirs["local_robustness"][0], 4),
                    dir_proxy_eov_today=round(dirs["proxy_eov_today"][0], 4),
                    dir_Readiness=round(rd[0], 4), Readiness_p=round(rd[1], 6),
                    Readiness_effect=round(rd[2], 5),
                    Readiness_ci_lo=round(rd[3], 5), Readiness_ci_hi=round(rd[4], 5),
                    exploratory_best_name=best[0], exploratory_best_rate=round(best[1][0], 4),
                    exploratory_best_p=round(best[1][1], 6),
                    verdict=("PASS" if (len(pairs) >= 20 and rd[1] < 0.05 and rd[3] > 0) else "FAIL")))
                print("  B %s %-11s B%-4d pairs=%4d  sd_ratio=%.3f [%.3f,%.3f] "
                      "var_explained=%.3f  Readiness dir=%.3f p=%.3g  (explor. best=%s p=%.3g)" % (
                          name, pol, B, len(pairs), ratio, r_lo, r_hi, var_explained,
                          rd[0], rd[1], best[0], best[1][1]), flush=True)
    with open(OUT_B, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pair_rows[0].keys()))
        w.writeheader()
        for r in pair_rows:
            w.writerow(r)
    print()
    print("WROTE", OUT_A, len(rows), "rows")
    print("WROTE", OUT_B, len(pair_rows), "rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
