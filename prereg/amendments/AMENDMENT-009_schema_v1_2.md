# AMENDMENT-009 — schema v1.2（metadata-only）：task_panel、许可 provenance 拆分、replicate/boundary 记账、modality 分离

| 字段 | 值 |
|---|---|
| 版本 | **9** |
| 时间 | **2026-09-19** |
| 状态 | **FROZEN**（用户已裁决；本修正案为 **v1.2 的 delta**） |
| **对 M1 历史的影响** | **`prereg/M1_SCHEMA_SPEC.md` v1.1 原文与其 sha256 `ca142f6b0b4836b47880bc0e202ab70037d23abcfeebbc34d71763c586eb50d4` 一律保留、不得覆写**；本文件是 v1.1 → v1.2 的唯一变更说明 |
| 时机 | EOV 分析仍未运行；M4 前分析禁令继续有效 |

> **v1.2 只改 metadata 语义与校验契约，不改任何科学定义**（EOV / `V_{B,π}` / regret 的定义一律不动）。

---

## 1｜`dataset_role += task_panel`（用户裁决）

新增枚举值，**语义冻结为**：

> `task_panel` —— 同一蛋白背景下存在**多个 task/substrate measurement**，可用于 **task holdout / readiness** 等问题，但**不存在足够的 combinatorial genotype neighborhood**，因此**不得用于 budgeted graph adaptation**。

**硬性保证（必须落在代码，不靠 notes）**：

```
task_panel  ⇒  NOT landscape_graph_eligible
```

**角色分配（更新后）**

| dataset_id | role |
|---|---|
| `TEM-1CML` | `strict_multi_task` |
| `Phillips2023_HA_CH65` | `strict_multi_task` |
| `Phillips2021_CR9114`（h1） | `single_task_control` |
| `TrpB4_Johnston2024` | `single_task_control` |
| `Jalal2020_ParB_NBS` / `Jalal2020_Noc_parS` | `single_task_control` |
| **`TEV_ProtRec`** | **`task_panel`**（原 `oracle_only`） |
| **`DAOx_multi_substrate`** | **`task_panel`**（原 `oracle_only`） |
| `AncSR1_Starr2017` | `conditional`（直到技术读取完成） |
| 其余 oracle-only（PTE / MPH / Kosterlitz / Mira2015 / Bank2016 / CTX-M-14 / DHFR / Hsp90 等） | `oracle_only` |
| glmS / Soo2021 / Rotrattanadumrong | `modality_control` |

---

## 2｜许可与 provenance 拆分（用户裁决，比"拆两列"更精确）

**替换** 原单列 `license`，改为五个字段：

| 字段 | 含义 |
|---|---|
| `paper_license` | 论文/文章的许可 |
| **`source_data_license`** | **我们实际 ingest 的那份 artifact 的许可** —— 不等于"论文对应的某个官方 deposit 的许可" |
| `code_license` | 代码仓库许可（**可空**） |
| `redistribution_allowed` | 布尔 |
| **`redistribution_basis`** | **必填文本**：指向 `redistribution_allowed` 判定所依据的**具体 provenance 事实** |

**冻结理由（必须写进注释）**：完全可能存在

```
primary deposit = CC0     但     third-party repackaged file = license unclear
```

因此 **`redistribution_allowed` 不得由 `source_data_license` 机械推导**，必须由 `redistribution_basis` 说明。示例：

- `redistribution_basis = "Dryad dataset API v2 的 license 字段 = CC0-1.0（2026-09-19 实测）"`
- `redistribution_basis = "论文 CC BY 4.0，但我们 ingest 的是作者 GitHub artifact 且仓库无 LICENSE 文件 → 按 C8-2 local-only"`

**已确认的实例**：AncSR1（Dryad CC0-1.0，`redistribution_allowed = TRUE`）—— 用户已认同。

---

## 3｜replicate 记账与边界（**M2 第一优先级**）

### 3.1 replicate 三计数（新增，必填）

每个 `(genotype_id, task_id, condition_id)` 组必须记录：

```
n_expected    # 该组计划测量的重复数（如 TEM-1 triplicate = 3）
n_observed    # 实际有非空值的重复数
n_missing     # = n_expected − n_observed
```

### 3.2 冻结规则：**缺失重复 ≠ 删失 ≠ floor**

> NaN / 缺失重复首先是 `missing replicate`，**不是 measurement floor**。

- **不得填补**；**不得把 NaN 记为 `censored`**。
- 状态判定改用**剩余有效重复**：
  1. 有多个有效重复、且未触**已验证**边界 → `measured_exact`
  2. 全部缺失 → `missing`
  3. 重复值一致 ∧ `SEM == 0` ∧ **命中已验证 boundary** → `censored`
  4. **仅一个有效重复** → **保留该 measurement**，但**不得虚构 SEM**；`informative` 按**预注册的保守规则**判（沿用现行：SEM 缺省 ⇒ 边界条件不满足 ⇒ `informative = False`）

### 3.3 边界来源（新增，必填）

```
boundary_status ∈ {explicit, inferred, unresolved}
boundary_source ∈ {assay_detection, transformation, plate_clipping, author_statement, replicate_pattern, none}
```

**硬性禁令**：

> **绝不能把 observed min/max 当作 assay floor/ceiling。**

- `0.176091` 只能继续叫 **placeholder**。
- M2 必须先从原始测量结构判定边界究竟来自：assay 检测限 / 变换边界 / 板读数裁剪 / 作者明确规定 / 可由重复的边界模式可靠恢复。
- **证据不足时标 `boundary_status = unresolved`，不得为了跑 CL-7 硬造 floor。**
- **若 `boundary_status = unresolved` ⇒ 不得产出任何 `censored` 分类。**

---

## 4｜measurement modality 分离（新增）

```
measurement_modality ∈ {functional, auxiliary}
```

- `functional`：真正的功能任务读数（如 Phillips2023 的 MA90 / SI06 / G189E）。
- `auxiliary`：**同一批基因型上的非功能读数** —— 典型例子是 **Phillips2023 的 expression axis**。

**冻结规则**：

> **expression axis 是独立 measurement modality，不得悄悄当成第四个 functional task。**
> 仅作为 auxiliary measurement 保存；未来是否进入 **Today Information Set** 由 `PHASE1_PROTOCOL.md` 决定，**不由 M2 决定**。

---

## 5｜`graph_eligible` 与 QC 范围（用户裁决）

```
graph_eligible = (role ∈ {strict_multi_task, single_task_control})
                 ∧ 完整/密集乘积空间
                 ∧ observed_genotype_count == theoretical_space_size
```

| 类别 | 允许输出的 QC |
|---|---|
| **graph_eligible** | `degree_topology`、`degree_effective`（**纯 measurement availability geometry，绝不涉及 fitness value**） |
| **非 graph_eligible**（含 `task_panel`） | **只输出**：task coverage、measured fraction、censored fraction、informative fraction、uncertainty completeness —— **不得输出任何 graph degree** |

> **理由（用户）**：DAOx / TEV 这类 `task_panel` 没有合法的 combinatorial neighborhood，给它算 effective degree 会**重新制造概念污染**。

---

## 6｜版本与迁移

- `prereg/M1_SCHEMA_SPEC.md` 保持 **v1.1**、哈希不变（审计链完整）。
- `eov/schema.py` 增加 **`SCHEMA_VERSION = "1.2"`** 与 `validate_dataset_record_v12` / 迁移函数。
- `data_registry/PROVENANCE_LEDGER.csv` 迁移到新列结构（**必须通过新校验器**）。
- 新增 `tests/test_schema_v1_2.py`：覆盖 ① `task_panel` 不得 graph-eligible（硬防守）② 许可五字段与 `redistribution_basis` 必填 ③ `n_expected/n_observed/n_missing` 自洽 ④ `boundary_status=unresolved ⇒ 无 censored` ⑤ `auxiliary` modality 不被计入 functional task 数。
- **不得修改** v1.1 的任何已冻结数字。

---

## 7｜M2 的定义与出口（用户裁决，逐字冻结）

**M2 — Measurement semantics & dataset materialization**

| 子阶段 | 内容 |
|---|---|
| **M2.0** | metadata amendment：`task_panel`、许可 provenance 拆分、schema v1.2、迁移/校验测试。**不修改 v1.1 历史记录。** |
| **M2.1** | TEM-1 measurement semantics：per-task floor/ceiling、46 个 NaN replicate、exact/censored/missing、uncertainty、informative 状态 → 重新 materialize TEM-1 measurement 表 |
| **M2.2** | Phillips2023：三个 landscape task 完整接入；表达轴作为 auxiliary |
| **M2.3** | CR9114：三个 task 都保留原始事实（h1 informative；h3 大量 censored/noninformative；fluB 几乎全 floor）；**不删除 h3 / fluB**；role = dense single-task control（本身即 CL-7/CL-9 的压力测试） |
| **M2.4** | QC：仅对 graph-eligible 输出 topology / effective degree |

**M2 出口审计表**（每个 dataset × task 一行）：

`total genotype space` · `present` · `exact` · `censored` · `missing` · `informative` · `uncertainty available` · `floor source` · `ceiling source` · `graph eligible` · `effective-degree summary`（仅 graph eligible 时）

> 用户评语：**"这张表以后会非常值钱 —— 它实际上是我们整个分析可信度的地基。"**

---

## 8｜M2 期间的禁令（不变）

```
NO EOV   NO regret   NO parent ranking   NO Tomorrow-Test outcome
```

甚至**不"顺手看看哪个 parent 好"**。M2 只允许回答：

> **我们到底测到了什么，以及这些 measurement 在图上覆盖得怎么样？**

---

## 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| 9 | 2026-09-19 | schema v1.2 delta：`task_panel` 枚举 + 硬防守；许可五字段与 `redistribution_basis`；replicate 三计数与 `boundary_status/source`（**禁止 observed min/max 冒充检测边界**）；`measurement_modality` 分离；`graph_eligible` 与 QC 范围；M2 定义与出口审计表；v1.1 原文与哈希保留 |
