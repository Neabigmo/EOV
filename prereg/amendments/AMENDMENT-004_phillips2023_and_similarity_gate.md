# AMENDMENT-004 — Phillips2023 实测裁决、任务相似度闸门生效、以及"processed ≠ raw"规则

| 字段 | 值 |
|---|---|
| 版本 | **4** |
| 时间 | **2026-09-19**（精确时间戳见 `data_registry/FREEZE_LEDGER.md`） |
| 状态 | **FROZEN** |
| 依据 | ① **我对 eLife 83628 source data 的直接实测** ② 子代理两份 DELTA（四资源穷尽检索 / RNA 更正） |
| **时机** | **任何 EOV 分析均未运行** → 预注册期修订。**但见 D-3：本修正案记录了一处"已知数据后再定阈值"的完整性事件，必须披露。** |

---

## D-1｜🔴 **Phillips2023 是完整合格的 L3 —— P0-0 已由我执行完毕**

**实测对象**：`https://cdn.elifesciences.org/articles/83628/elife-83628-fig1-data1-v3.xlsx`（14,142,772 B，HTTP 200）。
**论文身份已核实**：Phillips AM, Maurer DP, Brooks C, Dupic T, Schmidt AG, Desai MM, *"Hierarchical sequence-affinity landscapes shape the evolution of breadth in an anti-influenza receptor binding site antibody"*, eLife 83628（2023-01-10；VoR 2023-06-30）。

**Sheet1**（结合，65,535 数据行）：`geno, MA90_{rep1,rep2,mean,sem}, SI06_{rep1,rep2,mean,sem}, G189E_{rep1,rep2,mean,sem}`

| 任务 | n（有 mean） | sem = 0 | usable（sem>0） | **informative**（mean > floor+2SEM） | floor | 中位 SEM |
|---|---|---|---|---|---|---|
| **MA90** | 65,530 | 4,119 | 61,411（93.7%） | **61,395（93.7%）** | 7.948 | 0.027 |
| **G189E** | 63,840 | 9,478 | 54,362（85.2%） | **54,121（82.6%）** | 6.000 | 0.049 |
| **SI06** | 64,619 | 31,825 | 32,794（50.7%） | **28,206（43.0%）** | 6.000 | 0.074 |

**Sheet2（表达）**：`geno, exp_rep1_norm, exp_rep2_norm, exp_norm_mean, exp_norm_sem` —— **65,536 行、0 删失、100% 可用**，mean ∈ [0.78, 1.15]，中位 SEM **0.019**。

**裁决**：**满足全部 4 条判据**（① 16 位点完整 2¹⁶ ② 3 个抗原任务 + 1 条表达轴 ③ processed 数据可下载 ④ 每任务带 rep + SEM）。**这是本项目第一个真正可用的 multi-task + 真实噪声景观。**

**两项额外重大收益**
1. **表达轴（`exp_norm`）是实测的、带重复的**，不是预测的 ΔΔG。→ **直接替代**原决策 D2 中"没有实验稳定性/表达代理、只能用 FoldX/ThermoNet 预测"的妥协：H2 的表达/稳定性 proxy **现在可以是实测值**，论证强度显著上升。
2. 三个任务 + 表达轴共 4 条读数，全部同一 2¹⁶ 空间 → 严格 `N_k(x)`。

**被本修正案取代的旧表述**

| 位置 | 旧表述 | 更正为 |
|---|---|---|
| `DATA_AUDIT.md` v2 §1 注 | "目前没有任何数据集同时满足全部 4 条" | **对蛋白系统已不成立**：Phillips2023 满足全部 4 条；CR9114 h1 满足 ④ 但非多任务。**对 RNA 也不成立**（见 D-5） |
| `DATA_AUDIT.md` v2 §3.1 | 判据 ④"不满足（唯一硬缺口）" | 判据 ④ **在 Phillips2023 与 CR9114 h1 上成立**；缺口降级为"需按 CL-7 逐任务量化" |
| `AMENDMENT-002` B-3 表 | Phillips2023 "④✗" | **④✓**；角色升为**主 multi-task 系统** |
| `AMENDMENT-002` OP-24 | "若仅 1 个任务可用" | **已解决**：2 个任务 informative ≥ 82% |

---

## D-2｜新增 CL-9：**informative fraction**（usable_frac 单独不够用）

**我的实测给出一个反例**：`SI06` 的 `usable_frac = 50.7%`（按 CL-7 的 ≥50% 门槛**恰好通过**），但其 **mean 中位数 = 6.04**，而 floor = 6.000 → **超过一半的"可用"观测仍贴在检测限上**，实际有信息的只有 43.0%。

**新增冻结规则（CL-9）**：
1. 每个任务必须同时报告三元指标：`usable_frac`（sem>0）、**`informative_frac`（sem>0 ∧ mean > floor + 2·SEM）**、`censored_frac`。
2. **任务准入以 `informative_frac` 为准**：`≥50%` 主任务 / `20–50%` 敏感性 / `<20%` 排除。
3. `floor` 与 `ceiling` 必须由数据实测确定，并写入 manifest。
4. 该规则与 CL-7 一同适用于**所有**数据集。

---

## D-3｜⚠️ **完整性事件：我自己的相似度闸门把我最想要的配对否掉了**

**背景**：AMENDMENT-001 A-4 提出了强制前置闸门 **CL-5：作为 held-out future task 的任务，必须与 today task 的 Spearman `ρ ≤ 0.8`**（当时尚未签字）。

**我在 Phillips2023 上算出的实测值**（在 informative 交集上）：

| 任务对 | informative 交集 | **Spearman ρ** | 闸门结果 |
|---|---|---|---|
| MA90 vs **G189E** | 50,644 | **+0.886** | 🔴 **不通过**（>0.8） |
| SI06 vs G189E | 28,197 | +0.772 | ✅ 通过 |
| MA90 vs SI06 | 26,349 | **+0.645** | ✅ 通过 |

**完整性声明（必须记录）**：**ρ 值现在已经知道了。** 因此"是否保留 0.8 这个阈值"的决定**不再是盲的**。按本项目的门柱规则，只有两种合法处理：

- **(a) 保留 0.8**：MA90↔G189E **不得**进入主 Tomorrow Test；
- **(b) 若要把 MA90↔G189E 升为主分析**，必须在修订记录中**显式声明该阈值是在已知 ρ 之后放宽的**，并同时报告 (a) 下的结果。

**我的建议（推荐 a）**：
- **主 Tomorrow Test**：**`MA90`（today，93.7% informative）→ `SI06`（future，43.0%）**，ρ = 0.645，交集 26,349；
- **次**：`G189E`（today，82.6%）→ `SI06`（future），ρ = 0.772，交集 28,197；
- **`MA90 ↔ G189E`（ρ=0.886）仅作 robustness**，并注明"任务相似度过高，不构成严格 future-task holdout"。
- 代价必须写明：**SI06 是三个任务中最弱的一个**（informative 43.0%、floor 处堆积）→ 这是"任务越正交、测量越受限"的真实张力，**不得**用 ρ=0.886 的配对来回避它。

**新增 OP-25**：是否保留 CL-5 的 0.8 阈值（在已知 ρ 的前提下）。

---

## D-4｜CL-8 扩展：**processed ≠ raw**（已出现三次复现）

| # | 案例 | 派生版本丢失了什么 |
|---|---|---|
| 1 | GraphFLA ↔ eLife | 派生 CSV **丢掉 `rep`/`sem` 列**；且其"缺失"语义（442/1/2）与上游**删失**（2,643/58,374/65,343）完全不同 |
| 2 | **RNAGym processed ↔ raw** | processed assay 集把**整个配体浓度序列塌缩成单一 `DMS_score` 列**；raw 包里有 5 个浓度 + stErr |
| 3 | ProteinGym processed ↔ raw | processed 表丢失重复结构（本次 survey 第三次复现） |

**规则（已在 AMENDMENT-003 CL-8 确立，现扩充表述）**：
> **判据 ②/③/④ 的核实对象必须是原始 deposit。** 具体地：**"processed 无多条件列" 不能推断 "raw 无多条件"；"聚合仓库只有单列 fitness" 不能推断 "上游无重复"。**

落实到 Protocol：每个纳入数据集必须记录 `original_deposit_url`、`derived_sources_checked`、`columns_lost_in_derived`。

---

## D-5｜⚠️ 更正：**对蛋白成立，对 RNA 不成立**（glmS）

**更正**：本 survey 早期曾写"四个打包资源里没有任何 entry 同时满足 4 条判据"。**该句对蛋白成立，对 RNA 是错的。**

**`glmS` 核酶（Andreasson et al., *Nat Commun* 2020，`10.1038/s41467-020-15540-1`，**CC-BY-4.0** 已核实）**：
- 数据入口：`https://marks.hms.harvard.edu/rnagym/fitness_prediction/fitness_raw_data.zip`（🔷 **13,581,795 B，HTTP 206，首字节 `PK`**，匿名可取）
- 摘要原文（已读）："all possible single and double mutants … across a series of ligand concentrations, determining kcat and KM values for active variants"
- 🔷 未独立复核的细节：67 个可变位点、161,879 行、5 个配体浓度（40/160/640/2,500/10,000 µM）、每次测量带 `_stErr`、另有一条独立重复
- **判据 ①（Hamming-2 内穷举单+双突变）②（5 浓度 + kcat/KM + rescue）③ ④ 均 ✓**

**限制（冻结）**：**它是 RNA 不是蛋白**；held-out 轴是"配体浓度迁移"，不是蛋白条件轴。→ **只能作模态对照**（与 `Soo2021` 并列或替换后者，因 glmS 判据更完整）。**蛋白侧结论不变。**

**新增 OP-26**：glmS 是替换 `Soo2021` 还是并列。

**另两个 RNAGym raw 多条件集**：`li_2018`（酵母 tRNA，23,284 基因型 × 4 条件，但突变深度直方图 1:207/2:8101/3:6891/… → **随机文库而非组合文库，判据 ① ✗**）；`puchta_2016`（snoRNA，组合密度未核实）。

---

## D-6｜License 证据缺口（新增到 DATA_AUDIT license 列与再分发声明）

| 来源 | 事实 | 含义 |
|---|---|---|
| **ProteinGym** | README **只为 code 声明 MIT**，底层 DMS 数据**无可见许可声明** | 不能写"ProteinGym 数据是 MIT" |
| **CIS-BP** | 站点**任何地方都没有 license**；流传的 "Public Domain" **溯源到第三方 re3data**，非 CIS-BP 自己声明 | 同上 |
| **glmS / Nat Commun 2020** | Crossref license = **CC-BY-4.0** | ✅ 可再分发（署名） |

**规则**：**"我们用了 ProteinGym / CIS-BP" 在再分发时必须逐数据集回源**，不得引用聚合仓库的许可标签（与 CL-8 同源）。

---

## D-7｜三个对象升级为"仅差判据 ②"，以及两处陷阱

| 对象 | 已核实表头 | 规模 | 角色 |
|---|---|---|---|
| **`PHOT_CHLRE_Chen_2023`（CreiLOV）** | `HGVSp, rep1, rep2, rep3, mean, log_rep1..3, log_mean, mutant` | **165,407 个多突变体 / 118 位点** | 判据 ④ **可估**（此前记为未知）→ 档 B 外部校准候选 |
| **`GRB2_HUMAN_Faure_2021`** | `…, fitness, sigma, growthrate, growthrate_sigma` | 62,332 个双突变 / 56 位点 | 同上 |
| **`DLG4_HUMAN_Faure_2021`** | 同上 | 5,696 个双突变 | 同上 |

**陷阱 1（易误用）**：**MaveDB 里的 TF 条目不是 DNA 结合数据** —— 被检查的 TF-domain 条目实际是 **Human Domainome 1.0 的 DHFR 稳定性 DMS**（单条件、CC0）。将来不得当作"转录因子–DNA 结合"任务轴。

**陷阱 2（规模不可跨仓库互换）**：DLG4 在 ProteinGym 6,976 vs MaveDB 648,022；Hsp90 13,294 vs 189 → 疑为 nt/aa 级别与 curated 子集之别，**未确认**。→ 再次印证 CL-8。

**近失（若放宽门槛的第一顺位）**：**PAX6 paired-domain Y1H DMS**（McDonnell 2024, `10.1038/s44320-024-00043-8`, **CC BY**）：150 位点、**Hamming-1 完整**、**4 条件 = 2 个 DNA bait × ±geneticin**；但只有 **5,266 个多突变体（<10⁴）** 且未找到独立 processed deposit → 判据 ①（密度）与 ③ ✗。

---

## D-8｜穷尽性证据：**打包资源里不存在"多任务 × 密集组合"的蛋白条目**

对 **ProteinGym raw 包全部 213 个文件做表头扫描：每一个拥有 >1 个 score 列的文件都是单突变文库**。加上 MaveDB 全 2,063 个 experiment（35 个有多 score set，**无一组合多突变**）、RNAGym processed（原样嵌入 ProteinGym 蛋白 assay ID）、CIS-BP（PWM 构造）。

→ **方法学声明（写入 DATA_AUDIT §3）**：
> **"多任务 × 密集组合"的蛋白景观在任何打包资源里都不存在，只存在于原始文献的 curation 中。** 因此本项目的数据审计**必须逐文献 curation**；任何"我们的 landscape panel 来自现成 benchmark"的表述都不成立。

---

## D-9｜环境发现（写入 Protocol §13 复现性）

**`<PYTHON_BROKEN>` 是坏的**：`Fatal Python error: Failed to import encodings module` / `ModuleNotFoundError: No module named 'encodings'`。
→ **PATH 上的默认 `python` 不可用**；本项目一律使用 **`<PYTHON>`（3.12.3）** 或自建 conda 环境。此发现已在本次实测中阻塞过一次，务必写入环境清单。

---

## D-10｜连带影响汇总

| 条款 | 变化 |
|---|---|
| **INT-8** | 现在有实测支撑：`Phillips2023`（多任务蛋白，2 任务 informative ≥82% + 表达轴）→ **选项 (i) 可行**；"必须是酶"的 (ii) 仍不可行 |
| **OP-24** | **关闭**（≥2 任务可用） |
| **原决策 D2（stability proxy）** | **升级**：有实测表达轴（`exp_norm`，SEM 中位 0.019），不必用预测 ΔΔG 做主分析 |
| **A-2（H2 baseline 含 GraphFLA 20 特征）** | 不变；现可在**带真实重复**的数据上做增量检验 |
| **A-3 证据链** | 主数据仍为 TEM-1；**第二系统 = Phillips2023（已实测合格）**；`CR9114 h1` = 噪声校准床；glmS = 模态对照 |

---

## D-11｜新增待签字条目

| ID | 内容 | 默认 |
|---|---|---|
| **CL-9** | `informative_frac` 三元指标；任务准入以 informative 为准 | 见 D-2 |
| **OP-25** | 是否保留 CL-5 的 ρ ≤ 0.8（**已知 ρ 后决定，必须披露**） | 保留；MA90↔G189E 降为 robustness |
| **OP-26** | glmS 替换还是并列 `Soo2021` | 替换（判据更完整） |

---

## 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| 4 | 2026-09-19（预注册期） | ① 实测 Phillips2023：满足全部 4 条判据（MA90 93.7% / G189E 82.6% informative；SI06 43.0%），并附**实测表达轴** ② 新增 CL-9 informative fraction（SI06 反例）③ **完整性事件披露**：实测 ρ 后 CL-5 闸门否掉 MA90↔G189E，给出 (a)/(b) 两种合法处理与新 OP-25 ④ CL-8 扩展为"processed ≠ raw"，三次复现实证 ⑤ RNA 更正（glmS 满足 4 条，但仅作模态对照），"无资源满足 4 条"收窄为"对蛋白" ⑥ license 证据缺口 ⑦ 三个对象升级为"仅差判据 ②" + 两处陷阱 + PAX6 近失 ⑧ 穷尽性方法学声明 ⑨ 环境发现（`<PYTHON_BROKEN>` 损坏）。**未运行任何 EOV 分析。** |
