# DATA_AUDIT.md — Phase I 数据审计

| 字段 | 值 |
|---|---|
| 版本 | **v3** |
| 冻结时间 | **2026-09-19**（精确时间戳与哈希见 `data_registry/FREEZE_LEDGER.md`） |
| 状态 | **FROZEN** |
| 项目根 | `<PROJECT_ROOT>` |
| 上级命题 | Does evolutionary option value exist? — *Can starting points be valued before the future arrives?* |
| **本次修订** | **折叠 `AMENDMENT-001`…`AMENDMENT-005` 与 M0 实测结果，使本正文成为唯一权威**；被取代的旧表述已删除。**EOV 分析尚未运行。** |

> **本文件的铁律**
> 1. 每个数据集必须同时写清 **"能证明什么" 与 "不能证明什么"**。禁止跨级引用。
> 2. 每个数字必须标注核实状态：✅ 我已亲自核实 / 🔷 子代理核实（方法可查，逐条未由我复算）/ 🔶 用户提供 / ⚠️ 待核实。
> 3. **判据 ②/③/④ 的核实对象只能是原始 deposit**；聚合仓库（GraphFLA / ProteinGym / FLIP / SSMuLA / RNAGym）**只能**用于发现候选与计算 baseline 特征（CL-8）。
> 4. 一切规模、完整性、缺失率**只以实际文件的行数 / unique 序列数为准**；引用论文数字必须显式标注"**论文声明**"。
> 5. 修订只能**追加新版本**，不得静默改写。`data/` 中不得出现插补值冒充实验测量值。

---

## 0. v3 的四条头条变化

1. **判据 ④ 缺口关闭。** `Phillips2023`（eLife 83628）经我实测**满足全部 4 条判据**：完整 2¹⁶、3 个抗原任务（informative **MA90 93.7% / G189E 82.6% / SI06 43.0%**）、每任务 `rep×2 + SEM`，并附带**实测表达轴**（65,536 行、0 删失、SEM 中位 0.019）。→ **不再预先降级为 proof of principle。**
2. **`CR9114` 是单任务，不是 multi-task 景观。** h1 96.0% / h3 10.9% / fluB **0.3%**（193 个变体）→ 其角色是 **档 A 噪声校准床 + 单任务密集景观**。
3. **TEM-1 噪声天花板首次实测，并纠正了原文表述。** AMP 781 中位相对 SD **14.7%**、AZT 36 **10.5%**（原文称 "typically below 10%"，偏乐观）；且 **AZT 36 的 genotype 间 IQR 仅为噪声 SD 的 1.07 倍** → 多数基因型在噪声内不可区分。**AMP 是更好的 "today" 条件。**
4. **Novelty 风险有两个来源**：GraphFLA（景观几何 → DE 成败）**与 TrpB 原文本身**（逐起点 max-fitness ECDF，数学上即单任务 `R_{B,π}`）。护城河收窄为 **任务 holdout + selection regret + 跨任务一致性**。

---

## 1. 证据等级（Evidence Level）定义

| 等级 | 名称 | 结构条件（全部满足） | 可支持的结论 |
|---|---|---|---|
| **L3** | strict EOV | ① ≥3 位点、密集组合邻域 ② ≥2 个任务/条件且**至少一个 withheld** ③ processed 数据可下载 ④ 有测量重复/噪声结构 | 预算约束下的**前瞻性起点估值**（Tomorrow Test） |
| **L2** | budgeted starting-point | ① ≥3 位点、密集组合邻域 ② **单一**任务 ③ 有噪声结构 | V_{B,π} 数学性质、policy robustness、geometry → option value。**不支持** future-task uncertainty |
| **L1** | readiness / task transfer | ① 多任务/条件 ② **无**多突变组合邻域 | Immediate readiness、task transfer。**不支持** budgeted adaptation |
| **L0** | methodology control | 非蛋白模态的多环境完整 landscape | 检验数学定义。**非蛋白证据** |

**注（v3 更正）**：
- v2 曾写"目前没有任何数据集同时满足全部 4 条" —— **该表述对蛋白与 RNA 都已不成立**：`Phillips2023` 满足全部 4 条；`glmS`（RNA 核酶）亦满足全部 4 条但**非蛋白**。
- **满足"dense × multi-task"的蛋白集合 = { TEM-1CML, Phillips2023, CR9114(h1), Jalal2020, AncSR1（条件性） }**（见 §2.6）。
- 酶侧的**密集多任务不存在**：酶的多任务景观只存在于 ≤ 64 基因型的小空间。

---

## 2. 数据集清单

### 2.1 TEM-1 / TEM-1CML —— 主数据（唯一具备完整真实重复的主数据）

| 项目 | 内容 | 状态 |
|---|---|---|
| 正式论文 | *Nature Communications* `10.1038/s41467-026-77182-z`，2026-09-04 发表；"超过 900 万次 fitness measurements" | ✅ DOI 解析；🔶 日期与测量数由用户核实 |
| 历史版本 | bioRxiv `10.1101/2025.07.08.663783` v1（PMC12265529） | ✅ 已读 |
| 数据/代码 | GitHub `msadikyildiz/Gaszek_Yildiz_Meng_2025`；Zenodo concept `10.5281/zenodo.21442350` → records/21481201 | ✅ |
| **来源类型** | `journal_source_data` + `author_repository`（非二次分发） | ✅ |
| License | **GPL-3.0-or-later** | ✅ |
| 本地落地 | `data/external/TEM1_Gaszek2025`（sparse clone，**193.6 MB**，含 `data/raw` + `data/processed`） | ✅ |

**基因型空间（✅ M0 逐位点实测，替代 v2 的推算）**

来源 `data/processed/TEM1-combinatorial-mutagenesis-intended.csv`（**55,296 行 / 55,296 unique / profile 长度 13**）：

| 位点 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 等位数 | 2 | 2 | **3** | 2 | **4** | 2 | 2 | 2 | 2 | **3** | 2 | **3** | 2 |
| 替换 | P | K | L/V | K | **H/N/S** | T | T | S | K | C/S | M | L/Q | D |

**乘积 = 4 × 3³ × 2⁹ = 55,296 ✅（与行数完全一致）；拓扑 degree = 18 ✅；替换总数 = 18 ✅。**
→ v2 中标为"🔷 推算"的结论**已升级为实测**。

**预注册主条件（OP-15 已关闭）**

| 条件 | 浓度列 | 重复列 |
|---|---|---|
| AMP | 0.0 / 3.1 / 12.2 / 48.8 / 195.0 / **781.0** μg/mL | 各 3 个 ✓ |
| AZT | 0.0 / 0.44 / 1.33 / 4.0 / 12.0 / **36.0** / 108.0 / 324.0 μg/mL | 各 3 个 ✓ |

**🔴 噪声天花板（首次实测，H1 的分母）**

| 条件 | 满三重复 genotype 数 | median AUC-fitness | **median SD** | **median 相对 SD** | IQR | **IQR / SD** |
|---|---|---|---|---|---|---|
| **AMP 781** | 55,248 | 2.190 | **0.321** | **14.7%** | [1.87, 2.54] = 0.67 | **2.09** |
| **AZT 36** | 55,232 | 2.319 | **0.242** | **10.5%** | [2.20, 2.46] = 0.26 | **1.07** |

两条必须沿用的结论：
1. ⚠️ **原文"SD typically below 10%"偏乐观**；一切噪声引用**以实测值为准**。
2. 🔴 **AZT 36 的 genotype 间 IQR 仅 1.07 × 噪声 SD** —— 该条件下多数基因型**在噪声内不可区分**，信号主要在尾部。**H1 分析设计必须使用这一事实**（AMP 是更好的 today 条件）。

**其他**

- fitness 定义：**AUC-fitness = log10(AUC)**（归一化生长曲线的面积）。
- **processed wide 表 55,294 之谜 —— 已精确解出（M0-9 ✅）**：intended **55,296** vs wide **55,294**；**intended 有而 wide 无 3 个**（`PKL.STT.KCM.D`、`PKV..TT..CMQ.`、`PKVKSTT...MQD`）；**wide 有而 intended 无 1 个**（`XXXXXXXXXXXXX`）→ 算术自洽 55,296 − 3 + 1 = 55,294 ✓。
  - 🔴 **重要副产品**：`XXXXXXXXXXXXX` 就是 **`TEM-1dead` 参照行**，**确实存在于 processed 表中** → **WT/dead 双锚定归一化的 dead 锚点是真实可用的行**（`.............` 应为 WT 锚点，M1 确认）。
  - ⚠️ 同时**有 3 个真实基因型缺失**，M1 必须在 parent eligibility 中显式处理。
- `Epistasis_Combined.parquet`（50 列）确认含 `Genotype / Epistatic Term / Epistatic Order / Fitness / Error / Biochemical Definition / … / Drug / Concentration` → **逐 genotype × drug × concentration 的 fitness + error 齐备** ✅。
- **计算约束**：官方 epistasis 重算需 ≥40 GB VRAM；本机 8 GB → **禁止重算**，只用已 ship 的 parquet。
- **混淆**：① **Cheater effect**（共培养 → 只能称 *pooled competitive fitness*）② L21P 是失误产物、位于信号肽（表达/定位效应）③ `X` ≠ 缺失（是表型信息）④ barcode 级缺失。
- **附带资产**：`Mira2015_TEM_*`（同一蛋白 × 15 种 β-内酰胺，见 §2.6）。

**能证明**：单一 novel functional pressure（AMP→AZT）下的严格 Tomorrow Test；**唯一具备完整真实三重复的主数据**。
**不能证明**：task-general EOV；intrinsic evolvability（cheater）；9 种 β-lactam 的 MIC panel 不是额外 landscape。

---

### 2.2 TrpB4（TmTrpB 四位点）—— L2 预算型起点实验室

| 项目 | 内容 | 状态 |
|---|---|---|
| 论文 | PNAS 2024 `10.1073/pnas.2400439121`（PMID 39074291，PMC11317637） | ✅ |
| Processed + software | CaltechDATA `10.22002/h5rah-5z170` | ✅ DOI 解析 200 |
| Raw | SRA `PRJNA1127511` | 🔶；旁证 SRX25038208 ✅ |
| License | **CC0-1.0** | ✅ |
| 规模 | 20⁴ = 160,000；实测 159,129（99.45%）；4 位点（SSMuLA 记 `TrpB4` = V183/F184/V227/S228） | 🔶；M0 核实 |
| 拓扑 degree | 4 × 19 = 76 | 🔷 |
| 可能的第二轴 | 论文含 **T50 热稳定性**（覆盖子集） | ⚠️ M0 必查（OP-14） |
| 数据陷阱 | 社区副本（HuggingFace SaProtHub）**合并了 imputed 与实测值** | ✅ → 禁止作为数据源 |

**能证明**：V_{B,π} 性质、policy robustness、非共培养 assay 的跨测量验证。
**不能证明**：future-task uncertainty（单任务）。
⚠️ **Novelty 提示**：TrpB 原文可能已发表逐起点可达值分析（P0-9，见 §3.4）。

---

### 2.3 DAOx —— L1 readiness 对照

论文 *Nat Commun* 2026 `10.1038/s41467-026-69913-z`（PMID 41748636）；数据 Zenodo `10.5281/zenodo.15846928` ✅；License **CC-BY-4.0** ✅。
6,418 variant / 5 个 D-氨基酸底物 / 5,800 missense 共享（🔶）；**主体为单突变扫描**（🔶）。
**用途**：4 底物 → hide 底物 5 的 **readiness / task-transfer**，"readiness vs EOV 是否同一个问题"的最小对照。**严禁**当作多轮 evolution。

---

### 2.4 SSMuLA panel —— L2 群体 + 现成模拟基础设施

GitHub `fhalab/SSMuLA`；Zenodo `10.5281/zenodo.13910506` ✅；论文 bioRxiv `10.1101/2024.10.24.619774`。
16 个 landscape：ParD2/3、**GB1(4)**、DHFR、T7、TEV、**TrpB4(4)**、TrpB3A–3I。含 FASTA/PDB/EVmutation model、`scale2max` 处理表、zero-shot（EVmutation/ESM/ESM-IF/CoVES/Triad）、**DE + MLDE/ftMLDE 模拟**（`n_samples=[96,384]`、`n_replicate=50`、`n_split=5`）、ALDE（`alde4ssmula`）、ESM-2 LoRA finetune。

⚠️ **重叠警告**：我们的 `search_policies.py` 本质上会重建 SSMuLA 的 DE/MLDE 实现 → **应复用而非重写**，并显式声明差异（SSMuLA **没有 future-task holdout**）。

---

### 2.5 GraphFLA 公开发布的 landscape 语料 —— **派生来源，不得用于判据 ③/④**

| 项目 | 内容 | 状态 |
|---|---|---|
| 论文 | NeurIPS 2025 **Spotlight**，arXiv `2510.24826` | ✅ |
| 代码/数据 | GitHub `COLA-Laboratory/GraphFLA`，**MIT（仅覆盖仓库本身）**；`pip install graphfla`（wheel ~166 KB，**不含数据**） | ✅ README 已读 |
| 语料 | `data/BioSequence/*.csv`，统一 `sequences,pos1..posN,fitness`，可 `raw.githubusercontent.com` 直取 | 🔷 |
| 规模口径不一致 | 论文称 **155 个 landscape**（DNA 55 / 蛋白 63 / RNA 37，2.2M 序列，出自 61 篇；另一处写 "more than 67 studies"）；TeX 长表实际 **149 行**；仓库实际 **163 个 CSV** | ✅ + 🔷 |
| 二十个特征 | ruggedness / epistasis / navigability / neutrality / correlation / robustness / fitness distribution，含 **per-config 可及性**量（`global_optima_accessibility`、`evolvability_enhancing_mutations (φ_EE)`、`extradimensional_bypass`、`basin_fitness_correlation` …） | ✅ README |
| **🔴 Windows 环境限制** | `git checkout` 在 Windows **失败**：文件名含非法字符 **`*`**（`data/BioSequence/NEW_Rotrattanadumrong2022_F1*U(m)_…csv`）→ **163 个 CSV 无法在 Windows 上通过 git checkout 落地**；全量校验改为**逐文件 HTTP 直取**（`raw.githubusercontent.com` + URL 编码） | ✅ |
| **定位（CL-8）** | **派生来源**：只能用于**发现候选**与**计算 baseline 特征**；**不得**作为噪声、缺失率、完整性的判定依据 | 冻结 |

**已实测的"派生版本丢失信息"四次复现**（CL-8 的实证基础）：

| # | 案例 | 派生版本丢失了什么 |
|---|---|---|
| 1 | GraphFLA ↔ eLife（CR9114） | 派生 CSV **丢掉 `rep`/`sem` 列**；其"缺失"语义（442/1/2）与上游**删失**（2,643/58,374/65,343）完全不同 |
| 2 | RNAGym processed ↔ raw | processed assay 集把**整个配体浓度序列塌缩成单一 `DMS_score` 列**；raw 有 5 个浓度 + stErr |
| 3 | ProteinGym processed ↔ raw | processed 表丢失重复结构 |
| 4 | GraphFLA 只收 PTE 的 2/9 个底物 | 源数据 9 个底物（含真实重复），派生版只有 2 个 |

**规模声明 vs 实际文件（硬规则依据）**

| 文件 | 论文表格声明 | 仓库实际 | 实际/声明 |
|---|---|---|---|
| `Papkou2023_DHFR.csv` | 4⁹ = 262,144（99.7% 实测） | **135,178** | **51.6%** |
| `Westmann2024.csv` | 4⁸ = 65,536 | **17,765** | **27.1%** |
| `Kuo2020.csv` | 262,144 | 197,890 | 75.5% |

另有：`benchmarks/_datasets.py` 引用的 `Papkou2023_DHFR_RAW.csv` **返回 404**；`Skwara2023_Butyrate.csv` **格式损坏**（表头 27 列，第 2 行仅 3 字段）。

**M0-1 全量校验结果（✅ 完成，162/163）** —— 结果存于 `data_registry/M0_csv_sweep.csv`

- **162 成功 / 1 失败**：`learning.csv`（在 git tree 中但 raw 返回 **404**，待查）。
- 行数：min **8** / median **128** / max **197,890**。
- **位点取值域分布**：二元 `0/1` **79 个**；蛋白 20AA **18 个**；DNA 7 个；RNA 5 个；其余为混合/受限字母表（如 `DEFHKNPQTV`、`DEGKLMNS`）。
- **精确完整乘积空间：58 个**。规模最大者：

| 规模 | 文件 | 空间 |
|---|---|---|
| 160,000 | `Jalal2020_parS` / `Jalal2020_NBS` | 20⁴ |
| 65,536 | `Soo2021_30C` / `Soo2021_37C` | 4⁸（RNA） |
| 65,536 | **`Phillips2023_{SI06,MA90,G189E}`** | 2¹⁶ |
| 65,536 | **`Phillips2021_CR9114_{h1,h3,fluB}`** | 2¹⁶ |
| 32,768 | `Moulana2023_{S309,REGN10987,CoV555,CB6}` | 2¹⁵ |

- **缺失 fitness 的文件：22 个**，最大者为 `Moulana2023_CB6`（16,257 / 32,768）、`CoV555`（12,901）、`REGN10987`（9,082）——与子代理报告**逐位吻合**；`Phillips2021_CR9114_h1` 的 442 行亦吻合。
- **⚠️ 潜在多任务组（同前缀 ≥3 文件）**：Mira2015 (15)、Bakerlee2022 (12)、**`Johnston2024` (10)**、Guerrero2019 (9)、Hall2019 (8)、Wu2020 (7)、Anderson (6)、Frohlich21 (6)、Skwara2023 (6)、Lovsky (5)、Michael2024 (5)、Phillips2021 (5)、Moulana2023 (4)、Tamer (4)、Khan2011Flynn2013 (3)、Lunzer2005 (3)、Phillips2023 (3)、Wong2018 (3)。
  → **`Johnston2024` 有 10 个文件**（TrpB 论文语料），**M1 必须展开**——它可能提供 TrpB4 之外的额外任务轴（与 P0-9 的 novelty 核实直接相关）。

---

### 2.6 **最终证据链（operational；取代 AMENDMENT-001 A-3 / AMENDMENT-002 B-3 / AMENDMENT-004 D-10）**

| 角色 | 数据 | 空间 | 任务 | 噪声 | 判定 | 来源类型 |
|---|---|---|---|---|---|---|
| **主数据** | **TEM-1CML** | 55,296（13 位点/18 突变，deg 18） | AMP → AZT（唯一 strict future） | triplicate ✓（实测 SD 0.321/0.242） | **L3** | journal + author repo |
| **第二系统（实测合格）** | **Phillips2023** | 65,536（2¹⁶，deg 16） | MA90 / SI06 / G189E + **表达轴** | rep×2 + SEM ✓ | **L3** | journal source data |
| **噪声校准床** | CR9114（Phillips2021） | 65,536（2¹⁶） | **仅 h1 可用 96.0%**（h3 10.9% / fluB 0.3% → 排除） | rep×3 + SEM ✓ | **L2** | journal source data |
| 同蛋白宿主轴 | Kosterlitz blaTEM | 32（2⁵） | ×**3 宿主** × cefotaxime 梯度 | ⚠️ | oracle-only | Zenodo（`10.5281/zenodo.10045641`） |
| 同蛋白药物轴 | Mira2015 TEM | 16（2⁴） | **15 种 β-内酰胺** | ⚠️ 无重复 | oracle-only | **`secondary_distribution`（GraphFLA）** |
| 20 字母表多任务 | Jalal2020 | 160,000（20⁴，deg 76） | NBS / parS | 0 缺失；重复未核 | 判据 ①②③✓ / ④⚠️ | `secondary_distribution` |
| 条件性 L3 | AncSR1 | 160,000（20⁴） | ERE/SRE × 2 背景 | 2 重复 + SEM | 🔶 数据入口未找到 → **P2** | 待定 |
| 酶-多底物（小空间） | **PTE（源数据）** | 64（2⁶） | **9 底物** | **n=3–10 + tech n=3 ✓** | oracle-only（B ≤ 16） | 作者 GitHub |
| 酶-多环境（小空间） | **MPH（源数据）** | 32（2⁵） | **8 环境** | **三次生物学重复 + SD ✓** | oracle-only | 作者 GitHub + Zenodo |
| 多底物任务面板（L1） | **TEV ProtRec** | 29,716 × ≤134 底物 | **134 底物** | ⚠️ | L1（非组合空间） | Zenodo（CC-BY-4.0） |
| 多底物单突变（L1） | DAOx / AMIE-Wrenbeck | — | 5 / 3 底物 | — | L1 | Zenodo |
| 同家族复制 | CTX-M-14 | 49,096 双突变（17 位点） | CAZ / AMP | σ = 0.27 / 0.28 | robustness | 作者 GitHub |
| oracle-only 其他 | Lunzer2005 / Michael2024 / Wu2020 / Bakerlee2022 / Hall2019 / … | 16–1,022 | 2–12 | 多为 ⚠️ | oracle-only | `secondary_distribution` |
| 档 B 外部校准集 | HSP82 / CreiLOV / GRB2 / DLG4 | — | 6 / 1 / 1 / 1 | 有 rep / sigma ✓ | 校准 | 聚合 raw |
| 模态对照（L0） | **glmS（RNA）** / Soo2021 | 161,879 行 / 67 位点 | 5 配体浓度 / 2 温度 | stErr + 1 重复 ✓ | L0 | RNAGym raw（CC-BY-4.0） |

**M0 实测补充（本节数据的来源）**

- **Phillips2023**（`cdn.elifesciences.org/articles/83628/elife-83628-fig1-data1-v3.xlsx`，14,142,772 B）：Sheet1 `geno, {MA90,SI06,G189E}×{rep1,rep2,mean,sem}`；informative = **61,395（93.7%）/ 54,121（82.6%）/ 28,206（43.0%）**；floor = **7.948 / 6.000 / 6.000**；中位 SEM = **0.027 / 0.049 / 0.074**。Sheet2 表达轴 `exp_rep1_norm, exp_rep2_norm, exp_norm_mean, exp_norm_sem`：**65,536 行、0 删失、100% 可用**，mean ∈ [0.78, 1.15]，中位 SEM **0.019**。
- **CR9114**（`…/71393/elife-71393-fig1-data1-v2.csv`，12,258,680 B）：65,536 行 = 完整 2¹⁶，`som_mut` 直方图**精确等于 C(16,k)**；可用率 **h1 96.0%（62,893）/ h3 10.9%（7,162）/ fluB 0.3%（193）**；中位 SEM 0.035 / 0.068 / 0.081。
- **跨任务相似度（informative 交集上）**：MA90↔G189E **+0.886（50,644）**；SI06↔G189E +0.772（28,197）；MA90↔SI06 **+0.645（26,349）**。
- **Jalal2020**：NBS / parS 各 **160,000 行 = 完整 20⁴**（每个位点 20 种氨基酸**各 8,000 次**，完全均衡）；**0 缺失**；fitness 不同取值 **11,255 / 10,912**（连续量、无阈值化、无明显地板堆积）；范围 NBS [-14.183, +1.420]、parS [-12.946, +0.646]；序列长 9（4 个可变位点）；**deg = 4 × 19 = 76**。
- **Mira2015**：**WT = `MEGN`，fitness = 0.0** → fitness 是"**相对 WT 的 log 倍数**"；等位集 M/L、E/K、G/S、N/D；⚠️ **存在地板裁剪 `-1.90534896288408`（在不同基因型上反复出现）**；⚠️ 无重复列。
- **PTE**（`karolbuda/rba-error-propagation`）：**9 个底物 CSV 全部存在**（2NH, DHC, POE, POM, PTE, PTM, acetate, butyrate, tbbl）；`2NH.csv` = **64 行 = 完整 2⁶**；列 = `Code, p233, p254, p271, p272, p306, p313, exp1…exp9, pte1…pte24`（**6 位点 / 9 个实验重复 / 24 个技术重复列**）→ **判据 ④ ✅ 实测确认**。
- **MPH**（`danderson8/MPH_Epistasis`）：`MPH Pt-methyl Recalculated.xlsx` = **8 个 sheet（8 种金属）**，**各有 3 个重复列**；⚠️ 基因型行数与位点结构**待澄清**。
- **Kosterlitz**（`livkosterlitz/crowdsourcing`）：5 位点（g4205a / A42G / E104K / G238S / M182T）、**32 基因型**；`competition_analysis/data/genotype_format.csv` **96 行 = 32 × 3 宿主** ✅；宿主标签为 **`Ec`（*E. coli*）/ `Kp`（*K. pneumoniae*）/ `Se`（*S. enterica*）**；`treatment_master.xlsx` = **87 个 treatment**，含 `Species / Time / Antibiotic(CTX) / Concentration` → **宿主 × cefotaxime 浓度**设计 ✅。
  - ⚠️ **但该实验是 `pooled competition assay`（`competition_analysis`）→ 与 TEM-1CML 同类的 assay-context 警示（不是 genotype-intrinsic）**；引用时必须与 §2.1 的 cheater 政策同等对待。
- ⚠️ **PTE / MPH / Kosterlitz 三个仓库均无 LICENSE 文件** → license **未核实**，**不得进入任何再分发声明**。

---

### 2.7 结构性发现（必须写进实现）

1. **fitness 量纲在任务间根本不可比（硬证据）**：`Phillips2023` 为负值、`Phillips2021_CR9114` 为正值（-logKD 7–9.84）；`Tamer_DHFR` 的 `kcat ∈ [-2.925, 0.002]` 而 `ki ∈ [0, 5.006]`——**同一蛋白同一空间，两个任务量纲完全不同**。`Mira2015` 又是"相对 WT 的 log 倍数"（WT = 0）。
   → **跨 task 归一化不是理论担忧，而是当场会爆炸的 bug**；且必须先验证各数据集中**是否真有 WT / dead 行**可供锚定。
2. **`Anderson2021_MPH` 的 pos2 取值域是 `-`/`S`** → 缺失/indel 状态而非氨基酸替换，不参与 Hamming-1 边。
3. **混合字母表乘积空间是常态**：Lunzer2005 = 2×4×8×2×2×2 = 512；Wu2020 = 4×4×3×… = 576；TEM-1 = 4×3³×2⁹。
   → `eov/landscape.py` **必须**按"混合字母表乘积空间"实现（每节点度 = `Σ(等位数−1)`，恒定但各位点分支因子可差 4 倍），**不得**假设二元超立方体（CL-6）。
4. **"完整立方体"必须限定语义**：CR9114 的完整性成立的是**序列空间**（65,536 全覆盖），**不是每任务的可用测量空间**（h3 下 89% 的观测被钉在检测限）。

---

## 3. 缺口裁决与方法学声明

### 3.1 判据逐条（v3 更新）

| 判据 | 状态 |
|---|---|
| ① ≥3 位点 + 密集组合覆盖 | **充分满足**（TEM-1 55,296 / Phillips2023 与 CR9114 各 65,536 / Jalal2020 160,000） |
| ② ≥2 任务且至少一个可 withheld | **充分满足**（Phillips2023 3 任务 + 表达轴；Moulana 5 任务；TEM-1 1 strict future） |
| ③ processed 数据可下载 | **充分满足**（eLife source data / Zenodo / CaltechDATA 均可直取） |
| ④ 测量重复 / 可估噪声 | **已被实测推翻 v2 的"不满足"判断**：TEM-1 triplicate ✅；CR9114 **h1 96.0%**（rep×3 + SEM）✅；Phillips2023（rep×2 + SEM）✅；Jalal2020 待核 ⚠️ |

**缺口降级**：判据 ④ 不再构成硬缺口。剩余问题是**逐任务的删失量化**（CL-7 / CL-9），不是"缺数据"。

### 3.2 穷尽性方法学声明（写入正文，供论文引用）

> **`{≥3 位点 ∧ ≥10⁴ 多突变体 ∧ ≥2 条件}` 这个交集在任何打包资源里都不存在** —— 经 ProteinGym（raw 包全部 **213** 个文件：每一个拥有 >1 个 score 列的都是**单突变文库**）、CIS-BP、MaveDB（全 **2,063** 个 experiment，筛出 ≥2 个 score set 的 **35** 个，**无一组合多突变**）、多底物与多环境文献的检索，该交集**只存在于原始文献及其原始 deposit**。多底物 / 多环境侧的联合集最大只有 **64（PTE）** 与 **32（MPH、Kosterlitz）** 个基因型。
> 因此**"下载一个 benchmark"无法完成数据审计，必须逐文献 curation**；任何"我们的 landscape panel 来自现成 benchmark"的表述都不成立。

**"查不到 ≠ 不存在"**：未认证 GitHub REST API 在本次 survey 期间**全局限流（60 req/h/IP）**，导致 `LSSI-ETH`、`klawrence26/bnab-landscapes` 等仓库树**无人能枚举**，Taft 2022 DML 与 Shlesinger 2026 血清面板的 processed 表**未能核实**。所有阴性结论一律写成"**在已核实的检索范围内未发现**"。

### 3.3 汇总裁决

| 等级 | 归属 |
|---|---|
| **L3（满足全部 4 条）** | **TEM-1CML**（主）、**Phillips2023**（第二系统）；RNA 侧 `glmS` |
| **L2（单任务 + 密集 + 有噪声）** | **CR9114 h1**（噪声校准床）、TrpB4、GB1 等 SSMuLA panel |
| **L1（多任务 + 无组合邻域）** | DAOx、**TEV ProtRec（134 任务）**、AMIE-Wrenbeck、DHFR-TMP、MBE `msag106` |
| **oracle-only（空间过小，OP-21）** | Mira2015（16）、Kosterlitz（32）、MPH（32）、PTE（64）、Lunzer2005（512）、Michael2024、Wu2020、Bakerlee2022、Hall2019、Frohlich21_OXA-48、Khan2011Flynn2013、Lovsky_DHFR、Tamer_DHFR、Ogbunugafor22 |
| **robustness** | CTX-M-14（同家族复制） |
| **L0（模态对照）** | glmS（RNA，5 配体浓度）、Soo2021 |
| **排除** | FLIP2（distribution-shift 切分，**投入为 0**）、DHFR-TMP（判据 ①✗）、MBE `msag106`（判据 ①✗，仅作 TEM-1 辅助环境轴）、群落景观、非生物模态 |

### 3.4 Novelty 风险（v3：**两个来源**）

**风险 A —— GraphFLA（NeurIPS 2025 Spotlight，Appendix F / §4.5）**：20 个 3-/4-位点饱和**蛋白**景观 × **5 种 DE 方法**（greedy adaptive walk / MLDE / MLDE+zero-shot / ALDE / ALDE+zero-shot）× 100 次随机初始化，指标 = 达到的最优变体 **fitness percentile**，并给出"景观特征 vs DE 表现"的 Spearman 表。→ **"景观几何 → 演化成败"已被发表。**

**风险 B（更近）—— TrpB 原文本身**（Johnston et al., *PNAS* 2024，`10.1073/pnas.2400439121`）：🔷 子代理核实，⚠️ **独立确认进行中（P0-9）** —— 该文可能已发表：**从每一个起点基因型出发的 max fitness ECDF**、3 种 in-silico DE、local-optima / accessible-path 分析、**注入噪声的 null model**。
> **"从每个起点出发的最大适应度分布"在数学上就是单任务下的 `R_{B,π}(x,τ)`。** GraphFLA 是"整张景观 × 随机起点取平均"，而 TrpB 原文是"**逐起点**" —— 后者与我们的分析单位**完全一致**。

**定位段（无论 P0-9 结果如何都要写）**：

> 在单任务、单分布的条件下，**逐起点可达值的分布**已有先例（Johnston et al., PNAS 2024 在 TrpB 20⁴ 完整景观上的 ECDF 分析；GraphFLA 在 20 个蛋白景观上的景观级 DE 分析）。因此本文的增量**不在**"起点差异存在"或"给定预算下起点可达值不同"，而在于：(i) **任务维度的 holdout** —— 未来任务的任何测量都不进入特征构造、超参选择与排序；(ii) 以 **selection regret**（选错起点的决策损失）而非可达最大值分位数为主指标；(iii) 检验 **`Corr(EOV_τ1, EOV_τ2)`**，区分"通用 option value"与"任务族条件化的 option value"；(iv) 将可达价值分解为 `R_0` / `R_k^oracle` / `R_{B,π}` 三层，把**景观机会**与**搜索能力**分开。

**必须作为 H2 baseline 纳入的既有特征**（否则会被直接指出）：GraphFLA **全部 20 个特征**，含 `global_optima_accessibility`、`local_optima_accessibility`、`mean_path_length_to_global_optimum`、**`evolvability_enhancing_mutations (φ_EE)`**、`extradimensional_bypass`、`basin_fitness_correlation`、`fdc`、`gamma`、`local_optima_ratio`、`neutrality` 等。

**其他风险**
- **SSMuLA** 已实现 DE/MLDE/ftMLDE/ALDE（96/384、50 replicates）→ 我们的 `search_policies.py` 是该线的重建，**必须复用并声明差异**（无 future-task holdout）。
- **"multi-environment" 本身不是新意**：`ChenFT22`（Nat Ecol Evol 2022，"phenotype-environment-fitness landscape"）、`Anderson2021`（environment-dependent epistasis）。
- **"我们收集了一个 landscape panel" 不再是贡献**（GraphFLA 已公开 155/163 个）—— 但在方法与致谢中引用可省大量时间。
- 论文数字口径不一致（155 / 149 行 / 163 文件；`TEM-FSP` vs 文件名 `TEM_FEP`）→ **引用时写"该仓库发布的 landscape 集合（论文称 155 个）"**，不要自行推断。

### 3.5 决策规则（冻结）

| 结果 | Phase I 后果 |
|---|---|
| ≥1 个满足 ①②③④ 的候选 | **可争取 publication-level 的"跨系统"结论**（H1 需在 ≥2 个 dense landscape 成立） |
| 判据 ④ 仅在小空间成立 | H1 降级为"跨任务可复现"；跨系统结论**保留但降级措辞** |
| 候选全部不可用 | 结论预先降级为 *proof of principle for prospective starting-point valuation* |

**已签字的相关裁决（批次 #7）**：**INT-8 = (i)** —— 结论限定为"**跨酶、转录因子与结合蛋白**的 starting-point option value"；"第二个系统必须是酶"的 (ii) **正式放弃**（数据上不可行）。**OP-25**：CL-5 闸门阈值放宽至 **ρ ≤ 0.9**（**非盲决定，必须逐字引用 `FREEZE_LEDGER.md` 中的强制披露文本，并同时报告 0.8 阈值下的全部结果**）。

---

## 4. 跨数据集统一 schema 与规范化规则（冻结）

```
protein | system_type | sequence | parent | task | condition | replicate |
fitness | fitness_error | measurement_state | source_id | source_type | evidence_level | provenance_note
```

1. **原始 fitness 永远保留**；归一化只新增列。
2. 跨 task 比较**只能**在 task 内归一化后进行（Protocol §3）；**必须先用 §2.7-1 的证据验证锚点是否存在**。
3. **禁止插值**；imputation 仅作 sensitivity 且必须标注。
4. `measurement_state` 必须是四值之一：**`measured` / `censored` / `missing` / `inactive`**（TEM-1 的 `X`、MPH 的 `-` 归入后两类，`X` 是表型信息）。
5. Hamming 图只用**实测（measured）**节点建边；边的存在性与 fitness 可用性分开记录。
6. 必须记录：`original_deposit_url`（≠ 聚合来源）、`derived_sources_checked`、`columns_lost_in_derived`、`has_replicate_columns`、`censoring_rule`、`floor`、`ceiling`、`usable_frac`、`informative_frac`。
7. `source_type` ∈ { `author_deposit` / `journal_source_data` / `secondary_distribution` / `derived_aggregate` }；**license 不具传递性**。

---

## 5. License 与再分发

| 状态 | 数据集 |
|---|---|
| ✅ **已核实** | TEM-1CML **GPL-3.0-or-later**；TrpB **CC0-1.0**；TEV **CC-BY-4.0**；Kosterlitz **CC-BY-4.0**；DAOx **CC-BY-4.0**；amiE **CC-BY-4.0**；glmS **CC-BY-4.0**；DHFR **MIT**；Hsp90 EMPIRIC **CC-BY** |
| ⚠️ **未核实（不得进入再分发声明）** | **PTE、CTX-M-14、Bank2016、Mira2015、MaveDB score sets、以及 CR9114 的数据文件本身**；SSMuLA；MPH |

**证据缺口（必须记录）**
- **ProteinGym**：README **只为 code 声明 MIT**，底层 DMS 数据**无可见许可声明** → 不能写"ProteinGym 数据是 MIT"。
- **CIS-BP**：站点**任何地方都没有 license**；流传的 "Public Domain" **溯源到第三方 re3data**，非其自述。
- **PTE / MPH / Kosterlitz 三个作者仓库均无 LICENSE 文件**。

**规则**：`data/` 只保存来源 URL/DOI + sha256 + 获取时间，**不重分发**任何第三方数据；再分发场景必须**逐数据集回源**，不得引用聚合仓库的许可标签。

---

## 6. 数据核验规程（冻结）

### 6.1 CL-7 删失闸门（censored ≠ missing ≠ measured）

**定义**：若某任务下某变体满足 `rep_a = rep_b = rep_c` 且 `sem = 0` 且值位于滴定/检测边界，则该观测为**删失**——含义是"信号弱于/强于检测限"，**不是"零噪声的精确测量"**。

1. 删失观测是**有界的真实观测**，必须与 `missing`、`measured` 三者分列。
2. 主分析**只用 measured 子集**；删失在 sensitivity 中用**区间/序数处理**（如 `F ≤ 边界值`），**不得**当作精确 fitness 参与 `max` 或排序，**也不得**直接丢弃（丢弃会引入相反方向的偏差）。
3. **有效 degree 必须按 measured 计算**（与 TEM-1 的"拓扑 degree 18 vs 有效 fitness degree"同源）。
4. 适用于**所有**数据集；`floor` / `ceiling` 必须由数据实测确定并写入 manifest。

**语料级独立交叉验证（M0-1，✅ 强证据）**：GraphFLA 派生 CSV 的**地板占比**与我对上游 eLife 源数据的**可用率实测完全吻合**：

| 文件 | 地板占比（派生 CSV） | 我的 eLife 源数据实测 | 关系 |
|---|---|---|---|
| `Phillips2021_CR9114_fluB` | **0.997** | 可用率 **0.3%** | 1 − 0.997 = 0.3% ✅ **完全吻合** |
| `Phillips2021_CR9114_h3` | **0.891** | 可用率 **10.9%** | 1 − 0.891 = 10.9% ✅ **完全吻合** |
| `Podgornaia2015_PhoQ` | 0.637 | — | — |
| `Bendixsen2019_hdv` | 0.429 | — | — |
| `Mira2015_TEM_{AMP,CAZ}` | 0.250（**仅 3 个不同取值**） | 与 M0-3 的地板裁剪发现一致 ✅ | — |

→ **全语料仅 4 个文件地板占比 > 30%**；**删失不是抗体数据独有**，而是这些文库的普遍特征。**CL-7 必须在所有数据集上执行，不得只对 Phillips 系列执行。**

### 6.2 CL-9 informative fraction 与任务准入闸门

**反例**：`SI06` 的 `usable_frac = 50.7%`（按 CL-7 的 ≥50% 门槛恰好通过），但 **mean 中位数 = 6.04 而 floor = 6.000** → 实际有信息的只有 **43.0%**。

1. 每个任务必须同时报告三元指标：`usable_frac`（sem>0）、**`informative_frac`（sem>0 ∧ mean > floor + 2·SEM）**、`censored_frac`。
2. **任务准入以 `informative_frac` 为准**：`≥50%` 主任务 / `20–50%` 仅敏感性 / `<20%` 排除。
3. 按此裁决 **Phillips2023**：MA90（93.7%）与 G189E（82.6%）为主任务，SI06（43.0%）仅敏感性；**CR9114**：h1（96.0%）主任务、h3（10.9%）仅敏感性、fluB（0.3%）**排除**。

### 6.3 CL-8 原始 deposit 优先 + `processed ≠ raw`

1. **判据 ②/③/④ 的核实对象只能是原始 deposit**（eLife source data / CaltechDATA / Zenodo / SRA / Figshare / 作者 GitHub）。
2. 聚合仓库（GraphFLA / ProteinGym / FLIP / SSMuLA / RNAGym）**只能**用于**发现候选**与**计算 baseline 特征**。
3. **"processed 无多条件列" 不能推断 "raw 无多条件"；"聚合仓库只有单列 fitness" 不能推断 "上游无重复"。**（四次复现见 §2.5）

### 6.4 任务相似度闸门（CL-5，OP-25 已签字放宽至 0.9）

**规则**：作为 held-out future task 的任务，必须与 today task 的 Spearman **`ρ ≤ 0.9`**；否则不得用作 Tomorrow Test 的 future task（可保留为 robustness）。矩阵必须写入 M2 出口报告，**不得在看过 EOV 结果后修改阈值**。

**强制披露文本（一切写作中必须逐字引用）**：
> 用于判定 future task 是否与 today task 充分正交的相似度闸门阈值为 **Spearman ρ ≤ 0.9**。该阈值是在已算出各任务对的 ρ 值（MA90↔G189E = 0.886、SI06↔G189E = 0.772、MA90↔SI06 = 0.645）**之后**确定的；在更严格的 ρ ≤ 0.8 阈值下，MA90↔G189E 不通过。**0.8 阈值下的全部结果一并报告。**

**由此冻结的 Phillips2023 主分析设计**

| 层 | today → future | informative 交集 | ρ |
|---|---|---|---|
| **主分析** | **MA90 → G189E** | **50,644** | 0.886 |
| **强制共同报告** | MA90 → SI06 | 26,349 | 0.645 |
| **强制共同报告** | G189E → SI06 | 28,197 | 0.772 |

### 6.5 预算-空间硬规则（OP-21，待签字）

`B ≤ |space| / 4`（coverage ≤ 25%），每个 `(landscape, B)` 必须报告 coverage；违规 landscape **降为 oracle-only**，不得参与预算型主张。由此：PTE 上限 `B ≤ 16`、MPH/Kosterlitz `B ≤ 8`、Mira2015 `B ≤ 4`（事实上 oracle-only）。

### 6.6 环境限制（复现性）

| 项 | 事实 |
|---|---|
| **Python** | `<PYTHON_BROKEN>` **损坏**（`ModuleNotFoundError: No module named 'encodings'`）→ PATH 上的默认 `python` 不可用；一律用 `<PYTHON>`（**3.12.3**）或自建 conda 环境 |
| **GPU** | RTX 4070 Laptop **8 GB**；ESM-2 650M fp16 推理可用；**禁止**重算 TEM-1 epistasis（需 ≥40 GB） |
| **GraphFLA 数据** | 163 个 CSV **无法在 Windows 上 git checkout**（文件名含 `*`）→ 逐文件 HTTP 直取 + URL 编码 |
| **GitHub 核实** | 未认证 REST API **60 req/h/IP** 全局限流 → 依赖仓库树的核实必须用**带认证调用**或 `git clone --depth 1` |

---

## 7. 禁止事项（数据层，冻结）

1. 用二手镜像（尤其合并了 imputed 值的副本）替代原始数据源。
2. 把 MIC panel 当作完整 landscape。
3. 把 DAOx 单突变扫描当作多轮 evolution。
4. 用插补值做任何主分析。
5. 让 future task 的任何 fitness/标签/统计量进入特征构造、超参选择或 parent 排序。
6. 事后挑选最有利的浓度/条件。
7. 在看见结果后修改 EOV 定义或 GO 判据。
8. 把"任务相似度 ≈ 1"的两个条件当成 future task。
9. **用聚合仓库的派生版本判定判据 ②/③/④**（噪声、缺失率、完整性）。
10. **把删失观测当作精确测量**，或直接丢弃。
11. **在未定义地板处理之前**使用 `Mira2015_TEM_*` 的 15 个任务面板。
12. **用 GraphFLA 的 2 个派生文件代替 PTE 源数据的 9 个底物 CSV**。
13. **在再看一遍结果之后放宽 CL-5 阈值**（当前已固定在 0.9，且必须同时报告 0.8 下的结果）。
14. 引用论文声明的规模数字而不标注"论文声明"。

---

## 8. M0 状态与未完成项

**已完成**：M0-2a（TEM-1 全套，含噪声实测）、M0-3（Mira2015 语义）、**P0-0（Phillips2023 source data 实测裁决）**、Jalal2020 结构核实、M0-4 原始 deposit 复核（PTE/MPH/Kosterlitz 存在性 + license 缺失）。

| # | 未完成项 | 状态 |
|---|---|---|
| M0-1 | **163 个 GraphFLA CSV 全量校验** | ✅ **完成（162/163）** → `data_registry/M0_csv_sweep.csv`；仅 `learning.csv` 404 待查 |
| M0-1b | **展开 `Johnston2024` 的 10 个文件**（TrpB 语料的任务轴） | ⏳ 新增（与 P0-9 相关） |
| M0-2 | 各数据集 fitness 语义与 floor/ceiling | ✅ TEM-1 / Phillips2023 / CR9114 / Jalal2020 / Mira2015 / PTE / MPH / Kosterlitz；⚠️ **MPH 行数结构待澄清** |
| M0-4 | PTE / MPH / Kosterlitz 原始 deposit 复核 | ✅ 完成（**三者均无 LICENSE 文件**） |
| M0-9 | TEM-1 完整性 + Kosterlitz 宿主定位 | ✅ 完成（见 §2.1 与 §2.6） |
| M0-10 | `PHASE1_DATA_GATE.md`（M0 出口裁决） | ✅ 完成（**GO 有条件**）—— 本文件 §8 的出口判据已由该文件承接 |
| M0-5 | license 回源（PTE / CTX-M-14 / Bank2016 / Mira2015 / MaveDB / CR9114 数据文件 / SSMuLA / MPH） | 🟡 后台 agent `28c077ea` |
| M0-6 | **TrpB novelty 独立核实（P0-9）** | 🟡 后台 agent `28c077ea` |
| M0-7 | AncSR1 数据入口（P2，不阻塞） | 🟡 后台 agent `28c077ea` |
| — | ⚠️ **MPH 的基因型行数与位点结构**仍待澄清 | ⏳ 唯一残留的数据结构缺口 |
| M0-8 | 本文件 v3 | ✅ |

**M0 出口**：**`data_registry/PHASE1_DATA_GATE.md` 已产出（裁决：GO 有条件）**。数据层判据见 §3.5；**M0 未通过前禁止进入 M4 及以后（CL-4）**。

---

## 9. 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| v1 | 2026-09-19 01:10 | 初版冻结：4 个数据集裁决、TEM-1 拓扑/有效 degree 区分、cheater 政策、缺口与决策规则。 |
| v2 | 2026-09-19 01:21 | 并入缺口搜索结果（GraphFLA 语料 + multi-task 候选梯队）、判据 ④ 缺口、Novelty 风险升级、三条结构发现；schema 加 `system_type` / `missingness_flag`。 |
| **v3** | **2026-09-19** | **折叠 AMENDMENT-001…005 与 M0 实测结果**：① 判据 ④ 缺口关闭（Phillips2023 满足全部 4 条；CR9114 h1 满足 ④ 但为单任务）② 新增最终证据链表（§2.6，取代 A-3/B-3/D-10）③ 并入 TEM-1 逐位点实测、噪声天花板、AZT IQR/SD 发现 ④ 并入 PTE/MPH/Kosterlitz/Jalal2020/Mira2015 实测 ⑤ 新增 §6 数据核验规程（CL-7 / CL-9 / CL-8 / CL-5+OP-25 披露文本 / OP-21 / 环境限制）⑥ 升级 §3.2 穷尽性方法学声明 ⑦ §3.4 补入 TrpB 原文 novelty 风险 ⑧ license 表改为「已核实 / 未核实」两栏 ⑨ 禁止事项扩到 14 条 ⑩ 并入 **M0-1 全量校验结果（162/163、58 个精确完整乘积空间、22 个缺失文件）与语料级删失交叉验证**（CR9114 fluB/h3 地板占比与我的 eLife 实测完全吻合）。**本次修订发生在 EOV 分析运行之前，无需盲法重跑。** |
| v4（待） | — | M0 剩余项（163 CSV 全量校验、MPH 结构、license 回源、TrpB novelty 独立确认）完成后追加。 |
