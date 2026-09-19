# AMENDMENT-010 — schema v1.3（metadata-only）：`value_group` 组代表值、`genotype_id` 规范性、fail-loud 原则

| 字段 | 值 |
|---|---|
| 版本 | **10** |
| 时间 | **2026-09-19** |
| 状态 | **FROZEN**（依据我在 M2 验收中实测发现的两处缺陷） |
| **对历史的影响** | `prereg/M1_SCHEMA_SPEC.md` v1.1（`ca142f6b…`）与 `prereg/AMENDMENT-009_schema_v1_2.md` v1.2（`162e54c0…`）**原文与哈希一律保留**；本文件是 v1.2 → v1.3 的唯一变更说明 |
| 时机 | EOV 分析仍未运行；M4 前分析禁令继续有效 |

> v1.3 只修**两个会导致静默错误**的缺陷，不改变任何科学定义。

---

## 1｜缺陷 B 的修法：新增 `value_group`（组代表值）并由它计算 `informative`

### 问题（实测）

`informative` 被从**某一个重复值**计算 → **依赖输入行序**。逐任务复算显示三处都精确命中 "first replicate"：

| 任务 | first-rep | mean | median | 交付值 |
|---|---|---|---|---|
| CR9114 h1 | **62,916** | 62,817 | 62,762 | **62,916** |
| CR9114 h3 | **6,506** | 6,475 | 6,344 | **6,506** |
| Phillips2023 SI06 | **28,064** | 28,507 | 28,507 | **28,064** |

→ 文件换个排序，SI06 的 `informative` 就变 **443**（1.6%），**且不报错**。

### 冻结规则（v1.3）

1. measurement 长表**新增列 `value_group`**：该 `(dataset_id, task_id, condition_id, genotype_id)` 组的**代表值**。
2. **`value_group = median(该组全部有效重复值)`** —— 三个数据集一律用 median。
   **依据**：TEM-1 作者自己的约定即 median（`DATA_README.md`：`Fitness : Median AUC value (from local/processed long format files)`，且 `Epistasis_Combined.parquet.Fitness = median AUC`）；对 eLife 两个数据集，median 与作者直觉一致且不受单一重复值支配。
3. `value_group` 与 `value_sem` / `value_sd` / `measurement_state` / `informative` / `floor` / `ceiling` 同属**组级字段**，在组内**必须恒定**。
4. **`informative` 一律且只能由 `value_group` 计算**：

$$
\text{informative} = (\text{state}=\texttt{measured\_exact}) \wedge (\text{SEM} \ne \text{NULL}) \wedge (v_g > \text{floor} + 2\,\text{SEM}) \wedge (\text{ceiling}=\text{NULL} \vee v_g < \text{ceiling} - 2\,\text{SEM})
$$

   **禁止**再用任何单个重复值、任何"第一个/最后一个"取值。
5. **`floor` 为 NULL 时该侧视为无约束**（已由 MA90 的实测确立：MA90 无下限，`informative` = 65,530 = 全部 present）；**`ceiling` 为 NULL 同理**。
6. **SEM 为 NULL 时该侧条件视为不满足** → `informative = False`（保守，沿用 v1.1 既定规则）。

### 普遍原则（写入规程，适用于未来任何数据集）

> **任何组级派生标志，必须由规范化的组代表值计算，绝不能依赖某一行的位置。**
> 凡"逐行计算再断言其组内恒定"的实现，都是**行序依赖**的伪装形式 —— 即使当前数据恰好恒定，换一次排序就会暴露。

---

## 2｜缺陷 A 的修法：`genotype_id` 的**规范性**

### 问题（实测）

CR9114 的 `genotype_id` **丢失前导零**：唯一值长度分布为 `{1:2, 2:2, 3:4, …, 15:16384, 16:32768}`（指数型剥零签名），仅 **50%** 命中规范 16 位串。
**成因**：读 CSV 时未指定 `dtype=str`，`genotype` 列被解析为整数。
**后果**：**非规范 key 根本无法构造基因型空间** —— 我的审计表生成器直接抛错：
`ValueError: profiles have inconsistent lengths: [1, 2, 3, …, 16]`。

### 冻结规则（v1.3）

1. `genotype_id` 必须是**该数据集空间的正则编码**，且**唯一由位点列构造**，不得来自可能被数值解析的列：

| 数据集 | `genotype_id` 的规范形式 | 长度 |
|---|---|---|
| TEM-1CML | `mut_profile_masked`（`.` = WT，字母 = 替换，`X` = dead） | **13** |
| Phillips2023 | xlsx 的 `geno`（共享字符串，文本） | **16** |
| Phillips2021_CR9114 | **`pos1..pos16` 拼接的 0/1 串**（不得用被读成整数的 `genotype` 列） | **16** |

2. 一切 CSV 读取，凡涉及基因型/序列字符串，**必须 `dtype=str`**。
3. **fail-loud 原则**：任何按 `genotype_id` 构造图或 join 的代码，遇到非规范 key 必须**立即抛错**，不得静默跳过或部分匹配。
   （反例警示：非规范 key 与规范 key 恰好约 50% 重合时会产出"均值恰好等于理论最大值一半"的**看似合理但完全错误**的结果。）

---

## 3｜验收要求（返工后必须提供）

1. `genotype_id` 长度分布：CR9114 全部为 **16**；TEM-1 全部为 13；Phillips2023 全部为 16。
2. 组级字段（`value_group` / `informative` / `value_sem` / `value_sd` / `measurement_state` / `floor` / `ceiling`）在**正确组键**下 **0 违规**。
3. `M2_INFORMATIVE_RECONCILIATION.csv`：逐 (dataset, task) 给出 `first_rule_count / mean_rule_count / median_rule_count / delivered_count` 与边界反例样本行。
4. 重跑 `validate_measurement_table_v12`（并新增 v1.3 校验入口）的真实输出，**0 错误**。
5. 三个文件的 sha256。

---

## 4｜对既有交付的处置

| 文件 | 处置 |
|---|---|
| `data/processed/M2_measurements.parquet`（`1fc7bb39…`，含 A/B 两缺陷） | ⚠️ **作废，由返工版替换**（台账批次 #14 已留痕） |
| `data_registry/M2_QC_EVIDENCE.md`（`35e103b9…`） | ✅ 有效（含缺陷对账证据与我自己的两次误判留档） |
| `eov/audit_table.py`（`1ba70b72…`） | ✅ 有效；其 fail-loud 行为即缺陷 A 的证据 |
| `present` / `censored` / `missing` 结构性计数 | ✅ 已验证一致，返工不得改变它们 |

---

## 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| 10 | 2026-09-19 | schema v1.3 delta：新增 **`value_group`（冻结 median）** 且 `informative` 只能由它计算；**`genotype_id` 规范性**按数据集定义 + `dtype=str` 强制 + **fail-loud 原则**；写入"组级派生标志不得依赖行位置"的普遍规程；v1.1 / v1.2 原文与哈希保留 |
