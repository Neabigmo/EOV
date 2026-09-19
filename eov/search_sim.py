"""M4 共享组件：product-space 上的一致性搜索模拟器。

**唯一实现**。Exp 1 / Exp 2 / Exp 3 必须全部调用本模块，禁止各自复制一份策略代码
（PHASE1_PROTOCOL.md §fail-loud：graph key 与 measurement key 必须来自同一构造路径；
策略实现同样不得分叉）。

冻结口径
--------
OP-1  预算 B = 被 assay 的 **unique 基因型数**；起点 x **不计入 B**，但计入被测集合
      `A_{B,pi}(x)`（它的值本来就已知）。3 轮：b1 = ceil(B/2)，之后每轮
      b = ceil((B - b1)/2)，末轮取余数。
OP-2  预算档位 B in {24, 96, 384}
OP-21 B <= |space|/4

可达值
------
`R_{B,pi}(x,tau) = max over A_{B,pi}(x) 的 value_group`（含起点）。

策略（2-3 个最简单的，AMENDMENT-001 §B-6 允许的最小集合）
--------------------------------------------------------
random        在候选池内均匀随机采样（不用任何 fitness）
greedy_ssm    steepest ascent：从当前最优出发，测其未测的 Hamming-1 邻居；超额则随机取 b
mlde_ridge    在已测数据上拟合 **ridge**（one-hot + 截距，λ 固定为 1.0 且 **不做任何调参**，
              y 先标准化使 λ 无量纲），预测全部未测，取 top-b；预测并列时**随机**打破

**三者都只用 `values`（即该任务自己的测量）；没有任何一个能看到别的任务。**

实现修正（AMENDMENT-013 §3，**在看任何 V/regret 之前**冻结）
----------------------------------------------------------
C3a 名字是 ridge、原实现却是 `lstsq`（零正则 OLS）。该 one-hot + 截距设计**恒为秩亏**
    （每个位点的哑变量之和恒等于截距列），且 B=24 时 n=12 < p=17。→ 改为真 ridge。
C3b 预测并列时 `argpartition` 按索引序取 top-b → 所有起点收敛到同一批低索引基因型
    → V 退化为常数（Exp 1 首跑 9/9 个 MLDE 相关系数为 nan 即此因）。→ 并列随机打破。
"""
from __future__ import annotations

from typing import Optional, Sequence

import numpy as np

BUDGETS = (24, 96, 384)
POLICIES = ("random", "greedy_ssm", "mlde_ridge")


def budget_schedule(B: int) -> tuple:
    """OP-1：把 B 拆成 3 轮。返回 (b1, b2, b3)，起点不计入。"""
    if B <= 0:
        raise ValueError("budget must be positive")
    b1 = -(-B // 2)
    b2 = -(-(B - b1) // 2)
    b3 = B - b1 - b2
    assert b1 + b2 + b3 == B and b1 >= b2 >= b3 >= 0
    return (b1, b2, b3)


class SearchContext:
    """预计算 one-hot 设计矩阵与邻居表，供大批量模拟复用。

    只应由 `make_context(space)` 构造。
    """

    __slots__ = ("space", "n_positions", "space_size", "degree", "codes",
                 "design", "n_features", "neighbors")


def make_context(space) -> SearchContext:
    """构建 SearchContext：编码与邻居表均派生自 `space` 自身的等位顺序。"""
    n_positions = space.n_positions
    n_total = space.space_size()
    idx = np.arange(n_total, dtype=np.int64)
    radix = np.ones(n_positions, dtype=np.int64)
    for pos in range(n_positions - 2, -1, -1):
        radix[pos] = radix[pos + 1] * len(space.alleles_at(pos + 1))
    ctx = SearchContext.__new__(SearchContext)
    ctx.space = space
    ctx.n_positions = n_positions
    ctx.space_size = n_total
    ctx.degree = space.degree_topology()
    codes = np.stack([(idx // radix[p]) % len(space.alleles_at(p)) for p in range(n_positions)], axis=1)
    ctx.codes = codes
    n_allele = [len(space.alleles_at(p)) for p in range(n_positions)]
    onehot = np.zeros((n_total, sum(n_allele)), dtype=np.float32)
    off = 0
    for pos in range(n_positions):
        onehot[np.arange(n_total), off + codes[:, pos]] = 1.0
        off += n_allele[pos]
    ctx.design = np.hstack([onehot, np.ones((n_total, 1), np.float32)])
    ctx.n_features = ctx.design.shape[1]
    nbr = np.empty((n_total, ctx.degree), dtype=np.int64)
    for i in range(n_total):
        row = []
        for pos in range(n_positions):
            base = codes[i, pos]
            for a in range(n_allele[pos]):
                if a == base:
                    continue
                row.append(int(i + (a - base) * radix[pos]))
        assert len(row) == ctx.degree, (i, len(row))
        nbr[i] = row
    ctx.neighbors = nbr
    return ctx


class Scratch:
    """可复用的工作区，避免每次 simulate 分配 55k 布尔数组。"""

    def __init__(self, space_size: int) -> None:
        self.mask = np.zeros(space_size, dtype=bool)
        self.buf = np.empty(space_size, dtype=np.float64)


def simulate_search(ctx: SearchContext, start: int, values: np.ndarray,
                    cand: np.ndarray, policy: str, budget: int,
                    rng: np.random.Generator, scratch: Scratch) -> float:
    """返回 `R_{B,pi}(start)`；起点在该任务不可测时返回 NaN。

    `values` : (space_size,) float，NaN = 不可测（未测/非 informative）
    `cand`   : 可测基因型的索引数组（= 该任务 informative 集合）
    """
    if policy not in POLICIES:
        raise ValueError("unknown policy %r" % (policy,))
    # fail-loud：`cand` 必须是**本任务**的可测集合。若把别的任务的候选池传进来，
    # random/MLDE 会挑到 value=NaN 的基因型，而 `np.max` 会被 NaN 吞掉整格结果
    # （Exp 1 首轮 SI06/G189E 大量 "全部 NaN" 即此因）。宁可报错，不要静默 NaN。
    if np.isnan(values[cand]).any():
        raise ValueError("cand contains non-informative genotypes for this task")
    mask = scratch.mask
    mask[:] = False
    if np.isnan(values[start]):
        return float("nan")
    mask[start] = True
    for b in budget_schedule(budget):
        if b <= 0:
            continue
        n_seen = int(mask.sum())
        n_avail = len(cand) - n_seen
        if n_avail <= 0:
            continue
        if policy == "mlde_ridge":
            ms = np.flatnonzero(mask)
            y = values[ms].astype(np.float64)
            ys = y.std()
            y = (y - y.mean()) / ys if ys > 0 else y - y.mean()
            X = ctx.design[ms].astype(np.float64)
            p = X.shape[1]
            # 真 ridge，λ = 1.0（无量纲：y 已标准化）；截距列不惩罚
            pen = np.eye(p, dtype=np.float64)
            pen[-1, -1] = 0.0
            A = X.T @ X + 1.0 * pen
            w = np.linalg.solve(A, X.T @ y)
            unseen = cand[~mask[cand]]
            pred = ctx.design[unseen].astype(np.float64) @ w
            k = min(b, len(unseen))
            if k >= len(unseen):
                pick = unseen
            else:
                # 并列时随机打破（C3b）：先按预测值降序，再在并列带内取随机 k 个
                order = np.argsort(-pred, kind="stable")
                thr = pred[order[k - 1]]
                tied = np.flatnonzero(pred >= thr)
                if len(tied) > k:
                    pick = unseen[rng.choice(tied, size=k, replace=False)]
                else:
                    pick = unseen[order[:k]]
        elif policy == "greedy_ssm":
            ms = np.flatnonzero(mask)
            best = int(ms[np.argmax(values[ms])])
            nb = ctx.neighbors[best]
            nb = nb[~mask[nb]]
            nb = nb[~np.isnan(values[nb])]
            if len(nb) == 0:
                pool = cand[~mask[cand]]
                pick = rng.choice(pool, size=min(b, len(pool)), replace=False) if len(pool) else nb
            elif len(nb) <= b:
                pick = nb
            else:
                pick = rng.choice(nb, size=b, replace=False)
        else:  # random
            pool = cand[~mask[cand]]
            pick = rng.choice(pool, size=min(b, len(pool)), replace=False) if len(pool) else pool
        mask[pick] = True
    return float(np.max(values[mask]))


def utility_from_values(values: np.ndarray, scale: str = "q05q95",
                        ref: Optional[Sequence[float]] = None):
    """OP-12（§3.3，无 dead 锚点 landscape）：返回 (u, q05, q95)。

    **冻结公式没有 clip**（AMENDMENT-013 §1）：
        u_τ(z) = (z − q05) / (q95 − q05)
    分位数在**该景观实测 informative 分布**上定义，且 `u` 与候选 x 无关（DECISION §2.4 不变量 1）。

    `scale="scale2max"` 为 §3.3 的敏感性尺度：`u(z) = z / max`。
    """
    if ref is None:
        v = values[~np.isnan(values)]
        if v.size == 0:
            raise ValueError("no informative values")
        q05, q95 = float(np.percentile(v, 5)), float(np.percentile(v, 95))
    else:
        q05, q95 = float(ref[0]), float(ref[1])
    if q95 <= q05:
        raise ValueError("degenerate utility scale: q95 <= q05")
    vmax = float(np.nanmax(values)) if ref is None else float(ref[2])

    if scale == "q05q95":
        def u(z):
            return float((z - q05) / (q95 - q05))       # 无 clip（AMENDMENT-013 §1）
    elif scale == "scale2max":
        def u(z):
            return float(z / vmax)
    else:
        raise ValueError("unknown scale %r" % (scale,))
    return u, q05, q95
