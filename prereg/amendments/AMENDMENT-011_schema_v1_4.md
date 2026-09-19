# AMENDMENT-011 — schema v1.4（metadata-only）：四态 measurement semantics、`censoring_evidence`、`degree_present` vs `degree_informative`

| 字段 | 值 |
|---|---|
| 版本 | **11** |
| 时间 | **2026-09-19** |
| 状态 | **FROZEN**（用户裁决） |
| **对历史的影响** | v1.1 `ca142f6b…`、v1.2 `162e54c0…`、v1.3 `26ac6bb4…` **原文与哈希一律保留**；本文件是 v1.3 → v1.4 的唯一变更说明 |
| 时机 | EOV 分析仍未运行；M4 前分析禁令继续有效 |

---

## 1｜measurement state 由**三态升级为四态**

### 1.1 问题

`boundary_status = inferred` 的边界（TEM-1 的 `log10(1.5)`、Phillips2023 的 SI06/G189E = 6.0）陷入两难：

- 判为 `censored` → **把推断冒充事实**；
- 判为 `measured_exact` → **把可疑 floor 当成精确值**，过度声明确定性。

### 1.2 冻结的四态与判定表

$$
\boxed{\;\texttt{exact},\quad \texttt{censored},\quad \texttt{boundary\_ambiguous},\quad \texttt{missing}\;}
$$

| 情况 | canonical state |
|---|---|
| **明确文档化的 assay floor** 且满足 CL-7（重复全等 ∧ `SEM=0` ∧ 命中边界） | **`censored`** |
| `boundary_status = inferred` 且命中该 inferred floor | **`boundary_ambiguous`** |
| 未命中边界且正常测得 | **`exact`** |
| 无有效 measurement | **`missing`** |

> ⚠️ 三态时代的 `measured_exact` 一词**作废**，改称 **`exact`**；`boundary_ambiguous` 是**新增的独立状态，不得计入 `exact`，也不得计入 `censored`**。

### 1.3 逐数据集的落地结果（冻结）

| 数据集 | task | floor | `boundary_status` | 产生的状态 |
|---|---|---|---|---|
| CR9114 | h1 / h3 / fluB | 7.0 / 6.0 / 6.0 | `explicit` | **可产出真 `censored`** |
| **TEM-1CML** | AMP / AZT | log10(1.5) = 0.1760912591 | `inferred`（transformation） | **`boundary_ambiguous`** |
| **Phillips2023** | SI06 / G189E | 6.0 | `inferred`（assay_detection） | **`boundary_ambiguous`** |
| Phillips2023 | MA90 | 无 | `none` | **不产生任何边界删失** |
| Phillips2023 | expression | 无 | `none` | 全部 `exact` |

---

## 2｜新增 `censoring_evidence`，保留 `at_inferred_floor`

```
censoring_evidence ∈ {explicit, inferred, none}      # 新增（组级）
at_inferred_floor  ∈ {TRUE, FALSE}                    # 保留（诊断用，v1.2 已引入）
```

- `censoring_evidence` 记录**该组被判定为边界删失所依据的证据等级**（未命中边界者为 `none`）。
- `at_inferred_floor` **保留**，作为不依赖 canonical state 的独立诊断标记。

### 2.1 预注册的两条分析分支（M4 使用，M3 不执行）

$$
\text{primary}: \text{只把 } \texttt{censored}\ (\text{evidence}=\texttt{explicit}) \text{ 当删失}
$$
$$
\text{sensitivity}: \text{把 } \texttt{boundary\_ambiguous} \text{ 按 left-censored 处理}
$$

> **两分支必须在 Protocol 中预先写死，且在 M4 之前不得改动。**

---

## 3｜`degree_present` vs `degree_informative`（**禁止再笼统写 "effective degree"**）

### 3.1 问题

现有单一 `effective_degree` 容易掩盖一个关键事实 —— **CR9114 已给出极好的反例**：

| task | 上限钉扎 | `d_present` | `informative` 数 |
|---|---|---|---|
| h1 | 0.67% | 近似满值 | 62,762 |
| h3 | 88.69% | **仍近似满值** | **6,344** |
| fluB | 99.55% | **仍近似满值** | **164** |

→ h3 / fluB **几乎全都"看得见"，但真正有判别力的邻居已经塌掉**。

### 3.2 冻结定义

$$
d_{\texttt{present}}(x,\tau) = \#\{\,y \in \mathcal N_1(x) : \text{state}(y,\tau) \ne \texttt{missing}\,\}
$$

$$
d_{\texttt{informative}}(x,\tau) = \#\{\,y \in \mathcal N_1(x) : \texttt{informative}(y,\tau) = \text{TRUE}\,\}
$$

- **旧字段 `effective_degree` ≡ `d_present`**（**不删除、不改名**，保持历史兼容；文档中必须明确此等价关系，并**禁止**在其他语境继续使用"effective degree"这一笼统说法）。
- **M3 新增 `degree_informative`**。
- `boundary_ambiguous` 在 `d_present` 中**算作 present**（它不是 missing）；在 `d_informative` 中**是否计入由 §2.1 的分支决定** → **primary 分支下不计入**。

> **今后任何"local neighborhood"表述都必须写明**：**present neighborhood 还是 informative neighborhood？**

---

## 4｜未交付文件的处置（用户裁决，不再补做）

在台账与 closeout 中记录一条即可：

> **planned artifacts superseded by `M2_AUDIT_TABLE.csv` and `M2_QC_EVIDENCE.md`; never released as authoritative outputs.**

涉及：`M2_MATERIALIZATION_STATS.csv`、`M2_MATERIALIZATION_REPORT.md`、`M2_INFORMATIVE_RECONCILIATION.csv`。
**理由**：重复维护三套相同统计会造成数值漂移。

---

## 5｜TEM-1 结构化 missingness：冻结为 future analysis caveat（**不阻塞**）

已知事实（`M2_QC_EVIDENCE.md` §3）：AMP 46 组 / AZT 62 组缺 1 个重复，**逐药物内部全部浓度共享同一批**（批次级技术假象），且**偏向高突变负载**（均值 8.49 vs 全体 7.25）；规模 0.083% / 0.112%。

### 5.1 冻结的**禁止泄漏规则**（写入 Protocol）

> **不得因为某些 genotype 在 future task 上缺 measurement，就事后把它们从 Day-0 候选池中删除。**

候选池的构成只能由 **Day-0 信息**决定；future task 的可用性只能影响**评估**，不得影响**入选**。违反此条即构成 subtle leakage。

### 5.2 M3 范围内**不做**结果分析

此 caveat 在 parent eligibility / neighborhood comparison 中**仅作为 sensitivity 维度**保留，M3 不产出任何结论。

---

## 6｜M3 定义与执行顺序（用户裁决，逐字冻结）

**M3 — Measurement freeze & task-panel integration**

| 子阶段 | 内容 |
|---|---|
| **M3.0** | `AMENDMENT-011` + schema v1.4：新增 `boundary_ambiguous`、`censoring_evidence`、`degree_informative`；明确 `effective_degree ≡ degree_present`；更新 validators/tests。**随后重新生成 M2 audit table**，确认 inferred-floor 点**不再被计为 `exact`** |
| **M3.1** | **DAOx materialization**：严格 `task_panel`，5 个 substrate 独立 task，**不构图** |
| **M3.2** | **TEV_ProtRec materialization**：134 substrate/task，只做 measurement panel QC；**双向审计** $n_{\text{tasks per variant}}$ 与 $n_{\text{variants per task}}$，防止"134 tasks"只是极稀疏矩阵 |
| **M3.3** | **graph measurement geometry freeze**：仅 graph-eligible 输出 $d_{\text{topology}}, d_{\text{present}}, d_{\text{informative}}$；**CR9114 为压力测试** |
| **M3.4** | **`PHASE1_ANALYSIS_READY_MANIFEST.csv`**（M4 的真正入口，**不是分析结果**） |

### 6.1 `task_panel` 允许/禁止的输出（DAOx / TEV）

**允许**：task 数量、genotype/variant 数量、per-task measured fraction、`exact` / `censored` / `boundary_ambiguous` / `missing`、informative fraction、uncertainty coverage、cross-task measurement completeness。

**绝对禁止**：`d_topology` / `d_present` / `d_informative`（任何 degree 字段）。

> 目的：统一 schema 覆盖 **combinatorial landscape** 与 **task panel** 两类数据，**但不把它们强行塞进同一种数学对象**。

### 6.2 `PHASE1_ANALYSIS_READY_MANIFEST.csv` 的列（每个 dataset × task 一行）

`role` · `graph_eligible` · `task_panel_eligible` · `future_task_eligible` · `boundary_status` · `measurement_state_policy` · `informative_fraction` · `usable_uncertainty` · `source_hash` · `processed_hash` · `inclusion_exclusion_reason`

> 用户原话：**"从这一刻以后，哪些数据能进入哪一种科学问题，已经不能根据结果再改。"**

### 6.3 执行顺序（**不得颠倒**）

> **先升级四态 measurement semantics，再重生 M2 audit table；随后 materialize DAOx / TEV；最后冻结 present-vs-informative neighborhood 与 analysis-ready manifest。**

### 6.4 M4 前禁令（不变）

**不算 EOV，不算 regret，不排 parent，不看 Tomorrow-Test outcome。**

---

## 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| 11 | 2026-09-19 | schema v1.4 delta：**measurement state 四态**（新增 `boundary_ambiguous`，`measured_exact` → `exact`）；新增 `censoring_evidence`、保留 `at_inferred_floor`；**预注册 primary/sensitivity 两条分支**；新增 `degree_informative` 并明确 **`effective_degree ≡ degree_present`**；未交付三文件正式作废；TEM-1 结构化 missingness 冻结 + **禁止泄漏规则**；M3 定义、顺序与 MANIFEST 列冻结 |
