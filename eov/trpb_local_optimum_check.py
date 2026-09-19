"""TrpB 外部校验的**归因检验**：残差差距是"算法不同"还是"我的搜索没收敛"？

`M4_TRPB_EXTERNAL_CHECK.csv` 显示：预算 B 增大时，我的 `greedy_ssm` 终点相对原文
`single_step_DE` 的比例从 0.602 升到 0.931（B=384），但**停在 0.953（B=1920）**，
`exact_equal` 也只到 0.275。两种解释：

    (a) **算法不同**：原文是"24 种固定位点顺序的坐标上升扫描"，我的 `greedy_ssm` 是最陡上升。
        在 4 位点景观上，某些起点的坐标扫描路径需要经过一个陡升不会走的中间点。
        → 两者停在**不同的局部最优**，差距是**真实的算法差异**。
    (b) **我的搜索没收敛**：终点还有更好的 Hamming-1 邻居 → 说明预算不足或实现有问题。

**本脚本给出判据**：对每个起点，检查 `greedy_ssm` 在 B=1920 的终点是否满足
"**没有任何 Hamming-1 邻居的 fitness 更高**"。若是，则它是**严格局部最优** → 支持 (a)。

同时报告 `B=1920` 相对 `B=384` 的**新增改进量**（用于判断是否已饱和）。
"""
from __future__ import annotations

import csv
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landscape import MixedAlphabetSpace  # noqa: E402
from search_sim import Scratch, make_context, simulate_search  # noqa: E402
from trpb_baseline import AA20, DATA, N_SITES, load_trpb, simulate_single_step_DE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data_registry", "M4_TRPB_LOCAL_OPTIMUM_CHECK.csv")
N_START = 400
B_CHECK = 1920
SEED = 20260919


def main() -> int:
    if not os.path.isdir(DATA):
        print("缺少", DATA)
        return 1
    df, _, _ = load_trpb()
    df = df.dropna(subset=["AAs", "fitness (min 0)"]).copy()
    df["AAs"] = df["AAs"].astype(str)
    space = MixedAlphabetSpace([AA20] * N_SITES)
    n = space.space_size()
    ctx = make_context(space)
    scratch = Scratch(n)
    val = np.zeros(n, dtype=float)
    idx = np.array([space.index_of(tuple(s)) for s in df["AAs"]], dtype=np.int64)
    val[idx] = df["fitness (min 0)"].values
    cand = np.arange(n, dtype=np.int64)

    act = df[df["active"]]["AAs"].values
    pick0 = np.linspace(0, len(act) - 1, min(N_START, len(act))).astype(int)
    sample = act[pick0]
    theirs = simulate_single_step_DE(df, "AAs", "fitness (min 0)", verbose=False, starts=sample)
    per = theirs.groupby("start_seq").final_fitness.max()

    import search_sim
    rng = np.random.default_rng(SEED)
    rows = []
    for s in sample:
        x0 = int(space.index_of(tuple(s)))
        # 逐预算跑，并记录终点 index（用 mask 反推）
        ends = {}
        for B in (384, B_CHECK):
            scratch.mask[:] = False
            r = simulate_search(ctx, x0, val, cand, "greedy_ssm", B, rng, scratch)
            ms = np.flatnonzero(scratch.mask)
            ends[B] = int(ms[np.argmax(val[ms])]) if len(ms) else x0
        e = ends[B_CHECK]
        nbf = val[ctx.neighbors[e]]
        best_nb = float(np.max(nbf))
        rows.append(dict(
            start_seq=s, theirs_best=float(per.loc[s]),
            mine_B384=float(val[ends[384]]), mine_B1920=float(val[e]),
            end_is_strict_local_opt=bool(best_nb <= val[e] + 1e-12),
            end_best_neighbor_delta=round(best_nb - float(val[e]), 8),
            improved_from_384_to_1920=round(float(val[e]) - float(val[ends[384]]), 8)))
    R = pd.DataFrame(rows)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(R.columns))
        w.writeheader()
        for r in R.to_dict("records"):
            w.writerow(r)

    frac_lo = float(R.end_is_strict_local_opt.mean())
    print("=== 归因检验（n=%d，B=%d）===" % (len(R), B_CHECK))
    print("终点是**严格局部最优**的比例：%.4f" % frac_lo)
    print("终点仍有更好邻居的比例：%.4f（若显著>0 → 支持 (b) 未收敛）" % (1 - frac_lo))
    print("邻居最大改进量的中位数：%.3g" % float(R.end_best_neighbor_delta.median()))
    print("B=384 → B=1920 的平均新增改进：%.5f" % float(R.improved_from_384_to_1920.mean()))
    print("  （原口径下 mine_B384 均值 %.4f、mine_B1920 均值 %.4f、theirs 均值 %.4f）" % (
        R.mine_B384.mean(), R.mine_B1920.mean(), R.theirs_best.mean()))
    print("在终点已为局部最优的起点里，仍低于原文终点的比例：%.4f" % float(
        (R[R.end_is_strict_local_opt].mine_B1920 <
         R[R.end_is_strict_local_opt].theirs_best - 1e-12).mean()))
    print("\nWROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
