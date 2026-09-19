"""M5 Part 3（干净版）：transferability 的可解释性检验。

要回答的问题：**task→task 的起点价值迁移，能不能被少数 task-pair 属性解释？**

关键的三道防线（防止把假相关当发现）：
  D1 **簇假象**：21 对里有 15 对是"同药不同浓度"、3 对是 Phillips、3 对跨药。
     若把它们混在一起，任何"相似 → 迁移好"的相关都可能是两个簇的产物。
     → 必须**在单一数据集内部**重复同一检验。
  D2 **机械重复**：`f5_task_distance = 1 − f1_landscape_rho` 与 f1 是同一个量的镜像，
     留在表里会让"多个特征一致指向同一结论"看起来更强。→ **剔除 f5**。
  D3 **多重比较**：5 个特征 × 3 个 outcome = 15 个相关。报告时必须给出全部 15 个，
     不得只报显著的。
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "data_registry")
OUT = os.path.join(REG, "M5_FEATURE_VS_TRANSFER_CLEAN.csv")

CAND = ["f1_landscape_rho", "f2_beneficial_overlap", "f3_sign_epistasis_agree",
        "f4_neighborhood_agree", "f6_robustness_consistency"]
OUTCOMES = ["rho", "reg", "beta"]


def sp(a, b):
    if len(a) < 6 or np.all(a == a[0]) or np.all(b == b[0]):
        return float("nan")
    ra = pd.Series(a).rank().values
    rb = pd.Series(b).rank().values
    ra = ra - ra.mean(); rb = rb - rb.mean()
    d = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
    return float((ra * rb).sum() / d) if d > 0 else float("nan")


def main() -> int:
    M = pd.read_csv(os.path.join(REG, "M5_TRANSFER_MAP.csv"))
    F = pd.read_csv(os.path.join(REG, "M5_PAIR_FEATURES.csv"))
    for d in (M, F):
        d["pk"] = ["|".join(sorted([a, b])) for a, b in zip(d.task_A, d.task_B)]
    agg = (M.dropna(subset=["rho_rank"])
           .groupby(["dataset", "pk"])
           .agg(rho=("rho_rank", "mean"), reg=("regret_A_to_B", "mean"),
                beta=("beta", "mean"), r2=("r2", "mean"), n=("rho_rank", "size"))
           .reset_index())
    J = agg.merge(F, on=["dataset", "pk"], suffixes=("", "_f"))

    # 标注组别：cross 由 f1 无法判断，用任务名判断（AZT vs AMP）
    def grp(row):
        a, b = row.task_A, row.task_B
        if row.dataset.startswith("Phillips"):
            return "Phillips(3 任务)"
        drugs = {x.split("@")[0] for x in (a, b)}
        return "TEM-1 跨药" if len(drugs) > 1 else "TEM-1 同药"
    J["grp"] = J.apply(grp, axis=1)

    rows = []
    for label, sub in [("ALL 21 对", J),
                       ("TEM-1 全部 18 对", J[J.dataset == "TEM-1CML"]),
                       ("TEM-1 同药 15 对", J[J.grp == "TEM-1 同药"]),
                       ("TEM-1 跨药 3 对", J[J.grp == "TEM-1 跨药"]),
                       ("Phillips 3 对", J[J.dataset.str.startswith("Phillips")])]:
        for c in CAND:
            for o in OUTCOMES:
                z = sub[[c, o]].apply(pd.to_numeric, errors="coerce").dropna()
                rows.append(dict(subset=label, n_pairs=len(sub), feature=c, outcome=o,
                                 n_used=len(z), spearman=round(sp(z[c].values, z[o].values), 4)
                                 if len(z) >= 6 else ""))
    R = pd.DataFrame(rows)
    R.to_csv(OUT, index=False)
    print("WROTE", OUT, len(R), "rows\n")

    pd.set_option("display.width", 220)
    for label in ("ALL 21 对", "TEM-1 全部 18 对", "TEM-1 同药 15 对"):
        z = R[(R.subset == label) & (R.outcome == "rho")]
        print("=== %s : 各特征 vs rho_rank ===" % label)
        for _, x in z.iterrows():
            print("   %-28s %s (n=%s)" % (x.feature, x.spearman, x.n_used))
        print()

    print("=== 幅度校准 β（\"幅度能不能迁移\"的直读）===")
    b = M.dropna(subset=["beta"]).beta.astype(float)
    print("   β: min=%.3f q25=%.3f **median=%.3f** q75=%.3f max=%.3f" % (
        b.min(), b.quantile(.25), b.median(), b.quantile(.75), b.max()))
    print("   β ≤ 0 的格数：%d / %d" % (int((b <= 0).sum()), len(b)))
    print("   R² 中位数：%.4f" % M.dropna(subset=["r2"]).r2.astype(float).median())
    z = J[["rho", "beta"]].apply(pd.to_numeric, errors="coerce").dropna()
    print("   spearman(rho_rank, beta) = %+.4f  (n=%d)" % (sp(z.rho.values, z.beta.values), len(z)))

    print("\n=== 选择 regret（在 A 上选，去 B 上兑现）===")
    g = M.dropna(subset=["regret_A_to_B"]).regret_A_to_B.astype(float)
    print("   regret: min=%.3f median=%.3f max=%.3f  （0 = 选中 oracle，1 = 选中 5%% 分位）" % (
        g.min(), g.median(), g.max()))
    print("   regret > 0.5 的格数：%d / %d" % (int((g > 0.5).sum()), len(g)))

    print("\n=== 组别之间的水平差异（描述性）===")
    print(J.groupby("grp")[["rho", "beta", "f1_landscape_rho"]].agg(["mean", "count"]).round(4).to_string())
    J.to_csv(os.path.join(REG, "M5_PAIR_LEVEL.csv"), index=False)
    print("\nWROTE M5_PAIR_LEVEL.csv  pairs=%d" % len(J))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
