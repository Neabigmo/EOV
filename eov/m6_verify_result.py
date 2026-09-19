"""M6 结果独立核验器 —— 用**独立的代码路径**重算主判据，并核对 JSON 中的每个手抄数字。

独立性措施：
  * 不 import `m6_wu2020_run`；自行从 NPZ 重算
  * Spearman 用 `scipy` 而非 pandas rank（若 scipy 可用），否则用秩-协方差手写式
  * 退化格规则按 AMENDMENT-019 §2.1 独立重实现
  * 另附**标签置换零分布**（描述性，不参与判定；判定用 §3 的 bootstrap CI）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NPZ = ROOT / "data" / "processed" / "M6_WU2020_R.npz"
RES = ROOT / "data" / "manifests" / "M6_WU2020_RESULT.json"
MAP = ROOT / "results" / "tables" / "M6_WU2020_TRANSFER_MAP.csv"
POLICIES = ("random", "greedy_ssm", "mlde_ridge")
BUDGETS = (24, 96)
N_BOOT = 2000
BOOT_SEED = 20260919 + 7
PERM_SEED = 20260919 + 13
N_PERM = 20000

F: list[tuple[str, object, object]] = []


def ck(label, got, want):
    F.append((label, got, want))


def rank(x):
    """平均秩（与 scipy.stats.rankdata 的默认 'average' 一致）。"""
    x = np.asarray(x, float)
    order = np.argsort(x, kind="mergesort")
    r = np.empty(len(x), float)
    sx = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sx[j + 1] == sx[i]:
            j += 1
        r[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return r


def spear(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ok = ~np.isnan(a) & ~np.isnan(b)
    if ok.sum() < 3:
        return float("nan")
    ra, rb = rank(a[ok]), rank(b[ok])
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(((ra - ra.mean()) * (rb - rb.mean())).mean()
                 / (ra.std() * rb.std()))


def u_q05q95(z):
    """OP-12 无 clip，独立重实现。"""
    z = np.asarray(z, float)
    q05, q95 = np.percentile(z, 5), np.percentile(z, 95)
    if q95 <= q05:
        raise ValueError("degenerate")
    return (z - q05) / (q95 - q05)


def main() -> int:
    d = np.load(NPZ, allow_pickle=True)
    R = d["R"]
    tasks = [str(x) for x in d["tasks"]]
    vals = {t: d["vals_" + t] for t in tasks}
    res = json.loads(RES.read_text(encoding="utf-8"))

    ck("R shape", list(R.shape), [3, 2, 6, 576])
    ck("n tasks", len(tasks), 6)
    ck("task list", tasks, ["Bei89", "Bk79", "Bris07", "HK68", "Mos99", "NDako16"])
    ck("budgets", res["budgets"], [24, 96])
    ck("coverage B=24", res["coverage"]["24"], round(24 / 576, 4))
    ck("coverage B=96", res["coverage"]["96"], round(96 / 576, 4))
    ck("degree", res["degree"], 12)
    ck("states", res["states_per_position"], [4, 4, 3, 2, 3, 2])

    # ---- 独立重算 f1 与 pair 级 rho_rank ----
    f1s, rhos, used_counts = {}, {}, {}
    n_deg = 0
    for i in range(len(tasks)):
        for j in range(i + 1, len(tasks)):
            A, B = tasks[i], tasks[j]
            va, vb = vals[A], vals[B]
            m = ~np.isnan(va) & ~np.isnan(vb)
            f1s[(A, B)] = spear(va[m], vb[m])
            cells = []
            for si, _pol in enumerate(POLICIES):
                for bi, _B in enumerate(BUDGETS):
                    ra, rb = R[si, bi, i], R[si, bi, j]
                    mm = ~np.isnan(ra) & ~np.isnan(rb)
                    if mm.sum() < 50:
                        continue
                    xa, xb = ra[mm], rb[mm]
                    if (np.percentile(xa, 95) <= np.percentile(xa, 5)
                            or np.percentile(xb, 95) <= np.percentile(xb, 5)):
                        n_deg += 1
                        continue
                    cells.append(spear(u_q05q95(xa), u_q05q95(xb)))
            rhos[(A, B)] = float(np.mean(cells)) if cells else float("nan")
            used_counts[(A, B)] = len(cells)

    pa = np.array([f1s[k] for k in f1s]); pr = np.array([rhos[k] for k in f1s])
    stat = spear(pa, pr)
    ck("n_pairs", len(pa), 15)
    ck("degenerate cells", n_deg, 15)
    ck("PRIMARY spearman(f1, rho)", round(stat, 6), res["spearman_f1_vs_rho"])
    ck("median f1", round(float(np.median(pa)), 6), round(res["median_f1"], 6))
    ck("median rho (pair level)", round(float(np.median(pr)), 6),
       round(res["median_rho_rank_pair_level"], 6))
    ck("f1 min", round(float(pa.min()), 4), round(min(res["f1"].values()), 4))
    ck("f1 max", round(float(pa.max()), 4), round(max(res["f1"].values()), 4))
    ck("rho min", round(float(pr.min()), 4), round(min(res["rho_pair_level"].values()), 4))
    ck("rho max", round(float(pr.max()), 4), round(max(res["rho_pair_level"].values()), 4))

    # 逐对核验 JSON
    for k in f1s:
        key = "%s~%s" % k
        ck("f1[%s]" % key, round(f1s[k], 6), res["f1"][key])
        ck("rho[%s]" % key, round(rhos[k], 6), res["rho_pair_level"][key])

    # ---- bootstrap CI 复现 ----
    rng = np.random.default_rng(BOOT_SEED)
    n = len(pa); boot = np.empty(N_BOOT)
    for b in range(N_BOOT):
        s = rng.integers(0, n, n)
        boot[b] = spear(pa[s], pr[s])
    lo, hi = np.nanpercentile(boot, [2.5, 97.5])
    ck("boot lo", round(float(lo), 6), res["boot_ci"][0])
    ck("boot hi", round(float(hi), 6), res["boot_ci"][1])
    ck("CI excludes 0", bool(lo > 0), True)
    ck("threshold met", bool(stat >= 0.45 and lo > 0), True)
    ck("verdict", res["verdict"], "CONFIRMED")

    # ---- 标签置换零分布（描述性，不参与判定） ----
    prng = np.random.default_rng(PERM_SEED)
    null = np.empty(N_PERM)
    for b in range(N_PERM):
        null[b] = spear(pa, pr[prng.permutation(n)])
    p_perm = float((np.sum(null >= stat) + 1) / (N_PERM + 1))
    print("descriptive permutation null (labelled post-hoc, NOT a decision rule):")
    print("  null median=%.4f  q95=%.4f  q99=%.4f  max=%.4f"
          % (np.median(null), np.percentile(null, 95),
             np.percentile(null, 99), null.max()))
    print("  p_perm = %.5f  (%d perms)" % (p_perm, N_PERM))

    # ---- transfer map CSV 一致性 ----
    mp = pd.read_csv(MAP)
    ck("map rows", int(len(mp)), 15 * 6 + 15)     # 90 格 + 15 个 pair 级行
    pl = mp[mp["policy"] == "<pair-level mean>"]
    ck("map pair rows", int(len(pl)), 15)
    okmap = all(abs(float(r.rho_rank) - rhos[(r.task_A, r.task_B)]) < 5e-6
                for r in pl.itertuples())
    ck("map pair-level rho matches", bool(okmap), True)

    # ---- 报告正文手抄数字核验 ----
    rep = (ROOT / "data_registry" / "M6_CONFIRMATORY_REPORT.md").read_text(
        encoding="utf-8")
    for must in [
        "Spearman = +0.754", "[+0.232, +0.944]", "≥0.45",
        "`Spearman(f1, pair-level ρ_rank)`** | **+0.7536**",
        "**[+0.2318, +0.9445]**",
        "中位数 = **0.0021**",
        "**15 / 90 = 16.7%**",
        "**0.694%**", "**0.586%**",
        "**55 / 55 checks，0 失败**",
        "`max|diff| = 0.0`",
        "0.00085",
        "| Bei89 ~ Bk79 | **+0.9325** | +0.1522 |",
        "| Bk79 ~ Bris07 | **−0.2798** | **−0.1627** |",
        "| Mos99 ~ NDako16 | +0.8012 | **+0.2008** |",
    ]:
        ck("report contains %r" % must[:34], must in rep, True)
    # 逐对表：报告里的 15 行 f1/rho 必须与 JSON 完全一致（含符号写法）
    for k, v in f1s.items():
        r_ = rhos[k]
        def fmt(x):
            return ("%+.4f" % x).replace("-", "−")
        ck("report pair row %s~%s" % k,
           ("| %s ~ %s | " % k) in rep and fmt(v) in rep and fmt(r_) in rep, True)

    bad = [(l, g, w) for l, g, w in F if g != w]
    print()
    print("=" * 78)
    print("M6 RESULT VERIFICATION (independent code path)")
    print("=" * 78)
    for l, g, w in F:
        print("  %-4s %-38s got=%-22s want=%s"
              % ("OK" if g == w else "FAIL", l, repr(g)[:22], repr(w)[:22]))
    print()
    print("TOTAL: %d checks, %d failures" % (len(F), len(bad)))
    for l, g, w in bad:
        print("  FAIL %-38s got=%r want=%r" % (l, g, w))
    print()
    print("used cells per pair (of the 6 pre-specified):",
          sorted(set(used_counts.values())))
    out = ROOT / "data" / "manifests" / "M6_WU2020_VERIFY.json"
    out.write_text(json.dumps(
        {"n_checks": len(F), "n_fail": len(bad),
         "perm_null": {"median": float(np.median(null)),
                       "q95": float(np.percentile(null, 95)),
                       "q99": float(np.percentile(null, 99)),
                       "p_perm": p_perm, "n_perm": N_PERM,
                       "label": "post-hoc descriptive, not a decision rule"},
         "cells_used_per_pair": {("%s~%s" % k): v for k, v in used_counts.items()}},
        indent=2), encoding="utf-8")
    print("->", out)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
