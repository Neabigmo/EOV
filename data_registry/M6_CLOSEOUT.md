# M6 收口记录 —— CONFIRMED，主线转入"可迁移边界"

| 字段 | 值 |
|---|---|
| 日期 | 2026-09-19 |
| 用户裁决 | **CONFIRMED — continue** |
| 影响 | ① M5 标签 `discovery` → **`confirmed`** ② 论文主线由"寻找跨任务普适 EOV 标量"改为**刻画 EOV 的可迁移边界** ③ **不再寻找第三个确认集，不再扫 landscape** |
| 状态 | M6 **彻底收口**；M7（短）为下一阶段 |

---

## 1｜四层结论结构（M4–M6 合并支持）

| 层 | 命题 | 证据 | 状态 |
|---|---|---|---|
| ① | **within-task value is budget-stable** | M4 跨预算 ρ = **0.833 / 0.929 / 0.994**（不变量 5 修正后，`M4_REPORT.md §8.2`）；`R_0 / R_k^oracle / R_k^adaptive / R_{B,π}` 四层分解 | 坚实 |
| ② | **cross-task value is usually poorly transferable** | M5 discovery pair 级中位 `ρ_rank` = **0.0599**；M6 独立确认 = **0.0021** | 坚实（且确认后**更强**） |
| ③ | **task similarity predicts how much transfer remains** | M5 同质子组 `ρ(f₁,ρ_rank)` = **+0.7441**（16 对）；M6 独立 **+0.7536**，CI **[+0.2318, +0.9445]** | 坚实（已确认） |
| ④ | **EOV 是 relational，不是 intrinsic** | ①–③ 的直接推论 | 表述层 |

> ①③ 的组合构成全文骨架：**Budget ⇒ stable**，而 **Task change ⇒ large information loss**，
> 但损失程度受 **task similarity** 系统性调节。

**数字核验**（本条已实测复核，见 §6）：`0.833/0.929/0.994`（M4）、`0.7441`（M5 同药，16 对）、
`0.5610`（M5 全 21 对）、`0.0599` / `0.0021`（pair 级 `ρ_rank` 中位）、`0.7536` 与 CI（M6）。

---

## 2｜EOV 的正式重新定义（取代 `EOV(x)` 的标量写法）

**不再**写成 `EOV(x)`。冻结为：

$$
\boxed{\;EOV_{B,\pi}(x \mid \tau)\;}
$$

强调"从已知任务到未来任务"的迁移时，引入**迁移算子**：

$$
\boxed{\;T(\tau_s \to \tau_t) \;=\; \operatorname{Corr}_x\!\left[\,V(x,\tau_s),\; V(x,\tau_t)\,\right]\;}
$$

论文实际研究的正是：

$$
\boxed{\;T(\tau_s \to \tau_t) \;\approx\; g\!\left(S(\tau_s,\tau_t)\right)\;}
$$

其中 `S` 为 task/landscape similarity（M6 中 `S = f1_landscape_rho`，`g` 在该范围内单调增）。

**随之作废/保留的旧定义**（不变）：
- `EOV = R_B − R_0` —— **仍然作废**；
- `AdaptationPremium` —— **仍然绝不是优化目标**；
- `V_{B,\pi}(x,\tau) = u_\tau(R_{B,\pi}(x,\tau))`、`u_τ` = OP-12 无 clip —— **未改**。

> **论文中最有分量的一句话**（用户指定方向）：
> **"Evolutionary starting-point value is not a task-general property of a protein;
> it is a task-conditional quantity whose transferability is governed by landscape similarity."**

---

## 3｜⛔ 必须守住的边界（**否则"结果是真的，故事讲过头"**）

**M6 解决的是**：*为什么有些 task pair 可以迁移，而另一些不可以？* —— **解释性 / boundary-characterizing**。

**M6 没有解决**：*在明天的任务还没有被测量时，我怎么提前知道能不能迁移？* —— **前瞻性**。

`f₁` **需要两个任务的景观值**才能计算。因此：

| ✅ 可以写 | ❌ 不可以写 |
|---|---|
| landscape similarity **predicts** transferability | we can predict transferability **before the future task is observed** |
| 诊断 / 设计层面（要不要做 multi-task campaign、预期多少迁移） | "今天就能预测明天" |

**此边界已逐字进入 `M6_CONFIRMATORY_REPORT.md` §0 摘要**（`AMENDMENT-017` §8 的强制要求）。
M7 若成功，才把这条边界**向前推一步**；M7 之前，任何"前瞻"措辞都是无证据的。

---

## 4｜指定正式措辞（写进论文，逐字采用）

### 4.1 Wu2020 的 oracle-degeneration（与确认结果**同处出现，不藏 supplementary**）

> Confirmation used only non-degenerate cells under the pre-amended OP-21 handling rule;
> 15/90 cells showing oracle-like saturation were excluded from the transfer summary
> according to the frozen amendment.

**支撑事实**：`B=96` 时 coverage = **16.67%**（TEM-1 0.694% / Phillips 0.586%，高 24–28 倍），
`mlde_ridge` 从几乎每个起点都能买到全局最优 → `R` 唯一值个数 **1/1/1/2/3/5** → `ρ_rank` 无定义。
退化格 **15/90 = 16.7%**，**每对恰好用 6 格中的 5 格**。
处置规则在看任何 `f₁`/`ρ_rank` **之前**冻结于 `prereg/AMENDMENT-019_degenerate_cell_rule.md`。

> **不淡化**：它是 `AMENDMENT-002 B-2` 所描述失效模式的实证兑现，也是本确认集的**固有代价**。

### 4.2 确认集筛选（**主文只写这一句**）

> Candidate confirmation datasets were screened using phenotype-blind structural eligibility
> criteria; AncSR1 and subsequent candidates failed prespecified eligibility gates before
> Wu2020 was selected.

**完整过程**（184 个文件的更正、Dryad API 401、Anubis PoW、`degree = 76 = 4×19`、
`OP-18` 剔除 3/5 任务、`Jalal2020` 两蛋白）→ **全部移入 reproducibility supplement**，
**不进主文**。

> `degree = 76 = 4×19` 保留为 supplementary 中"**审计为什么必要**"的范例：
> 它同时推翻了 `AMENDMENT-007` 记的"单核苷酸邻接陷阱"，
> 说明**只读 API 第 1 页就会得出错误的数据集画像**。

---

## 5｜四图定稿

| 图 | 标题 | 内容 |
|---|---|---|
| **Fig. 1** | *Future value is not present value* | 定义 starting-point value、budget、task withholding（概念图，无数据） |
| **Fig. 2** | *Starting-point value is budget-stable* | M4：跨预算 ρ = **0.833 / 0.929 / 0.994**；`R_0 / R_k^oracle / R_k^adaptive / R_{B,π}` 四层分解 |
| **Fig. 3** | *Starting-point value collapses across tasks* | M5：transfer matrix、`ρ_rank` 接近 0、regret 高、magnitude transfer 接近 0。**全文最打人的图** |
| **Fig. 4** | *The boundary is predictable* | 左 discovery **0.7441** ／ 右 independent confirmation **0.7536**；同时显示**两个数据中绝对 transfer 都很低** |

**Fig. 4 拟定标题**：

> **Task similarity predicts when evolutionary value transfers—but transfer is usually weak.**

**Fig. 4 必须同时呈现的三件事**（缺一即误导）：
1. 两边的 `ρ(f₁, ρ_rank)`（0.7441 / 0.7536）与 CI；
2. 两边的**绝对迁移水平**（pair 级 `ρ_rank` 中位 0.0599 / 0.0021）；
3. Wu2020 的 coverage = 16.67% 与退化格比例 16.7%。

---

## 6｜本轮完成的工作（供 traceability）

| 项 | 路径 |
|---|---|
| M6 确认报告 | `data_registry/M6_CONFIRMATORY_REPORT.md`（85/85 数值核验通过） |
| M6 预注册 | `prereg/AMENDMENT-017_m6_confirmatory_freeze.md` |
| 确认集替换 | `prereg/AMENDMENT-018_m6_wu2020_substitution.md` |
| 退化格规则 | `prereg/AMENDMENT-019_degenerate_cell_rule.md` |
| 资格审计 | `data_registry/M6_ELIGIBILITY_REPORT.md` |
| 台账 | `FREEZE_LEDGER.md` 批次 **#44**（AncSR1 不适格 + §7）与 **#45**（CONFIRMED） |

**核验状态**：M6 独立核验器 **85/85**；删 checkpoint 从零重跑 `R` **逐位相同**；
`pytest tests` **86/86**；`AMENDMENT-017` 阈值**一字未动**。

---

## 7｜下一步（**仅此一项，不扩**）

**M7 — From explanatory similarity to prospective similarity**（短）

> **能不能在不知道完整 future landscape 的情况下，估计足够准确的 task similarity，
> 从而判断 transfer 是否值得相信？**

**只做 A（稀疏 future-task probing）**：
允许测 `m = 4, 8, 16, 32, …` 个 shared genotypes，用它们估 `f̂₁`，再问 `f̂₁ → ρ_rank` 是否仍成立。

**B（zero-measurement task descriptors：底物理化描述符 / 抗生素身份与浓度 / assay-环境描述符 /
结构或 task embedding）本轮不做** —— 用户明示"可以作为后续，不必现在拖慢论文"。

**协议须在计算之前冻结**（`prereg/AMENDMENT-020_*.md`）。
