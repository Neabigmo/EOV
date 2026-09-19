"""`eov/search_sim.py` 的回归测试。

存在理由：Exp 1 / Exp 2 / Exp 3 的全部策略行为都**只**由该模块决定。任何静默分叉都会
同时污染三个实验，且不会报错——正是本项目反复遇到的失效模式（见 AMENDMENT-013 §3）。

覆盖：
  T1  budget_schedule 的不变式（OP-1）
  T2  混合字母表邻居表 ≡ `MixedAlphabetSpace.neighbors`
  T3  `ctx.codes` ↔ `space.node_from_index/index_of` 一致性
  T4  三种策略 vs **独立**的暴力参考实现（小空间，逐基因型）
  T5  OP-1 预算语义：新测基因型数 == B，起点不计入
  T6  C3b 回归：MLDE 在随机景观上不得退化为常数（并列必须随机打破）
  T7  C3a 回归：MLDE 在 n < p 时仍给出有限预测（真 ridge，不是秩亏 OLS）
  T8  C1 回归：OP-12 **无 clip**（u 可以 > 1）
  T9  仿射不变性：OP-12 与 scale2max 下 NR 恒等
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eov"))

from landscape import MixedAlphabetSpace  # noqa: E402
from search_sim import (BUDGETS, POLICIES, Scratch, budget_schedule,  # noqa: E402
                        make_context, simulate_search, utility_from_values)


# --------------------------------------------------------------------------- T1
@pytest.mark.parametrize("B", [1, 2, 3, 4, 5, 23, 24, 25, 96, 97, 384, 385])
def test_budget_schedule_invariants(B):
    b1, b2, b3 = budget_schedule(B)
    assert b1 + b2 + b3 == B
    assert b1 >= b2 >= b3 >= 0
    assert b1 == -(-B // 2)


def test_budget_schedule_rejects_nonpositive():
    with pytest.raises(ValueError):
        budget_schedule(0)
    with pytest.raises(ValueError):
        budget_schedule(-4)


# --------------------------------------------------------------------------- 小空间夹具
@pytest.fixture(scope="module")
def tiny():
    space = MixedAlphabetSpace([(".", "A"), (".", "B", "C")])
    ctx = make_context(space)
    return space, ctx


# --------------------------------------------------------------------------- T2
def test_neighbor_table_matches_space(tiny):
    space, ctx = tiny
    assert ctx.neighbors.shape == (space.space_size(), space.degree_topology())
    for i in range(space.space_size()):
        expected = {space.index_of(n) for n in space.neighbors(space.node_from_index(i))}
        got = set(ctx.neighbors[i].tolist())
        assert got == expected, (i, got, expected)


def test_neighbor_table_matches_space_tem1_like():
    """用一个 4x3x2 的混合空间再验一次（含 4 等位位点）。"""
    space = MixedAlphabetSpace([(".", "A", "B", "C"), (".", "D"), (".", "E")])
    ctx = make_context(space)
    assert space.space_size() == 16 and space.degree_topology() == 3 + 1 + 1
    for i in range(space.space_size()):
        expected = {space.index_of(n) for n in space.neighbors(space.node_from_index(i))}
        assert set(ctx.neighbors[i].tolist()) == expected


# --------------------------------------------------------------------------- T3
def test_codes_agree_with_index_of(tiny):
    space, ctx = tiny
    for i in range(space.space_size()):
        node = space.node_from_index(i)
        for pos in range(space.n_positions):
            assert ctx.codes[i, pos] == space.alleles_at(pos).index(node[pos])


def test_design_matrix_is_onehot_plus_intercept(tiny):
    space, ctx = tiny
    assert ctx.design.shape == (space.space_size(), sum(
        len(space.alleles_at(p)) for p in range(space.n_positions)) + 1)
    assert np.allclose(ctx.design[:, -1], 1.0)
    assert set(np.unique(ctx.design)) <= {0.0, 1.0}
    # 每个位点的哑变量之和恒为 1 → 与截距列线性相关（这正是 C3a 的秩亏来源）
    off = 0
    for pos in range(space.n_positions):
        k = len(space.alleles_at(pos))
        assert np.allclose(ctx.design[:, off:off + k].sum(axis=1), 1.0)
        off += k


# --------------------------------------------------------------------------- T4 参考实现
def _ref_simulate(space, ctx, start, values, cand, policy, budget, rng):
    """逐基因型暴力参考实现（与 search_sim 相互独立）。"""
    assayed = [start]
    seen = {start}
    for b in budget_schedule(budget):
        if b <= 0:
            continue
        if policy == "random":
            avail = [int(x) for x in cand if int(x) not in seen]
            k = min(b, len(avail))
            pick = list(rng.choice(np.array(avail), size=k, replace=False)) if k else []
        elif policy == "greedy_ssm":
            best = max(assayed, key=lambda i: values[i])
            nb = [j for j in ctx.neighbors[best].tolist()
                  if j not in seen and not np.isnan(values[j])]
            if not nb:
                avail = [int(x) for x in cand if int(x) not in seen]
                k = min(b, len(avail))
                pick = list(rng.choice(np.array(avail), size=k, replace=False)) if k else []
            elif len(nb) <= b:
                pick = nb
            else:
                pick = list(rng.choice(np.array(nb), size=b, replace=False))
        else:  # mlde_ridge —— 参考实现用独立的正规方程形式
            ms = np.array(sorted(seen))
            X = ctx.design[ms].astype(np.float64)
            y = values[ms].astype(np.float64)
            ys = y.std()
            y = (y - y.mean()) / ys if ys > 0 else y - y.mean()
            p = X.shape[1]
            pen = np.eye(p)
            pen[-1, -1] = 0.0
            w = np.linalg.solve(X.T @ X + pen, X.T @ y)
            avail = np.array([int(x) for x in cand if int(x) not in seen], dtype=np.int64)
            pred = ctx.design[avail].astype(np.float64) @ w
            k = min(b, len(avail))
            if k >= len(avail):
                pick = list(avail)
            else:
                order = np.argsort(-pred, kind="stable")
                thr = pred[order[k - 1]]
                tied = np.flatnonzero(pred >= thr)
                pick = (list(rng.choice(avail[tied], size=k, replace=False))
                        if len(tied) > k else list(avail[order[:k]]))
        for j in pick:
            seen.add(int(j))
            assayed.append(int(j))
    return float(np.max(values[list(seen)])), seen


@pytest.mark.parametrize("policy", POLICIES)
def test_policies_match_reference(tiny, policy):
    space, ctx = tiny
    rng = np.random.default_rng(12345)
    values = rng.normal(size=space.space_size())
    cand = np.arange(space.space_size())
    for start in range(space.space_size()):
        for B in (2, 4, 6):
            r1 = np.random.default_rng(999)
            got = simulate_search(ctx, start, values, cand, policy, B, r1, Scratch(space.space_size()))
            r2 = np.random.default_rng(999)
            want, _ = _ref_simulate(space, ctx, start, values, cand, policy, B, r2)
            assert got == pytest.approx(want), (policy, start, B)


# --------------------------------------------------------------------------- T5
@pytest.mark.parametrize("policy", POLICIES)
@pytest.mark.parametrize("B", BUDGETS)
def test_budget_semantics_counts_unique_genotypes(tiny, policy, B):
    space, ctx = tiny
    rng = np.random.default_rng(4)
    values = rng.normal(size=space.space_size())
    cand = np.arange(space.space_size())
    scratch = Scratch(space.space_size())
    simulate_search(ctx, 0, values, cand, policy, B, rng, scratch)
    # |space| = 6，故最多测到 1 + min(B, 5)
    assert int(scratch.mask.sum()) == 1 + min(B, space.space_size() - 1)


def test_start_is_counted_in_value_but_not_in_budget(tiny):
    space, ctx = tiny
    values = np.zeros(space.space_size())
    values[3] = 10.0            # 起点就是全局最优
    cand = np.arange(space.space_size())
    r = simulate_search(ctx, 3, values, cand, "random", 2,
                        np.random.default_rng(0), Scratch(space.space_size()))
    assert r == pytest.approx(10.0)


def test_nan_start_returns_nan(tiny):
    """起点在本任务不可测 → 返回 NaN（但 cand 本身必须合法）。"""
    space, ctx = tiny
    values = np.array([np.nan, 1.0, 2.0, 3.0, 4.0, 5.0])
    cand = np.array([1, 2, 3, 4, 5])
    assert np.isnan(simulate_search(ctx, 0, values, cand, "random", 2,
                                    np.random.default_rng(0), Scratch(space.space_size())))


def test_cand_with_nan_raises(tiny):
    """cand 含 NaN 值是**调用方错误**：random/MLDE 会挑到它，而 np.max 会被 NaN 吞掉整格。"""
    space, ctx = tiny
    values = np.array([0.0, np.nan, 2.0, 3.0, 4.0, 5.0])
    with pytest.raises(ValueError, match="non-informative"):
        simulate_search(ctx, 2, values, np.array([0, 1, 2, 3, 4, 5]), "random", 2,
                        np.random.default_rng(0), Scratch(space.space_size()))


# --------------------------------------------------------------------------- T6 C3b 回归
def test_mlde_does_not_degenerate_to_constant():
    """C3b：并列按索引序取 top-b 会让所有起点收敛到同一批基因型 → V 为常数。"""
    space = MixedAlphabetSpace([(".", "A"), (".", "B"), (".", "C")])
    ctx = make_context(space)
    rng = np.random.default_rng(7)
    values = rng.normal(size=space.space_size())
    cand = np.arange(space.space_size())
    scratch = Scratch(space.space_size())
    got = []
    for start in range(space.space_size()):
        got.append(simulate_search(ctx, start, values, cand, "mlde_ridge", 4,
                                   np.random.default_rng(1000 + start), scratch))
    assert len(set(np.round(got, 12))) > 1, "MLDE 退化：所有起点的 R 相同"


def test_mlde_ties_are_broken_randomly():
    """常数景观上所有预测并列 —— 必须由 rng 决定，而不是索引序。"""
    space = MixedAlphabetSpace([(".", "A"), (".", "B"), (".", "C")])
    ctx = make_context(space)
    values = np.zeros(space.space_size())
    cand = np.arange(space.space_size())
    scratch = Scratch(space.space_size())
    masks = set()
    for s in range(40):
        simulate_search(ctx, 0, values, cand, "mlde_ridge", 2,
                        np.random.default_rng(s), scratch)
        masks.add(tuple(np.flatnonzero(scratch.mask).tolist()))
    assert len(masks) > 1, "并列未被随机打破"


# --------------------------------------------------------------------------- T7 C3a 回归
def test_mlde_finite_when_n_less_than_p(tiny):
    """C3a：n=1 < p 时真 ridge 仍给出有限解（零正则 OLS 的 min-norm 解亦有限，但
    原实现还叠加了索引序并列，见 T6）。这里只断言不产生 NaN/inf。"""
    space, ctx = tiny
    values = np.array([0.0, 1.0, 2.0, 3.0, 4.0, np.nan])
    r = simulate_search(ctx, 0, values, np.array([0, 1, 2, 3, 4]), "mlde_ridge", 4,
                        np.random.default_rng(3), Scratch(space.space_size()))
    assert np.isfinite(r)


# --------------------------------------------------------------------------- T8 C1 回归
def test_op12_has_no_clip():
    values = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 100.0])
    u, q05, q95 = utility_from_values(values, scale="q05q95")
    assert u(100.0) > 1.0, "OP-12 被加了 clip —— 违反 AMENDMENT-013 §1"
    assert u(values.min()) < 0.0
    # 仿射且严格单调
    zs = np.linspace(0, 100, 50)
    us = np.array([u(z) for z in zs])
    assert np.all(np.diff(us) > 0)


def test_scale2max_is_also_monotone_and_unclipped():
    values = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
    u, _, _ = utility_from_values(values, scale="scale2max")
    assert u(5.0) == pytest.approx(1.0)
    assert u(-1.0) < 0.0


def test_utility_rejects_degenerate_scale():
    with pytest.raises(ValueError):
        utility_from_values(np.ones(10), scale="q05q95")
    with pytest.raises(ValueError):
        utility_from_values(np.arange(10.0), scale="nope")


# --------------------------------------------------------------------------- T9
def test_nr_is_invariant_under_affine_scales():
    """OP-12 与 scale2max 都是仿射 → NR = (V_o - V_s)/(V_o - V_rw) 恒等。"""
    rng = np.random.default_rng(2026)
    r = rng.normal(size=400) * 3 + 5
    u1, _, _ = utility_from_values(r, scale="q05q95")
    u2, _, _ = utility_from_values(r, scale="scale2max")
    v1 = np.array([u1(z) for z in r])
    v2 = np.array([u2(z) for z in r])
    for _ in range(20):
        i = rng.integers(0, len(r))
        o = float(np.max(v1)); rw = float(np.percentile(v1, 5))
        nr1 = (o - v1[i]) / (o - rw)
        o2 = float(np.max(v2)); rw2 = float(np.percentile(v2, 5))
        nr2 = (o2 - v2[i]) / (o2 - rw2)
        assert nr1 == pytest.approx(nr2, abs=1e-9)
    # 秩恒等
    assert np.array_equal(np.argsort(np.argsort(v1)), np.argsort(np.argsort(v2)))
