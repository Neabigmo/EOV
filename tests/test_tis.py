"""`eov/tis.py` 的合规测试 —— 即 **`PHASE1_PROTOCOL.md` L39 的合规证据**。

两类断言：
  T1 **拒绝测试**：含 future（AZT）键的输入必须导致构造失败；白名单外的访问必须被拒。
  T2 **逐位复现测试**（最强的一类）：用 `TIS` 重建 8 个 Day-0 特征，与
     `data/processed/M4_EXP2_V.npz` 里**已落盘**的 `feat_*` 逐位比对，要求 `max|diff| == 0`。
     —— 它同时证明"重构没有改变任何数值"与"特征确实只依赖 τ₀"。
"""
from __future__ import annotations

import os
import sys

import warnings

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "eov"))

from landscape import MixedAlphabetSpace  # noqa: E402
from search_sim import make_context  # noqa: E402
from tis import (FEATURE_NAMES, TIS, TISViolation,  # noqa: E402
                 TODAY_CONDITIONS_DEFAULT)

DS = "TEM-1CML"
TODAY_PRIMARY = ("AMP", "781.0")


def _load():
    df = pd.read_parquet(os.path.join(ROOT, "data", "processed", "M2_measurements.parquet"))
    df = df[df.dataset_id == DS]
    ids = sorted(set(df.genotype_id.astype(str).unique()))
    space = MixedAlphabetSpace.from_masked_profiles([s for s in ids if "X" not in s])
    ctx = make_context(space)
    arrs = {}
    for c in TODAY_CONDITIONS_DEFAULT:
        s = df[(df.task_id == "AMP") & (df.condition_id == c)]
        # 死哨兵 `XXXXXXXXXXXXX` 不属于乘积空间（不是替换），按 v1.4 语义排除
        s = s[~s.genotype_id.astype(str).str.contains("X", regex=False)]
        v = np.full(space.space_size(), np.nan)
        idx = np.array([space.index_of(tuple(x)) for x in s.genotype_id.astype(str)], dtype=np.int64)
        ok = s.informative.astype(bool).values
        v[idx[ok]] = pd.to_numeric(s.value_group, errors="coerce").values[ok]
        arrs[("AMP", c)] = (v, None, None)
    # 故意加入 future 键（给真实值，使测试针对"白名单拒绝"而非"NaN 退化"）—— 验证 TIS 会拒绝
    for c in ("0.44", "36.0"):
        w = arrs[("AMP", "781.0")][0].copy()
        w[~np.isnan(w)] += 0.5
        arrs[("AZT", c)] = (w, None, None)
    return arrs, space, ctx


# --------------------------------------------------------------------- T1
def test_tis_rejects_future_keys():
    arrs, space, ctx = _load()
    allowed = [("AMP", c) for c in TODAY_CONDITIONS_DEFAULT]
    # 直接构造（绕过 for_dataset）才会出现 stray 键；这正是 __init__ 的纵深防御
    with pytest.raises(TISViolation) as e:
        TIS({k: v[0] for k, v in arrs.items()}, allowed=allowed,
            primary=TODAY_PRIMARY, ctx=ctx, space=space)
    assert "AZT" in str(e.value)


def test_tis_accepts_only_amp_when_narrowed():
    arrs, space, ctx = _load()
    allowed = [("AMP", c) for c in TODAY_CONDITIONS_DEFAULT]
    tis = TIS.for_dataset(DS, arrs, ctx, space)
    assert all(k[0] == "AMP" for k in tis.allowed_keys)
    with pytest.raises(TISViolation):
        tis.value(("AZT", "0.44"))
    with pytest.raises(TISViolation):
        tis.u(("AZT", "36.0"), 1.0)


def test_tis_rejects_missing_whitelisted_key():
    arrs, space, ctx = _load()
    allowed = [("AMP", c) for c in TODAY_CONDITIONS_DEFAULT]
    partial = {k: v for k, v in arrs.items() if k != ("AMP", "0.0")}
    with pytest.raises(TISViolation):
        TIS.for_dataset(DS, partial, ctx, space)


def test_tis_rejects_primary_outside_whitelist():
    arrs, space, ctx = _load()
    with pytest.raises(TISViolation):
        TIS.for_dataset("NOT_A_REGISTERED_DATASET", arrs, ctx, space)


# --------------------------------------------------------------------- T2
def test_features_reproduce_persisted_bit_exactly():
    """**L39 的核心证据**：TIS 重建的特征必须与已落盘的 `feat_*` 逐位相同。"""
    npz = os.path.join(ROOT, "data", "processed", "M4_EXP2_V.npz")
    if not os.path.exists(npz):
        pytest.skip("缺少 %s" % npz)
    d = np.load(npz)
    parents = d["parents"]
    arrs, space, ctx = _load()
    tis = TIS.for_dataset(DS, arrs, ctx, space)
    got = tis.features(parents, ctx=ctx)
    assert set(got) == set(FEATURE_NAMES)
    worst = 0.0
    for name in FEATURE_NAMES:
        want = d["feat_" + name]
        a, b = got[name], want
        both_nan = np.isnan(a) & np.isnan(b)
        diff = np.where(both_nan, 0.0, np.abs(np.nan_to_num(a, nan=0.0) - np.nan_to_num(b, nan=0.0)))
        worst = max(worst, float(np.max(diff)))
    assert worst == 0.0, "TIS 重建的特征与落盘值不符：max|diff| = %r" % worst


def test_tis_never_sees_azt_rows():
    """结构性证明：即使把 AZT 行以 NaN 之外的值塞进输入，只要不在白名单里就无法进入特征。"""
    arrs, space, ctx = _load()
    allowed = [("AMP", c) for c in TODAY_CONDITIONS_DEFAULT]
    a1 = TIS.for_dataset(DS, arrs, ctx, space)
    # 把 AZT 数组换成全 999（若被读入必然改变结果）
    arrs2 = dict(arrs)
    for c in ("0.44", "36.0"):
        arrs2[("AZT", c)] = (np.full(space.space_size(), 999.0), None, None)
    a2 = TIS.for_dataset(DS, arrs2, ctx, space)
    p = np.sort(np.random.default_rng(0).choice(
        np.flatnonzero(~np.isnan(a1.value(TODAY_PRIMARY))), 50, replace=False))
    f1, f2 = a1.features(p, ctx=ctx), a2.features(p, ctx=ctx)
    for k in FEATURE_NAMES:
        assert np.array_equal(f1[k], f2[k], equal_nan=True), k


# --------------------------------------------------------------------- T3
def _legacy_exp3_feats_for(arrs, us, ctx, space, today_keys, P):
    """**逐字复刻** Exp 3 迁移前的 `feats_for`（旧版）。

    注意它用的是**向量化** u 变换 `(v - q05)/(q95 - q05)`，而 exp2 的 `feats` 用的是**标量** lambda ——
    两者可差 1 ULP。该差异在迁移前就已存在，不是迁移引入的。
    """

    def uv(v, key):
        vv = v[~np.isnan(v)]
        q05, q95 = float(np.percentile(vv, 5)), float(np.percentile(vv, 95))
        return np.where(np.isnan(v), np.nan, (v - q05) / (q95 - q05))

    vp = arrs[TODAY_PRIMARY]
    has = ~np.isnan(vp)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        S = np.vstack([uv(arrs[k], k) for k in today_keys])
        fam_mean = np.nanmean(S, axis=0)
        fam_worst = np.nanmin(S, axis=0)
    n = vp.size
    n_inf = np.zeros(n, dtype=np.int64)
    mean_nb = np.full(n, np.nan)
    n_bet = np.zeros(n, dtype=np.int64)
    n_wor = np.zeros(n, dtype=np.int64)
    for i in range(n):
        nb = ctx.neighbors[i]
        ok = has[nb]
        n_inf[i] = int(ok.sum())
        if ok.any():
            vals = vp[nb[ok]]
            mean_nb[i] = float(np.mean(vals))
            if not np.isnan(vp[i]):
                n_bet[i] = int((vals > vp[i]).sum())
                n_wor[i] = int((vals < vp[i]).sum())
    pool = np.flatnonzero(has)
    ab = int(pool[np.argmax(vp[pool])])
    dist = (ctx.codes != ctx.codes[ab]).sum(axis=1)
    u_today = us[TODAY_PRIMARY]
    return {
        "current_fitness": np.array([u_today(vp[x]) for x in P]),
        "known_family_mean": fam_mean[P], "known_family_worst": fam_worst[P],
        "local_robustness": np.array([u_today(mean_nb[x]) if not np.isnan(mean_nb[x])
                                      else np.nan for x in P]),
        "neighbor_informative_frac": n_inf[P] / float(space.degree_topology()),
        "dist_to_best": -dist[P].astype(float),
        "n_better_neighbors": -n_bet[P].astype(float),
        "local_ruggedness": np.array([(n_wor[x] / n_inf[x]) if n_inf[x] > 0 else np.nan
                                      for x in P]),
    }


def test_migration_to_tis_is_numerically_inert():
    """T3：迁移到 `TIS` 后，特征与迁移前**至多差 ULP 级**，且不改变任何决策相关量。

    逐个 leave-one-concentration-out 变体都查（Exp 3-S1 用的正是这些）。
    """
    arrs, space, ctx = _load()
    # _load 的 value 是 (arr, None, None) 形式，这里统一成裸数组
    arrs_v = {k: (v[0] if isinstance(v, tuple) else v) for k, v in arrs.items()}

    def mk_u(v):
        vv = v[~np.isnan(v)]
        q05, q95 = float(np.percentile(vv, 5)), float(np.percentile(vv, 95))
        return lambda z: float((z - q05) / (q95 - q05))
    us = {k: mk_u(v) for k, v in arrs_v.items()}
    tis = TIS.for_dataset(DS, arrs_v, ctx, space)

    P = np.sort(np.random.default_rng(1).choice(
        np.flatnonzero(~np.isnan(arrs_v[TODAY_PRIMARY])), 300, replace=False))
    worst = 0.0
    for hold in TODAY_CONDITIONS_DEFAULT:
        if hold == "781.0":
            continue
        keys = [("AMP", c) for c in TODAY_CONDITIONS_DEFAULT if c != hold]
        legacy = _legacy_exp3_feats_for(arrs_v, us, ctx, space, keys, P)
        new = tis.without(("AMP", hold)).features(P, ctx=ctx)
        for k in FEATURE_NAMES:
            a, b = new[k], legacy[k]
            both = np.isnan(a) & np.isnan(b)
            d = np.where(both, 0.0,
                         np.abs(np.nan_to_num(a, nan=0.0) - np.nan_to_num(b, nan=0.0)))
            worst = max(worst, float(np.max(d)))
            fa, fl = np.isfinite(a), np.isfinite(b)
            assert np.array_equal(fa, fl), (hold, k, "finite 集合不同")
            assert np.argmax(a[fa]) == np.argmax(b[fl]), (hold, k, "argmax 改变")
    assert worst < 1e-12, "迁移引入了超过 ULP 级的差异：max|diff| = %r" % worst
