# M1_REPORT.md — schema 冻结 + provenance ledger + 无权 genotype graph

| 字段 | 值 |
|---|---|
| 阶段 | **M1**（执行指令见 `prereg/AMENDMENT-008_m1_preconditions.md` §5） |
| 时间 | **2026-09-19** |
| 环境 | `<PYTHON>` = **Python 3.12.3**，pandas **3.0.0**，pytest **9.0.1**（`<PYTHON_BROKEN>` 已损坏，未使用） |
| 状态 | 完成；**未写任何 EOV / regret / ranking 逻辑**（见 §8 声明） |

---

## 1. 结论

M1 的三件事全部完成并**自验证通过**：

1. **schema 冻结**：两平面分离（拓扑 vs 测量）、`measurement_state` 三态互斥、五个互斥 `dataset_role`、四种 `source_type`、14 列 measurement 长表、`informative` 定义、`degree_topology ≠ degree_effective`。
2. **provenance ledger**：**25 个数据集**逐项登记 `analysis_allowed` / `redistribution_allowed`（按 C8 provenance 原则），全部通过 `validate_dataset_record`。
3. **无权 genotype graph**：混合字母表乘积空间；节点/边**零载荷**；TEM-1 拓扑被 **21 个单元测试**完整验证（55,296 节点 / deg 18 / 497,664 边）。

---

## 2. 交付物与 sha256

| 文件 | 字节 | sha256 |
|---|---|---|
| `prereg/M1_SCHEMA_SPEC.md` | 10,328 | `ca142f6b0b4836b47880bc0e202ab70037d23abcfeebbc34d71763c586eb50d4` |
| `eov/schema.py` | 16,445 | `bb9471526a1d0e70fbbce8a12acc9f79d87c953e51b3ce9a29c534ead9fda7dc` |
| `eov/landscape.py` | 18,392 | `6cfba8c0b58456ee1e2e69e289e761a79ccb405044e211b2e689f4dfcbbca236` |
| `data_registry/PROVENANCE_LEDGER.csv` | 9,384 | `3e4513a9fa73198f1e7ddbf6a11952363352741cdb803d1ca812bbcd69832e17` |
| `tests/test_tem1_topology.py` | 17,622 | `537afe9bc681ff242a99c34d67de1d23c5e32c36e82d79f172cfdf4f6abbbcec` |
| `data_registry/M1_REPORT.md`（本文件） | — | **自指哈希不可自包含**：由父代理写入 `FREEZE_LEDGER.md` 时复算：<br>`(Get-FileHash -Algorithm SHA256 data_registry\M1_REPORT.md).Hash.ToLower()` |

未改动任何其他文件。

---

## 3. Schema 摘要（`prereg/M1_SCHEMA_SPEC.md` v1.1）

### 3.1 两个平面（M1 的核心防护）

| 平面 | 内容 | 是否可含 fitness |
|---|---|---|
| **拓扑** | genotype 节点 + "一步合法突变"边 | 🔴 **绝对不可** |
| **测量** | `(genotype_id, task_id, condition_id, replicate)` 上的观测 | ✅ 仅此处有 `value` |

future-task 的测量**天然挂在测量平面**，因此构图时**不可能**把未来任务信息混进拓扑。

### 3.2 三态互斥（C2 / CL-7）

`measured_exact` ｜ `censored`（**重复值完全相同 ∧ `sem == 0` ∧ 值落在 `floor`/`ceiling`**）｜ `missing`

* `censored` **不得**并入 `missing`（丢弃会引入反向偏差）；
* `censored` **不得**当作精确值（`sem=0` 是"未测到"：M0 实测 `CR9114_fluB` 地板占比 **0.997** ↔ 可用率 **0.3%**，逐位吻合）；
* `missing` 一律不得插补进主分析。

### 3.3 `informative`（CL-9）

`informative := state == measured_exact ∧ value > floor + 2·SEM ∧ value < ceiling − 2·SEM`（SEM 缺省时保守判 False；censored / missing 恒 False）。

### 3.4 两个 degree

| 量 | 定义 | 位置 |
|---|---|---|
| `degree_topology` | `Σ(位点等位数 − 1)`（完整乘积空间下恒定） | 拓扑平面；TEM-1 = **18** |
| `degree_effective` | 该节点在给定 `task_id` 下有可用测量的邻居数 | **由外部 measurement 表导出，绝不写进图** |

### 3.5 §3.1 构造规则（**v1.1 新增**，由真实数据冒烟测试反推）

> **未观测到的重复不得出现在长表里**；单元格完全无观测时只发射**一条** `missing` 行。

该规则消除了冒烟测试暴露的 46 行 / 20 组不一致（详见 §7）。

---

## 4. Provenance ledger 摘要（25 行 × 13 列）

| 维度 | 分布 |
|---|---|
| `source_type` | `author_deposit` **13** / `derived_aggregate` **9** / `journal_source_data` **2** / `secondary_distribution` **1** |
| `role` | `oracle_only` **15** / `single_task_control` **4** / `modality_control` **3** / `strict_multi_task` **2** / `conditional` **1** |
| `analysis_allowed` | TRUE **24** / FALSE **1**（AncSR1，需 R 读 Dryad `.rda`） |
| `redistribution_allowed` | TRUE **9** / FALSE **16** |

**关键登记（按 C8 = provenance-specific）**

| 数据 | license | redistribution |
|---|---|---|
| TEM-1CML | GPL-3.0 | ✅ |
| Phillips2023 / CR9114 | eLife **CC BY** | ✅ 署名 |
| TrpB4 | **CC0-1.0** | ✅ |
| Bank2016（Hsp90）原始 Dryad `th0rj` | **CC0-1.0** | ✅ |
| Bank2016（GraphFLA repack） | 派生 | 🔴 不得再打包 |
| CTX-M-14（woson2020 / MBE 2022） | 论文 CC BY，仓库无 LICENSE | ⚠️ local-only |
| CTX-M-14（Palzkill / PNAS 2024） | **CC BY-NC-ND** | 🔴 不得发布派生表 |
| PTE / MPH / Kosterlitz | **仓库无 LICENSE** | ⚠️ local-only |
| Mira2015（15 CSV） | 原始 PLoS One **CC BY**，**经 GraphFLA 二次分发** | ⚠️ 须回源补充材料 |
| MaveDB | 逐 score set **CC0 1.0** | ✅ |
| AncSR1 | **未核** | ⚠️ 未核 |
| TEV / DAOx / amiE / glmS | CC BY | ✅ / amiE local-only（原始 deposit URL 未核） |
| DHFR（Lozovsky）/ Hsp90 EMPIRIC | MIT / CC-BY（**父代理提供，M1 未独立复核**） | ⚠️ local-only |

**`validate_dataset_record` 逐行校验：25/25 通过，0 非法。**

---

## 5. Graph 接口与复杂度（`eov/landscape.py`）

### 5.1 接口

`MixedAlphabetSpace`：`space_size()`｜`degree_topology()`｜`allele_count_vector()`｜`iter_nodes()`（生成式）｜`neighbors()`（生成式）｜`neighbors_list()`｜`node_from_index()` / `index_of()`｜`node_id()` / `node_from_id()`｜`validate_node()`｜`from_masked_profiles()`｜`from_intended_csv()`

`GenotypeGraph`：`space_size()`｜`topology_degree(node=None)`｜`neighbors()`｜`iter_nodes()`｜`iter_edges(limit=None)`｜`edge_count()`（算术式）｜`materialize()`（受上限保护）｜**`effective_degree(node, measurement_table, task_id, condition_id, require_informative)`**｜`payload_audit()`

`MeasurementIndex`：**只保留 `(genotype_id, task_id, condition_id) → present/informative`，主动丢弃 `value`**（`__slots__` 里不存在任何数值槽）。这是"fitness 不得进入图平面"的**实现层**保障。

### 5.2 复杂度

| 空间 | \|V\| | d_topology | \|E\| = \|V\|·d/2 | 物化 |
|---|---|---|---|---|
| **TEM-1**（4×3³×2⁹） | **55,296** | **18** | **497,664** | ✅ 允许（≤ 60,000 上限） |
| Moulana（2¹⁵） | 32,768 | 15 | 245,760 | ✅ 允许 |
| Soo2021（4⁸，RNA） | 65,536 | 24 | 786,432 | ❌ 拒绝 → 生成式 |
| Phillips2023 / CR9114（2¹⁶） | 65,536 | 16 | 524,288 | ❌ 拒绝 → 生成式 |
| Jalal2020 / TrpB4（20⁴） | 160,000 | 76 | 6,080,000 | ❌ 拒绝 → 生成式 |

* `iter_nodes` / `neighbors` / `iter_edges`：**O(1) 额外内存**（生成式）；
* `materialize()`：O(|V| + |E|)，超过 `DEFAULT_MATERIALIZE_LIMIT = 60,000` 抛 `MemoryError`；
* 上限取值依据 M1 指令原文（"55,296 可全建；65,536 / 160,000 必须支持不显式建全图"）→ 取在 55,296 与 65,536 之间。

---

## 6. 测试运行结果（逐字粘贴）

### 6.1 直接运行

```
$ & '<PYTHON>' tests\test_tem1_topology.py
========================================================================
M1 TEM-1 topology tests — 21 tests
========================================================================
PASS  test_all_nodes_have_topology_degree_18
PASS  test_classify_informative_rules
PASS  test_classify_measurement_state_boundary_rules
PASS  test_degree_and_substitutions
PASS  test_edge_count_matches_closed_form
PASS  test_edge_enumeration_on_small_space_matches_formula
PASS  test_effective_degree_uses_only_measurement_state
PASS  test_graph_contract_has_no_fitness_payload
PASS  test_index_roundtrip
PASS  test_intended_csv_exists
PASS  test_iter_edges_limit_and_laziness
PASS  test_large_space_is_lazy_and_guarded
PASS  test_materialize_limit_policy_matches_m1_instruction
PASS  test_materialized_adjacency_agrees_with_lazy_neighbors
PASS  test_measurement_index_discards_values
PASS  test_mixed_alphabet_is_not_hypercube
PASS  test_neighbors_are_wellformed
PASS  test_node_id_roundtrip_on_real_profiles
PASS  test_product_identity_4x3pow3x2pow9
PASS  test_soo2021_style_rna_space_degree
PASS  test_space_geometry
------------------------------------------------------------------------
passed=21  failed=0  total=21
ALL TESTS PASSED
EXITCODE=0
```

### 6.2 pytest

```
$ & '<PYTHON>' -m pytest tests/ -q
.....................                                                    [100%]
21 passed in 0.76s
```

### 6.3 关键断言（M1 硬要求逐条对应）

| 要求 | 测试 | 结果 |
|---|---|---|
| 55,296 个节点 | `test_space_geometry` / `test_all_nodes_have_topology_degree_18`（**全枚举** 55,296 个节点） | ✅ |
| 13 位点 | `test_space_geometry` | ✅ |
| 等位数 = 2,2,3,2,4,2,2,2,2,3,2,3,2 | `test_space_geometry` | ✅ |
| 乘积 = 4×3³×2⁹ = 55,296 | `test_product_identity_4x3pow3x2pow9` | ✅ |
| 替换总数 = 3 + 3×2 + 9 = 18 | `test_degree_and_substitutions` | ✅ |
| 所有完整节点 degree = 18 | `test_all_nodes_have_topology_degree_18`、`test_neighbors_are_wellformed`（无自环/无重复/对称） | ✅ |
| 边数 = 55,296×18/2 = 497,664 | `test_edge_count_matches_closed_form` + 小空间**完整枚举**验证 `\|E\| = \|V\|d/2` | ✅ |
| 读取方式不用 `.split()` | 全部经 `pandas.read_csv`（`test_intended_csv_exists` 守卫） | ✅ |
| 大空间走生成式 | `test_large_space_is_lazy_and_guarded`、`test_materialize_limit_policy_matches_m1_instruction` | ✅ |

---

## 7. 真实数据冒烟测试（**仅 schema 层**）与由此产生的 spec v1.1

**动作**：把 TEM-1 `amp_auc_wide_df.parquet` 的 `Ampicillin 781.0` 三个重复列按长表 schema 展开，逐单元格跑三态判定 + 全表校验（**不做任何 EOV/regret/ranking**）。

**第一次运行发现两处真实不一致**：

```
invalid_rows=46  invalid_groups=20
  ['state=measured_exact requires a value']                      ← 某些重复列为 NaN
  declared state 'censored' != recomputed 'missing'              ← 组代表值误取 rows[0] 的空值
```

**根因**：源表存在 **46 个 NaN 重复单元格**，而我把"未观测到的重复"也发射成了行。

**修正两处**：
1. `prereg/M1_SCHEMA_SPEC.md` → **v1.1 §3.1 构造规则**：未观测重复不得发射；完全无观测只发一条 `missing` 行；
2. `eov/schema.py::validate_measurement_group` → 组代表值改取**第一个非空** `value`。

**修正后**：

```
rows=55294  AMP781 observed floor=0.176091
state counts: {'measured_exact': 55236, 'censored': 58, 'missing': 0}
emitted replicate rows=165836  skipped NaN replicate cells=46
validate_measurement_table -> rows=165836 groups=55294 invalid_rows=0 invalid_groups=0 ok=True
negative-control errors: ['state=censored requires informative=False', 'state=censored requires floor and/or ceiling to be set']
```

⚠️ **该冒烟测试的口径声明**：这里的 `floor = 0.176091` 是**观测最小值占位符**，**不是** assay 的真实检测下限；"censored = 58" 只是"值与观测最小值相同且零方差"的计数，**不构成对该 assay 删失率的任何主张**。真实 per-task `floor`/`ceiling` 必须按 DATA_AUDIT 规程在 **M2** 以实测方式确定。
唯一有价值的副产品：**`AMP 781` 存在 46 个 NaN 重复单元格**（数据质量观察，移交 M2）。

---

## 8. 禁令遵守声明（M1，AMENDMENT-008 §5）

> **本阶段未计算任何 EOV、regret、parent ranking 或 Tomorrow-Test 结果。**
> **未编写任何**搜索策略、预算模拟、可达性最大值（`R_k` / `R_{B,π}`）、selection regret、parent 排序、模型拟合代码。
> **图平面不含任何 task fitness**：节点与边均为纯 `tuple`，`MeasurementIndex` 主动丢弃 `value`，`effective_degree` 只读测量状态且结果**不缓存**到图上（`test_graph_contract_has_no_fitness_payload`、`test_measurement_index_discards_values`、`test_effective_degree_uses_only_measurement_state` 三项测试守住该约束）。

---

## 9. 已知缺口与移交 M2

| # | 缺口 | 影响 | 建议 |
|---|---|---|---|
| 1 | 冻结枚举**无 `task_panel` 值** | TEV（134 底物）/ DAOx（5 底物）暂以 `oracle_only` 登记并在 `notes` 强制标注"L1 task-panel, NOT a combinatorial landscape" | 需一条 amendment 决定是扩枚举还是维持现状 |
| 2 | `AMP 781` 有 **46 个 NaN 重复单元格** | 三态展开时必须跳过（spec §3.1 已规则化） | M2 报告实际可用重复数 |
| 3 | 真实 per-task `floor` / `ceiling` 未定 | `censored` 判定目前只能靠观测最小值占位 | **M2 首要动作**：逐 task×condition 实测边界 |
| 4 | TEM-1 processed wide 表 55,294 < 55,296（少 3 个真实基因型、多 `XXXXXXXXXXXXX` dead 锚点行） | `degree_effective` 必然 < 18 | M2 显式报告有效度分布 |
| 5 | `PROVENANCE_LEDGER.csv` 中 5 行的 URL/license 标为 `NOT_VERIFIED_IN_M1`（Jalal2020×2、Soo2021、Rotrattanadumrong、amiE、Hsp90 EMPIRIC、DHFR 等） | 只影响再分发，不阻塞分析 | 回源后补登 |
| 6 | AncSR1 需 R 读 Dryad `.rda` | `analysis_allowed=FALSE` | 用户已决定暂不索取 |
| 7 | **C9 = G-FTI（future-task identifiability）** | M4 前置，**不阻塞 M2** | M4 前对全部 AZT 浓度做预注册选点 |

**M1 结束时状态**：`eov/` 下只有 `schema.py` 与 `landscape.py`；`experiments/`、`analyses/`、`figures/` 仍为空；`data/` 未新增任何下载。
