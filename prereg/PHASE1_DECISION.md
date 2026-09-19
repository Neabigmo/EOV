# PHASE1_DECISION.md — Phase I 判据与决策规则

| 字段 | 值 |
|---|---|
| 版本 | **v1** |
| 冻结时间 | **2026-09-19 01:10 (+08:00)** |
| 状态 | **FROZEN**（哈希见 `data_registry/FREEZE_LEDGER.md`） |
| 标题 | **Does evolutionary option value exist?** |
| 一句话目标 | *Proteins that look equally good today can carry profoundly different futures.* |

> ## 门柱不可移动规则（本文件存在的全部意义）
> 1. 本文件中的**每一个阈值在看见任何 EOV 结果之前冻结**。
> 2. 看见结果之后，**禁止**修改任何阈值、判据、或 EOV 定义。
> 3. 若确实必须修改：只能新增版本小节（v2/v3…），写明**修改原因、时间、修改者**，并且**必须在新版本下盲法重跑全部主分析**。禁止"改一点、沿用旧结果"。
> 4. `AdaptationPremium` 不允许成为任何选择/优化目标（见 §2.4）。
> 5. 未来任务的任何 measurement **不得**进入 Day-0 特征、超参选择或 parent 排序（见 §6）。

---

## 1. 核心命题（已重写）

**不再问**："starting genotype matters?" —— 这在 TEM-1 正式论文中已被回答（AZT 条件下轨迹高度依赖起始基因型），不构成增量。

**现在问**：

| 编号 | 问题 |
|---|---|
| **Q1** | Can starting-point value be defined **prospectively** under a **fixed adaptation budget**? |
| **Q2** | Is prospective value **reducible** to properties we already use to choose parents（current fitness / stability / promiscuity / conservation / PLM score）? |
| **Q3** | Can information available **today** select tomorrow's better starting points **without seeing tomorrow's measurements**? |

一句话边界：

> **Given that starting points matter, can we value them before the future task is known?**

---

## 2. 数学定义（v1 定稿）

### 2.1 记号

| 符号 | 含义 |
|---|---|
| `x` | 候选起点（parent / starting genotype） |
| `τ` | 未来任务/future task（含条件，如 AZT 36 μg/mL） |
| `F_τ(y)` | 基因型 `y` 在任务 `τ` 下的 fitness（task 内原始量纲） |
| `𝒜_{B,π}(x)` | 在起点 `x`、预算 `B`、搜索策略 `π` 下**实际被测量到**的基因型集合 |
| `u_τ` | **事先固定的 task-specific utility normalization** |
| `R_0(x,τ)` | `= F_τ(x)`，即 immediate readiness（今天的直接表现） |

### 2.2 三个量

$$
R_{B,\pi}(x,\tau) \;=\; \mathbb{E}\Big[\max_{y\in\mathcal A_{B,\pi}(x)} F_\tau(y)\Big]
\qquad\text{（期望对测量噪声与策略随机性取）}
$$

$$
\boxed{\;V_{B,\pi}(x,\tau) \;=\; u_\tau\big(R_{B,\pi}(x,\tau)\big)\;}
\qquad\text{（future terminal value，utility 单位）}
$$

$$
\boxed{\;EOV_{B,\pi}(x) \;=\; \mathbb{E}_{\tau\sim\mathcal T}\big[V_{B,\pi}(x,\tau)\big]\;}
$$

$$
Readiness(x) \;=\; \mathbb{E}_{\tau\sim\mathcal T}\big[u_\tau\big(R_0(x,\tau)\big)\big]
$$

$$
AdaptationPremium_{B,\pi}(x) \;=\; EOV_{B,\pi}(x) - Readiness(x)
\qquad\text{（仅用于解释）}
$$

### 2.3 语义（这是本次最重要的修正）

- **EOV = final future value**：回答"如果今天选 `x`，未来任务出现后、给定固定预算 `B`，最终预计能做到多好"。
- **AdaptationPremium = evolution added how much**：仅用于解释机制。
- **废除了 `EOV = R_B − R_0` 的旧定义。** 原因：绝对 improvement 会**结构性偏向低 `R_0` 的 parent**，把"起点差"误装扮成"未来选择权高"——而这恰好会伪造出我们最想证明的结论。绝对差与比值仍要报告，但**只能作为 secondary，且不得称为 EOV**。

### 2.4 不变量（违反即结果作废）

1. **`u_τ` 必须与候选 `x` 无关**，只由任务 `τ` 与**预注册的参照点**决定（TEM-1：WT/dead 双锚定；其他：见 Protocol §3）。
2. **`u_τ` 单调非降**，且在每个 task family 内形式固定。
3. **选择永远优化 `EOV`，永不优化 `AdaptationPremium`。**
4. **Ground truth 与预测侧不对称**：ground-truth `V`/`EOV` 使用已揭晓 `τ` 的 utility 尺度（oracle 侧）；Day-0 预测侧**只能**使用 Today Information Set（TIS）。这个不对称正是 Tomorrow Test 的全部意义。
5. `R_{B,π}` 的期望必须对**测量噪声**取（不得用单次 max 的点估计充数）。

### 2.5 Regret（主指标）

$$
Regret_{B,\pi} \;=\; V_{B,\pi}(x_{\text{oracle}},\tau) - V_{B,\pi}(x_{\text{selected}},\tau)
$$

$$
NR_{B,\pi} \;=\; \frac{V_{B,\pi}(x_{\text{oracle}},\tau) - V_{B,\pi}(x_{\text{selected}},\tau)}
{V_{B,\pi}(x_{\text{oracle}},\tau) - V_{B,\pi}(x_{\text{robust-worst}},\tau)}
$$

- `x_robust-worst` = eligible parents 的 **5% 分位**（**不再**用 raw minimum；raw minimum 会让分母趋 0 而爆炸）。
- **任何 NR 结果必须同时报告 absolute terminal value `V`。**
- 主指标 = **future-task parent-selection regret**；相关性（Spearman 等）只作 secondary endpoint。

---

## 3. 假设与判据（阈值已冻结）

### H1 — Measurable option heterogeneity

**判据（全部满足才算通过）**
1. 在 **≥2 个 dense protein landscape** 中，eligible parents 之间 `V_{B,π}` 的 **IQR ≥ 2 × median measurement/bootstrap uncertainty**；
2. 该结论在 **≥2 个预算** 与 **≥2 个 search policy** 下成立。

**辅助报告（不参与判定，但必须报）**：variance decomposition（parent 主效应 vs replicate 残差）、permutation test p 值、**effect/noise ratio**。只报 p 值不报 effect size 视为不合格报告。

### H2 — Not reducible to existing proxies

**proxy-only 基线**必须包含（今天可得）：`current fitness`、`local robustness`、`cross-task activity`（在有该数据的数据集上）、`conservation`、`frozen zero-shot score`。

**判据**：在**严格 held-out** evaluation 上，加入**额外 today-available information** 后：
- **(A)** `ΔCV-R² ≥ 0.05`，**或**
- **(B)** `selection regret reduction ≥ 20%`；
- 且对应 **bootstrap 95% CI 不跨 0**。

**判定**：
- (A)(B) 均不满足 → H2 失败。
- 满足其一 → **至少进入 MODIFY**。
- **两条都达到 → strong GO**（H2 维度）。

> ⚠️ 核心纪律：**低 correlation 不能证明新性质**。只有 out-of-sample incremental value 算数。

### Matched-pair confirmation（"same present, different future"）

**procedure**：discovery/confirmation split（见 Protocol §8）。

**判据（全部满足）**
1. confirmation split 中至少有 **20 对**按**噪声定义的容差**匹配的 parent（匹配在 `Readiness` 与全部 proxy 上，**容差由实验噪声决定，不得人工调 ε**）；
2. 未来值差异的**方向性成功率显著高于 0.5**（二项检验 p < 0.05）；
3. aggregate effect 的 **95% bootstrap CI 不跨 0**。

**理由**：20 不是生物学魔法数字，只是防止 Fig.2 最终靠三对 cherry-picked example 支撑。

### Tomorrow Test

**procedure**：冻结 Day-0 信息 → 模型冻结 → 才揭晓未来任务 → 比较选出的 starting parents 在真实未来 landscape 中的表现。

**判据**：相对于**最强 heuristic selector**（**不是** random）：
- future-task normalized regret **降低 ≥ 20%**，且 bootstrap CI 排除 0。

**对照选择器**：random / current-fitness / stability / promiscuity（可用处）/ EOV-based / oracle。

**降级条款**：TEM-1 只有一个 strict future task，因此**仅凭 TEM-1 达成此条 = proof-of-concept GO，不得称 task-general**。

### 跨系统要求（publication-level）

- 声称 **general** claim 需要 **第二个独立的 multi-task dense/combinatorial protein landscape**（判据见 `DATA_AUDIT.md` §3.1）。
- 找不到 → Phase I 继续，但结论**预先降级**为：*proof of principle for prospective starting-point valuation*；**禁止**写 *general protein evolutionary option value*。

---

## 4. 决策表

### 4.1 主决策逻辑

| 条件组合 | 裁决 |
|---|---|
| H1 失败（异质性 ≤ 噪声） | **NO-GO** |
| H1 通过，但 H2 失败 且 matched-pair 失败 且 Tomorrow Test 无改善 | **NO-GO** |
| H1 通过，H2 仅满足 (A) 或 (B) 之一 | **MODIFY**（至少） |
| H1 通过，但 `Corr(EOV_{τ1}, EOV_{τ2}) ≈ 0`（task-specific，见 §4.2） | **MODIFY** → 改称 **task-family-conditioned option value** |
| H1 + H2(≥1 项) + matched-pair(≥20 对) + Tomorrow Test(≥20% vs 最强 heuristic)，**仅在 TEM-1** | **GO — proof of concept** |
| 上述全部 + H2 两项同时达到 + 跨系统要求满足 | **GO — strong / publication-level** |
| matched-pair confirmation 未达 20 对 | 不得给 GO（无论其他指标多好） |

### 4.2 解释性阈值登记（**本文件新增，需你签字或否决**）

以下阈值把用户原文中的定性表述（"≈ stability"、"≈ promiscuity"、"≈ 0"）操作化。**如不签字，视为未冻结，Phase I 不得据此下任何 NO-GO/MODIFY 裁决。**

| ID | 表述 | 冻结默认操作化 | 状态 |
|---|---|---|---|
| INT-1 | `EOV ≈ stability`（或 ≈ promiscuity / ≈ current fitness） | proxy-only 模型对该 proxy 的 held-out `CV-R² ≥ 0.80`，**且**加入全部其他 today-available 信息后 `ΔCV-R² < 0.02` | ⏳ 待签字 |
| INT-2 | `Corr(EOV_{τ1}, EOV_{τ2}) ≈ 0` | 跨任务 Spearman `ρ < 0.30` 且 95% CI 上界 < 0.50 | ⏳ 待签字 |
| INT-3 | "parent ordering 基本随机" | 跨任务 parent 排序的 Kendall τ 的 95% CI 覆盖 0 | ⏳ 待签字 |
| INT-4 | H1 中"dense protein landscape" | 满足 `DATA_AUDIT.md` §3.1 判据 1+3+4 的 landscape | ⏳ 待签字 |
| INT-5 | H1 的 uncertainty 定义 | replicate-level bootstrap SD（不是解析误差传播） | ⏳ 待签字 |

### 4.3 NO-GO 的明确形态（即使 H1 通过）

出现下列任一，即判 **NO-GO**，**不得**继续造复杂模型：

1. `EOV ≃ stability`；
2. `EOV ≃ promiscuity`；
3. 换掉未来任务后 parent ordering 基本随机、且不存在可预测结构。

---

## 5. Cheater effect 政策（冻结）

**不删除、不"校正到看起来干净"。** 三层处理：

| 层 | 数据 | 角色 |
|---|---|---|
| L1 | TEM-1 pooled AUC landscape | 主数据（明确命名为 **pooled competitive fitness**） |
| L2 | 作者仓库 `validation/` 的单培养 IC50 子集 | assay-context sensitivity |
| L3 | TrpB / GB1 等**非共培养** landscape | 跨测量机制验证 |

**结论约束（冻结）**
- 仅 TEM-1 成立 → **NO general biological claim**。
- 若非共培养 landscape 也出现同样的 option-value geometry → cheater effect 难以解释整个现象。

---

## 6. 禁止事项（冻结）

1. 不做生成式 protein design。
2. 不重新训练 / 不 finetune protein foundation model（frozen 推理允许）。
3. 不声称"发现了通用 evolvability"。
4. 不使用 predicted future-task fitness（含 PLM 预测的未来任务表现）。
5. 不拿 DAOx 单突变数据伪装多轮 evolution。
6. 不把 task-specific latent activity 叫 EOV。
7. 不把 imputed fitness 当 experimental truth（不得进入主分析）。
8. 不为得到 positive result 修改 EOV 定义或任何阈值。
9. 不用 `AdaptationPremium` 作为选择目标。
10. 不用 random 作为 Tomorrow Test 的唯一对照（必须对最强 heuristic）。
11. 不报 p 值而不报 effect size / 不报 absolute terminal value。
12. 不在 concentration/条件上事后择优。
13. 不用二手镜像数据（合并了 imputed 值的副本）。

---

## 7. 时间戳与哈希

本文件的 sha256 记录在 `data_registry/FREEZE_LEDGER.md`。任何后续修改都必须在该 ledger 中产生新行，并保留旧行。

## 8. 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| v1 | 2026-09-19 01:10 (+08:00) | 初版冻结：Q1–Q3 重写、EOV 重新定义为 utility 化的 final future value、废除 `R_B − R_0` 主指标、H1/H2/matched-pair/Tomorrow/跨系统阈值、cheater 三层政策、禁止清单。新增 INT-1…INT-5 待签字解释性阈值。 |
