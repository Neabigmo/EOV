"""M4 / Exp 3 —— TEM-1 严格 Tomorrow Test。

用户冻结的触发条件：「TEM-1 strict Tomorrow Test **only if G-FTI passes**，否则写
'measurement resolution insufficient' 并降级为敏感性」。M4.0 已执行 G-FTI：14 个 TEM-1 条件中
**10 个通过**（ratio >= 2）→ 满足触发条件，本实验成立。

严格性由三步保证
----------------
S1 **模型选择只用今天的数据**：把 AMP 族的每个非主浓度轮流当作"伪未来任务"
   （leave-one-concentration-out），在**不含该浓度**的特征上评估每个候选选择器的 NR，
   取平均 NR 最小者为 Phase-I selector。**AZT 的任何测量在这一步完全不可见。**
S2 **冻结**该选择（写盘 `M4_EXP3_FROZEN_SELECTOR.md`）。
S3 **才揭晓** AZT@0.44（主）/ AZT@36.0（强制复现），计算全部选择器的 NR 与 bootstrap CI。

判据（`PHASE1_DECISION.md` §Tomorrow Test，冻结）
-----------------------------------------------
相对**最强 heuristic selector**（不是 random）：future-task NR 降低 >= 20%，且 bootstrap 95% CI 排除 0。
降级条款：TEM-1 只有一个 strict future task → 仅凭 TEM-1 达成 = proof-of-concept GO，**不得**称 task-general。

两阶段执行（工程约束，非分析选择）
--------------------------------
S1 的搜索模拟昂贵，故独立成阶段并**先落盘再出报告**：`--s1-only` 只跑 S1 并存
`data/processed/M4_EXP3_S1_R.npz`；`--report-only` 载入该文件与 S1 汇总，直接执行 S2/S3。
AMP@781.0 / AZT@0.44 / AZT@36.0 的可达值**不重算**，直接读 `M4_EXP2_V.npz`
（Exp 2 产出，同一 `search_sim`），以保证 Exp 2/3 完全同源。
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landscape import MixedAlphabetSpace  # noqa: E402
from search_sim import BUDGETS, POLICIES, Scratch, make_context, simulate_search  # noqa: E402
from tis import TIS  # noqa: E402  （L39：特征只由 TIS 产出，调用方无法传入 future 数组）

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
NPZ2 = os.path.join(ROOT, "data", "processed", "M4_EXP2_V.npz")
NPZ3 = os.path.join(ROOT, "data", "processed", "M4_EXP3_S1_R.npz")
OUT_FREEZE = os.path.join(ROOT, "data_registry", "M4_EXP3_FROZEN_SELECTOR.md")
OUT = os.path.join(ROOT, "data_registry", "M4_EXP3_TOMORROW.csv")
OUT_S1 = os.path.join(ROOT, "data_registry", "M4_EXP3_S1_MODEL_SELECTION.csv")

DS = "TEM-1CML"
AMP_CONDITIONS = ["0.0", "3.1", "12.2", "48.8", "195.0", "781.0"]
TODAY_PRIMARY = ("AMP", "781.0")
FUTURES = [("AZT", "0.44"), ("AZT", "36.0")]
N_BOOT = 2000
BOOT_SEED = 20260919 + 11

CANDIDATES = ["current_fitness", "known_family_mean", "known_family_worst",
              "local_robustness", "neighbor_informative_frac", "dist_to_best",
              "n_better_neighbors", "local_ruggedness", "proxy_eov_today"]


def nr_cell(V, col, denom_pct=5.0):
    """返回 (NR, v_oracle, v_rw, v_sel)；col=None 表示 random。"""
    ok = ~np.isnan(V)
    vo = float(np.max(V[ok])); vr = float(np.percentile(V[ok], denom_pct))
    dn = vo - vr
    if col is None:
        vs = float(np.nanmean(V[ok]))
    else:
        fin = np.isfinite(col) & ok
        if fin.sum() < 10:
            return None
        vs = float(V[fin][np.argmax(col[fin])])
    return ((vo - vs) / dn if dn > 0 else float("nan")), vo, vr, vs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--s1-only", action="store_true", help="只跑 S1 的搜索模拟并落盘")
    ap.add_argument("--report-only", action="store_true", help="跳过一切模拟，载入已落盘结果执行 S2/S3")
    args = ap.parse_args()
    t0 = time.time()

    df = pd.read_parquet(MEAS)
    t = df[df.dataset_id == DS]
    ids = sorted(set(t.genotype_id.astype(str).unique()))
    space = MixedAlphabetSpace.from_masked_profiles([s for s in ids if "X" not in s])
    n = space.space_size()
    assert n == 55296 and space.degree_topology() == 18
    ctx = make_context(space)
    scratch = Scratch(n)
    rng = np.random.default_rng(4242)

    def load_raw(tid, cid):
        s = t[(t.task_id == tid) & (t.condition_id == cid)]
        s = s[~s.genotype_id.astype(str).str.contains("X", regex=False)]
        v = np.full(n, np.nan)
        idx = np.array([space.index_of(tuple(x)) for x in s.genotype_id.astype(str)], dtype=np.int64)
        ok = s.informative.astype(bool).values
        v[idx[ok]] = pd.to_numeric(s.value_group, errors="coerce").values[ok]
        return v

    arrs = {("AMP", c): load_raw("AMP", c) for c in AMP_CONDITIONS}

    def mk_u(v):
        vv = v[~np.isnan(v)]
        q05, q95 = float(np.percentile(vv, 5)), float(np.percentile(vv, 95))
        return lambda z: float((z - q05) / (q95 - q05))

    us = {k: mk_u(v) for k, v in arrs.items()}
    u_today = us[TODAY_PRIMARY]
    # L39：τ₀ 白名单由 eov/tis.py 的 TODAY_SPEC 决定，本文件无法扩大它
    tis = TIS.for_dataset(DS, arrs, ctx, space)

    # ================================================================= S1
    if args.report_only:
        d3 = np.load(NPZ3)
        parents = d3["parents"]
        R_amp = {("AMP", c): d3["R_AMP_%s" % c] for c in AMP_CONDITIONS}
        s1 = list(csv.DictReader(open(OUT_S1, encoding="utf-8")))
        print("report-only：载入 S1 的 %d 个 R 场与 %d 行选择结果" % (len(R_amp), len(s1)), flush=True)
    else:
        # parent 样本：**不依赖 Exp 2 的产物**即可复现（同一 seed 与同一抽样规则）。
        # S1 只需 parent 列表，故可与其他阶段并行执行；S3 会与 Exp 2 的 NPZ 交叉核对。
        pool = np.flatnonzero(~np.isnan(arrs[TODAY_PRIMARY]))
        parents = np.sort(np.random.default_rng(20260919).choice(
            pool, size=min(1000, len(pool)), replace=False))
        if os.path.exists(NPZ2):
            p2 = np.load(NPZ2)["parents"]
            assert np.array_equal(parents, p2), "parent 样本与 Exp 2 不一致 —— 抽样规则已分叉"
            print("parent 样本与 M4_EXP2_V.npz 逐一相等（n=%d）" % len(parents), flush=True)
        else:
            print("Exp 2 NPZ 尚未生成；parent 样本由同一 seed 独立复现（n=%d）" % len(parents),
                  flush=True)

        def feats_for(tis_sub, P):
            """L39：签名只接受 `TIS` 实例 —— **没有任何途径**把 future 数组传进来。"""
            return tis_sub.features(P, ctx=ctx)

        R_amp = {}
        for c in AMP_CONDITIONS:
            v = arrs[("AMP", c)]
            cand = np.flatnonzero(~np.isnan(v))
            acc = np.full((len(POLICIES), len(BUDGETS), len(parents)), np.nan)
            for si, pol in enumerate(POLICIES):
                for bi, B in enumerate(BUDGETS):
                    for pi, x in enumerate(parents):
                        acc[si, bi, pi] = simulate_search(
                            ctx, int(x), v, cand, pol, B, rng, scratch)
            R_amp[("AMP", c)] = acc
            print("  R(clean) 完成 AMP@%-7s (%.0f s)" % (c, time.time() - t0), flush=True)
        np.savez_compressed(NPZ3, parents=parents,
                            **{"R_AMP_%s" % c: R_amp[("AMP", c)] for c in AMP_CONDITIONS})
        print("  CHECKPOINT 已落盘 %s" % NPZ3, flush=True)

        # ---- S1：leave-one-concentration-out（AZT 不可见）----
        s1 = []
        for hold in AMP_CONDITIONS:
            if hold == TODAY_PRIMARY[1]:
                continue
            F = feats_for(tis.without(("AMP", hold)), parents)
            u_h = us[("AMP", hold)]
            for si, pol in enumerate(POLICIES):
                for bi, B in enumerate(BUDGETS):
                    a = R_amp[("AMP", hold)][si, bi]
                    V = np.array([np.nan if np.isnan(z) else u_h(z) for z in a])
                    F["proxy_eov_today"] = np.array([
                        np.nan if np.isnan(z) else u_today(z)
                        for z in R_amp[TODAY_PRIMARY][si, bi]])
                    for sel in CANDIDATES:
                        r = nr_cell(V, F[sel])
                        if r is None:
                            continue
                        s1.append(dict(holdout="AMP@%s" % hold, policy=pol, budget=B,
                                       selector=sel, NR=round(r[0], 4)))
            print("  S1 holdout AMP@%-7s done (%.0f s)" % (hold, time.time() - t0), flush=True)
        with open(OUT_S1, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["holdout", "policy", "budget", "selector", "NR"])
            w.writeheader()
            for r in s1:
                w.writerow(r)
        if args.s1_only:
            print("S1-only 完成 (%.0f s)" % (time.time() - t0))
            return 0

    # ================================================================= S2 冻结
    s1df = pd.DataFrame(s1)
    s1df["NR"] = s1df["NR"].astype(float)
    mean_nr = s1df.groupby("selector").NR.mean().sort_values()
    print()
    print("=== S1：各选择器在 5 个伪未来任务上的平均 NR（越小越好；AZT 未曾参与）===")
    print(mean_nr.to_string(), flush=True)
    frozen = str(mean_nr.index[0])
    others = mean_nr.drop(index=[frozen])
    heuristic = str(others.index[0])
    with open(OUT_FREEZE, "w", encoding="utf-8") as f:
        f.write("# Exp 3 — S1 模型选择冻结记录\n\n")
        f.write("> S1 只用 AMP 族的 leave-one-concentration-out；**AZT 的任何测量在此时不可见**。\n")
        f.write("> 判据：平均 NR 最小者被选为 Phase-I selector。\n\n")
        f.write("| 选择器 | 5 个伪未来任务上的平均 NR |\n|---|---|\n")
        for k, v in mean_nr.items():
            f.write("| %s | %.4f |\n" % (k, v))
        f.write("\n**冻结的 Phase-I selector = `%s`**\n\n" % frozen)
        f.write("**冻结的最强 heuristic（S1 口径）= `%s`**\n\n" % heuristic)
        f.write("S1 的 5 个 holdout：%s。它们与 `AMP@781.0` 的 CL-5 rho 跨度为 "
                "0.0996（AMP@0.0）～0.7585（AMP@48.8），故 S1 不是同任务自比。\n"
                % ", ".join(sorted(set(s1df.holdout))))
    print("FROZEN Phase-I selector = %s ；S1 最强 heuristic = %s" % (frozen, heuristic), flush=True)

    # ================================================================= S3 揭晓
    d2 = np.load(NPZ2)
    # fail-loud：Exp 2 与 Exp 3 的 parent 必须逐一致，否则全部按位置索引的对齐都是静默错误
    assert np.array_equal(parents, d2["parents"]), \
        "Exp 2 与 Exp 3 的 parent 样本不一致 —— 对齐已失效"
    print("交叉核对：Exp 2 与 Exp 3 的 parent 样本逐一致（n=%d）" % len(parents), flush=True)
    rows = []
    boot_rng = np.random.default_rng(BOOT_SEED)

    def feats_full():
        """S3 的完整 Day-0 特征。L39：同样只走 TIS。"""
        return tis.features(parents, ctx=ctx)

    F = feats_full()
    for key in FUTURES:
        u_f = mk_u(load_raw(*key))
        Ra = d2["R_%s_%s" % key]
        for si, pol in enumerate(POLICIES):
            for bi, B in enumerate(BUDGETS):
                V = np.array([np.nan if np.isnan(z) else u_f(z)
                              for z in np.nanmean(Ra[si, bi], axis=1)])
                F["proxy_eov_today"] = np.array([
                    np.nan if np.isnan(z) else u_today(z)
                    for z in np.nanmean(d2["R_%s_%s" % TODAY_PRIMARY][si, bi], axis=1)])
                cell = {}
                for sel in CANDIDATES:
                    r = nr_cell(V, F[sel])
                    if r is not None:
                        cell[sel] = r
                r_rnd = nr_cell(V, None)
                ok = ~np.isnan(V)
                vo = float(np.max(V[ok])); vr = float(np.percentile(V[ok], 5)); dn = vo - vr
                for sel, r in list(cell.items()) + [("random", r_rnd)]:
                    bs = []
                    for _ in range(N_BOOT):
                        pidx = boot_rng.integers(0, len(V), len(V))
                        Vb = V[pidx]
                        o = ~np.isnan(Vb)
                        if o.sum() < 50:
                            continue
                        vb_o = float(np.max(Vb[o])); vb_r = float(np.percentile(Vb[o], 5))
                        dnb = vb_o - vb_r
                        if dnb <= 0:
                            continue

                        def nr_b(col):
                            if col is None:
                                return (vb_o - float(np.nanmean(Vb[o]))) / dnb
                            fin = np.isfinite(col) & o
                            if fin.sum() < 10:
                                return None
                            return (vb_o - float(Vb[fin][np.argmax(col[fin])])) / dnb

                        nf = nr_b(F[frozen][pidx])
                        cs = None if sel == "random" else F[sel][pidx]
                        ns = nr_b(cs)
                        if nf is None or ns is None:
                            continue
                        bs.append(ns - nf)
                    lo, hi = (np.percentile(bs, [2.5, 97.5]) if len(bs) >= 100
                              else (float("nan"), float("nan")))
                    rows.append(dict(
                        future="%s@%s" % key,
                        role=("primary" if key == FUTURES[0] else "replication"),
                        policy=pol, budget=B, frozen_selector=frozen, opponent=sel,
                        NR_frozen=round(cell[frozen][0], 4), NR_opponent=round(r[0], 4),
                        NR_opp_minus_frozen=round(r[0] - cell[frozen][0], 4),
                        reduction_pct=(round(100.0 * (r[0] - cell[frozen][0]) / r[0], 2)
                                       if r[0] else ""),
                        CI_lo=round(lo, 4), CI_hi=round(hi, 4),
                        CI_excludes_0=bool(lo == lo and (lo > 0 or hi < 0)),
                        beats_frozen_by_20pct_and_CI=bool(
                            r[0] < cell[frozen][0] * 0.8 and lo == lo and lo > 0)))
                print("  %s@%s %-11s B%-4d done (%.0f s)" % (key[0], key[1], pol, B, time.time() - t0),
                      flush=True)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print()
    print("WROTE", OUT_FREEZE)
    print("WROTE", OUT_S1)
    print("WROTE", OUT, len(rows), "rows")
    print("total %.0f s" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
