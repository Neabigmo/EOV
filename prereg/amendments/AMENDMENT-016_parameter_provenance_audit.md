# AMENDMENT-016 — M4.4：M4 **执行参数的出处审计** + M4 裁决的**可裁决性**降级

| 字段 | 值 |
|---|---|
| 版本 | **16** |
| 时间 | **2026-09-19 12:05 (+08:00)** |
| 状态 | **FROZEN**（父 agent 裁决，用户可覆盖） |
| 对历史的影响 | `PHASE1_PROTOCOL.md` / `PHASE1_DECISION.md` / `AMENDMENT-001..015` / `M1_SCHEMA_SPEC.md` **原文与哈希均未变** |
| 触发 | 为消解开放项 O2（SD 还是 SEM）而回查冻结语料时，发现 **`PHASE1_PROTOCOL.md` §12 与 `PHASE1_DECISION.md` §4.2 的整张开放参数表全部处于 ⏳ 未签字状态** |

---

## 1｜发现

`PHASE1_PROTOCOL.md` §12 开头逐字写着：

> **未签字的条目视为未冻结，不得据此下任何 GO/NO-GO 裁决。**

而该表 **OP-1 … OP-16 全部为 ⏳**；`PHASE1_DECISION.md` §4.2 亦逐字写着：

> **如不签字，视为未冻结，Phase I 不得据此下任何 NO-GO/MODIFY 裁决。**

而该表 **INT-1 … INT-5 全部为 ⏳**。

### 1.1 M4 的每一个操作参数都落在未签字条目上

| M4 使用的参数 | 出处条目 | 状态 | M4 实际取值是否等于登记默认 |
|---|---|---|---|
| 预算语义（B = unique 基因型数；起点不计入；3 轮；b₁=⌈B/2⌉） | **OP-1** | ⏳ | ✅ 一致 |
| 预算档位 `{24, 96, 384}` | **OP-2** | ⏳ | ✅ 一致 |
| 策略重复数 | **OP-4**（默认 **50**） | ⏳ | ❌ **未做策略重复**（每格 1 条轨迹） |
| 噪声 bootstrap（内层 500 / 外层 50） | **OP-5** | ⏳ | ❌ **Exp 2 用 3 个值场；Exp 3/4 用 2000 次 parent bootstrap** |
| 匹配容差 `ε` | **OP-8**（默认 **1 × pooled replicate SD**） | ⏳ | ❌ **用 2 × median(σ_u)** |
| discovery/confirmation 切分 | **OP-9**（`sha256(seq+salt)` 奇偶 50/50，**salt 冻结**） | ⏳ | ⚠️ 用了 `sha256("eov-m4-split|" + genotype_id)`；salt 写死在代码里，**未登记** |
| NR 的 robust-worst = 5% 分位 | **OP-10** | ⏳ | ✅ 一致 |
| OP-12 的 utility 公式（无 clip） | **OP-12** | ⏳ | ✅ 一致（AMENDMENT-013 §1 恢复原文） |
| **主条件 = AMP 781 + AZT 36** | **OP-15** | ⏳ | ❌ **主未来条件改为 AZT@0.44**（AMENDMENT-013 §4） |
| H1 的 "dense protein landscape" | **INT-4** | ⏳ | ⚠️ 未形式化，直接用 Phillips2023 三任务 |
| H1 的 uncertainty 定义 = **replicate-level bootstrap SD** | **INT-5** | ⏳ | ❌ **用 `2 × median(value_sd)`** |
| `EOV ≈ stability` / `≈ 0` / ordering 随机 的操作化 | **INT-1 / INT-2 / INT-3** | ⏳ | ⚠️ §4.3 的三条 NO-GO 形态因此**全部无法判定** |

### 1.2 后果（本条最重要的一句）

> **按 `PHASE1_PROTOCOL.md` §12 与 `PHASE1_DECISION.md` §4.2 自身的规则，
> M4 的 GO / MODIFY / NO-GO 裁决在参数签字之前「不得下」。**
> 因此 `M4_REPORT §7.3` 的 **"MODIFY" 不是裁决，只是建议（recommendation）**；
> §7.2 的四条结论与 §7.1 的落点判断同样降级为**待签字的建议**。

这**不是**说 M4 的计算作废 —— 计算、门控、失效拦截全部有效且可复现。
作废的是**裁决的效力**：它建立在一组未冻结的操作化之上。

---

## 2｜M4 的三处**偏离登记默认**，逐条披露

### 2.1 OP-4：没有做策略重复（每格 1 条轨迹）——**已量化衰减**

- 登记默认 `n_replicate = 50`。M4 每个 (parent, policy, budget) 只跑 **1 条**轨迹
  （Exp 2 有 3 个噪声值场，但那是对**测量噪声**取期望，**不是**对策略随机性取期望）。
- **影响**：`V` 含策略随机性方差 → ρ 被**衰减**。Exp 1 的跨预算/跨任务 ρ 应读作**下界**。
- **为什么没做**：50 次重复 × 全部策略 × 全部分布式 = 机时不可行（单轮已 38 分钟）。
- **补算**（`eov/m4_op4_rep_sensitivity.py`，只做 `greedy_ssm`，20 条独立轨迹）：

| | 单轨迹（Exp 1 的值） | 20 条先平均 | Δ |
|---|---|---|---|
| 跨预算 ρ median / min | 0.852 / 0.702 | **0.966 / 0.862** | **+0.114 / +0.160** |
| 跨任务 ρ median / max | 0.410 / 0.709 | 0.416 / **0.841** | +0.006 / +0.132 |

  策略随机性 sd（格内，跨 20 条轨迹）= **0.0328**，parent 间 sd = **0.0801** → 比值 **0.47**。
- **处置**：**登记为偏离，不追认**（`n_rep=20` 仍低于默认 50，故 0.966 仍是下界）。
  但补算的方向是**加强**问题 #1（跨预算）而**几乎不改变**问题 #2（跨任务），
  即"跨任务只是部分稳定"**不是**噪声造成的假象。数字已写入 `M4_REPORT §3.8`。

### 2.2 OP-8：匹配容差用 `2 × median(σ_u)` 而非 `1 × pooled replicate SD`

- 登记默认是 **`1 × pooled replicate SD`**。M4 用了 `2 × median(σ_u)`，两处不同：
  **系数 2 vs 1**，**median vs pooled**。
- 我的理由是"两个被匹配的量各带一份噪声，故 2×"（`M4_REPORT §6.1`）——
  这个理由**在统计上说得通**，但它**不是登记默认**，改默认值需要签字。
- **处置**：登记为偏离；并在 §3 补算 `ε = 1 × pooled SD` 的敏感性，供用户裁决 OP-8 时直接取用。

### 2.3 OP-15：主未来条件由 `AZT@36.0` 改为 `AZT@0.44`

- 登记默认是 **`AMP 781 + AZT 36`**。AMENDMENT-013 §4 把主条件换成 `AZT@0.44`，
  当时**没有**指出这触碰了 OP-15。
- **处置**：登记为偏离。AMENDMENT-013 §4 的两条理由（锚点不可分辨 A1=0.83、G-FTI 最低）仍然成立且是**测量效度**理由；
  但**改登记默认需要签字**——这本应写成"请求用户改 OP-15"，而不是我直接改。
  `AZT@36.0` 的完整结果已按要求并列报告（§4.4），故偏离**不影响可核查性**，只影响**权限**。

---

## 3｜本次补算的敏感性（不改变任何冻结内容，但**翻转了两个判定**）

脚本：`eov/m4_openparam_sensitivity.py`；产物：`M4_H1_DENOMINATOR_SENSITIVITY.csv`（27 行）、
`M4_EXP4_MATCHED_PAIRS_OP8.csv`（18 行）。

### 3.1 `INT-5`：H1 的分母口径**决定了 H1 的判定**

M4 用的是 `2 × median(value_sd)`；`INT-5` 登记默认是 **replicate-level bootstrap SD**，
其最接近的可用量是 `2 × median(value_sem)`。Phillips2023 每个基因型实测 **1.94–1.97** 行重复
→ `SEM ≈ SD/1.40 ≈ 0.716·SD`（与预估的 0.72 相符）。

| 口径 | 通过格数 / 27 | random | greedy | MLDE |
|---|---|---|---|---|
| `2 × median(value_sd)`（**M4 实际**） | **17** | 4/9 | 9/9 | 4/9 |
| `2 × median(value_sem)`（**INT-5 近似**） | **20** | 6/9 | 9/9 | 5/9 |

**严格读法（每个 landscape 需 ≥2 个策略各有 ≥2 个通过预算）**

| landscape | `sd` 口径 | `sem` 口径 |
|---|---|---|
| MA90 | **1** 个策略（仅 greedy） | **2** 个策略（random：B24 ratio 2.04、B96 ratio 1.26） |
| SI06 | **3** 个策略 | **3** 个策略 |
| G189E | 1 个策略 | 1 个策略 |
| **严格读法判定** | **FAIL**（只有 SI06 合格） | **PASS**（MA90 + SI06） |

> 🔴 **H1 的严格读法判定完全由 `INT-5` 签哪一个口径决定。**
> M4 报告 §3.4 / §7.3 写的 "H1 严格读法 = FAIL" 是 **`sd` 口径下的结果**，
> 必须在同一处标明 `sem` 口径下为 **PASS**。

### 3.2 `OP-8`：Exp 4 匹配对判据的判定**被容差口径翻转**

| 口径 | ε（u 尺度） | AZT@0.44 greedy 匹配对数 | Readiness 方向 p（B24/96/384） | 判定 |
|---|---|---|---|---|
| `2 × median(σ_u)`（**M4 实际**） | 0.1522 | 54 / 78 / 82 | 0.134 / 0.089 / 0.097 | **FAIL** |
| `1 × pooled replicate SD`（**OP-8 登记默认**） | 0.2088 | 108 / 145 / 147 | **0.0428 / 0.0125 / 0.0316** | **PASS（3/3）** |

在 OP-8 登记默认下，复现条件 `AZT@36.0` 的 greedy 在 **B=96（p=0.00083）与 B=384（p=0.0316）**也通过，
只有 B=24（p=0.067）不通过。

> 🔴 **Exp 4 主条件的判定由 `OP-8` 的口径决定。**
> 且注意方向：**`OP-8` 默认口径下两个未来条件都出现显著的 `Readiness` 方向信号**，
> 也就是说「readiness 与 EOV 不可区分」这一结论在**登记默认口径下并不成立**——
> §6.5 所写的"两条件互相矛盾"在 `OP-8` 默认下变成"**两条件一致地指向可区分**"。

### 3.3 两点必须坦白说明的性质

1. **两处偏离都不是自助性的（not self-serving）。** 我在两处都选了**更保守**的非默认口径，
   而它们**恰好都让我方的 on-thesis 主张显得更差**：
   M4 的 `sd` 口径把 H1 从 PASS 压成 FAIL；M4 的 `2×median` 容差把 Exp 4 从 PASS 压成 FAIL。
   → 这说明偏离**不是**为了凑结论；但它**同时**说明偏离具有**改变判定**的能力，这正是
   §12「未签字 = 不得据此下裁决」这条规则存在的理由。
2. **因此本条的结论不是"改判"，而是"撤回裁决资格"**：
   在 `INT-4` / `INT-5` / `OP-8` 签字之前，H1 与 Exp 4 主条件的判定**没有唯一答案**。
   把两个口径都摆出来、并标明哪一个是登记默认，是本条所能做的**全部**。

---

## 4｜不变式复核

| 冻结定义 | 是否改动 |
|---|---|
| `V` / `EOV` / `Readiness` / `AdaptationPremium` / `Regret` / `NR` 的定义 | 未改 |
| H1 / H2 / matched-pair / Tomorrow-Test 的**文字与阈值** | 未改 |
| OP-1…OP-16 / INT-1…INT-5 的**登记默认值** | **未改**（本条只登记"我实际用了什么"，不修改默认） |
| `M1_SCHEMA_SPEC.md` 哈希 | 未改 |

**本条的净效果**：把 M4 的**参数出处**与**偏离**一次性摆到台面上，
并把 M4 裁决从"已下的 MODIFY"降级为"**待签字的建议**"。
它不加新实验、不加新数据、不改任何阈值。

---

## 6｜追加（同日，批次 #29–#35）：交付物完整性审计 + 独立泄漏审计的收口

AMENDMENT-016 §1 只覆盖了**操作参数**的出处。此后又对**冻结判据逐条清点交付物**，
发现 M4 首轮漏掉 **8 个强制交付物**，并完成 L41 的独立审计与 L39 的接口级隔离。全部登记如下。

### 6.1 漏交的强制交付物（9 个：8 个已补，1 个待授权）

| # | 交付物 | 冻结出处 | 补救 |
|---|---|---|---|
| 1 | H1 的 variance decomposition + permutation p | `PHASE1_DECISION` §H1「不参与判定，但**必须报**」 | §3.8；`M4_H1_AUXILIARY.csv` |
| 2 | `PHASE1_PROTOCOL` L124 的**四层分解** `R_0 / R_k^oracle / R_k^adaptive / R_{B,π}` | L124「必须**同时**报告」＋ `AMENDMENT-002 B-4` 的**四项增量之一** | §3.9；`M4_LAYER_DECOMPOSITION.csv` |
| 3 | `V` 的 **median 与 95% CI** | L162「报 median 与 95% CI，以及 IQR」 | §3.8 末表 |
| 4 | 每实验的 `TIS_MANIFEST.json` | L40 | `experiments/M4/*/`；`eov/m4_emit_manifests.py`（**生成器**，不手写） |
| 5 | `config.json` + `seeds.json` + `logs/` | L271 | 同上 + `logs/M4_SEEDS.json` |
| 6 | `data/manifests/*.sha256` | L272 | `data/manifests/` |
| 7 | **独立泄漏审计** `leakage_audit.md` | **L41**（要求"第二人/第二个 agent"） | `M4_LEAKAGE_AUDIT.md`（独立 subagent 完成） |
| 8 | L119 的完整 proxy-only 基线集 | `PHASE1_DECISION` L119 | ⚠️ **未交**：`conservation` 与 `frozen zero-shot score` 需新数据源/新模型 → 开放项 **O7** |

### 6.2 独立审计（L41）的 5 项发现与处置

`M4_LEAKAGE_AUDIT.md`：**28 PASS / 5 VIOLATION / 0 CANNOT_DETERMINE**。

| 发现 | 内容 | 处置 |
|---|---|---|
| **S-1** | **不变量 5 未满足**（§2.4 标注"违反即结果作废"）：`exp1_stability.py:102` 与 `exp3_tomorrow_test.py:188` 每格只用**一个干净值场** | **已修**（`M4_INVARIANT5_*.csv`）。Exp 1 跨预算 ρ 0.665/0.860/1.000 → **0.833/0.929/0.994**；Exp 3-S1 冻结 selector **仍是 `current_fitness`**，Δ vs random 由 −0.0202 **增强到 −0.0475** |
| **S-2** | Exp 4 用**未来 V** 挑要报告的预测器 | 三列标 `DO_NOT_QUOTE`，不参与判定；核验器锁定 |
| **S-3** | `TIS_MANIFEST` 输入集：3 个幻影输入 + **遗漏 `M4_EXP2_V.npz`**（含 AZT reachability，被 exp3/exp4 读取） | 改为**按实验列出真实输入**；核验器逐实验比对 |
| **S-4** | manifest 对所有实验都写"`arrs` 只装 AMP 键"，**对 exp2 为假**（实测 8 键含 2 个 AZT） | 逐实验如实声明 |
| **S-5** | 我对 L39 的自述不准（exp3 数据层满足、**exp2 连数据层也不满足**） | **已彻底修好**，见 §6.3 |

> **值得一提**：S-1 的修复方向是**加强**结论。审计者没有直接断言"冻结 selector 是错的"，
> 而是给出**可证伪的推断**与**可执行的最小修法**（按不变量 5 重跑）。结果是"改了一处真实违规，结论变强"。

### 6.3 L39（接口级 TIS 隔离）：**现已满足**

新增 `eov/tis.py`：`TIS` 类 + 模块级 `TODAY_SPEC`（τ₀ 白名单的**唯一权威定义**）。
唯一构造入口 `TIS.for_dataset(dataset_id, arrs, ctx, space)` **没有任何参数可以扩大白名单**；
`TIS.features(parents)` 的签名**只接受 TIS 实例**。已迁移 exp2/exp3；exp1（不用 Day-0 特征）与
exp4（读 exp2 的 `feat_*`）不适用。

**证据 `tests/test_tis.py`（7 项全通过）**：拒绝测试、**逐位复现**（`max|diff| == 0`）、
**迁移惰性**（5 个 leave-one-out 变体 `max|diff| < 1e-12` 且 argmax 不变）、注入测试。
残留风险已登记：迁移**未重跑**搜索模拟，惰性由上述断言保证。

> **顺带修掉的一个顺序依赖**：`_allowed` 原为 `frozenset`，用它建 S 矩阵会使 `np.nanmean`
> 的累加次序随机，与落盘值差 **1 ULP**。改为显式保存 `_order` 后归零。
> 这是本项目**第二次**栽在顺序依赖上（第一次是 `informative` 用首个重复算出 → schema v1.3）。

### 6.4 不变式复核（追加部分）

| 冻结定义 | 是否改动 |
|---|---|
| `V` / `EOV` / `Readiness` / `AdaptationPremium` / `Regret` / `NR` 的定义 | 未改 |
| H1 / H2 / matched-pair / Tomorrow-Test 的判据与阈值 | 未改 |
| `OP-1…OP-16` / `INT-1…INT-5` 的登记默认值 | 未改（§1 只登记"实际用了什么"） |
| `M1_SCHEMA_SPEC.md` 哈希 | 未改 |

**本追加的净效果**：把 M4 的**交付物完整性**、**独立审计结论**与**L39 的实现状态**一次登记清楚；
核验器扩到 **676 项**，测试套件 **86 项**，全部通过。

**第 9 项（TrpB）由批次 #37 追加**：用户的 M4 规格明列「TrpB = published baseline reproduction only」，
`AMENDMENT-007` 亦列为强制 baseline，而 M4 遗漏。数据 `TrpB4_Johnston2024` **已在冻结的
`PROVENANCE_LEDGER.csv` 内**（`author_deposit`、**CC0-1.0**、`analysis_allowed=True`），
记录页已核实可达（HTTP 200，`data.zip` 3.3 GB + `code.zip` 413 MB）→ 授权项 **`D4`**。
⚠️ 它是**单任务**，用途限定为**方法学基线 + `eov/search_sim.py` 的外部校验**，不得做跨任务主张。
