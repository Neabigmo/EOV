# M1_SCHEMA_SPEC.md — Phase I 测量 schema 与数据契约（冻结）

| 字段 | 值 |
|---|---|
| 版本 | **1.0** |
| 时间 | **2026-09-19** |
| 状态 | **FROZEN** |
| 实现 | `eov/schema.py`（枚举 + 行校验 + 三态判定） |
| 上游依据 | `prereg/AMENDMENT-008_m1_preconditions.md`、`PHASE1_DATA_GATE.md` v3（C1–C9）、`data_registry/DATA_AUDIT.md` v3、`data_registry/M0_verification_log.md` |

> **本 spec 冻结"数据长什么样"，不冻结"怎么分析"。**
> 本阶段（M1）**只允许**构建 schema、provenance ledger 与**无权** genotype graph。
> **禁止**：EOV、regret、parent ranking、任何 Tomorrow-Test 结果、搜索策略、预算模拟、可达性最大值、模型拟合。

---

## 1. 两个平面：拓扑 vs 测量

| 平面 | 对象 | 是否携带 fitness |
|---|---|---|
| **拓扑平面** | `genotype` 节点 + "一步合法突变"边 | 🔴 **绝对不携带**（`eov/landscape.py`） |
| **测量平面** | `(genotype_id, task_id, condition_id, replicate)` 上的观测 | ✅ 只有这里可以有 `value` |

**设计后果（这是 M1 的核心防护）**：future-task 的测量**天然挂在测量平面**上，因此**不可能**在构图时泄漏进拓扑平面。图里**没有**任何 `task_id`、`condition_id`、`value`、`weight`。

---

## 2. 枚举（互斥，冻结）

### 2.1 `measurement_state`（**三态互斥**，AMENDMENT-008 §5-4）

| 值 | 定义 | 允许的 `value` | `informative` |
|---|---|---|---|
| `measured_exact` | 有可用测量，且**不是**删失 | 非空 | 可能 True |
| `censored` | **重复值完全相同 ∧ `value_sem == 0` ∧ 值落在 `floor`/`ceiling` 边界上** | 等于边界值 | **必须 False** |
| `missing` | 未测 / 不可用 / 值缺失 | 必须为空 | **必须 False** |

**铁律**：三者**互斥**，且
1. **`censored` 不得并入 `missing`**（删失是"有界的真实观测"，丢弃会引入反向偏差）；
2. **`censored` 不得当作精确值**（`sem=0` 的含义是"未测到"，不是"零噪声"——M0 实测：`CR9114_fluB` 地板占比 **0.997** ↔ 可用率 **0.3%**，逐位吻合）；
3. `missing` 一律**不得插补**进入主分析。

### 2.2 `dataset_role`（**互斥**，AMENDMENT-008 §3）

| 值 | 含义 | 当前归属 |
|---|---|---|
| `strict_multi_task` | 组合完整 ∧ 真多任务 | **TEM-1CML、Phillips2023** |
| `single_task_control` | 组合完整但**单任务**（**不得当作 multi-task evidence**） | **CR9114-h1**、TrpB4 |
| `oracle_only` | 空间过小（`B ≤ \|space\|/4` 不成立）或非组合空间 | Mira2015、Kosterlitz、PTE、MPH、（TEV/DAOx：L1 任务面板） |
| `modality_control` | 非蛋白模态（仅作定义普适性检验） | glmS、Soo2021、Rotrattanadumrong |
| `conditional` | 依赖未决前提 | AncSR1 |

> ⚠️ **已知缺口（需后续 amendment）**：冻结枚举**没有** `task_panel` 值。TEV ProtRec（134 底物）与 DAOx（5 底物）在 `PHASE1_DATA_GATE.md` v3 中被归为 **L1 任务面板**，本表**暂以 `oracle_only` 登记并强制在 `notes` 中写明 "L1 task-panel, NOT a combinatorial landscape"**；不得据此把它们当作可做预算型主张的组合景观。

### 2.3 `source_type`（**互斥**，AMENDMENT-008 §2.1）

`author_deposit` ｜ `journal_source_data` ｜ `secondary_distribution` ｜ `derived_aggregate`

**再分发政策按 provenance 判定，不按数据集名判定（C8）**：

| provenance | redistribution |
|---|---|
| 原始 deposit 有明确开放许可（CC0 / CC BY / MIT / GPL） | 按该许可（署名等照办） |
| 第三方 repack / 无 LICENSE 的 GitHub artifact | **local-only**：只存 URL/DOI + sha256 + 获取时间，**不随仓库再分发** |
| 含 **ND** 条款 | **不得发布派生表**，仅内部 robustness |

---

## 3. measurement 长表（冻结列）

每行 = **一个 replicate 的一次观测**；组级汇总字段（`value_sem`/`value_sd`/`measurement_state`/`floor`/`ceiling`/`informative`）在同一 `(genotype_id, task_id, condition_id)` 组内**全部相同**（反规范化，便于逐 replicate 重采样）。

| # | 列 | 类型 | 说明 |
|---|---|---|---|
| 1 | `protein` | str | 蛋白/系统标识（如 `TEM-1`、`influenza HA RBS`） |
| 2 | `dataset_id` | str | 唯一数据集 ID（与 `PROVENANCE_LEDGER.csv` 主键一致） |
| 3 | `genotype_id` | str | **必须等于拓扑平面节点的字符串形式**（TEM-1 = 13 位 `mut_profile_masked`，`.` = WT） |
| 4 | `task_id` | str | 任务（如 `AMP`、`AZT`、`MA90`、`G189E`、`exp_norm`） |
| 5 | `condition_id` | str | 任务内条件（如 `781.0 ug/mL`、`36.0 ug/mL`、`metal=Mn`） |
| 6 | `replicate` | str/int | 重复标识（`1/2/3` 或 `repa/repb/repc`） |
| 7 | `value` | float\|null | **本 replicate** 的测量值（原始量纲，永不覆盖） |
| 8 | `value_sem` | float\|null | 组级 SEM（无则空） |
| 9 | `value_sd` | float\|null | 组级 SD（无则空） |
| 10 | `measurement_state` | enum | §2.1 三态 |
| 11 | `floor` | float\|null | 该 task×condition 的检测下限（**实测确定**，不得沿用论文措辞） |
| 12 | `ceiling` | float\|null | 检测上限 |
| 13 | `informative` | bool | 见 §4 |
| 14 | `source_row_ref` | str | 原始文件内的行定位（文件相对路径 + 行号/索引），用于回溯 |

**不允许的列**：任何归一化后的 fitness 覆盖列（归一化只能**新增**列，原始 `value` 永久保留）。

### 3.1 构造规则（**长表只发射被观测到的重复**）

1. **未观测到的重复不得出现在长表里**：若某重复列为空/NaN，就不要发射该行。一个 `(genotype × task × condition)` 单元格若**完全没有**观测，只允许发射**一条** `measurement_state = missing` 的行（`value` 为空，`replicate` 仍须填写以便定位）。
2. 因此 `measured_exact` / `censored` 组内**不允许出现空 `value`** —— 空值即违反 schema（`validate_row` 会报错）。
3. 组代表值（用于边界检验）取该组**第一个非空** `value`；`censored` 组因"重复值完全相同"而必然等于边界值。
4. `value_sem` / `value_sd` / `floor` / `ceiling` / `measurement_state` / `informative` 为**组级**字段，组内每行必须相同。

> 依据：M1 冒烟测试在真实 TEM-1 `AMP 781` 数据上发现 46 行"measured_exact 但某重复为 NaN"、
> 20 组"声明与重算不一致"，全部由"把未观测重复也发射出来"引起。规则 1 消除该不一致的根源。

---

## 4. `informative` 的定义（CL-9）

$$
\text{informative} \;=\; \big(\text{state} = \texttt{measured\_exact}\big) \;\wedge\; \big(\text{value} > \text{floor} + 2\cdot\text{SEM}\big) \;\wedge\; \big(\text{value} < \text{ceiling} - 2\cdot\text{SEM}\big)
$$

（`SEM` 缺省时该侧条件视为**不满足** → `informative = False`，保守。）
`censored` 与 `missing` **一律** `informative = False`。

**用途**：任务准入闸门用 **`informative_frac`**（≥50% 主 / 20–50% 敏感 / <20% 排除）。
**M0 反例**：`SI06` 的 `usable_frac = 50.7%` 但 `informative_frac = 43.0%`（mean 中位数落在 floor 上）→ 只看 usable 会放过它。

---

## 5. 图侧的两个 degree（**必须分开**，AMENDMENT-008 §5-3）

| 量 | 定义 | 写在哪儿 |
|---|---|---|
| `degree_topology` | `Σ(位点等位数 − 1)`，**完整乘积空间下对每个节点恒定** | **拓扑平面**；TEM-1 = **18** |
| `degree_effective` | 该节点的 Hamming-1 邻居中，在**给定 `task_id`（可选 `condition_id`）**下**存在可用测量**的个数 | **由 measurement 表导出，绝不写进图**（`GenotypeGraph.effective_degree(node, measurement_table, task_id, ...)`） |

**"可用"的两种口径**（显式选择，不得混用）：
- `require_informative=False` → 存在 `measurement_state != missing` 的记录（**present**）；
- `require_informative=True` → 存在 `informative == True` 的记录（**informative**）。

**TEM-1 实例**：拓扑 degree 恒为 18；但 processed wide 表只有 **55,294** 行（少 3 个真实基因型，多 1 个 `XXXXXXXXXXXXX` = dead 锚点行）→ **有效度必然低于 18**，且必须在 M2 显式报告。

---

## 6. 数据集级元数据（冻结字段）

| 字段 | 说明 |
|---|---|
| `theoretical_space_size` | 乘积空间大小（TEM-1 = 55,296 = 4×3³×2⁹） |
| `complete_product` | bool：**实测**行数是否等于 `theoretical_space_size` |
| `observed_genotype_count` | 实测唯一基因型数 |
| `source_type` / `original_deposit_url` / `fetched_url` / `license` | provenance（§2.3） |
| `analysis_allowed` | 科学分析能否进行 |
| `redistribution_allowed` | release 能否带原始文件 |
| `role` | §2.2 |

> `analysis_allowed` 与 `redistribution_allowed` **不得互相阻塞**（AMENDMENT-008 §2.2）。

---

## 7. 校验契约（`eov/schema.py`）

- `validate_row(row) -> list[str]`：空列表 = 合法。检查：必需列、枚举取值、三态与 `value`/`informative` 的一致性、边界与状态一致性、`replicate` 非空、非负误差。
- `validate_measurement_table(rows) -> dict`：逐行校验 + 返回统计（各状态计数、合法/非法行数）。
- `validate_dataset_record(rec) -> list[str]`：数据集级元数据校验（含 `complete_product` 与两个计数的自洽）。
- `classify_measurement_state(replicates, sem, value, floor, ceiling) -> MeasurementState`：三态判定（**只读重复值与边界，不做任何 fitness 分析**）。
- `classify_informative(state, value, sem, floor, ceiling) -> bool`：§4。

**声明**：`schema.py` 内**不含**任何 EOV / regret / ranking / 搜索 / 阈值选择逻辑。

---

## 8. 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| 1.0 | 2026-09-19 | M1 初版冻结：两平面分离、三态互斥、五个互斥 role、四种 provenance、14 列长表、`informative` 定义、degree 二分、数据集级元数据、校验契约。记录 `task_panel` 枚举缺口。 |
| 1.1 | 2026-09-19 | 新增 **§3.1 构造规则（只发射被观测到的重复）**：由真实 TEM-1 AMP 781 冒烟测试发现的不一致（46 行 / 20 组）反推得出；同步修正 `eov/schema.py` 的组级校验（组代表值取第一个非空 `value`）。 |
