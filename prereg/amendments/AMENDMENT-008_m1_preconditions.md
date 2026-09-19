# AMENDMENT-008 — M1 前置：C6 拆分、C8 改为 provenance 原则、角色重分类、future-task identifiability

| 字段 | 值 |
|---|---|
| 版本 | **8** |
| 时间 | **2026-09-19** |
| 状态 | **FROZEN**（用户已裁决；本修正案在 M1 schema hash-freeze **之前**生效） |
| 依据 | 用户 M1 裁决 + 我对两处 provenance 的独立复核（见 §2.0） |
| 时机 | **任何 EOV 分析均未运行**；本修正案**不阻塞 M1**（除 §4 的 G-FTI 属 M4 前置） |

---

## 1｜C6 拆分：**两类 baseline 不得混为一锅**（用户决定，确认保留为硬条件）

原 C6 措辞过宽。拆为：

### **C6a — published-search / reproduction baseline gate**

**对象**：TrpB 原文（PNAS 2024）已发表的：
- 3 种 in-silico DE（Method 1 位点并行取优后重组；Method 2 遍历全部 4!=24 种位点顺序的单步贪心；Method 3 加性模型预测后直接合成 top N=96）；
- path accessibility 扫描（允许下降步长 0–100%）；
- local optima（520 个，占 active 5.3%）；
- **噪声 null landscape**（两次重复差拟合指数分布）及其上的同一套 DE。

**要求**：在 M4 之前必须满足

$$\text{our reproduction} \;\approx\; \text{published TrpB outputs}$$

**只有在此之后**，才允许宣称我们在 **task-holdout / regret / `B`-valuation** 上的增量。**复用其实现，不得重写。**

### **C6b — prospective-selector baselines**（与 C6a 分开登记）

**对象**：`current fitness`、`robustness`、`known-task activity`、**GraphFLA 全部 20 个景观特征**（含 per-config 可及性）、`PLM zero-shot`、`linear / RF / XGB`。

**要求**：H2 的"增量价值"必须**同时**相对 C6a 与 C6b 成立。

> **措辞纪律**：今后禁止写"我们首次逐 starting point 研究 fixed-landscape adaptation outcome" —— 已被 TrpB 原文覆盖。

---

## 2｜C8 修正：**redistribution policy follows provenance, not dataset name**

### 2.0 我的独立复核（本次）

| 项 | 核实结果 |
|---|---|
| **Bank2016 原始 deposit** | Dryad `10.5061/dryad.th0rj` → API 返回 **`license = CC0-1.0`** ✅（我实测）→ **原始数据不是"不得再分发"**。原 C8 表述**不准确**，已更正。 |
| **CTX-M-14 存在两个不同数据集** | ① `github.com/woson2020/CTXM-14` ✅ 存在（对应用户引用的 *Mol Biol Evol* 2022, `10.1093/molbev/msac086`, "Prediction of Antibiotic Resistance Evolution by Growth Measurement of All Proximal Mutants of Beta-Lactamase", 论文 **CC BY 4.0**）；② `github.com/Palzkill-Lab/CTXM_epistasis` ✅ 存在（PNAS 2024, `10.1073/pnas.2313513121`, **CC BY-NC-ND**）。**两者须分别登记，不得混称。** |

### 2.1 新的 C8（替换原措辞）

> **C8 — 再分发政策按 provenance 判定，不按数据集名判定。**
>
> 1. **原始 deposit 有明确开放许可**（如 CC0 / CC BY）→ **按该许可处理**（署名等要求照办）。
> 2. **第三方 repack、或 GitHub artifact 无明确 LICENSE 文件** → **local-only**：只保存 URL/DOI + sha256 + 获取时间，**不随本仓库再分发**，改用 **fetch instruction**（脚本按 manifest 拉取）。
> 3. **CC BY-NC-ND 等含 ND 条款者** → **不得发布派生表**，仅作内部 robustness。

**按新 C8 的逐项裁决**

| 数据 | provenance | `analysis_allowed` | `redistribution_allowed` |
|---|---|---|---|
| Bank2016（Hsp90，640 突变体） | **Dryad `th0rj`，CC0-1.0**（✅ 实测） | ✅ **回源 Dryad** | ✅ 按 CC0 |
| Bank2016（GraphFLA 整理版） | 第三方 repack | ✅（仅作便利） | 🔴 **不得再打包** |
| CTX-M-14（woson2020 / MBE 2022） | 论文 **CC BY 4.0**；仓库**无 LICENSE** | ✅ | ⚠️ 论文侧可，**GitHub artifact local-only** |
| CTX-M-14（Palzkill / PNAS 2024） | 论文 **CC BY-NC-ND**；仓库无 LICENSE | ✅ | 🔴 **不得发布派生表** |
| PTE（karolbuda） | 论文 CC BY；仓库无 LICENSE | ✅ | ⚠️ **local-only** |
| MPH（danderson8）/ Kosterlitz（livkosterlitz） | 仓库无 LICENSE | ✅ | ⚠️ **local-only** |
| Mira2015（15 CSV） | **只经 GraphFLA 二次分发**；原论文 PLoS One **CC BY** | ✅ | ⚠️ 须回源 PLoS One 补充材料 |
| CR9114 / Phillips2023 | eLife **CC BY** ✅ | ✅ | ✅ 署名 |
| TEM-1CML | **GPL-3.0** ✅ | ✅ | ✅ 按 GPL |
| AncSR1 | Dryad `10.5061/dryad.jsxksn0hk`（`.rda`，未核许可） | ⚠️ P2 | ⚠️ 未核 |

### 2.2 两个许可状态必须分列（用户要求）

```
analysis_allowed        # 科学分析能不能做
redistribution_allowed  # 最终 release 能不能带原始文件
```

→ 二者**不得互相阻塞**（避免 AncSR1 / CTX-M-14 一类许可/格式问题中断科学工作）。

---

## 3｜角色重分类：CR9114-h1 **移出** `dense × multi-task`

原表述把 CR9114 放在 `dense × multi-task` 标题下，**与自身实测矛盾**（h1 96.0% 可用，h3 10.9%，fluB 0.3%）。更正为：

| 角色 | 数据 |
|---|---|
| **strict dense + multi-task** | **TEM-1CML**、**Phillips2023** |
| **dense single-task control** | **CR9114-h1** |
| **conditional / pending** | **AncSR1** |

> **理由（用户）**：M1 要冻结 `dataset_role` / `task_role`；不改的话，后续代码很容易把 CR9114 **默默当成 multi-task evidence**。

`schema` 中必须存在**互斥**的 `dataset_role ∈ {strict_multi_task, single_task_control, oracle_only, modality_control, conditional}`。

---

## 4｜新增 **G-FTI：future-task identifiability gate**（M4 前置，**不阻塞 M1**）

**问题**：AZT 36 的 genotype 间 IQR 仅 **1.07 × 噪声 SD**。即使 AMP 是合格的 Day-0 条件，**Tomorrow Test 最终仍要在 AZT 上评判谁适应得最好** —— 若 future landscape 的体部差异接近噪声，`R_{B,π}(x, AZT)` 的 **parent ranking 本身可能不稳定**。

**规则（新增）**：

> **future task 也必须通过 outcome-identifiability gate，而不只是 today task。**

**动作（M4 之前完成，不得阻塞 M1）**：对**全部 AZT 浓度**计算

$$\frac{\text{between-genotype signal}}{\text{measurement uncertainty}}$$

并按**预注册规则**选择 future condition —— **不得默认沿用 AZT 36**。

**最坏情形（必须避免）**：模型选对了 parent，但 ground truth 没有分辨率。

---

## 5｜M1 执行指令（用户原话，逐字冻结）

> **进 M1。只构建统一 schema、provenance ledger 和无权 genotype graph；不得计算 EOV、regret、parent ranking 或任何 Tomorrow-Test 结果。M4 前分析禁令继续有效。**

**M1 = schema freeze + genotype graph**，具体要求：

1. **图是纯 genotype topology**：$G=(V,E)$，边**只由"一步合法突变"决定**，**不得把任何 task fitness 塞进 graph 权重**。
2. **measurement 单独挂**在 $(\text{genotype\_id},\ \text{task\_id})$ 上 → 天然防止 future-task information 混进 graph construction。
3. **明确区分** $degree_{\text{topology}} \neq degree_{\text{effective}}$。
4. **schema 必须原生包含**：`missing` / `censored` / `measured_exact` **三态分离**；`floor` / `ceiling`；`SEM` / `SD`；`informative`；`source` / `provenance` / `license` / `redistribution_policy`；`complete-product` / `theoretical_space_size`。
5. **TEM-1 unit test**（必须自动验证）：
   $$4 \times 3^3 \times 2^9 = 55{,}296,\qquad 3 + 3\times2 + 9 = 18$$
   即**所有完整节点的 topology degree = 18**。

---

## 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| 8 | 2026-09-19 | ① **C6 拆为 C6a（published-search/reproduction gate）与 C6b（prospective-selector baselines）**，并加"复现 ≈ 原文输出"前置要求 ② **C8 改为 provenance-specific redistribution policy**；更正 Bank2016 原始 Dryad = **CC0-1.0（我实测）**；**CTX-M-14 更正为两个不同数据集**（MBE 2022 woson2020 / PNAS 2024 Palzkill）③ **CR9114-h1 移出 dense×multi-task** → dense single-task control ④ 新增 **G-FTI future-task identifiability gate**（M4 前置，不阻塞 M1）⑤ 新增两个许可状态 `analysis_allowed` / `redistribution_allowed` ⑥ 冻结 M1 执行指令与 5 条 schema 要求 |
