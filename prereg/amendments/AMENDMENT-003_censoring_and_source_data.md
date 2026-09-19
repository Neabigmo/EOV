# AMENDMENT-003 — 判据 ④ 的实测裁决、删失闸门、以及原始 deposit 优先原则

| 字段 | 值 |
|---|---|
| 版本 | **3** |
| 时间 | **2026-09-19**（精确时间戳见 `data_registry/FREEZE_LEDGER.md`） |
| 状态 | **FROZEN** |
| 依据 | 子代理 DELTA（`LANDSCAPE_HUNT_v0.md` 现为终版）+ **我对 eLife source data 的直接实测** |
| **时机** | **任何分析均未运行** → 预注册期修订，**无需盲法重跑** |

## 修正范围

| 被修正对象 | 修正 |
|---|---|
| `AMENDMENT-002` B-1（判据 ④ 满足者 = AncSR1） | **C-1**：改为实测证据；AncSR1 降级 |
| `AMENDMENT-002` B-3（Phillips2021 = 高密度多任务复制） | **C-1 + C-7**：降为"噪声校准 + 单任务密集" |
| `AMENDMENT-002` B-8 / P0-0（AncSR1 可达性 = 最高 ROI） | **C-3**：替换为 Phillips2023 source data 抓取与逐任务量化 |
| `PHASE1_PROTOCOL.md` §2.3 / §4（缺失与噪声） | **C-2**：新增 CL-7 删失闸门 |
| `DATA_AUDIT.md` §2.5 / §5（核实对象） | **C-4**：原始 deposit 优先原则 |
| `DATA_AUDIT.md` §3（benchmark 检索） | **C-5**：阴性结论与方法学声明 |

---

## C-1｜我实测了 eLife source data：判据 ④ 成立，**但三个"任务"里只有一个是可用的**

**实测对象（我亲自拉取并解析，非转述）**：`https://cdn.elifesciences.org/articles/71393/elife-71393-fig1-data1-v2.csv`（**12,258,680 B**，eLife 71393 = Phillips et al. 2021 流感 HA × CR9114）。

**结构确认** ✅：33 列 = `genotype` + `{h1,h3,fluB}×{repa,repb,repc,mean,sem}` + `pos1..pos16` + `som_mut`；**65,536 行 = 完整 2¹⁶**；`pos` 列**严格 0/1**；`som_mut` 直方图**精确等于 C(16,k)**（1,16,120,560,1820,4368,8008,11440,12870,…）→ **完整超立方体由独立自洽性检查确认**。CR6261 文件（`fig1-data2-v2.csv`，358,244 B）同样存在。

**但逐任务量化后（这是我实测的、子代理未量化的关键部分）**：

| 任务 | sem = 0 的行 | 三条 rep 完全相同 | **可用**（sem > 0） | **可用率** | mean 范围 | 中位 SEM |
|---|---|---|---|---|---|---|
| **h1** | 2,643 | 878 | **62,893** | **96.0%** | 7.04 – 9.79 | 0.035 |
| **h3** | 58,374 | 58,128 | 7,162 | **10.9%** | 6.00 – 9.04 | 0.068 |
| **fluB** | 65,343 | 65,245 | **193** | **0.3%** | 6.00 – 8.06 | 0.081 |

**结论（比子代理的判断更严格）**：
1. ✅ **判据 ④ 成立**：h1 有 62,893 个变体的三重复 + SEM，中位 SEM 0.035（论文报平均 0.047 -logKD，一致）。**H1 的档 A 不再需要押注 AncSR1。**
2. 🔴 **但 `Phillips2021_CR9114` 在实践上不是 multi-task 景观**：h3 只有 10.9% 可用、fluB 只有 **193 个变体（0.3%）**。它的真实身份是 **"单任务（h1）+ 真实重复测量" 的高密度景观** —— 而这正好是我们此前最缺的东西：**H1 噪声校准的第二蛋白证据床**。
3. 🔴 **"完整立方体"必须限定语义**：完整性成立的是**序列空间**（65,536 全覆盖），**不是每任务的可用测量空间**。h3 下 89% 的观测被钉在检测限。
4. AncSR1 由"判据 ④ 的唯一满足者"降为 **nice-to-have（P2）**。

**修正 B-3 表**：`Phillips2021_CR9114` 的角色从"高密度多任务复制"改为 **"档 A 噪声校准床 + 单任务密集景观（h1）"**；h3 仅作敏感性、fluB 排除。

---

## C-2｜新增 CL-7：**删失（censoring）识别与任务可用率闸门**

**定义**：若某任务下某变体满足 `rep_a = rep_b = rep_c` 且 `sem = 0` 且值位于滴定边界，则该观测为**删失（censored）**——它的含义是"信号弱于/强于检测限"，**不是"零噪声的精确测量"**。

**新增冻结规则**：

1. **删失 ≠ 缺失，也 ≠ 精确值**。删失观测是有界的真实观测，必须三者分列：`censored` / `missing` / `measured`。
2. **任务可用率** `usable_frac(τ) = #{sem > 0} / #space`，每个任务必须报告。
3. **任务准入闸门**：
   - `usable_frac ≥ 50%` → 可作**主任务**；
   - `20% ≤ usable_frac < 50%` → 仅 sensitivity；
   - `usable_frac < 20%` → **排除出主分析**。
4. **主分析只用 measured 子集**；删失观测在 sensitivity 中用**区间/序数处理**（例如 `F ≤ 边界值`），**不得**当作精确 fitness 参与 `max` 或排序，**也不得**直接丢弃（丢弃会引入相反的偏差）。
5. **有效 degree 必须按 measured 计算**：`R_k^oracle`、`R_{B,π}` 的邻域可达性只能建立在 measured 邻居上（与 TEM-1 的"拓扑 degree 18 vs 有效 fitness degree"规则同源）。
6. **适用于所有数据集**，不只 Phillips：任何"重复完全相同 + 零误差 + 值位于边界"的观测都按删失处理（TEM-1 的 `X` 是另一类，仍是"表型信息"而非删失）。

**按此规则裁决 Phillips2021**：h1 = 主任务（96.0%）；h3 = 仅敏感性（10.9%）；fluB = **排除**（0.3%，193 个变体）。

---

## C-3｜P0-0 替换：从"AncSR1 可达性"改为"**Phillips2023 source data**"

**理由**：AncSR1 的 processed 表至今找不到确切 URL；而 Phillips2023（CH65: SI06/MA90/G189E）是**同一实验室、同一期刊、同一 Tite-Seq 流程**，极可能有同结构的 `*_rep*` / `*_sem` 列。若成立 → 我们同时拿到 **3 个抗原任务 + 真实重复**，这才是"multi-task + 判据 ④"的真正候选。

**P0-0（新）动作**：
1. 定位 eLife 83628 的 source data 文件（URL 模式：`https://cdn.elifesciences.org/articles/83628/elife-83628-fig<N>-data<M>-v<V>.csv`；先抓文章页提取确切链接）。
2. 若存在，**逐任务量化 usable fraction / 删失率 / 中位 SEM**（同 C-1 的脚本）。
3. **准入判定**：至少需要 **≥2 个任务 usable_frac ≥ 50%** 才算"可用的 multi-task + 真实重复"景观。
4. 若 Phillips2023 也不可用 → 启用 A-1 的档 B（外部噪声校准）或档 C（降级表述），并把结论天花板写死。

**P0-0 旧条目（AncSR1 可达性）** → 降为 **P2**（有时间再做；不再阻塞任何决策）。

---

## C-4｜新增方法论硬规则：判据 ③/④ 的核实对象必须是**原始 deposit**

**实证案例**：GraphFLA 的派生 CSV 与上游 eLife deposit 对同一数据集给出**完全不同**的图景：

| 指标 | GraphFLA 派生 CSV（`Phillips2021_CR9114_h1/h3/fluB`） | 上游 eLife deposit（我实测） |
|---|---|---|
| rep / sem 列 | **无** | **有**（三重复 + SEM） |
| "缺失"行数 | 442 / 1 / 2 | sem = 0 行数 = **2,643 / 58,374 / 65,343** |

→ 派生版的 `fitness` 单列既有自己的过滤逻辑，其"缺失"语义与上游的**删失**完全不是一回事。

**硬规则（写入 DATA_AUDIT §2.5/§5 与 Protocol §1.3）**：
1. **判据 ③（数据可下载）与 ④（噪声结构）的核实对象只能是原始 deposit**（eLife source data / CaltechDATA / Zenodo / SRA / Figshare / 作者 GitHub），**不得**用聚合仓库的再分发版本。
2. 聚合仓库（GraphFLA / ProteinGym / FLIP / SSMuLA）**只能**用于发现候选与做 baseline 特征，**不得**作为噪声、缺失率或完整性的判定依据。
3. 每个纳入数据集必须记录：`original_deposit_url`（≠ 聚合来源）、`has_replicate_columns`、`censoring_rule`。

---

## C-5｜打包 benchmark 的阴性结论（写入 DATA_AUDIT 方法学声明）

| 来源 | 检索规模 | 结论 |
|---|---|---|
| **MaveDB** | 全量 2,063 个 experiment；筛出 ≥2 个 score set 的 **35 个**逐个读摘要 | **没有一个同时是组合多突变**。已核实 `urn:mavedb:00000040-a`（HSP90，4 条件 {30/36 °C}×{±0.5 M NaCl}，CC0，但仅 **189 个变体、全单突变**）；`urn:mavedb:00000053-a`（PDZ3 pairwise，648,022 变体，CC0，**单条件**） |
| **RNAGym** | HF 镜像 `reference_sheet_final.parquet` | **原样嵌入 ProteinGym 的蛋白 assay ID**（BLAT/GFP/DLG4/P53/SPIKE/OXDA/CAPSD…）→ **不提供任何新的蛋白多条件条目** |
| **CIS-BP / Codebook** | — | **确定没有**逐基因型 × 多条件数据 |

⚠️ **一条撤回**：并行线程曾给出的 MaveDB URN `00000056`（Dutta 2010 B2L11）**未经核实，现撤回**。该数据已核实的形态是 ProteinGym raw 的 `B2B11_HUMAN_Dutta_2010_binding-Mcl-1.csv` 族，表头 `…, 100 nM Mcl-1, 1 uM Mcl-1, 100 nM Bcl-xL, 1 uM Bcl-xL` → 4 条件 / ~170 计分变体 / **全单突变**。

**方法学声明（写入 DATA_AUDIT §3）**：**"下载一个 benchmark"无法完成数据审计；必须逐文献 curation。** 任何"我们的 landscape panel 来自现成 benchmark"的表述都是不成立的。

---

## C-6｜新增已核实的对照 / 校准对象

| 对象 | 结构 | 角色 | 核实 |
|---|---|---|---|
| **`HSP82_YEAST_Flynn_2019`** | 13,294 单突变 × **6 条件** + **2 个显式重复列**（论文 R² = 0.90） | **档 B 的外部噪声校准集**（AMENDMENT-001 A-1 当时只写了名字，现补齐） | 🔷 |
| **`PHOT_CHLRE_Chen_2023`**（CreiLOV） | raw = `HGVSp, rep1, rep2, rep3, mean, …` | 判据 ④ ✅ 但**单条件**；**并作为 C-4 的实证案例**（GraphFLA 派生版 `NEW_Chen2023_CreiLOV.csv` 165,428 行，已丢 rep 列） | 🔷 |
| **`AMIE_PSEAE_Wrenbeck_2017`** | **3 种底物**（acetamide / isobutyramide / propionamide）× 6,227 变体，**全单突变** | "多底物任务轴"的对照（判据 ① ✗） | 🔷 |
| **CTX-M-14 成对 DMS** | Palzkill lab, *PNAS* 2024;121(12):e2313513121；**17 个活性位点、49,096 个双突变**（19²×136 自洽）；cefotaxime / ampicillin；σ = 0.27 / 0.28；`github.com/Palzkill-Lab/CTXM_epistasis` | **同家族（β-内酰胺酶）不同酶的复制集** → 判据 ① 严格 ✗（仅 Hamming-2）→ 作 **robustness**，不作主 panel | 🔷 |
| Bonnin et al. 2025 bioRxiv（FMN riboswitch 多环境，`10.1101/2025.04.17.649428`） | 标题暗示同一 DMS 文库在 ≥3 环境读出 | 待核 | ⚠️ **未核实**（bioRxiv 两次 429） |

---

## C-7｜对既有条款的连带影响

1. **A-2（H2 baseline 含 GraphFLA 全 20 特征）不变**，但依据加强：GraphFLA 的派生 CSV **确实丢了 rep 列**，说明其数据层是二次加工品 —— 用它做 baseline 特征可以，用它做数据判定不行（C-4）。
2. **INT-8 的事实进一步收紧**：可用的 multi-task 蛋白景观比预期**更稀少**（CR9114 实际只有 1 个可用任务）。若 Phillips2023 也不可用，则跨系统主张只能建立在 **AncSR1（条件性）+ Jalal2020 + TEM-1/Mira2015** 之上，或接受 (ii) 的降级。
3. **A-1 档位现况**：**档 A 已可用**（CR9114 h1：62,893 变体 × 三重复，中位 SEM 0.035）+ TEM-1 triplicate。档 B/C 仅作后备。

---

## C-8｜新增待签字条目

| ID | 内容 | 默认 |
|---|---|---|
| **CL-7** | 删失识别规则 + 任务准入闸门（usable ≥50% 主 / 20–50% 敏感 / <20% 排除）；删失在 sensitivity 用区间处理 | 见 C-2 |
| **CL-8** | 判据 ③/④ 的核实对象必须是原始 deposit；聚合仓库只用于发现与 baseline | 见 C-4 |
| **OP-24** | Phillips2023 若仅 1 个任务可用时的应对（接受单任务 → 退回 INT-8 (i) 或 (ii)） | 待 P0-0 结果 |

---

## 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| 3 | 2026-09-19（预注册期） | ① 实测 eLife 71393 source data：判据 ④ 成立，但 h1/h3/fluB 可用率 = 96.0% / 10.9% / 0.3% → Phillips2021 降为"噪声校准 + 单任务密集"，AncSR1 降为 P2 ② 新增 CL-7 删失闸门 ③ P0-0 替换为 Phillips2023 source data ④ 新增原始 deposit 优先原则（CL-8，CreiLOV 实证）⑤ 打包 benchmark 阴性结论 + 撤回 `00000056` ⑥ 新增 4 个已核实对照对象 ⑦ 新增 OP-24。**分析未运行，无需盲法重跑。** |
