"""TrpB4（Johnston et al. 2024）**已发表基线的复现** —— 用户 M4 规格的第五项。

用户 M4 规格逐字：**"TrpB = published baseline reproduction only, no new figures"**；
`AMENDMENT-007` 把它列为**强制 baseline**。M4 首轮遗漏（`M4_REPORT §8.7`）。

## 数据与代码出处（CC0-1.0，已在冻结的 `PROVENANCE_LEDGER.csv` 内）

    dataset_id : TrpB4_Johnston2024
    DOI        : 10.22002/h5rah-5z170  (CaltechDATA, author_deposit)
    license    : CC0-1.0   analysis_allowed=True  redistribution_allowed=True
    code.zip   : md5 26e4605d3aaa7553ebc36498d91ae016  (413 MB)
    data.zip   : md5 210f5d23474cf9661bd61504735db475  (3.3 GB)

## 复现对象：论文的 **3 个已发表 DE 方法**（逐字来自 `run_all_simulations`）

    1. simulate_single_step_DE        —— 对 4 个位点的**全部 24 种顺序**做坐标上升扫描
    2. simulate_simple_SSM_recomb_DE  —— 逐位点饱和突变 + 重组，取 {起点, 重组, 4 个 SSM} 最优
    3. sample_SSM_test_top_N (N=96)   —— 用 SSM 的"乘性改进"预测 top-96 组合并实测

论文报告的指标（`print_characteristics`）：`final_fitness` 的
**mean / median / fraction reaching max**，按 (方法 × 蛋白) 分组。

**实现约定（必须逐字保持，否则不是"复现"）**
  · 数据 = KNN 插补表 + 实测表拼接，实测表先剔除 `# Stop > 0`
  · 缺失的序列 → **fitness 记为 0**（原文 `except: temp_fitness = 0`）
  · `AAs` 列是 4 个字母连写；原文内部用 `'_'.join` 分割再拼回
  · ECDF = `rank(method="first") / N`（注意 `method="first"` 是**顺序依赖**的并列处理）

> ⛔ **本脚本只做复现，不产生任何新的 TrpB 图或新主张**（用户规格："no new figures"）。
> TrpB4 是**单任务**（`single_task_control`）→ **不得**据此做跨任务主张。
"""
from __future__ import annotations

import csv
import itertools
import os
import pickle
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRPB = os.path.join(ROOT, "data", "external", "TrpB4_Johnston2024")
DATA = os.path.join(TRPB, "data")
OUT = os.path.join(ROOT, "data_registry", "M4_TRPB_BASELINE_REPRODUCTION.csv")
OUTCHK = os.path.join(ROOT, "data_registry", "M4_TRPB_INPUT_HASHES.csv")

AA20 = list("ACDEFGHIKLMNPQRSTVWY")
N_SITES = 4
N_TOP = 96


# --------------------------------------------------------------- 原文方法（逐字移植）
def _mk(seq, aa, pos):
    return seq[:pos] + aa + seq[pos + 1:]


def simulate_single_step_DE(data, seq_col, fitness_col, n_sites=N_SITES, verbose=True,
                            starts=None):
    """原文 `simulate_single_step_DE`：全部 24 种位点顺序的坐标上升。

    `starts` 是**本移植新增**的可选参数（原文没有），仅供外部校验时抽样用；
    取值表 `d` 仍由**完整** `data` 构建，故结果与全量跑法逐位一致。
    """
    data = data.copy()
    data[seq_col] = data[seq_col].apply(lambda x: "".join(str(x).split("_")))
    d = dict(zip(data[seq_col].values, data[fitness_col].values))
    # 原文：`data[data['active']][seq_col].values`（**列名为 `active`**，不是 `active_AAs`）
    active = data[data["active"]][seq_col].values
    if starts is not None:
        active = np.asarray(starts)
    orders = list(itertools.permutations(range(n_sites)))
    recs = []
    for i, start in enumerate(active):
        start_fit = d[start]
        for order in orders:
            best_seq, best_fit = start, start_fit
            for pos in order:
                for aa in AA20:
                    t = _mk(best_seq, aa, pos)
                    tf = d.get(t, 0.0)          # 原文：缺失记为 0
                    if tf > best_fit:
                        best_seq, best_fit = t, tf
            recs.append((start, order, start_fit, best_seq, best_fit))
        if verbose and (i + 1) % 2000 == 0:
            print("      single_step %d/%d" % (i + 1, len(active)), flush=True)
    return pd.DataFrame(recs, columns=["start_seq", "order", "start_fitness",
                                       "final_seq", "final_fitness"])


def simulate_simple_SSM_recomb_DE(data, seq_col, fitness_col, n_sites=N_SITES, verbose=True):
    """原文 `simulate_simple_SSM_recomb_DE`：逐位点 SSM + 重组。"""
    data = data.copy()
    data[seq_col] = data[seq_col].apply(lambda x: "".join(str(x).split("_")))
    d = dict(zip(data[seq_col].values, data[fitness_col].values))
    # 原文：`data[data['active']][seq_col].values`（**列名为 `active`**，不是 `active_AAs`）
    active = data[data["active"]][seq_col].values
    recs = []
    for i, start in enumerate(active):
        start_fit = d[start]
        top = {}
        for pos in range(n_sites):
            bs, bf = start, start_fit
            for aa in AA20:
                t = _mk(start, aa, pos)
                tf = d.get(t, 0.0)
                if tf > bf:
                    bs, bf = t, tf
            top[pos] = bs
        recomb = "".join(top[pos][pos] for pos in range(n_sites))
        rf = d.get(recomb, 0.0)
        bs, bf = start, start_fit
        if rf > bf:
            bs, bf = recomb, rf
        for s in top.values():
            sf = d.get(s, 0.0)
            if sf > bf:
                bs, bf = s, sf
        recs.append((start, start_fit, tuple(top.values()), bs, bf))
        if verbose and (i + 1) % 2000 == 0:
            print("      SSM_recomb %d/%d" % (i + 1, len(active)), flush=True)
    return pd.DataFrame(recs, columns=["start_seq", "start_fitness", "top_SSM_variants",
                                       "final_seq", "final_fitness"])


def _try_start_seq(start_seq, d, n_sites=N_SITES, N=N_TOP):
    """原文 `try_start_seq`，但把 **160,000 个组合的乘性改进向量化**。

    原文对每个组合做 `p = 1.0; for i in range(n_sites): p *= ssm[i][c[i]]/start_fit`，
    共 160,000 × 4 次 Python 乘法 × 9,783 个起点 ≈ **6.3e9** 次运算
    （单进程约 48 min；原文用 `Pool(16)`）。这里用 4 维广播得到同一组乘积，
    **乘法顺序与原文一致**（按 i = 0,1,2,3 依次相除相乘），展平顺序与
    `itertools.product(AA20, repeat=4)` 的 C 序一致。

    唯一刻意的差异：并列时用 `argsort(kind="stable")` 而非 pandas `sort_values` 的默认快排，
    以保证**可复现**（本项目已有一次并列处理不当的教训：`AMENDMENT-013 §3b`）。
    """
    start_fit = d[start_seq]
    ssm = {}
    for pos in range(n_sites):
        ssm[pos] = {}
        for aa in AA20:
            ssm[pos][aa] = d.get(_mk(start_seq, aa, pos), 0.0)
    if not start_fit:
        return (start_fit, start_seq, start_fit)
    m = np.array([[ssm[i][aa] for aa in AA20] for i in range(n_sites)], dtype=float)
    sh = [(1,) * k + (-1,) + (1,) * (n_sites - 1 - k) for k in range(n_sites)]
    imp = np.ones((len(AA20),) * n_sites, dtype=float)
    for i in range(n_sites):
        imp = imp * (m[i].reshape(sh[i]) / start_fit)
    flat = imp.ravel()
    order = np.argsort(-flat, kind="stable")[:N]
    bs, bf = start_seq, start_fit
    for k in order:
        v = "".join(AA20[(int(k) // (len(AA20) ** (n_sites - 1 - p))) % len(AA20)]
                    for p in range(n_sites))
        vf = d.get(v, 0.0)
        if vf > bf:
            bs, bf = v, vf
    for pos in ssm:
        for s, sf in ssm[pos].items():
            if sf > bf:
                bs, bf = s, sf
    return (start_fit, bs, bf)


def sample_SSM_test_top_N(data, seq_col, fitness_col, n_sites=N_SITES, N=N_TOP, verbose=True):
    """原文 `sample_SSM_test_top_N`（N=96）。单进程版（原文用 Pool，结果与并行度无关）。"""
    data = data.copy()
    data[seq_col] = data[seq_col].apply(lambda x: "".join(str(x).split("_")))
    d = dict(zip(data[seq_col].values, data[fitness_col].values))
    # 原文：`data[data['active']][seq_col].values`（**列名为 `active`**，不是 `active_AAs`）
    active = data[data["active"]][seq_col].values
    recs = []
    for i, s in enumerate(active):
        recs.append((s,) + _try_start_seq(s, d, n_sites, N))
        if verbose and (i + 1) % 2000 == 0:
            print("      SSM_top%d %d/%d" % (N, i + 1, len(active)), flush=True)
    return pd.DataFrame(recs, columns=["start_seq", "start_fitness", "final_seq",
                                       "final_fitness"])


def ecdf_transform(data):
    """原文的 `ecdf_transform`：`rank(method="first") / len`（**顺序依赖**，逐字保留）。"""
    return data.rank(method="first") / len(data)


def characteristics(df):
    f = df["final_fitness"].astype(float).values
    return dict(n=len(f), mean=float(np.mean(f)), median=float(np.median(f)),
                frac_reaching_max=float(np.sum(f == 1) / len(f)))


# --------------------------------------------------------------- 数据装载
def load_trpb():
    imp = pd.read_csv(os.path.join(DATA, "figure_data", "4-site_imputed",
                                   "20230828_KNN_imputed_TrpB.csv"), index_col=0)
    imp["imputed"] = True
    mea = pd.read_csv(os.path.join(DATA, "figure_data", "4-site_merged_replicates",
                                   "20230827", "four-site_simplified_AA_data.csv"))
    mea = mea[mea["# Stop"] == 0].copy().drop(columns=["# Stop"])
    mea["imputed"] = False
    df = pd.concat([imp, mea]).sort_values("AAs").reset_index(drop=True)
    df["fitness (min 0)"] = df["fitness"].apply(lambda x: max(0, x))
    return df, imp, mea


def main() -> int:
    t0 = time.time()
    if not os.path.isdir(DATA):
        print("缺少 %s —— 请先解压 data.zip" % DATA)
        return 1
    df, imp, mea = load_trpb()
    print("TrpB_data: rows=%d  imputed=%d  measured=%d" % (
        len(df), int(imp.shape[0]), int(mea.shape[0])), flush=True)
    print("  unique AAs=%d  fitness[min0]: min=%.4f median=%.4f max=%.4f" % (
        df["AAs"].nunique(), df["fitness (min 0)"].min(),
        df["fitness (min 0)"].median(), df["fitness (min 0)"].max()), flush=True)
    # 原文用 `data['active']` 过滤；此处核对列名
    print("  columns:", list(df.columns), flush=True)

    rows = []
    for name, fn in [("single_step_DE", simulate_single_step_DE),
                     ("SSM_recomb_DE", simulate_simple_SSM_recomb_DE),
                     ("SSM_top96", sample_SSM_test_top_N)]:
        print("  running %s ..." % name, flush=True)
        out = fn(df, "AAs", "fitness (min 0)")
        c = characteristics(out)
        rows.append(dict(method=name, protein="TrpB", **c))
        print("    -> n=%d mean=%.4f median=%.4f frac_max=%.4f" % (
            c["n"], c["mean"], c["median"], c["frac_reaching_max"]), flush=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    # 输入文件哈希
    chk = []
    for rel in ("figure_data/4-site_imputed/20230828_KNN_imputed_TrpB.csv",
                "figure_data/4-site_merged_replicates/20230827/four-site_simplified_AA_data.csv"):
        p = os.path.join(DATA, *rel.split("/"))
        if os.path.exists(p):
            import hashlib
            chk.append(dict(path=rel, bytes=os.path.getsize(p),
                            sha256=hashlib.sha256(open(p, "rb").read()).hexdigest()))
    with open(OUTCHK, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "bytes", "sha256"])
        w.writeheader()
        for r in chk:
            w.writerow(r)
    print("\nWROTE", OUT)
    print("WROTE", OUTCHK)
    print("total %.0f s" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
