"""M4 / Exp 1 —— Phillips2023 的 parent-level V_{B,pi}(x,tau)：跨预算与跨任务稳定性。

这是"生死第一图"：如果 parent 的价值排序在不同预算/不同任务下随机，task-general EOV 不成立。

**策略实现一律调用 `eov/search_sim.py`（唯一实现）**；本文件不复制任何策略代码。

尺度（AMENDMENT-013）
---------------------
Phillips2023 三个任务都**没有** `X...X` dead 行 → `anchor_resolvability = NaN` → 按
PROTOCOL §3.3 用 OP-12：`u_τ(z) = (z − q05)/(q95 − q05)`，**无 clip**。同时报 `scale2max` 敏感性。

口径
----
OP-1  预算 B = 被 assay 的 unique 基因型数；起点不计入 B；3 轮 schedule 见 search_sim
OP-2  预算档位 B in {24, 96, 384}
OP-21 B <= |space|/4 = 16384
R_{B,pi}(x,tau) = max over 被测集合（含起点）的 value_group；V = u_tau(R)

本脚本**不含** EOV 预测模型、不含 baseline ladder、不含 regret 选择器（那是 Exp 2/3）。
"""
from __future__ import annotations

import csv
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from search_sim import (BUDGETS, POLICIES, Scratch, make_context,  # noqa: E402
                        simulate_search, utility_from_values)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
OUT = os.path.join(ROOT, "results", "tables", "M4_EXP1_STABILITY.csv")
OUT_RAW = os.path.join(ROOT, "data_registry", "M4_EXP1_RAW_V.csv")
NPZ = os.path.join(ROOT, "data", "processed", "M4_EXP1_V.npz")

DS = "Phillips2023_HA_CH65"
TASKS = ["MA90", "SI06", "G189E"]
N_PARENTS = 1000
SEED = 20260919
N_BITS = 16


def main() -> int:
    from landscape import MixedAlphabetSpace
    t0 = time.time()
    df = pd.read_parquet(MEAS)[lambda d: d.dataset_id == DS]
    raw = {}
    for t in TASKS:
        s = df[df.task_id == t]
        # fail-loud：value_group 必须逐 (genotype, condition) 恒定，否则 last-wins 赋值是静默错误
        nun = s.groupby(["genotype_id", "condition_id"]).value_group.nunique(dropna=False)
        assert int((nun > 1).sum()) == 0, "value_group varies within (genotype, condition) for %s" % t
        # fail-loud：informative 是 v1.4 冻结判据，**不得**由 value_group 非空重新推导
        bad = int((s.informative.astype(bool) &
                   (s.at_inferred_floor.astype(bool) |
                    (s.measurement_state.astype(str) != "exact"))).sum())
        assert bad == 0, "%s: %d informative rows violate the v1.4 contract" % (t, bad)
        v = np.full(1 << N_BITS, np.nan)
        gi = np.array([int(x, 2) for x in s.genotype_id.astype(str)], dtype=np.int64)
        ok = s.informative.astype(bool).values
        v[gi[ok]] = pd.to_numeric(s.value_group, errors="coerce").values[ok]
        raw[t] = v
    space = MixedAlphabetSpace.from_masked_profiles(
        [format(i, "0%db" % N_BITS) for i in range(1 << N_BITS)])
    assert space.space_size() == (1 << N_BITS) and space.degree_topology() == N_BITS
    ctx = make_context(space)
    scratch = Scratch(1 << N_BITS)
    rng = np.random.default_rng(SEED)

    us, sus = {}, {}
    for t in TASKS:
        us[t], q05, q95 = utility_from_values(raw[t], scale="q05q95")
        sus[t], _, _ = utility_from_values(raw[t], scale="scale2max")
        print("%-6s informative=%d  q05=%.4f q95=%.4f  max=%.4f  (无 clip)" % (
            t, int((~np.isnan(raw[t])).sum()), q05, q95, np.nanmax(raw[t])), flush=True)

    cand = np.flatnonzero(~np.isnan(raw[TASKS[0]]))
    print("候选池（MA90 informative）= %d" % len(cand), flush=True)
    parents = np.sort(rng.choice(cand, size=min(N_PARENTS, len(cand)), replace=False))
    print("parent 样本 = %d（seed=%d）" % (len(parents), SEED), flush=True)

    V = np.full((len(POLICIES), len(BUDGETS), len(TASKS), len(parents)), np.nan)
    Vs = np.full_like(V, np.nan)
    Rraw = np.full_like(V, np.nan)
    R0 = np.full((len(TASKS), len(parents)), np.nan)
    for ti, t in enumerate(TASKS):
        a = raw[t]
        # fail-loud：候选池必须**逐任务**取该任务的 informative 集合；
        # 用别的任务的池会让 random/MLDE 挑到 NaN 值并静默毁掉整格结果。
        cand_t = np.flatnonzero(~np.isnan(a))
        for pi, p in enumerate(parents):
            if not np.isnan(a[p]):
                R0[ti, pi] = us[t](a[p])
        for si, pol in enumerate(POLICIES):
            for bi, B in enumerate(BUDGETS):
                for pi, p in enumerate(parents):
                    r = simulate_search(ctx, int(p), a, cand_t, pol, B, rng, scratch)
                    if np.isnan(r):
                        continue
                    Rraw[si, bi, ti, pi] = r
                    V[si, bi, ti, pi] = us[t](r)
                    Vs[si, bi, ti, pi] = sus[t](r)
        print("  task %-6s done  cand=%d 可评估 parents=%d  (%.0f s)" % (
            t, len(cand_t), int((~np.isnan(a[parents])).sum()), time.time() - t0), flush=True)
    np.savez_compressed(NPZ, V=V, Vs=Vs, Rraw=Rraw, R0=R0, parents=parents,
                        policies=np.array(POLICIES), budgets=np.array(BUDGETS),
                        tasks=np.array(TASKS))

    # ---------------- 分布诊断（先看有没有退化）----------------
    print()
    print("=== V 分布诊断（frac_eq_max = 该档位 V 已达到本档位最大值的比例）===")
    for si, pol in enumerate(POLICIES):
        for bi, B in enumerate(BUDGETS):
            for ti, t in enumerate(TASKS):
                v = V[si, bi, ti]
                v = v[~np.isnan(v)]
                if v.size == 0:
                    print("  %-11s B%-4d %-6s 全部 NaN" % (pol, B, t))
                    continue
                print("  %-11s B%-4d %-6s n=%4d mean=%.4f sd=%.4f range=[%.4f, %.4f]" % (
                    pol, B, t, v.size, v.mean(), v.std(), v.min(), v.max()), flush=True)

    def spearman(a, b):
        if np.all(a == a[0]) or np.all(b == b[0]):
            return float("nan")
        ra = pd.Series(a).rank().values
        rb = pd.Series(b).rank().values
        ra = ra - ra.mean(); rb = rb - rb.mean()
        d = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
        return float((ra * rb).sum() / d) if d > 0 else float("nan")

    rows = []
    rawrows = []

    def add(kind, a_name, b_name, rho, n, label, scale):
        rawrows.append(dict(kind=kind, a=a_name, b=b_name, label=label, scale=scale,
                            spearman="" if rho != rho else round(rho, 4), n=n,
                            verdict=("" if rho != rho else ("STABLE" if rho >= 0.7 else
                                                            ("MODERATE" if rho >= 0.4 else "UNSTABLE")))))

    for scale, arr in (("q05q95", V), ("scale2max", Vs)):
        if scale == "q05q95":
            print()
            print("=== 跨预算稳定性（同一任务、同一策略，不同 B）===")
        for si, pol in enumerate(POLICIES):
            for ti, t in enumerate(TASKS):
                for bi in range(len(BUDGETS)):
                    for bj in range(bi + 1, len(BUDGETS)):
                        a, b = arr[si, bi, ti], arr[si, bj, ti]
                        m = ~np.isnan(a) & ~np.isnan(b)
                        if m.sum() < 50:
                            continue
                        r = spearman(a[m], b[m])
                        add("cross_budget", "%s_B%d" % (pol, BUDGETS[bi]), "%s_B%d" % (pol, BUDGETS[bj]),
                            r, int(m.sum()), t, scale)
                        if scale == "q05q95":
                            print("  %-11s %-6s B%-4d vs B%-4d  rho=%+.4f  n=%d" % (
                                pol, t, BUDGETS[bi], BUDGETS[bj], r, m.sum()), flush=True)
        if scale == "q05q95":
            print()
            print("=== 跨任务稳定性（同一预算、同一策略，不同任务）===")
        for si, pol in enumerate(POLICIES):
            for bi, B in enumerate(BUDGETS):
                for ti in range(len(TASKS)):
                    for tj in range(ti + 1, len(TASKS)):
                        a, b = arr[si, bi, ti], arr[si, bi, tj]
                        m = ~np.isnan(a) & ~np.isnan(b)
                        if m.sum() < 50:
                            continue
                        r = spearman(a[m], b[m])
                        add("cross_task", "%s_B%d" % (pol, B), "%s_B%d" % (pol, B),
                            r, int(m.sum()), "%s~%s" % (TASKS[ti], TASKS[tj]), scale)
                        if scale == "q05q95":
                            print("  %-11s B%-4d %-6s vs %-6s  rho=%+.4f  n=%d" % (
                                pol, B, TASKS[ti], TASKS[tj], r, m.sum()), flush=True)

    print()
    print("=== 参照：R_0（readiness，原始量纲）与 V 的关系（Spearman）===")
    for ti, t in enumerate(TASKS):
        for si, pol in enumerate(POLICIES):
            a, b = R0[ti], V[si, -1, ti]
            m = ~np.isnan(a) & ~np.isnan(b)
            if m.sum() < 50:
                continue
            print("  %-6s %-11s rho(R0, V_B384)=%+.4f" % (t, pol, spearman(a[m], b[m])), flush=True)

    # ---- H1 预备：效应/噪声比（**原始量纲**，AMENDMENT-013 §4.4）----
    print()
    print("=== H1 预备：可达值离散度 vs 测量噪声（原始量纲）===")
    noise = {t: float(np.nanmedian(df[df.task_id == t].value_sd.values)) for t in TASKS}
    for ti, t in enumerate(TASKS):
        for si, pol in enumerate(POLICIES):
            for bi, B in enumerate(BUDGETS):
                r = Rraw[si, bi, ti]
                r = r[~np.isnan(r)]
                if r.size < 50:
                    continue
                iqr = float(np.percentile(r, 75) - np.percentile(r, 25))
                print("  %-6s %-11s B%-4d IQR(R)=%.4f  2*noise=%.4f  ratio=%5.2f  H1(IQR>=2*noise)=%s" % (
                    t, pol, B, iqr, 2 * noise[t], iqr / (2 * noise[t]), iqr >= 2 * noise[t]),
                    flush=True)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["kind", "pair", "label", "spearman", "n", "verdict"])
        w.writeheader()
        for r in rawrows:
            if r["scale"] != "q05q95":
                continue
            w.writerow(dict(kind=r["kind"], pair="%s|%s" % (r["a"], r["b"]), label=r["label"],
                            spearman=r["spearman"], n=r["n"], verdict=r["verdict"]))
    with open(OUT_RAW, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["kind", "a", "b", "label", "scale", "spearman", "n", "verdict"])
        w.writeheader()
        for r in rawrows:
            w.writerow(r)
    print()
    print("WROTE", OUT)
    print("WROTE", OUT_RAW, len(rawrows), "rows")
    print("WROTE", NPZ)
    print("total %.0f s" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
