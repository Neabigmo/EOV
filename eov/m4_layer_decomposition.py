"""M4.12 — 补齐 `PHASE1_PROTOCOL.md` §124 的**强制四层分解**。

冻结原文（逐字）：

> **分解纪律**：对每个合格 parent 必须**同时**报告 `R_0`、`R_k^{oracle}`、`R_k^{adaptive}`、`R_{B,π}`。
> 禁止只给单一 "EOV score"——否则事后无法区分"附近没有好序列"与"算法找不到"。

而 `AMENDMENT-002 B-4` 把这一层分解列为**四项可辩护增量之一**：
> (iv) 将可达价值分解为 `R_0` / `R_k^oracle` / `R_{B,π}` 三层，把**景观机会**与**搜索能力**分开。

⛔ **M4 首轮完全没有算 `R_k^{oracle}` 与 `R_k^{adaptive}`** —— 这是一个**漏掉的强制交付物**，
且直接关系到我们声称的增量。本脚本补上。

定义（按 `OP-3` / `OP-7` 的登记默认）
------------------------------------
    R_0(x)          = F_τ(x)                                   即时准备度
    R_k^oracle(x)   = max{ F_τ(y) : Hamming(x,y) <= k }         **景观机会**（k=1 主；k=2,3 敏感性）
    R_k^adaptive(x) = 在"每步允许下降 <= delta"的约束下、k 步内可达的最大 F   **可适应可及**
    R_{B,pi}(x)     = 搜索模拟的终点值                            **搜索能力**（读 Exp 1 的 NPZ）

    delta = 1 x pooled replicate SD（`OP-7` 登记默认），pooled = sqrt(mean(value_sd^2)) over informative

`R_k^oracle` 与 `R_k^adaptive` 都**只用该任务自己的测量**，与任何策略无关 → 度量的是**景观本身**。
两者的差 = "有好邻居但走不过去"（适应性约束造成的损失）；
`R_k^oracle` 与 `R_{B,π}` 的差 = "景观里有、搜索没找到"（搜索能力造成的损失）。
"""
from __future__ import annotations

import csv
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landscape import MixedAlphabetSpace  # noqa: E402
from search_sim import Scratch, make_context  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
NPZ1 = os.path.join(ROOT, "data", "processed", "M4_EXP1_V.npz")
OUT = os.path.join(ROOT, "results", "tables", "M4_LAYER_DECOMPOSITION.csv")

DS = "Phillips2023_HA_CH65"
TASKS = ["MA90", "SI06", "G189E"]
KS = [1, 2, 3]
N_BITS = 16
B_PRIMARY = 384
POLICY = "greedy_ssm"
SEED = 20260919


def main() -> int:
    t0 = time.time()
    d = np.load(NPZ1, allow_pickle=True)
    pol = list(d["policies"]); bud = list(d["budgets"]); tk = list(d["tasks"])
    parents = d["parents"]
    si = pol.index(POLICY); bi = bud.index(B_PRIMARY)
    R_B = d["Rraw"][si, bi]                     # (task, parent) 原始可达值

    df = pd.read_parquet(MEAS)[lambda x: x.dataset_id == DS]
    space = MixedAlphabetSpace.from_masked_profiles([format(i, "0%db" % N_BITS)
                                                     for i in range(1 << N_BITS)])
    ctx = make_context(space)
    n = 1 << N_BITS

    rows = []
    for ti, t in enumerate(TASKS):
        s = df[df.task_id == t]
        v = np.full(n, np.nan)
        gi = np.array([int(x, 2) for x in s.genotype_id.astype(str)], dtype=np.int64)
        ok = s.informative.astype(bool).values
        v[gi[ok]] = pd.to_numeric(s.value_group, errors="coerce").values[ok]
        sd = pd.to_numeric(s.value_sd, errors="coerce").values[ok]
        pooled = float(np.sqrt(np.nanmean(sd ** 2)))
        delta = 1.0 * pooled                                     # OP-7
        inf = ~np.isnan(v)
        print("  %-6s pooled SD = %.5f  delta = %.5f" % (t, pooled, delta), flush=True)

        # ---- R_k^oracle：k 跳邻域内的最大值（纯 BFS，不设适应约束）
        oracle = {k: np.full(len(parents), np.nan) for k in KS}
        adaptive = {k: np.full(len(parents), np.nan) for k in KS}
        for pi, x0 in enumerate(parents):
            x0 = int(x0)
            if not inf[x0]:
                continue
            # BFS 收集 <=max(KS) 跳的节点与深度
            seen = {x0: 0}
            frontier = [x0]
            for depth in range(1, max(KS) + 1):
                nxt = []
                for u in frontier:
                    for w in ctx.neighbors[u]:
                        w = int(w)
                        if w not in seen and inf[w]:
                            seen[w] = depth
                            nxt.append(w)
                frontier = nxt
                if not frontier:
                    break
            bydepth = {}
            for node, dep in seen.items():
                bydepth.setdefault(dep, []).append(node)
            for k in KS:
                nodes = [nd for dep in range(k + 1) for nd in bydepth.get(dep, [])]
                if nodes:
                    oracle[k][pi] = float(np.max(v[nodes]))
            # ---- R_k^adaptive：每步允许下降 <= delta；同样 BFS，但边有条件
            for k in KS:
                best = v[x0]
                visited = {x0}
                frontier = [x0]
                for _ in range(k):
                    nxt = []
                    for u in frontier:
                        for w in ctx.neighbors[u]:
                            w = int(w)
                            if w in visited or not inf[w]:
                                continue
                            if v[w] >= v[u] - delta:          # 中性或更好
                                visited.add(w)
                                nxt.append(w)
                                if v[w] > best:
                                    best = v[w]
                    frontier = nxt
                    if not frontier:
                        break
                adaptive[k][pi] = float(best)
        for k in KS:
            for pi in range(len(parents)):
                rows.append(dict(
                    task=t, policy=POLICY, budget=B_PRIMARY, k=k,
                    genotype_id=space.node_id(space.node_from_index(int(parents[pi]))),
                    R_0=round(float(v[parents[pi]]), 5) if inf[parents[pi]] else "",
                    R_k_oracle=round(oracle[k][pi], 5) if oracle[k][pi] == oracle[k][pi] else "",
                    R_k_adaptive=round(adaptive[k][pi], 5) if adaptive[k][pi] == adaptive[k][pi] else "",
                    R_B_pi=round(float(R_B[ti, pi]), 5) if not np.isnan(R_B[ti, pi]) else "",
                    delta=round(delta, 5)))
        print("  %-6s done (%.0f s)" % (t, time.time() - t0), flush=True)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    R = pd.DataFrame(rows)
    for c in ("R_0", "R_k_oracle", "R_k_adaptive", "R_B_pi"):
        R[c] = pd.to_numeric(R[c], errors="coerce")
    print("\nWROTE", OUT, len(rows), "rows\n")
    print("=== 四层分解：逐 (task, k) 的均值与两段差额 ===")
    print("%-6s %2s %8s %10s %12s %9s %10s %12s" % (
        "task", "k", "R_0", "R_k_oracle", "R_k_adaptive", "R_B_pi",
        "oracle-R0", "oracle-adapt"))
    for t in TASKS:
        for k in KS:
            z = R[(R.task == t) & (R.k == k)]
            zo = z.dropna(subset=["R_k_oracle"])
            za = z.dropna(subset=["R_k_adaptive"])
            zb = z.dropna(subset=["R_B_pi"])
            print("%-6s %2d %8.4f %10.4f %12.4f %9.4f %10.4f %12.4f" % (
                t, k, z.R_0.mean(), zo.R_k_oracle.mean(), za.R_k_adaptive.mean(),
                zb.R_B_pi.mean(),
                zo.R_k_oracle.mean() - zo.R_0.mean(),
                za.R_k_adaptive.mean() - za.R_0.mean()))
    print("\n=== 关键分解：逐 k 的「搜索差距」= R_k^oracle − R_{B,π} ===")
    print("（正值 = 景观在 k 步内有比搜索终点更好的序列，即搜索没找到；负值 = 搜索已越过 k 步球）")
    for t in TASKS:
        line = "  %-6s" % t
        for k in KS:
            z = R[(R.task == t) & (R.k == k)].dropna(subset=["R_k_oracle", "R_B_pi"])
            line += "  k=%d gap=%+.4f" % (k, z.R_k_oracle.mean() - z.R_B_pi.mean())
        print(line)
    print("\n=== 中性约束是否绑定：R_k^oracle − R_k^adaptive ===")
    g = R.dropna(subset=["R_k_oracle", "R_k_adaptive"])
    dd = g.R_k_oracle - g.R_k_adaptive
    print("  全部 k：max 差 = %.6f，差 > 1e-9 的 parent 占比 = %.4f（k=1 时恒为 0，属恒等式）" % (
        dd.max(), (dd > 1e-9).mean()))
    g2 = g[g.k >= 2]
    d2 = g2.R_k_oracle - g2.R_k_adaptive
    print("  仅 k>=2：max 差 = %.6f，差 > 1e-9 的占比 = %.4f（n=%d）" % (
        d2.max(), (d2 > 1e-9).mean(), len(g2)))
    print("total %.0f s" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
