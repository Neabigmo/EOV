# PHASE1_PROTOCOL.md — Phase I 可执行预注册协议

| 字段 | 值 |
|---|---|
| 版本 | **v1** |
| 冻结时间 | **2026-09-19 01:10 (+08:00)** |
| 状态 | **FROZEN**（哈希见 `data_registry/FREEZE_LEDGER.md`） |
| 适用 | 所有 Phase I 计算（TEM-1 / TrpB4 / DAOx / SSMuLA panel） |

> 本协议必须**在写任何分析代码之前**冻结。任何偏离都必须写成书面修正案（amendment），并在结果中显式标注受影响的分析。

---

## 1. Today Information Set (TIS) 与泄漏防火墙

### 1.1 TIS 定义（Day-0 允许使用的一切）

对给定数据集与给定的 **known task `τ₀`**（TEM-1 = AMP 781 μg/mL），TIS 只包含：

| # | 允许的 Day-0 信息 | 备注 |
|---|---|---|
| 1 | `τ₀` 下每个基因型的实测 fitness（含重复与误差） | 唯一的功能信息来源 |
| 2 | 基因型本身（序列/编码）与 Hamming 结构 | 序列层面的信息 |
| 3 | 由 `τ₀` 数据**内部**算出的量：mutational robustness（Hamming-1 邻域均值/分位）、local smoothness、landscape 拓扑特征 | 必须只依赖 `τ₀` |
| 4 | 保守性（MSA / 同源序列统计） | 与任务无关的序列信息 |
| 5 | **frozen** PLM 零样本分数（ESM / EVmutation / ESM-IF，仅推理，不 finetune） | 复用 SSMuLA 现成分数 |
| 6 | 结构（PDB）与由结构算出的、**不涉及未来任务**的代理 | 不含预测型 ΔΔG 的主分析用途 |

### 1.2 明确禁止进入 TIS（泄漏）

1. 未来任务 `τ` 的任何 fitness、标签、排序、统计量、分布分位、上界/下界。
2. 由未来任务数据训练/选择的任何模型、超参、特征筛选结果。
3. 由未来任务算出的 `Readiness`（`u_τ(R_0(x,τ))`）—— **例外**：仅在 §8 的 **Tier-2 描述性** matched-pair 分析中作为**匹配变量**使用；**严禁**进入任何预测模型或选择规则。
4. 未来任务的"任务身份"本身（例如知道"未来是 AZT"）：Tomorrow Test 中模型必须在不知道 `τ` 的前提下输出 parent 排序。
5. 任何跨任务 pooling 的 statistic 若其计算包含了 withheld task 的数据。

### 1.3 执行机制

- TIS 的构造代码必须放在 `eov/` 下并被 `experiments/` 引用；所有特征函数签名只接受 `τ₀` 数据对象，**在类型/接口层面就无法访问 `τ`**。
- 每个实验目录必须包含 `TIS_MANIFEST.json`：列出用到的每一个输入文件（含 sha256）与每一个特征。
- 泄漏审计（M7 前）：由第二人/第二个 agent 独立复查代码路径，出具 `leakage_audit.md`。

---

## 2. Parent eligibility（eligibility = 数据可用性，不是性能筛选）

### 2.1 两类 degree

| 名称 | 定义 | TEM-1 | TrpB4 |
|---|---|---|---|
| **拓扑 degree** | `Σ(alleles_i − 1)`，完整乘积空间下恒定 | 18 | 76 |
| **有效 fitness degree** | 18/76 个 Hamming-1 邻居中，在 `τ₀` 下**可用**（已测 ∧ 非 `X` ∧ 通过质量门槛）的个数 | 待实测 | 待实测 |

**冻结规则：一切 eligibility 判定只能使用有效 fitness degree。** 禁止用拓扑 degree 代替（否则会把"邻居看不见"误读成"附近没有好未来"）。

### 2.2 纳入规则

- **主分析**：所有满足 `有效 fitness degree ≥ 50% × 拓扑 degree` 的基因型（TEM-1 ≥ 9/18；TrpB4 ≥ 38/76）。
  → 不人为 top-k（避免选择偏差）。
- **敏感性集合 A（near-WT）**：从 WT 出发总突变数 ≤ 2 的子集（TEM-1 约 1+18+153 = 172 个基因型；TrpB4 待算）。
- **敏感性集合 B（degree-matched）**：按有效 degree 分层抽样，使各层 parent 数均衡，用于检验 §2.1 的混杂是否驱动结论。
- 被排除的基因型必须出现在 `exclusions.csv`（含排除理由），并报告排除率。

### 2.3 `X` 与缺失

- `X`（non-functional/dead）与"未测/低质量"是**两个不同状态**：前者是表型信息（可入图），后者是缺失（不可入图，且禁止插补）。
- ⚠️ M0 必须确认 `X` 在编码文件中的确切语义（是"该替换组合失活"的编码约定，还是占位符）。
- 未测节点：TEM-1 待核（作者称 55,296 全覆盖）；TrpB4 约 871 个缺失（待核）。

---

## 3. 归一化（跨 task 可比性）

### 3.1 主尺度：WT/dead 双锚定（TEM-1）

$$
u^{\text{anchor}}_\tau(z) \;=\; \mathrm{clip}\!\left(\frac{z - F_\tau^{\text{dead}}}{F_\tau^{\text{WT}} - F_\tau^{\text{dead}}},\, 0,\, 1\right)
$$

- `F_dead` = `TEM-1dead`（S70A+E166A spike-in）在该条件的 fitness；`F_WT` = 库中未突变变体。
- **不变量**：`u_τ` 只依赖任务级参照点，**与候选 `x` 无关**。

### 3.2 敏感性尺度：empirical quantile

$$
u^{\text{q}}_\tau(z) \;=\; \hat{F}^{-1}_\tau\big(\text{rank of } z \text{ among eligible parents}\big)
$$

用于检验"某个 task 的 dead/WT 标尺异常是否把结论带偏"。**主结论必须在两种尺度下同向**；不一致时以 anchor 为主并如实报告冲突。

### 3.3 无 dead 锚点的 landscape（TrpB4 / SSMuLA panel）

- 主尺度：`u_τ(z) = (z − q_{0.05}) / (q_{0.95} − q_{0.05})`，分位数在该 landscape 的**实测**分布上定义（预注册，不随结果调整）。
- 敏感性：`scale2max`（SSMuLA 现成约定，最大值归一为 1）。
- **禁止**跨 landscape 直接混用原始量纲。

### 3.4 原始量纲

原始 fitness（TEM-1：AUC-fitness = log10 AUC）**永久保留**，所有归一化只新增列。

---

## 4. Fitness 与噪声

1. 每个 `genotype × condition` 保留全部重复测量（TEM-1 triplicate）。
2. 主点估计：**median**（仓库已提供 median AUC + error + CV；原分析亦用 median）。
3. **禁止**用单次测量的 max 充当 `R`：`max` 对噪声向上偏（winner's curse），且偏向大邻域。
4. `R_{B,π}` 的期望必须通过对**重复测量重采样**得到的分布来取（见 §7）。
5. 噪声天花板（H1 的分母）必须**从数据实算**，不得引用原文措辞。

---

## 5. 邻域与可达性

| 量 | 定义 |
|---|---|
| `𝒩_k(x)` | 与 `x` 的 Hamming 距离 ≤ k 的**实测可用**基因型集合（k=1 主分析；k=2,3 敏感性） |
| `R_k^{oracle}(x,τ)` | `max_{y∈𝒩_k(x)} F_τ(y)` —— landscape opportunity（附近客观上有没有好东西） |
| `R_k^{adaptive}(x,τ)` | 只允许沿**可接受路径**前进的可达最大值 |
| `R_{B,π}(x,τ)` | 现实预算/策略下的可达值（§6） |

**可接受路径的冻结默认**：一步 `x→y` 允许当且仅当 `F_τ(y) ≥ F_τ(x) − δ`，其中 `δ = 1 × 该任务重复测量的 pooled SD`。`δ` 的敏感性：`0.5δ`、`2δ`。

**分解纪律**：对每个合格 parent 必须**同时**报告 `R_0`、`R_k^{oracle}`、`R_k^{adaptive}`、`R_{B,π}`。禁止只给单一 "EOV score"——否则事后无法区分"附近没有好序列"与"算法找不到"。

---

## 6. Search policy 与预算语义

### 6.1 预算 `B` 的语义（冻结默认，见 OP-1）

- `B` = 搜索过程中被 **assay 的 unique 基因型数量**（同一样本测两次则计两次）。
- **起点 `x` 的 `τ₀` fitness 属于 Day-0 已知信息，不计入 `B`**，但 `x` 计入 `𝒜_{B,π}(x)`（因此 readiness 是终值的下界）。
- 轮次 `R = 3`（默认），第 1 轮随机采样 `b₁ = ⌈B/2⌉`，此后每轮 `b = ⌈(B−b₁)/(R−1)⌉`。
- 预算档位：`B ∈ {24, 96, 384}`（SSMuLA 现成实现只有 96/384，24 由我们实现）。

### 6.2 策略 `π`（默认 4 种）

| 策略 | 定义 |
|---|---|
| `random` | 在合法空间内均匀随机采样（固定种子） |
| `greedy-ssm` | 从当前最优出发，测其未测 Hamming-1 邻居；若超过 `b` 则按固定种子随机取 `b` |
| `mlde` | 在已测数据上拟合 ridge / gradient boosting（复用 SSMuLA 的 `model_classes=[boosting, ridge]`），预测全部未测，取 top-`b` |
| `al` | 不确定性感知采集（UCB / expected improvement），参考 SSMuLA 的 `alde4ssmula` |

每个策略在每档预算下运行 `n_replicate = 50` 次（复用 SSMuLA 默认；见 OP-4）。

### 6.3 候选空间

- 只允许在**实测可用**节点上采样（TEM-1 全覆盖，TrpB4 有 871 缺失）。
- 禁止对缺失节点插值补全后参与搜索（敏感性分析除外）。

---

## 7. `V_B` 的估计与不确定度传播

**冻结：不报单点估计，报分布。**

1. 对每个 parent `x`、每个 `τ`、每个 `π`、每档 `B`：
   - 外层：`n_replicate = 50` 次策略运行（不同种子）。
   - 内层：`n_boot = 500` 次重复测量 bootstrap（重采样 triplicate），把噪声传播进 `max`。
2. 输出：`V_{B,π}` 的 bootstrap/replicate 联合分布 → 报 median 与 95% CI，以及 `IQR`。
3. H1 的 "uncertainty" 取 **replicate-level bootstrap SD**（见 `PHASE1_DECISION.md` INT-5）。
4. 所有 CI 用 percentile bootstrap（95%）。

---

## 8. Matched-pair 程序

### 8.1 两个匹配层级（**新增澄清，需签字**）

| 层级 | 匹配变量 | 用途 | 泄漏状态 |
|---|---|---|---|
| **Tier-1（present-known）** | Day-0 TIS 可观测量：`τ₀` fitness、local robustness、conservation、frozen zero-shot | 预测侧的 "same present" | 无泄漏 ✅ |
| **Tier-2（present-both）** | Tier-1 全部 **+ Readiness（未来任务上的即时值）** | **描述性**最强主张："明天一来就能做到的水平也一样，但最终可达价值不同" | 使用未来任务信息，**仅限描述性**，严禁进模型 ⚠️ |

### 8.2 容差与匹配

- 容差 `ε = 1 × 该任务的 pooled replicate SD`（**由噪声定义，禁止人工调 ε**）。
- 匹配变量先标准化，用 caliper matching；允许多对多，但每对必须唯一（不放回）。
- Discovery/confirmation：按 `sha256(sequence + 预注册 salt)` 的奇偶切分为 50/50（salt 冻结）。
- Pair 搜索**只在 discovery 半集**进行；方向性预测在 **confirmation 半集**用同一规则重新找对并检验。

### 8.3 判据

见 `PHASE1_DECISION.md` §3 "Matched-pair confirmation"（≥20 对、方向成功率显著 > 0.5、aggregate 95% CI 不跨 0）。

### 8.4 必须披露

- 搜索的 pair 空间大小（有多少对曾被检验）。
- 全部 pair 的清单（不只报告显著的）。
- 多重比较处理（Benjamini–Hochberg，FDR 0.05）。

---

## 9. Tomorrow Test 协议

1. **冻结**：Day-0 模型（只用 TIS）训练完成并**冻结权重与代码哈希**；写出每个 parent 的排序。
2. **审计**：执行 §1.3 的泄漏审计。
3. **揭晓**：加载 withheld task `τ` 的数据。
4. **评估**：对下列 selector 计算 `V_{B,π}(x,τ)`：
   `random` / `current-fitness` / `stability-proxy` / `promiscuity-proxy`（可用处）/ `conservation` / `PLM-zero-shot` / **`EOV-based`** / **`oracle`**。
5. **主输出**：`NR`（未来任务归一化 regret）+ absolute `V`；比较对象是**最强 heuristic**，不是 random。
6. **降级条款**：TEM-1 只有一个 strict future task → 仅凭其达成只能称 proof-of-concept。
7. 若存在 TrpB4 的 T50 子集（见 `DATA_AUDIT.md` §2.2），可作为**第二个条件轴**做 holdout，但必须标注它**不是** novel functional task。

---

## 10. 统计

| 用途 | 方法 | 参数 |
|---|---|---|
| H1 异质性 | variance decomposition（parent 主效应 vs replicate 残差）+ permutation test | `n_perm = 10,000` |
| Effect size | 一律报告 effect/noise ratio、IQR/σ，不只报 p | — |
| CI | percentile bootstrap | `n_boot = 10,000`（外层统计） |
| H2 | 严格 held-out CV（嵌套：外层 split 固定，内层调参） | 见 OP-13 |
| Matched pair | 二项检验 + BH-FDR | FDR = 0.05 |
| 多重比较（跨 landscape） | BH-FDR | FDR = 0.05 |

**报告纪律**：任何"显著"必须同时给出 effect size、CI、以及被检验的假设总数。

---

## 11. 执行顺序与里程碑

| 里程碑 | 内容 | 出口判据 |
|---|---|---|
| **M0** | 数据核验：编码等位表、`X` 语义、噪声实算、主条件列名、license、CaltechDATA/Zenodo 文件清单 | 一页 **data go/no-go**；`DATA_AUDIT.md` v2 |
| **M1** | schema 冻结 + manifests（sha256） | 统一长表可用 |
| **M2** | landscape graph 构建 + 拓扑/有效 degree 统计 | 无 EOV 计算；只出 degree 与缺失报告 |
| **M3** | 噪声天花板与 baseline 描述统计 | `IQR(parent)` vs `σ(noise)` 首次可见 |
| **M4** | **H1** | 按 `PHASE1_DECISION.md` §3 判定 |
| **M5** | proxy baseline + **H2** | 增量价值（ΔCV-R² / regret reduction） |
| **M6** | matched pairs（discovery/confirmation） | ≥20 对判定 |
| **M7** | **Tomorrow Test** + 泄漏审计 | NR 降低 ≥20%（vs 最强 heuristic） |
| **M8** | `PHASE1_DECISION` 执行 → GO/MODIFY/NO-GO 报告 + Fig A–D | 决策报告冻结 |

**M0 未通过前禁止进入 M4 及以后。**

---

## 12. 开放参数登记表（**每一条都需要你签字或改值**）

未签字的条目视为**未冻结**，不得据此下任何 GO/NO-GO 裁决。

| ID | 参数 | 冻结默认 | 影响 | 状态 |
|---|---|---|---|---|
| OP-1 | 预算语义 | `B` = assay 的 unique 基因型数；起点不计入；`R=3` 轮；`b₁=⌈B/2⌉` | 改变 `R_{B,π}` 的绝对水平与策略间差距 | ⏳ |
| OP-2 | 预算档位 | `{24, 96, 384}` | SSMuLA 只有 96/384；24 需自实现 | ⏳ |
| OP-3 | `k`（邻域半径） | 主 `k=1`；敏感性 `k=2,3` | 决定 oracle potential 的含义 | ⏳ |
| OP-4 | 策略重复数 | `n_replicate = 50` | 与 SSMuLA 对齐 | ⏳ |
| OP-5 | 噪声 bootstrap | 内层 `n_boot = 500`，外层 50 | 计算量 vs CI 稳定性 | ⏳ |
| OP-6 | 有效 degree 门槛 | `≥50% × 拓扑 degree` | parent 数量与混杂控制强度 | ⏳ |
| OP-7 | 中性阈值 `δ` | `1 × pooled replicate SD` | 决定 adaptive-accessible 的宽严 | ⏳ |
| OP-8 | 匹配容差 `ε` | `1 × pooled replicate SD` | pair 数量与可信度 | ⏳ |
| OP-9 | discovery/confirmation 切分 | `sha256(seq+salt)` 奇偶 50/50，salt 冻结 | 防挑选 | ⏳ |
| OP-10 | NR 的 robust-worst | eligible parents 的 5% 分位 | 分母稳定性 | ⏳ |
| OP-11 | DAOx 任务距离 | 侧链描述符（vdW 体积、logP、HBD、HBA、pH7 形式电荷、芳香环数）→ z-score → 欧氏距离；按 near/far 分层报告 | 决定"task uncertainty"难度解释 | ⏳ |
| OP-12 | 无 dead 锚点 landscape 的 utility | `(z − q₀.₀₅)/(q₀.₉₅ − q₀.₀₅)`；敏感性 `scale2max` | 跨 landscape 可比性 | ⏳ |
| OP-13 | H2 的 CV 方案 | 嵌套 CV：外层 5-fold 固定 split（按 sequence hash），内层调参；`ΔCV-R²` 与 regret 指标各自独立报告 | 决定"增量价值"是否可信 | ⏳ |
| OP-14 | TrpB4 T50 子集用途 | 默认仅作 robustness；若覆盖率 ≥50% 才升为第二条件轴 | 决定 TrpB4 是 L2 还是 L3-lite | ⏳ |
| OP-15 | 主条件 | TEM-1：AMP 781 μg/mL + AZT 36 μg/mL | 必须在 M0 与正式版核对 | ⏳ |
| OP-16 | Tier-2 描述性匹配是否启用 | 启用（仅描述性） | 决定 Fig.2 的强度与泄漏边界 | ⏳ |

---

## 13. 复现性

1. TEM-1 官方环境：`uv` + Python 3.12（本机无 uv → 需先装）；或 `env/epistasis_env.yml`。
2. 本项目自有代码：conda 环境（Python 3.11/3.12）。**不使用 `<PYTHON_BROKEN>`**（生态兼容性风险）。
3. 全部随机种子显式固定并写入 `logs/`；每个实验目录含 `config.json` + `seeds.json`。
4. 数据 manifest：`data/manifests/*.sha256`（下载时间、URL/DOI、sha256）。
5. 任何图必须可由 `logs/` 中的一份配置从原始数据重跑得到。
6. 硬件事实：RTX 4070 Laptop **8 GB VRAM**（ESM-2 650M fp16 推理可用；**禁止**尝试重算 TEM-1 epistasis，需 ≥40 GB）。

---

## 14. 禁止的泄漏模式（清单，代码评审用）

1. 用 withheld task 的 fitness 做特征标准化（均值/方差/分位）。
2. 用 withheld task 的数据做特征选择或超参搜索。
3. 用全库（含 withheld）算 PLM score 的归一化常数。
4. 用 `Readiness`（未来任务量）作为预测特征。
5. 用未来任务的"任务身份"做 one-hot 或路由。
6. 在发现 matched pair 之后才定义匹配变量或容差。
7. 用 confirmation 半集的信息去调整 discovery 半集的 pair 搜索规则。
8. 报告时省略被检验的 pair / 特征 / 模型总数。

---

## 15. 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| v1 | 2026-09-19 01:10 (+08:00) | 初版冻结：TIS 与泄漏防火墙、拓扑 vs 有效 degree、WT/dead 双锚定、预算语义、4 种策略、噪声传播、Tier-1/Tier-2 匹配、Tomorrow Test、M0–M8、OP-1…OP-16 待签字。 |
