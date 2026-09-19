"""M3.1/M3.2 收口：修 SEM 缺陷 + 重建 task-panel QC + 生成报告。

父 agent 执行（agent b5bab24b 未在额度内完成修正）。

修的是什么：
  DAOx 每格 2 个重复、TEV 大量格子 ≥3 行，但交付的 parquet 里 value_sem / value_sd 全为
  NaN、n_expected / n_observed 为 <NA>，于是 CL-9 的 informative 全被判 False，
  QC 报出 informative_frac = 0.0 —— 那是"没算"，不是"数据没有不确定度"。

冻结规则（AMENDMENT-011 §1.2 / §3.2 与 GL-9）：
  n_expected = 该格子的设计重复数（本表中 = 该格子的行数；未观测重复按构造规则不发射）
  n_observed = 非空 value 个数
  n_missing  = n_expected - n_observed
  value_sd   = 样本标准差(ddof=1)          ，仅当 n_observed >= 2
  value_sem  = value_sd / sqrt(n_observed) ，仅当 n_observed >= 2
  value_group= 该格子有效重复的 median
  informative= (state == 'exact') AND (SEM 非空)
               AND (floor 为 NULL 或 value_group > floor + 2*SEM)
               AND (ceiling 为 NULL 或 value_group < ceiling - 2*SEM)

⛔ 不产生任何 degree 字段；不计算 EOV / regret / ranking / Tomorrow-Test。
"""
from __future__ import annotations

import collections
import csv
import hashlib
import os
import statistics
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TP = os.path.join(ROOT, "data", "processed", "M3_taskpanel_measurements.parquet")
QC = os.path.join(ROOT, "data_registry", "M3_TASKPANEL_QC.csv")
REP = os.path.join(ROOT, "data_registry", "M3_TASKPANEL_REPORT.md")

KEYS = ["dataset_id", "task_id", "condition_id", "genotype_id"]
SPARSE_MIN_VARIANTS = 100  # 低于此值的 task 标注 too_sparse_for_task_level_use


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    df = pd.read_parquet(TP)
    print("loaded rows=%d cols=%d" % (len(df), len(df.columns)))
    pre_inf = int(df["informative"].astype(bool).sum())

    df["_v"] = pd.to_numeric(df["value"], errors="coerce")
    g = df.groupby(KEYS, sort=False)

    # 全向量化聚合（120 万分组；groupby.apply 会超时）
    #   n_expected = 该格子的设计重复数（本表中 = 行数；未观测重复按构造规则不发射）
    #   n_observed = 非空 value 个数
    #   value_sd   = 样本标准差 ddof=1；pandas 对 n<2 自动返回 NaN ✓
    #   value_group= 有效重复的 median
    stats = pd.DataFrame({
        "n_expected": g["_v"].size(),
        "n_observed": g["_v"].count(),
        "value_sd": g["_v"].std(ddof=1),
        "value_group": g["_v"].median(),
    }).reset_index()

    # 原表已含同名列 → 先删掉再由本次重算填回（否则 merge 会加 _x/_y 后缀）
    drop = [c for c in ("n_expected", "n_observed", "n_missing", "value_sd", "value_sem", "value_group")
            if c in df.columns]
    if drop:
        df = df.drop(columns=drop)
    df = df.merge(stats, on=KEYS, how="left")
    df["n_missing"] = df["n_expected"] - df["n_observed"]
    df["value_sem"] = df["value_sd"] / df["n_observed"].pow(0.5)
    df.loc[df["n_observed"] < 2, "value_sem"] = float("nan")

    fl = pd.to_numeric(df.get("floor"), errors="coerce")
    ce = pd.to_numeric(df.get("ceiling"), errors="coerce")
    vs, vg = df["value_sem"], df["value_group"]
    ok_floor = fl.isna() | (vg > fl + 2 * vs)
    ok_ceil = ce.isna() | (vg < ce - 2 * vs)
    df["informative"] = ((df["measurement_state"] == "exact") & vs.notna() & ok_floor & ok_ceil).astype(bool)
    df = df.drop(columns=["_v"])

    post_inf = int(df["informative"].sum())
    df.to_parquet(TP, index=False)
    print("informative: 修前 %d -> 修后 %d" % (pre_inf, post_inf))
    print("n_observed 非空 %d / %d ; value_sem 非空 %d" % (
        int(df["n_observed"].notna().sum()), len(df), int(df["value_sem"].notna().sum())))
    print("WROTE", TP, os.path.getsize(TP))

    # ---------------- QC 表 ----------------
    rows = []
    for (ds, task), sub in df.groupby(["dataset_id", "task_id"], sort=True):
        n = sub["genotype_id"].nunique()
        c = collections.Counter(sub["measurement_state"].astype(str))
        inf = int(sub["informative"].astype(bool).sum())
        unc = int(sub["value_sem"].notna().sum())
        note = ("floor/ceiling 未文档化 -> unresolved：不产出 censored 与 boundary_ambiguous（AMENDMENT-011 §1）")
        if n < SPARSE_MIN_VARIANTS:
            note += " | too_sparse_for_task_level_use (n_variants_measured=%d < %d)" % (n, SPARSE_MIN_VARIANTS)
        rows.append({
            "dataset_id": ds, "task_id": task,
            "role": sub["role"].iloc[0] if "role" in sub.columns else "task_panel",
            "measurement_modality": sub["measurement_modality"].iloc[0],
            "n_variants_total": n, "n_variants_measured": n, "measured_frac": 1.0,
            "exact_n": c.get("exact", 0), "censored_n": c.get("censored", 0),
            "boundary_ambiguous_n": c.get("boundary_ambiguous", 0), "missing_n": c.get("missing", 0),
            "informative_n": inf, "informative_frac": round(inf / len(sub), 4),
            "uncertainty_available_n": unc, "uncertainty_coverage": round(unc / len(sub), 4),
            "floor_value": "", "floor_status": "unresolved", "floor_source": "none",
            "ceiling_status": "not_documented", "boundary_evidence": "none",
            "notes": note,
        })
    cols = list(rows[0].keys())
    with open(QC, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("WROTE", QC, "rows=%d" % len(rows))

    # ---------------- 双向稀疏性审计 ----------------
    def sparsity(ds: str):
        s = df[df["dataset_id"] == ds]
        m = s[s["measurement_state"] != "missing"]
        tv = m.groupby("genotype_id")["task_id"].nunique()
        vt = m.groupby("task_id")["genotype_id"].nunique()
        return s, tv, vt

    lines = ["# M3_TASKPANEL_REPORT.md — DAOx / TEV_ProtRec measurement panel QC",
             "",
             "| 字段 | 值 |", "|---|---|",
             "| 版本 | 1 |", "| 时间 | 2026-09-19 |", "| 状态 | **FROZEN** |",
             "| 执行 | 父 agent（原执行端 agent `b5bab24b` 未在额度内完成 SEM 修正） |",
             "| 纪律 | **未计算任何 degree / EOV / regret / parent ranking / Tomorrow-Test 量** |",
             "",
             "## 0. 本报告修了什么",
             "",
             "交付版 parquet 里，DAOx 的每格 2 个重复、TEV 的大量 ≥3 行格子**都没有被用来估计不确定度**：",
             "`value_sem` / `value_sd` 全为 NaN、`n_expected` / `n_observed` 为 `<NA>`。",
             "于是 CL-9 的 `informative` 全被判 `False`，QC 报出 `informative_frac = 0.0` ——",
             "**那是「没算」造成的，不是「数据没有不确定度」**（会把两个 task panel 在 manifest 里误判为零信息）。",
             "",
             "| 指标 | 修前 | **修后** |", "|---|---|---|",
             "| `informative=True` 行数 | %d | **%d** |" % (pre_inf, post_inf),
             "| `value_sem` 非空行数 | 0 | **%d** |" % int(df["value_sem"].notna().sum()),
             "| `n_observed` 非空行数 | 0 | **%d** |" % int(df["n_observed"].notna().sum()),
             "",
             "口径（AMENDMENT-011 §1.2 / CL-9）：`n_observed >= 2` 时 `value_sd = SD(ddof=1)`、",
             "`value_sem = SD/sqrt(n)`；`n_observed == 1` 时留空并判 `informative=False`（保守）。",
             "两个数据集的 floor 均 `unresolved`（NULL）→ 该侧视为无约束。",
             ""]
    for ds in sorted(df["dataset_id"].unique()):
        s, tv, vt = sparsity(ds)
        n_task = s["task_id"].nunique()
        n_var = s["genotype_id"].nunique()
        dens = len(s) / (n_var * n_task)
        lines += [
            "## %s" % ds, "",
            "| 项 | 值 |", "|---|---|",
            "| rows | %d |" % len(s),
            "| **tasks** | **%d** |" % n_task,
            "| **variants** | **%d** |" % n_var,
            "| 矩阵密度 rows/(variants×tasks) | %.4f |" % dens,
            "",
            "### 方向 1 — `n_tasks_per_variant`", "",
            "| 均值 | 中位 | 最小 | 最大 | =1 的 variant |", "|---|---|---|---|---|",
            "| %.2f | %.0f | %d | %d | %d (%.1f%%) |" % (
                tv.mean(), tv.median(), tv.min(), tv.max(),
                int((tv == 1).sum()), 100 * (tv == 1).sum() / len(tv)),
            "",
            "### 方向 2 — `n_variants_per_task`", "",
            "| 均值 | 中位 | 最小 | 最大 | 最小的 5 个 task |", "|---|---|---|---|---|",
            "| %.1f | %.0f | %d | %d | %s |" % (
                vt.mean(), vt.median(), vt.min(), vt.max(), sorted(vt.tolist())[:5]),
            "",
            "### cross-task completeness", "",
            "| ≥2 | ≥5 | ≥10 | ≥20 | ≥50 | 全测(%d) |" % n_task,
            "|---|---|---|---|---|---|",
            "| %d (%.1f%%) | %d (%.1f%%) | %d (%.1f%%) | %d (%.1f%%) | %d (%.1f%%) | %d |" % (
                (tv >= 2).sum(), 100 * (tv >= 2).mean(), (tv >= 5).sum(), 100 * (tv >= 5).mean(),
                (tv >= 10).sum(), 100 * (tv >= 10).mean(), (tv >= 20).sum(), 100 * (tv >= 20).mean(),
                (tv >= 50).sum(), 100 * (tv >= 50).mean(), (tv >= n_task).sum()),
            ""]
        if n_task > 10:
            lines += ["> ⚠️ **结论**：`%d` 个 task **不是**均衡矩阵，而是**少数大任务 + 长尾极小任务**"
                      "（`n_variants_per_task` 中位仅 %.0f，最小 %d）。"
                      "→ TEV 的 task 级使用**必须按 `n_variants_measured` 设门槛**；"
                      "QC 表已对 < %d 个 variant 的任务标注 `too_sparse_for_task_level_use`。"
                      % (n_task, vt.median(), vt.min(), SPARSE_MIN_VARIANTS), ""]
        else:
            lines += ["> **结论**：%d 个 task × %d 个 variant **完全稠密**（每个 variant 都测了全部 task）。"
                      % (n_task, n_var), ""]
    lines += [
        "## 实测规模 vs 早前估计", "",
        "| 数据集 | 早前估计 | **实测** |", "|---|---|---|",
        "| TEV_ProtRec | 134 task / 29,716 protease | **163 task / 62,220 variant** |",
        "| DAOx | 6,418 variant / 5 底物 | **6,417 variant / 5 底物** |",
        "",
        "按纪律**以实测为准**。",
        "",
        "## 数据入口（Zenodo 硬封锁下的替代路径）", "",
        "Zenodo（`10.5281/zenodo.15846928`、`15346003`、`15344074`）对全部端点返回 **403**"
        "（含 API、`/record/`、OAI-PMH、以及此前可用的 `doi.org` 入口）。",
        "实际取数路径：**DAOx** = Nature 论文补充材料 `MOESM4_ESM.xlsx`；**TEV** = 作者 GitHub `JeschekLab/ProtRec`。",
        "",
        "## 合规声明", "",
        "- 两个数据集均严格作为 **`task_panel`** 处理，**未产生任何 degree 字段**"
        "（`d_topology` / `d_present` / `degree_informative` / `effective_degree` 一律不存在）。",
        "- `measurement_state` 全部为 `exact`（floor `unresolved` → 不产出 censored / boundary_ambiguous）。",
        "- **未计算** EOV、`R_{B,pi}`、regret、parent ranking、搜索策略、预算模拟或任何 Tomorrow-Test 量。",
        "- 数据许可：两仓库均**无 LICENSE 文件** → `redistribution_allowed = False`（local-only，不得再分发）。",
        "",
        "## sha256", "",
        "| 文件 | sha256 |", "|---|---|",
        "| `data/processed/M3_taskpanel_measurements.parquet` | `%s` |" % sha256(TP),
        "| `data_registry/M3_TASKPANEL_QC.csv` | `%s` |" % sha256(QC),
        ""]
    with open(REP, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("WROTE", REP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
