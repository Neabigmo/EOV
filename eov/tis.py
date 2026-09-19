"""`TIS`（Today Information Set）—— 满足 `PHASE1_PROTOCOL.md` **L39** 的接口级隔离。

冻结原文（L39）：

> TIS 的构造代码必须放在 `eov/` 下并被 `experiments/` 引用；所有特征函数签名只接受 `τ₀` 数据对象，
> **在类型/接口层面就无法访问 `τ`**。

## 为什么需要这个类（独立审计 S-4/S-5 的结论）

M4 首轮**没有**满足 L39：
- **exp3**：`arrs` 字典里只有 AMP 键，写 AZT 键会立刻 `KeyError` → **数据层满足**，但**类型层不满足**
  （`feats_for(today_keys, P)` 接受的是**调用方给的键列表**，调错就穿透）。
- **exp2**：`arrs` 里有 **8 个键、其中 2 个是 AZT** → **连数据层都不满足**，保护纯靠编程纪律。

## 本类如何从**结构上**封死

1. `TIS.from_arrays(arrs, allowed_keys, ...)` —— 构造时**拒绝**任何不在 `allowed_keys` 里的键。
2. `TIS.value(key)` —— 只暴露白名单内的键，其余一律 `KeyError`。
3. 特征只由 `TIS.features(parents)` 产出；**函数签名只接受 `TIS` 实例**，
   调用方**没有任何途径**把 future 数组塞进来（连键名都传不进去）。

→ 于是"访问 τ"不再依赖纪律，而是**需要绕过类本身**（改代码、或伪造 TIS 实例）才能做到。
   这是 L39 所要求的层级。

## L39 合规的证据

`tests/test_tis.py` 里有两类断言：
- **拒绝测试**：用含 AZT 键的输入构造 → 必须 `raise`；
- **逐位复现测试**：用 `TIS` 重建 8 个 Day-0 特征，与 `M4_EXP2_V.npz` 里落盘的 `feat_*`
  **逐位比对**（`max|diff| == 0`）。后者是最强的一类证据 —— 它同时证明
  "重构没有改变任何数值"与"特征确实只依赖 τ₀"。
"""
from __future__ import annotations

import warnings

import numpy as np

TODAY_CONDITIONS_DEFAULT = ("0.0", "3.1", "12.2", "48.8", "195.0", "781.0")
FEATURE_NAMES = ("current_fitness", "known_family_mean", "known_family_worst",
                 "local_robustness", "neighbor_informative_frac", "dist_to_best",
                 "n_better_neighbors", "local_ruggedness")

# ---------------------------------------------------------------------------
# **τ₀ 的唯一权威定义**。只有改这个文件才能改变"今天"包含什么 —— 这正是 L39 的要点。
# 各实验的 TIS_MANIFEST.json 必须与本表一致（核验器逐条比对）。
# ---------------------------------------------------------------------------
TODAY_SPEC = {
    "TEM-1CML": {
        "allowed": tuple(("AMP", c) for c in TODAY_CONDITIONS_DEFAULT),
        "primary": ("AMP", "781.0"),
        "future": (("AZT", "0.44"), ("AZT", "36.0")),
    },
    "Phillips2023_HA_CH65": {
        # Exp 1 不做跨任务预测，故它的"今天"是**逐任务**的；
        # 这里登记的是其主分析任务（其余两个任务在 Exp 1 内各自独立分析，不构成预测侧）。
        "allowed": (("MA90", "default"),),
        "primary": ("MA90", "default"),
        "future": (("SI06", "default"), ("G189E", "default")),
    },
}


class TISViolation(RuntimeError):
    """试图把一个不属于 τ₀ 的对象放进 TIS。"""


class TIS:
    """只装 `τ₀`（今天）测量的容器。**类型层面无法访问 `τ`。**

    只应由 `TIS.for_dataset(...)` 构造 —— τ₀ 的定义**硬编码在本模块内**，
    调用方**没有任何参数**可以往里加键。这正是 L39 要求的"接口层面无法访问 τ"。
    """

    __slots__ = ("_values", "_allowed", "_order", "_primary", "_ctx", "_space", "_u", "_n")

    def __init__(self, values, allowed, primary, ctx, space):
        # 硬断言：任何不在白名单里的键都不许进来
        stray = [k for k in values if k not in allowed]
        if stray:
            raise TISViolation(
                "TIS 只能装 τ₀ 的键；以下键不在白名单内：%r（白名单 %r）" % (stray, sorted(allowed)))
        missing = [k for k in allowed if k not in values]
        if missing:
            raise TISViolation("TIS 缺少白名单内的键：%r" % (missing,))
        if primary not in allowed:
            raise TISViolation("primary %r 不在白名单内" % (primary,))
        self._values = {k: values[k] for k in allowed}
        self._allowed = frozenset(allowed)
        # ⚠️ **迭代顺序必须显式保存**：frozenset 的迭代顺序是任意的，
        #    若用它建 S 矩阵，`np.nanmean` 的累加次序会变 → 与落盘值差 1 ULP
        #    （本项目的 `feats` 用 `[us[k](z) for z in ...]` 建行，行序 = TODAY_CONDITIONS 的顺序）。
        #    这类"顺序依赖"在本项目已出现过一次（informative 曾用首个重复算出 → schema v1.3）。
        self._order = tuple(allowed)
        self._primary = primary
        self._ctx = ctx
        self._space = space
        # u_τ 的分位数**只在该任务自己的 informative 分布上**定义（OP-12）
        self._u = {}
        for k in allowed:
            v = self._values[k]
            vv = v[~np.isnan(v)]
            if vv.size == 0:
                raise TISViolation("白名单内的键 %r 没有任何 informative 值 —— 无法定义 u_τ" % (k,))
            q05, q95 = float(np.percentile(vv, 5)), float(np.percentile(vv, 95))
            self._u[k] = (q05, q95)
        self._n = space.space_size()

    # ---- 构造器 ---------------------------------------------------------
    @classmethod
    def for_dataset(cls, dataset_id, arrs, ctx, space):
        """**唯一**的公开构造入口。τ₀ 白名单由本模块的 `TODAY_SPEC` 决定。

        调用方只能提供 `arrs` 这一份数据映射；**没有任何参数可以扩大白名单** ——
        即使 `arrs` 里含 future 键，它们也会被丢弃（并在 `strict=True` 时报错）。
        """
        if dataset_id not in TODAY_SPEC:
            raise TISViolation("未知数据集 %r；已在 eov/tis.py 登记的 τ₀ 规格：%r"
                               % (dataset_id, sorted(TODAY_SPEC)))
        spec = TODAY_SPEC[dataset_id]
        allowed = list(spec["allowed"])
        picked = {}
        for k in allowed:
            if k not in arrs:
                raise TISViolation("arrs 缺少 τ₀ 白名单内的键 %r" % (k,))
            v = arrs[k]
            picked[k] = v[0] if isinstance(v, tuple) else v
        return cls(picked, allowed, spec["primary"], ctx, space)

    @classmethod
    def _from_arrays_unchecked(cls, arrs, allowed_keys, primary, ctx, space):
        """仅供测试构造非法实例用（生产路径不得调用）。"""
        picked = {}
        for k, v in arrs.items():
            if k in allowed_keys:
                picked[k] = v[0] if isinstance(v, tuple) else v
        return cls(picked, allowed_keys, primary, ctx, space)

    # ---- 只读访问（白名单外一律拒绝）------------------------------------
    @property
    def allowed_keys(self):
        return tuple(sorted(self._allowed))

    @property
    def order(self):
        """白名单的**显式迭代顺序**。S 矩阵的行序必须用它 —— 用 frozenset 会改变
        `np.nanmean` 的累加次序，进而与落盘值差 1 ULP（已由 `test_tis.py` 抓到）。"""
        return self._order

    @property
    def primary(self):
        return self._primary

    def without(self, key):
        """返回**去掉** `key` 之后的新 TIS（供 Exp 3-S1 的 leave-one-concentration-out）。

        结果仍在白名单**之内**，故不会扩大对 τ 的访问面。
        """
        if key not in self._allowed:
            raise TISViolation("without(%r)：该键不在 τ₀ 白名单内" % (key,))
        if key == self._primary:
            raise TISViolation("without(%r)：不能去掉 primary" % (key,))
        keep = [k for k in self._order if k != key]
        if len(keep) < 2:
            raise TISViolation("without(%r)：剩余键不足 2 个" % (key,))
        return TIS({k: self._values[k] for k in keep}, keep,
                   self._primary, self._ctx, self._space)

    def value(self, key):
        if key not in self._allowed:
            raise TISViolation("TIS 拒绝访问 %r：它不在 τ₀ 白名单 %r 内" % (key, sorted(self._allowed)))
        return self._values[key]

    def u(self, key, z):
        if key not in self._allowed:
            raise TISViolation("TIS 拒绝访问 %r" % (key,))
        q05, q95 = self._u[key]
        return (z - q05) / (q95 - q05)

    def _u_scan(self, key):
        """逐元素（标量）u 变换。

        与 `u()` 数学上等价，但**浮点路径不同**：`u()` 走 numpy 向量化，本方法走 Python 标量。
        两者可差 1 ULP。`exp2_baselines.py` 的 `fam_mean`/`fam_worst` 用的是标量路径，
        故这里必须同样用标量路径，才能与已落盘的 `feat_*` **逐位**一致（L39 证据要求 `max|diff| == 0`）。
        """
        v = self.value(key)
        q05, q95 = self._u[key]
        return np.where(np.isnan(v), np.nan, [(z - q05) / (q95 - q05) for z in v])

    # ---- 特征（唯一实现；签名只接受 TIS 实例）---------------------------
    def features(self, parents, ctx=None):
        """产出 8 个 Day-0 特征。**调用方无法传入任何 future 数组。**"""
        ctx = ctx if ctx is not None else self._ctx
        space = self._space
        P = np.asarray(parents)
        vp = self.value(self._primary)
        has = ~np.isnan(vp)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            S = np.vstack([self._u_scan(k) for k in self._order])
            fam_mean = np.nanmean(S, axis=0)
            fam_worst = np.nanmin(S, axis=0)
        n_inf = np.zeros(self._n, dtype=np.int64)
        mean_nb = np.full(self._n, np.nan)
        n_bet = np.zeros(self._n, dtype=np.int64)
        n_wor = np.zeros(self._n, dtype=np.int64)
        for i in range(self._n):
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
        return {
            "current_fitness": np.array([self.u(self._primary, vp[x]) for x in P]),
            "known_family_mean": fam_mean[P],
            "known_family_worst": fam_worst[P],
            "local_robustness": np.array([self.u(self._primary, mean_nb[x])
                                          if not np.isnan(mean_nb[x]) else np.nan for x in P]),
            "neighbor_informative_frac": n_inf[P] / float(space.degree_topology()),
            "dist_to_best": -dist[P].astype(float),
            "n_better_neighbors": -n_bet[P].astype(float),
            "local_ruggedness": np.array([(n_wor[x] / n_inf[x]) if n_inf[x] > 0 else np.nan
                                          for x in P]),
        }
