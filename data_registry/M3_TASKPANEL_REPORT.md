# M3_TASKPANEL_REPORT.md — DAOx / TEV_ProtRec measurement panel QC

| 字段 | 值 |
|---|---|
| 版本 | 1 |
| 时间 | 2026-09-19 |
| 状态 | **FROZEN** |
| 执行 | 父 agent（原执行端 agent `b5bab24b` 未在额度内完成 SEM 修正） |
| 纪律 | **未计算任何 degree / EOV / regret / parent ranking / Tomorrow-Test 量** |

## 0. 本报告修了什么

交付版 parquet 里，DAOx 的每格 2 个重复、TEV 的大量 ≥3 行格子**都没有被用来估计不确定度**：
`value_sem` / `value_sd` 全为 NaN、`n_expected` / `n_observed` 为 `<NA>`。
于是 CL-9 的 `informative` 全被判 `False`，QC 报出 `informative_frac = 0.0` ——
**那是「没算」造成的，不是「数据没有不确定度」**（会把两个 task panel 在 manifest 里误判为零信息）。

| 指标 | 修前 | **修后** |
|---|---|---|
| `informative=True` 行数 | 0 | **539694** |
| `value_sem` 非空行数 | 0 | **539694** |
| `n_observed` 非空行数 | 0 | **1535281** |

口径（AMENDMENT-011 §1.2 / CL-9）：`n_observed >= 2` 时 `value_sd = SD(ddof=1)`、
`value_sem = SD/sqrt(n)`；`n_observed == 1` 时留空并判 `informative=False`（保守）。
两个数据集的 floor 均 `unresolved`（NULL）→ 该侧视为无约束。

## DAOx_multi_substrate

| 项 | 值 |
|---|---|
| rows | 65730 |
| **tasks** | **5** |
| **variants** | **6417** |
| 矩阵密度 rows/(variants×tasks) | 2.0486 |

### 方向 1 — `n_tasks_per_variant`

| 均值 | 中位 | 最小 | 最大 | =1 的 variant |
|---|---|---|---|---|
| 5.00 | 5 | 5 | 5 | 0 (0.0%) |

### 方向 2 — `n_variants_per_task`

| 均值 | 中位 | 最小 | 最大 | 最小的 5 个 task |
|---|---|---|---|---|
| 6417.0 | 6417 | 6417 | 6417 | [6417, 6417, 6417, 6417, 6417] |

### cross-task completeness

| ≥2 | ≥5 | ≥10 | ≥20 | ≥50 | 全测(5) |
|---|---|---|---|---|---|
| 6417 (100.0%) | 6417 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 6417 |

> **结论**：5 个 task × 6417 个 variant **完全稠密**（每个 variant 都测了全部 task）。

## TEV_ProtRec

| 项 | 值 |
|---|---|
| rows | 1469551 |
| **tasks** | **163** |
| **variants** | **62220** |
| 矩阵密度 rows/(variants×tasks) | 0.1449 |

### 方向 1 — `n_tasks_per_variant`

| 均值 | 中位 | 最小 | 最大 | =1 的 variant |
|---|---|---|---|---|
| 16.80 | 12 | 1 | 162 | 3588 (5.8%) |

### 方向 2 — `n_variants_per_task`

| 均值 | 中位 | 最小 | 最大 | 最小的 5 个 task |
|---|---|---|---|---|
| 6412.5 | 2892 | 1 | 56326 | [1, 3, 9, 112, 227] |

### cross-task completeness

| ≥2 | ≥5 | ≥10 | ≥20 | ≥50 | 全测(163) |
|---|---|---|---|---|---|
| 58632 (94.2%) | 51135 (82.2%) | 37984 (61.0%) | 12821 (20.6%) | 4022 (6.5%) | 0 |

> ⚠️ **结论**：`163` 个 task **不是**均衡矩阵，而是**少数大任务 + 长尾极小任务**（`n_variants_per_task` 中位仅 2892，最小 1）。→ TEV 的 task 级使用**必须按 `n_variants_measured` 设门槛**；QC 表已对 < 100 个 variant 的任务标注 `too_sparse_for_task_level_use`。

## 实测规模 vs 早前估计

| 数据集 | 早前估计 | **实测** |
|---|---|---|
| TEV_ProtRec | 134 task / 29,716 protease | **163 task / 62,220 variant** |
| DAOx | 6,418 variant / 5 底物 | **6,417 variant / 5 底物** |

按纪律**以实测为准**。

## 数据入口（Zenodo 硬封锁下的替代路径）

Zenodo（`10.5281/zenodo.15846928`、`15346003`、`15344074`）对全部端点返回 **403**（含 API、`/record/`、OAI-PMH、以及此前可用的 `doi.org` 入口）。
实际取数路径：**DAOx** = Nature 论文补充材料 `MOESM4_ESM.xlsx`；**TEV** = 作者 GitHub `JeschekLab/ProtRec`。

## 合规声明

- 两个数据集均严格作为 **`task_panel`** 处理，**未产生任何 degree 字段**（`d_topology` / `d_present` / `degree_informative` / `effective_degree` 一律不存在）。
- `measurement_state` 全部为 `exact`（floor `unresolved` → 不产出 censored / boundary_ambiguous）。
- **未计算** EOV、`R_{B,pi}`、regret、parent ranking、搜索策略、预算模拟或任何 Tomorrow-Test 量。
- 数据许可：两仓库均**无 LICENSE 文件** → `redistribution_allowed = False`（local-only，不得再分发）。

## sha256

| 文件 | sha256 |
|---|---|
| `data/processed/M3_taskpanel_measurements.parquet` | `f6ff57222596d0ae703ab8b2aef23ac4b17888abe3ddefa2d3bffecdd1a9abf3` |
| `data_registry/M3_TASKPANEL_QC.csv` | `ad071c5177c0b8e0b735a428839603b559e0724a4685a596b7bd90a424cb683d` |
