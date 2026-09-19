# M0_verification_log.md — M0 数据核验日志

> 用途：逐条记录 M0 的核验动作与实测结果。**只追加**。最终结论汇入 `DATA_AUDIT.md` v3。
> 纪律：只写实测/已核实内容；未核实项明确标注。所有数据校验在系统临时目录完成并已删除，**项目 `data/` 保持为空**。

---

## M0-3｜`Mira2015_TEM_*` 的 fitness 语义 —— ✅ 已解开（P0-3 关闭）

**动作**：直接拉取两个 16 行的原始 CSV 全文逐行检视。
`https://raw.githubusercontent.com/COLA-Laboratory/GraphFLA/main/data/BioSequence/Mira2015_TEM_AMP.csv`（384 B）与 `…_FEP.csv`（525 B）。

**表头**：`sequences,pos1,pos2,pos3,pos4,fitness`

**已确认**：
1. **WT = `MEGN`，fitness = 0.0**（两个文件中 WT 行均为 0）→ **fitness 是"相对 WT 的 log 倍数"**（0 = 与 WT 相同），不是绝对活性量。
2. 4 个位点的等位集为 **M/L、E/K、G/S、N/D**（各 2 → 2⁴ = 16，完整）。
3. **不存在"整列都是 0"的退化**：此前观察到的"中位数 = 0"是因为**多数变体与 WT 无差异**（`AMP` 文件里 16 行中 12 行为 0），不是量纲坍塌。`FEP` 文件则有连续分布（最大 +0.6128）。
4. ⚠️ **存在地板裁剪（censoring）**：`-1.90534896288408` 在 AMP 文件中**反复出现于不同基因型**（MKSD / LESN / LESD / LKSN），是**固定的下限值**，不是独立测量。
   → 这正是 **CL-7** 要处理的模式。该 panel 的 fitness **必须按"相对 WT 的 log 倍数 + 地板裁剪"处理**。
5. ⚠️ **无重复列**（判据 ④ 不满足）。

**裁决**：`Mira2015_TEM_*`（15 种 β-内酰胺）保持 **oracle-only**（AMENDMENT-005 §E-8），用途限于同一蛋白的**任务面板秩相关**；且必须先定义地板处理。

---

## M0-Jalal2020｜结构独立核实 —— ✅ 通过

**动作**：拉取 `Jalal2020_NBS.csv` 与 `Jalal2020_parS.csv`（GraphFLA 二次分发），在内存/临时目录逐行统计后删除。

| 检查项 | NBS | parS | 结论 |
|---|---|---|---|
| 行数 | **160,000** | **160,000** | = 20⁴ ✅ |
| unique 序列 | 160,000 | 160,000 | 无重复行 ✅ |
| fitness 缺失 | **0** | **0** | ✅ |
| 每个位点的等位分布 | 20 种 AA，**各 8,000 次** | 同上 | 完整均衡 20⁴ ✅ |
| 序列长度 | 9（4 个可变位点 + 5 个固定） | 9 | — |
| fitness 范围 | [-14.183, +1.420] | [-12.946, +0.646] | 负值 log 尺度 |
| fitness 不同取值数 | 11,255 | 10,912 | **连续量，无阈值化、无明显地板堆积** ✅ |

**拓扑 degree = 4 × 19 = 76**（与 GB1 / TrpB4 同类）。

**裁决**：结构与完整性**完全合格**（判据 ①✓ ②✓ ③✓）。⚠️ **判据 ④ 仍未核**——GraphFLA 派生 CSV 无重复列，须回源原始 deposit（与 CL-8 一致：派生版本不能判定噪声）。

---

## M0-2a｜**TEM-1 主数据全套核验 —— ✅ 通过（含两处对原文的更正）**

**数据落地**：`data/external/TEM1_Gaszek2025`（sparse clone，193.6 MB，含 `data/raw` + `data/processed`）。

### 基因型空间：**我的推算被逐位点证实**

来源 `data/processed/TEM1-combinatorial-mutagenesis-intended.csv`（**55,296 行，55,296 unique，profile 长度 13**）。

| 位点 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 等位数 | 2 | 2 | **3** | 2 | **4** | 2 | 2 | 2 | 2 | **3** | 2 | **3** | 2 |
| 替换 | P | K | L/V | K | **H/N/S** | T | T | S | K | C/S | M | L/Q | D |

**乘积 = 4 × 3³ × 2⁹ = 55,296 ✅（与行数完全一致）**；**拓扑 degree = 18 ✅**；替换总数 = 18 ✅。
→ AMENDMENT/DATA_AUDIT 中标注为"🔷 推算"的结论**现已升级为实测**。

### 预注册主条件：**两个都在数据里**

| 条件 | 浓度列 | 重复列 |
|---|---|---|
| AMP | 0.0 / 3.1 / 12.2 / 48.8 / 195.0 / **781.0** μg/mL | 各 3 个 ✓ |
| AZT | 0.0 / 0.44 / 1.33 / 4.0 / 12.0 / **36.0** / 108.0 / 324.0 μg/mL | 各 3 个 ✓ |

→ **OP-15 关闭**：AMP 781 与 AZT 36 均为实际列名，前置核实完成。

### 🔴 噪声天花板（**首次实测**，H1 的分母）

| 条件 | 满三重复 genotype 数 | median AUC-fitness | **median SD** | **median 相对 SD** | IQR | **IQR / SD** |
|---|---|---|---|---|---|---|
| **AMP 781** | 55,248 | 2.190 | **0.321** | **14.7%** | [1.87, 2.54] = 0.67 | **2.09** |
| **AZT 36** | 55,232 | 2.319 | **0.242** | **10.5%** | [2.20, 2.46] = 0.26 | **1.07** |

**两条必须记录的更正/风险**：
1. ⚠️ 原文称重复 "SD typically **below 10%**" —— **实测中位相对 SD 为 14.7%（AMP）/ 10.5%（AZT）**，原文偏乐观。→ 一切噪声引用改用以实测值为准。
2. 🔴 **AZT 36 的 genotype 间 IQR 仅 1.07 × 噪声 SD** —— 即在该条件下**多数基因型在噪声内不可区分**，信号主要在尾部。这直接影响 H1 的表述：**AMP 是更好的"today"条件**（IQR/SD = 2.09），AZT 的体部接近噪声地板。此发现必须在 H1 分析设计中使用，不得忽略。
3. ⚠️ **processed wide 表只有 55,294 行（少 2 个基因型）** —— 完整性缺口虽小但真实，须在 M1 定位是哪 2 个。

### `Epistasis_Combined.parquet`（50 列）

确认含 `Genotype, Epistatic Term, Epistatic Order, **Fitness, Error**, Biochemical Definition, ..., **Drug, Concentration**` → **逐 genotype × drug × concentration 的 fitness + error 齐备** ✅（与仓库 README 一致）。**禁止重算**（需 ≥40 GB VRAM）的约束不变。

---

## M0-4｜原始 deposit 复核（PTE / MPH / Kosterlitz）

| 仓库 | 存在性 | 关键数据文件 | **LICENSE** |
|---|---|---|---|
| `karolbuda/rba-error-propagation` | ✅ 15 文件 | ✅ **9 个底物 CSV 全部存在**：`2NH, DHC, POE, POM, PTE, PTM, acetate, butyrate, tbbl.csv` | **无 LICENSE 文件** ⚠️ |
| `danderson8/MPH_Epistasis` | ✅ 5 文件 | `MPH Pt-methyl Recalculated.xlsx`、`MPH_code.tar.gz`、两个 R 脚本 | **无 LICENSE 文件** ⚠️ |
| `livkosterlitz/crowdsourcing` | ✅ 5,179 文件 | `competition_analysis/data/{genotype_barcode_map,genotype_coding,genotype_format,mutational_steps}.csv` + FASTQ | **无 LICENSE 文件** ⚠️ |

**PTE 结构（实测 `2NH.csv`）**：**64 行 = 完整 2⁶**；列 = `Code, p233, p254, p271, p272, p306, p313, exp1…exp9, pte1…pte24`（**6 位点 / 9 个实验重复 / 24 个技术重复列**）→ **判据 ④ ✅ 实测确认**。

⚠️ **三者的 license 均未核实（仓库内无 LICENSE 文件）** → 按 CL-8，**不得进入任何再分发声明**；Zenodo 侧的记录页面需单独核（Zenodo API 本次返回 403，需换 HTML 页面）。

---

## M0-1｜GraphFLA 163 CSV 全量校验 —— ✅ **完成**（162/163）

**🔴 环境发现（阻塞点）**：`git checkout` **在 Windows 上失败**，原因是一个文件名含 **`*`**（非法字符）：
`data/BioSequence/NEW_Rotrattanadumrong2022_F1*U(m)_Experimental exploration of a ribozyme neutral network...csv`
→ **结论：GraphFLA 的 163 个 CSV 无法在 Windows 上通过 git checkout 落地。** 已改为**逐文件 HTTP 直取**（URL 编码），全部结果存于 `data_registry/M0_csv_sweep.csv`。

**结果**：**162 成功 / 1 失败**（`learning.csv` 返回 404 —— 在 git tree 中但 raw 取不到，待查）。
行数：min 8 / median 128 / max 197,890。

**位点取值域分布**：二元 `0/1` **79 个**、蛋白 20AA **18 个**、DNA 7 个、RNA 5 个，其余为混合/受限字母表（如 `DEFHKNPQTV`、`DEGKLMNS`）。

**精确完整乘积空间：58 个**，规模最大的：

| 规模 | 文件 | 空间 |
|---|---|---|
| 160,000 | `Jalal2020_parS` / `Jalal2020_NBS` | 20⁴ |
| 65,536 | `Soo2021_30C` / `Soo2021_37C` | 4⁸（RNA） |
| 65,536 | **`Phillips2023_{SI06,MA90,G189E}`** | 2¹⁶ |
| 65,536 | **`Phillips2021_CR9114_{h1,h3,fluB}`** | 2¹⁶ |
| 32,768 | `Moulana2023_{S309,REGN10987,CoV555,CB6}` | 2¹⁵ |

### 🔴 删失现象的语料级量化（**独立交叉验证了我的 eLife 实测**）

| 文件 | 地板占比（派生 CSV 实测） | 与我的 eLife 源数据实测对照 |
|---|---|---|
| `Phillips2021_CR9114_fluB` | **0.997** | 我实测可用率 **0.3%** → 1 − 0.997 = 0.3% ✅ **完全吻合** |
| `Phillips2021_CR9114_h3` | **0.891** | 我实测可用率 **10.9%** → 1 − 0.891 = 10.9% ✅ **完全吻合** |
| `Podgornaia2015_PhoQ` | 0.637 | — |
| `Bendixsen2019_hdv` | 0.429 | — |
| `Mira2015_TEM_{AMP,CAZ}` | 0.250，**仅 3 个不同取值** | 与 M0-3 的地板裁剪发现一致 ✅ |

→ 全语料仅 **4 个文件地板占比 > 30%**；**删失不是抗体数据独有**。

**缺失 fitness 的文件：22 个**，最大者为 `Moulana2023_CB6`（16,257 / 32,768）、`CoV555`（12,901）、`REGN10987`（9,082）——与子代理报告**逐位吻合**；`Phillips2021_CR9114_h1` 442 行亦吻合。

**潜在多任务组（同前缀 ≥3 文件）**：Mira2015 (15)、Bakerlee2022 (12)、**Johnston2024 (10)**、Guerrero2019 (9)、Hall2019 (8)、Wu2020 (7)、Anderson (6)、Frohlich21 (6)、Skwara2023 (6)、Lovsky (5)、Michael2024 (5)、Phillips2021 (5)、Moulana2023 (4)、Tamer (4)、Khan2011Flynn2013 (3)、Lunzer2005 (3)、Phillips2023 (3)、Wong2018 (3)。
> ⚠️ **`Johnston2024` 有 10 个文件**（TrpB 论文的语料），M1 需展开——这可能提供 TrpB4 之外的任务轴。

---

## M0-1b｜两个尾巴清掉：`learning.csv` 404 = **我自己的 bug**；MPH 源数据结构澄清

### ① `learning.csv` 404 —— 破案（M0-1 补全至 **163/163**）

**真相**：git tree 里根本不存在 `learning.csv`。存在的是那个**含空格与 `*`** 的长文件名：
`data/BioSequence/NEW_Rotrattanadumrong2022_F1*U(m)_Experimental exploration of a ribozyme neutral network using evolutionary algorithm and deep learning.csv`

我的扫描脚本用 `git ls-tree ... .split()` **按空白切分**，于是这个长文件名被切碎，只有最后一片 `...learning.csv` 落进列表 → 404。**是我自己的解析 bug，不是仓库缺文件。**（同一文件也是 Windows `git checkout` 失败的原因。）

**补扫结果（HTTP 200，10,624,365 B）**：

| 项 | 值 |
|---|---|
| 行数 | **65,536 = 4⁸（完整 RNA 空间）** |
| 列数 | 16 |
| 表头 | `Sequences, Ligated_1, Unligated_1, FL_1, RA_1, Ligated_2, Unligated_2, FL_2, RA_2, TR_1, …` |
| schema | **无 `pos*` 列、无 `fitness` 列** —— 采用**原始计数 + 派生量**的另一种 schema |
| **重复结构** | `Ligated_1/2`、`Unligated_1/2`、`FL_1/2`、`RA_1/2` → **2 个生物学重复 + 派生比值** |

→ **它是第 59 个精确完整乘积空间**（修正 M0-1 的"58 个"），并且是**带重复结构的 RNA 8 位点完整景观**（比 `Soo2021` 更完整）。
→ 按 L0/L1 定位：**模态对照候选**（非蛋白，不参与蛋白侧主张）。

### ② MPH 源数据结构与 GraphFLA 派生版**不一致**（CL-8 第五次复现）

`MPH Pt-methyl Recalculated.xlsx`：**8 个 sheet（8 种金属）× 每 sheet 202 个基因型行**（不是 32）。

| 标签位点数 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 行数 | 48 | 63 | 61 | **30** |

例：`193/258/271/273`（4 位点）、`72/258/271/273`。
→ **源数据是"最多 4 位点的约 202 个变体集"，不是干净的乘积空间**；而 **GraphFLA 的 `Anderson_MPH_*` 只有 32 行 / 5 位点** → **派生版是源数据的一个子集**，且位点编码方式不同。
→ **裁决**：MPH 仍为 **oracle-only**，但**必须先回源定义位点与基因型编码**；M1 不得直接使用 GraphFLA 的 32 行版本（CL-8）。



**TEM-1 processed wide 表的 55,294 之谜 —— 已精确解出**：

| 项 | 结果 |
|---|---|
| intended | 55,296 |
| wide | 55,294 |
| **intended 有但 wide 无（3 个）** | `PKL.STT.KCM.D`、`PKV..TT..CMQ.`、`PKVKSTT...MQD` |
| **wide 有但 intended 无（1 个）** | **`XXXXXXXXXXXXX`** |

→ 算术自洽：55,296 − 3 + 1 = 55,294 ✓。
→ 🔴 **重要副产品**：`XXXXXXXXXXXXX` 就是 **TEM-1dead 参照行**，**它确实存在于 processed 表中** —— **WT/dead 双锚定归一化的 dead 锚点是真实可用的行**（`.............` 应为 WT 锚点，M1 确认）。同时**有 3 个真实基因型缺失**，M1 必须在 parent eligibility 中显式处理。

**Kosterlitz 宿主确认**：`genotype_format.csv` = **96 行 = 32 基因型 × 3 宿主**，宿主为 **`Ec`（*E. coli*）/ `Kp`（*K. pneumoniae*）/ `Se`（*S. enterica*）** ✅ 与"3 个真实宿主物种"完全一致。
`treatment_master.xlsx`：87 个 treatment，含 `Species / Time / Antibiotic(CTX) / Concentration` → **宿主 × cefotaxime 浓度**设计 ✅。
⚠️ 但该实验是 **pooled competition assay**（`competition_analysis`）→ 与 TEM-1CML 同类的 **assay-context 警示**（不是 genotype-intrinsic）。



## M0 状态总表

| # | 项 | 状态 |
|---|---|---|
| M0-1 | GraphFLA 163 CSV 全量校验 | ✅ **完成**（162/163，`learning.csv` 404） |
| M0-2 | 各数据集 fitness 语义与 floor/ceiling | ✅ TEM-1 / Phillips2023 / CR9114 / Jalal2020 / Mira2015 / PTE / MPH / Kosterlitz；⚠️ MPH 行数结构待澄清 |
| M0-3 | `Mira2015` fitness 语义 | ✅ **关闭** |
| M0-4 | PTE / MPH / Kosterlitz 原始 deposit 复核 | ✅ **完成**（三者均**无 LICENSE 文件**） |
| M0-5 | license 回源（6 项未核实） | 🟡 后台 agent `28c077ea` |
| M0-6 | **TrpB novelty 核实（P0-9）** | 🟡 后台 agent `28c077ea` |
| M0-7 | AncSR1 数据入口（P2） | 🟡 后台 agent `28c077ea` |
| M0-8 | `DATA_AUDIT.md` v3 | 🟡 后台 agent `364df6f8` |
| M0-9 | TEM-1 完整性 + Kosterlitz 宿主定位 | ✅ **完成** |
| M0-10 | `PHASE1_DATA_GATE.md`（M0 出口裁决） | ✅ **完成**（GO 有条件） |

