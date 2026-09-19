# AMENDMENT-001 — 缺口搜索结果并入预注册（含 Novelty 重定位）

| 字段 | 值 |
|---|---|
| 版本 | **1** |
| 时间 | **2026-09-19**（精确时间戳见 `data_registry/FREEZE_LEDGER.md`） |
| 状态 | **FROZEN**（本文件本身即为修订载体，不修改 `PHASE1_DECISION.md` v1 / `PHASE1_PROTOCOL.md` v1 原文） |
| 依据 | `data_registry/LANDSCAPE_HUNT_v0.md`（子代理枚举，方法可查） |
| **时机** | **任何分析均未运行** → 本修正案属于预注册期修订，**无需盲法重跑**。 |

## 修正范围

| 被修正对象 | 修正内容 |
|---|---|
| `PHASE1_DECISION.md` v1 §3（H1 / H2 / 跨系统要求） | 见 A-1、A-2、A-3 |
| `PHASE1_DECISION.md` v1 §4.1（决策表） | 见 A-2 的 H2 门槛提升说明 |
| `PHASE1_PROTOCOL.md` v1 §1.1（TIS 特征） | 见 A-2（GraphFLA 特征必须进 baseline 而非可选） |
| `PHASE1_PROTOCOL.md` v1 §2.3（缺失处理） | 见 A-5 |
| `PHASE1_PROTOCOL.md` v1 §4 / §7（噪声） | 见 A-1 |
| `PHASE1_PROTOCOL.md` v1 §6.3（候选空间） | 见 A-6 |
| `PHASE1_PROTOCOL.md` v1 §11（M0） | 见 A-7 |
| `PHASE1_PROTOCOL.md` v1 §12（开放参数） | 新增 OP-17 … OP-20 |

---

## A-1｜H1 的噪声缺口与三段式补救阶梯（对应 OP-17 / INT-7）

**事实**：所有新 L3 候选（Phillips2021/2023、Moulana 面板）的公开 CSV **无 replicate/SD 列**，且 unique genotype 数 = 行数。判据 ④ 在已发布文件中**不满足**。

**修正**：H1 的"起点异质性 > 噪声"检验改为**阶梯式**，按可得性自上而下选用，**必须在 M0 结束时确定用哪一档并写死**：

| 档 | 条件 | H1 表述 |
|---|---|---|
| **A（最强）** | 回源取得 ≥2 次独立测量（eLife / Desai 实验室原始表含 `replicate`/`bin`/`tile`/`library`/`sd`） | 原表述：`IQR(V) ≥ 2 × 测量不确定性` |
| **B（外部校准）** | 无回源重复，但可借带重复列的外部数据集（如 `HSP82_YEAST_Flynn_2019`）标定噪声尺度 | `IQR(V) ≥ 2 × 外部校准噪声`，并**显式声明噪声尺度为外部借用** |
| **C（降级）** | 二者皆不可得 | 改用 **"起点效应跨 future task 可复现"**（跨任务方向一致 + CI 分离），**禁止**再声称"超过实验噪声" |

- **TEM-1 始终走 A 档**（triplicate 真实存在）→ H1 的 A 档至少在 TEM-1 上必须成立。
- **OP-17（新）**：档位选择规则与最终档位 → ⏳ 待签字。
- **INT-7（新）**：C 档下 `IQR ≥ 2×σ` 的替代判据（建议：跨 ≥3 个 future task 的方向一致性 + bootstrap CI 分离）→ ⏳ 待签字。

---

## A-2｜H2 的 baseline 必须升级（**门槛被显著提高，请确认**）

**事实**：GraphFLA（NeurIPS 2025 Spotlight）已发布 **20 个景观特征**的参考实现，其中包含与我们的 `R_k^oracle` 概念高度重叠的 **per-config 可及性**度量：
`global_optima_accessibility`、`local_optima_accessibility`、`mean_path_length_to_global_optimum`、**`evolvability_enhancing_mutations (φ_EE)`**、`extradimensional_bypass`、`basin_fitness_correlation`，以及 `fdc`、`gamma`、`local_optima_ratio`、`neutrality` 等。

**修正（H2 的 proxy-only 基线集合）**：
1. **GraphFLA 全部 20 个特征**（含所有 per-config 可及性量）**必须**进入 proxy-only 基线。
2. **SSMuLA 的 DE/MLDE 结果**（96/384 预算、50 replicates）必须作为**已有方法对照**，不得当作我们的新实现。
3. H2 判据（`ΔCV-R² ≥ 0.05` 或 `regret reduction ≥ 20%`，CI 不跨 0）**不变**，但因为基线变强，**通过难度显著上升**。
4. 若 EOV 的增量价值在加入 GraphFLA 特征后消失 → **H2 失败 → 按 NO-GO/MODIFY 处理**。这一点必须接受，不得事后削弱基线。

> **对决策表的影响**：H2 的 "strong GO" 门槛含义变为"**在最强的现有特征集之上**仍有增量"，这比 v1 的措辞更强。**请确认接受。**

---

## A-3｜跨系统要求：状态更新 + 证据链角色分配（对应 INT-8）

**状态**：v1 的"跨系统要求"（需第二个独立 multi-task dense landscape）**现已具备满足条件** → **不再预先降级为 proof of principle**（条件：判据 ④ 经 A-1 补救）。

**建议的证据链角色分配（请确认）**：

| 角色 | 数据 | 回答什么 |
|---|---|---|
| **主** | **TEM-1**（AMP → AZT；唯一有真实 triplicate） | 严格 Tomorrow Test；酶-新底物 |
| **第二例（酶，多条件）** | `new_PTE`（2NH / butyrate）或 `Lunzer2005`（fitness / NAD / NADP） | 同语义（酶活性）跨任务的起点估值 |
| **高密度多任务复制** | **`Phillips2023`**（16 位点 × 3 任务 × 65,536，缺失 0.01–0.04%）、`Moulana2023`（15 位点 × 5 任务，MNAR） | "TEM-1 是不是特例" |
| **同蛋白多任务面板** | `Mira2015_TEM_*`（TEM-1 × 15 抗生素，2^4） | `Corr(EOV_τ1, EOV_τ2)` → MODIFY 判据 |
| **模态对照** | `Soo2021`（RNA × 2 温度） | 定义的普适性（L0，非蛋白证据） |

**INT-8（新，须裁决）**：`Phillips*` / `Moulana*` 是**结合/免疫逃逸**景观，不是酶定向进化。用它们作"跨系统"证据时：
- **(i)** 接受为跨系统证据，但把结论限定为 **"protein starting-point option value（跨酶与结合蛋白）"**（推荐）；
- **(ii)** 要求第二个系统也必须是**酶** → 则跨系统证据只能用 `new_PTE` / `Lunzer2005` 这类小空间 L2，**publication-level 的跨系统主张将难以成立**；
- **(iii)** 分层主张：酶内结论 + 跨模态外推分别陈述。

---

## A-4｜新增硬门：任务相似度闸门（CL-5）

**理由**：若"future task"与 today task 的秩一致性 ≈ 1，则 Tomorrow Test 是假的（模型其实看见了同一个任务）。这是**最容易自欺的一步**。

**新增为强制前置检查（在 M4 之前、且在任何 H1/H2 计算之前）**：
1. 对每个数据集的任务面板，计算**跨任务秩一致性矩阵**（Spearman ρ，在共同可测基因型上）。
2. **闸门规则**：作为 held-out future task 的任务，必须与 today task 的 `ρ ≤ 0.8`；否则该任务**不得**用作 Tomorrow Test 的 future task（可保留为 robustness）。
3. 该矩阵与闸门结果必须写入 M2 出口报告，**不得在看过 EOV 结果后修改阈值**。
- **CL-5**：闸门阈值 `ρ ≤ 0.8` 与"每数据集至少 1 个合格 future task"的要求 → ⏳ 待签字。

---

## A-5｜MNAR / 缺失处理政策（对应 OP-18）

**事实**：Moulana 面板缺失率跨任务差异极大（S309 0% → CB6 49.6%），且**缺失很可能非随机**（低亲和力/不表达变体更可能测不到）。

**修正（冻结默认）**：
1. **主分析限定在"共同可测基因型交集"上**，并报告交集大小；不得用插补扩大交集。
2. **任务纳入门槛**：held-out 任务缺失率 ≤ **10%** 才可进主分析；10–25% 降为 sensitivity；> 25% **不得**作为主分析任务（CB6、CoV555 因此只能进 sensitivity）。
3. **MNAR 检验**：比较缺失与非缺失基因型在**有完整数据的其他任务**上的 fitness 分布（如用 S309 的 0% 缺失做参照）；若分布显著不同 → 标记为 MNAR 并在结论中显式限制。
4. `Anderson2021_MPH` 的 `-` 状态按 indel/missing 单独建模，不参与 Hamming-1 边。
- **OP-18**：上述门槛（10% / 25%）与 MNAR 检验方法 → ⏳ 待签字。

---

## A-6｜实现约束：混合字母表乘积空间（CL-6）

**事实**：新候选的空间形态是混合字母表的（Lunzer2005 = 2×4×8×2×2×2 = 512；Wu2020 = 4×4×3×… = 576；TEM-1 = 4×3³×2⁹ = 55,296），**不是**二元超立方体。每个节点的度恒定 = `Σ(位点等位数 − 1)`，但**不同位点分支因子可差 4 倍**。

**修正**：`eov/landscape.py` **不得**假设二元超立方体；必须以 `(位点, 等位集合)` 的通用乘积空间表示实现；Hamming-1 邻域 = "任一位点换成该位点的另一个等位"。此约束写入 Protocol §6.3 的候选空间定义。
- **CL-6** → ⏳ 待确认。

---

## A-7｜M0 的 P0 动作清单（更新，按优先级）

| # | 动作 | 为什么是 P0 |
|---|---|---|
| 1 | **回源取噪声结构**：Phillips2021/2023（eLife Data Availability）、Moulana2022/2023（Desai 实验室仓库），找 `replicate`/`bin`/`tile`/`library`/`sd` 列 | **决定 H1 是 A 档还是 C 档** |
| 2 | **确认 fitness 语义与量纲**（各文件 fitness 列的分布 + 原文 Methods）：是 log 亲和力、escape fraction、还是富集比 | 决定跨任务归一化方案（B4 已证会当场爆炸） |
| 3 | **读懂 `Mira2015_TEM_*` 的 fitness 列**（中位数 = 最大值 = 0 的含义） | 不理解它，15 个"任务"是假的 |
| 4 | **逐条独立复核**子代理数据（本文 §2.6 全部条目）：文件名、行数、缺失率、位点取值域 | 子代理核实方法可查但未由我复算 |
| 5 | **license 逐数据集回源核实**（尤其 eLife / Nat Commun / Science） | 再分发合规 |
| 6 | **验证 WT/dead 锚点是否存在**于各新数据集（否则 §3 归一化方案无锚可用） | 归一化的前提 |
| 7 | `ChenFT22`（Nat Ecol Evol 2022）单独核实：GraphFLA 引用了它但未放进 155 表，疑为遗漏的多环境蛋白景观 | 可能再补一个候选 |
| 8 | 确认全部 163 个 CSV 的 `pos` 取值域（本次只做了 28 个） | 空间形态的自动校验 |

**M0 出口**：一页 data go/no-go + `DATA_AUDIT.md` v3。

---

## A-8｜新增待签字条目汇总（并入 FREEZE_LEDGER）

| ID | 内容 | 默认 |
|---|---|---|
| **OP-17** | H1 噪声档位选择（A/B/C）与最终档位 | 先尝试 A，M0 结束前定档 |
| **OP-18** | MNAR 门槛：主分析 ≤10%、sensitivity 10–25%、>25% 排除 | 见 A-5 |
| **OP-19** | 跨系统证据链角色分配（A-3 表） | 见 A-3 |
| **OP-20** | GraphFLA 20 特征作为 baseline 的接入方式（复用 `pip install graphfla` vs 自实现） | 复用官方实现，固定版本号 |
| **INT-7** | C 档下 H1 的替代判据 | 跨 ≥3 任务方向一致 + CI 分离 |
| **INT-8** | 结合/逃逸景观是否算"跨系统"证据 | 接受 (i)，结论限定为跨酶与结合蛋白 |
| **CL-5** | 任务相似度闸门 `ρ ≤ 0.8` 及"每数据集 ≥1 个合格 future task" | 见 A-4 |
| **CL-6** | `landscape.py` 必须按混合字母表乘积空间实现 | 见 A-6 |

---

## A-9｜Novelty 定位段（建议直接用于论文/预注册摘要）

> 现有工作（GraphFLA, NeurIPS 2025）已证明**景观层面的几何特征**与 directed evolution 的成功率相关（20 个蛋白景观 × 5 种 DE 方法 × 100 次随机初始化，指标为达到的最优 fitness percentile）。本文不问"什么样的景观好演化"，而问一个**决策论问题**：在**同一张景观**上，今天在已知任务下表现相同的两个起点，面对一个**完全未知的未来任务**时，其**经过固定实验预算适应后的终值**是否不同，以及**仅凭今天可得的信息**能否提前选出更优的起点。为此我们（i）以**单个起点**而非整张景观为分析单位，（ii）引入**任务 holdout**（未来任务的任何测量都不进入特征构造、超参选择与排序），（iii）以 **selection regret** 而非最大适应度分位数为主指标，（iv）将可达价值分解为 `R_0`（即时准备度）、`R_k^oracle`（景观机会）与 `R_{B,π}`（预算与策略可及），从而把**景观机会**与**搜索能力**分开。所有基线（含 GraphFLA 的全部 20 个景观特征与 SSMuLA 的 DE/MLDE 实现）均在**同一 Today Information Set** 下比较。

---

## 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| 1 | 2026-09-19（预注册期） | 初版：H1 噪声三段阶梯、H2 baseline 升级为含 GraphFLA 全特征、跨系统状态更新与证据链角色、任务相似度硬闸门、MNAR 政策、混合字母表实现约束、M0 P0 清单、8 条新增待签字条目。**分析未运行，无需盲法重跑。** |
