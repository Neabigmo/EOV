# M1_INDEPENDENT_VERIFICATION.md — 我对 M1 关键数字的独立复算

> 目的：在 M1 交付物（schema / provenance ledger / 无权 genotype graph）之外，**由我独立复算**其必须满足的不变量，作为交叉核对基准。
> 方法：临时脚本在 `%TEMP%` 运行，**项目目录未落任何数据文件**。
> **本文件不含任何 EOV / regret / parent ranking / Tomorrow-Test 计算**（M4 前禁令有效）。

---

## 1｜TEM-1 genotype topology —— 全部不变量成立

数据源：`data/external/TEM1_Gaszek2025/data/processed/TEM1-combinatorial-mutagenesis-intended.csv`

| 检查项 | 实测值 | 判定 |
|---|---|---|
| 节点数 | **55,296**（unique 亦 55,296） | ✅ |
| 位点数 | 13 | ✅ |
| 各位点等位数 | **`2, 2, 3, 2, 4, 2, 2, 2, 2, 3, 2, 3, 2`** | ✅ |
| 各位点等位集 | `.P`｜`.K`｜`.LV`｜`.K`｜`.HNS`｜`.T`｜`.T`｜`.S`｜`.K`｜`.CS`｜`.M`｜`.LQ`｜`.D` | ✅ |
| 乘积 | $4 \times 3^3 \times 2^9 = \mathbf{55{,}296}$ | ✅ **= 节点数** |
| 替换总数 | $3\times1 + 3\times2 + 9\times1 = \mathbf{18}$ | ✅ |
| **degree 分布** | **`{18: 55296}`** —— 每个节点恰好 18 | ✅ |
| **空间对单步突变闭合** | **是**（无任何节点存在缺失邻居） | ✅ |
| sum(degrees) | 995,328 | ✅ |
| **边数** | $995{,}328 / 2 = \mathbf{497{,}664}$ | ✅ **= 55,296 × 18 / 2** |

→ **这组数字即 M1 单元测试必须断言的内容。** 我的复算与 AMENDMENT-008 §5-5 的要求逐条一致。

---

## 2｜🔴 **有效 degree（`degree_effective`）几乎完全 —— 一个重要的正面结果**

**定义**：在该节点的 18 个 topology 邻居中，`Ampicillin 781.0` 下**三个重复齐全**（即 `measured` 而非 missing/censored）的个数。

| 统计量 | 值 |
|---|---|
| wide 表行数 | 55,294 |
| AMP 781 下三重复齐全的基因型 | **55,248** |
| **mean effective degree** | **17.984** |
| median / min / max | 18 / **15** / 18 |
| **eff_deg = 18** | **54,453（98.48%）** |
| eff_deg = 17 | 807（1.46%） |
| eff_deg = 16 | 33（0.06%） |
| eff_deg = 15 | 3（0.01%） |
| **eff_deg ≥ 9（OP-6 的 50% 门槛）** | **55,296（100.0%）** |

### 含义（必须写进后续分析设计）

我在 AMENDMENT-001/002 把"**measured-neighborhood 大小不齐**"列为最危险的方法学漏洞（B2），担心"邻居看不见"会被误读成"附近没有好未来"。

> **实测结论：在 TEM-1 上这个混杂不成立。** 98.48% 的节点其 18 个邻居全部可用，且**全部节点都满足 OP-6 的 ≥50% 门槛**。
> → TEM-1 是**理想的主数据**：拓扑结构与有效测量几乎重合，`N_k(x)` 的边界效应可忽略。
> → 但该结论**不能外推**到其它数据集：Phillips2023 的 SI06（informative 43.0%）、Moulana 的 CB6（缺失 49.6%）仍必须逐任务做 effective degree 分层。

---

## 3｜交叉核对基准（供 M1 交付物比对）

| 量 | 我的独立值 |
|---|---|
| 节点数 | `55296` |
| 边数 | `497664` |
| topology degree（全体） | `18` |
| 等位数向量 | `[2,2,3,2,4,2,2,2,2,3,2,3,2]` |
| 替换总数 | `18` |
| AMP 781 下 measured 基因型 | `55248` |
| 最大 eff_deg / 最小 eff_deg | `18` / `15` |

**若 M1 交付物的测试输出与上表任一数字不符，以本表为准并回退修改。**

---

## 4｜许可空白关闭：Dryad 两处 deposit 均为 **CC0-1.0**（我实测）

`provenance ledger` 需要 `license` / `analysis_allowed` / `redistribution_allowed`。此前唯一未核的 AncSR1 现已核实：

| DOI | 标题（API 返回） | 版本 | **license** |
|---|---|---|---|
| `10.5061/dryad.jsxksn0hk`（**AncSR1**） | "Epistasis facilitates functional evolution in an ancient transcription factor" | v3, `submitted` | ✅ **CC0-1.0** |
| `10.5061/dryad.th0rj`（**Bank2016**，对照复核） | "Data from: On the (un)predictability of a large intragenic fitness landscape" | — | ✅ **CC0-1.0** |

**推论（对 schema/ledger 的影响）**：
1. **AncSR1 的阻塞是纯技术性的，不是法律性的** —— 数据为 **CC0-1.0**（`analysis_allowed = ✅`、`redistribution_allowed = ✅`），唯一障碍是 **20 个文件全是 R `.rda` / `.gexf`、无 CSV，需装 R 才能读**。
2. **Bank2016 的原始 deposit 亦为 CC0-1.0** → 与 AMENDMENT-008 §2.1 一致：**应从 Dryad 回源**，GraphFLA 的整理版**不得再打包**。
3. 两者均为 **CC0（无署名义务）**，是本项目许可最宽松的两个数据源。

---

## 5｜🔴 许可审计：**"论文许可" ≠ "数据 deposit 许可"**（必须进 schema）

我对 `provenance ledger` 里所有"CC BY / CC0"声明做了独立审计（Crossref API + CaltechDATA API + Zenodo API + Dryad API 实测）。

**审计发现：论文与数据 deposit 的许可可以完全不同，而决定"我们能否再分发下载到的数据文件"的是 deposit。**

| 数据 | **论文许可**（Crossref 实测） | **数据 deposit 许可**（实测） |
|---|---|---|
| **TrpB** | **CC BY-NC-ND 4.0** | **CaltechDATA `h5rah-5z170` = CC0-1.0** ✅ |
| **DAOx** | **CC BY-NC-ND 4.0** | **Zenodo `15846928` = CC BY 4.0** ✅ |
| **TEM-1 Gaszek** | **CC BY-NC-ND 4.0** | **GitHub 仓库 = GPL-3.0** ✅ |
| glmS | CC BY 4.0 ✅ | RNAGym raw（⚠️ 待核） |
| TEV ProtRec | CC BY 4.0 ✅ | Zenodo `15346003`（⚠️ 待核） |
| Kosterlitz | CC BY 4.0 ✅ | Zenodo `10045641`（⚠️ 待核） |
| Mira 2015 | CC BY 4.0（PLoS One）✅ | **仅 GraphFLA 二次分发** |
| Phillips2023 / CR9114 | CC BY 4.0 ✅ | eLife source data（随文，CC BY） |
| CTX-M-14（Palzkill, PNAS 2024） | CC BY-NC-ND 4.0 | 作者 GitHub **无 LICENSE** |
| CTX-M-14（woson, MBE 2022） | CC BY 4.0 | 作者 GitHub **无 LICENSE** |
| **Bank2016** | PNAS user license（Crossref 无 CC） | **Dryad `th0rj` = CC0-1.0** ✅ |
| **AncSR1** | — | **Dryad `jsxksn0hk` = CC0-1.0** ✅ |

### 结论（三条，必须写进 schema 与 ledger）

1. **`license` 必须拆成两列**：`paper_license` 与 `data_deposit_license`。
2. **`redistribution_allowed` 以 `data_deposit_license` 为准**（我们下载与再分发的是数据文件，不是论文）。
   → 例：**TrpB 的论文是 ND，但数据 deposit 是 CC0 → 数据可再分发**；**DAOx 数据为 CC BY → 可再分发（署名）**。
3. **不得用论文许可去否定数据 deposit 的宽许可，也不得用 deposit 许可去解释论文内容的使用** —— 两者服务于不同的用途（`analysis_allowed` 几乎总为 ✅；限制集中在 `redistribution_allowed`）。

---

## 6｜`PROVENANCE_LEDGER.csv` 审计（25 行）—— 需要应用的差异

我逐行核对了子代理产出的 ledger（25 个数据集；`source_type` 分布 author_deposit 13 / derived_aggregate 9 / journal_source_data 2 / secondary_distribution 1；`role` 分布 strict_multi_task 2 / single_task_control 4 / oracle_only 15 / conditional 1 / modality_control 3；`redistribution_allowed` TRUE 9 / FALSE 16）。

**判定正确的部分**（抽查确认）：`TrpB4 = CC0-1.0`（deposit 许可，非论文的 NC-ND）✅；`Bank2016` 拆成 Dryad（CC0，可再分发）与 GraphFLA repack（禁止再打包）✅；`CTX-M-14` 分成 woson2020 与 Palzkill2024 两个数据集 ✅；`CR9114 = single_task_control`（AMENDMENT-008 §3 已生效）✅；TEV / DAOx / glmS 的 CC BY 与我的 Crossref 实测一致 ✅。

**需要应用的差异（1 项实质 + 3 项标注）**：

| dataset_id | ledger 当前 | **应改为** | 依据 |
|---|---|---|---|
| **`AncSR1_Starr2017`** | `analysis_allowed = FALSE`、`redistribution_allowed = FALSE`、license = "NOT VERIFIED" | **`analysis_allowed = TRUE`**、**`redistribution_allowed = TRUE`**、`license = CC0-1.0` | **Dryad `10.5061/dryad.jsxksn0hk` API 实测 = CC0-1.0**（我本轮核实）。→ **AncSR1 的阻塞是纯技术性的（20 个文件全是 R `.rda`/`.gexf`，无 CSV，需装 R），不是法律性的** |
| `TEV_ProtRec` | CC BY 4.0 | 补注"paper CC BY 4.0（Crossref 实测）；**Zenodo `15346003` 的 deposit 许可未核**" | 见 §5 的"论文 ≠ deposit"规则 |
| `DAOx_multi_substrate` | CC BY 4.0 | 补注"**deposit（Zenodo `15846928`）CC BY 4.0 实测**；论文为 CC BY-NC-ND" | 同上 |
| `glmS_Andreasson2020` | CC-BY-4.0 | 标注"Crossref 实测 CC BY 4.0"；**RNAGym raw 包本身的许可仍待核** | 同上 |

**仍未核实（保持 FALSE / 待核，不得假定）**：`Jalal2020_*`（两项）、`Soo2021`、`Rotrattanadumrong2022`（三者均为 GraphFLA 派生来源）、`Kosterlitz_blaTEM` 的 Zenodo 记录、`DHFR_Lozovsky` 的 MIT、`Hsp90_EMPIRIC` 的 CC-BY、`amiE_Wrenbeck2017` 的 CC BY。

**结构性建议（非阻塞）**：`license` 目前是**单列复合字符串**（把论文许可与 deposit 许可写在同一个字段里）。按 §5 的结论，建议 schema 拆为 **`paper_license` + `data_deposit_license`** 两列，并令 `redistribution_allowed` 仅由后者推导 —— 使该判定可被机器校验而非依赖 notes 文字。

---

## 7｜**集成验证**：用真实 TEM-1 数据跑交付代码，逐格复现 ground truth ✅

我不只是重跑它的测试，而是**用真实数据调用它的 API**，与我独立算出的分布逐格比对。

**脚本在 `%TEMP%` 运行，项目目录未写入任何数据。**

```
space_size      = 55296      (我独立值 55296)      ✅
degree_topology = 18         (我独立值 18)         ✅
edge_count      = 497664     (我独立值 497664)     ✅
n_present       = 55248      (我独立值 55248)      ✅
```

**全量有效 degree 扫描（55,296 个节点）**：

| eff degree | 交付代码实测 | 我的独立 ground truth | 一致 |
|---|---|---|---|
| 18 | **54,453（98.48%）** | 54,453（98.48%） | ✅ |
| 17 | 807（1.46%） | 807 | ✅ |
| 16 | 33（0.06%） | 33 | ✅ |
| 15 | 3（0.01%） | 3 | ✅ |
| mean / median / min / max | **17.984 / 18 / 15 / 18** | 17.984 / 18 / 15 / 18 | ✅ |
| eff ≥ 9（OP-6 门槛） | **55,296 / 55,296（100%）** | 100% | ✅ |

**耗时**：全量 55,296 节点 **1.80 s**（传入预建 `MeasurementIndex`）。

**一处起初被我误判为缺陷、实为良好设计的地方**：直接传**原始行表**时单次调用需 0.048 s（外推全量 ~44 min）。但读源码后确认 `effective_degree` 第 423 行有

```python
index = measurement_table
if not isinstance(index, MeasurementIndex):
    index = MeasurementIndex(measurement_table)
```

—— **API 接受预建索引并复用**，因此是调用方用法问题，不是实现缺陷。**M1 无正确性缺陷。**（建议在 M2 的使用约定里写明："全量扫描必须传 `MeasurementIndex`"。）

---

## 8｜声明

- 本文件**未计算**：EOV、`R_{B,π}`、regret、parent ranking、任何搜索策略或 Tomorrow Test 结果。
- 唯一涉及的 fitness 相关操作是**"该观测是否存在且重复齐全"**（存在性/可用性判定），用于计算 `degree_effective`；**未读取或使用任何 fitness 数值**。
- 数据仅从 `data/external/TEM1_Gaszek2025/`（已核验的原始 deposit 副本）读取。
