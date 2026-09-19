# AMENDMENT-018 — M6 确认集替换为 Wu2020（用户裁决）+ 设计冻结

| 字段 | 值 |
|---|---|
| 版本 | **18** |
| 时间 | **2026-09-19** |
| 状态 | **FROZEN**（写入时点：**尚未计算 Wu2020 的任何 task 间相关**） |
| 依据 | ① 用户 2026-09-19 对 `M6_ELIGIBILITY_REPORT.md §6` 的裁决 ② `AMENDMENT-017` §7 第 3 项 |
| 对历史的影响 | `AMENDMENT-017` 的**阈值一字未改**；改变的是**确认集**，走的是 §7 预先写定的路径 |

---

## 1｜用户裁决（逐字）

> **问题**：`Wu2020` 的 `oracle-only` 分类是否解除？
> **裁决：A —— 按 `OP-21` 规则原文解除 `Wu2020` 的 `oracle-only`，执行 M6 确认检验。**
> **附带**：**"照预注册规则跑 {24, 96} 两档全跑，报告里显式标注 coverage 差异。"**

---

## 2｜替换的合规性论证（**必须在报告里原样出现**）

替换的**唯一**触发条件是 `AMENDMENT-017` §6 的结构资格审计（**结果盲**）：

* AncSR1 判不适格，失败项是 **E1（2 个任务 < 3）与 E2（1 对 < 10）**；
* 该审计**未计算任何 task 间相关、未读取任何 phenotype 分布**；
* 用户 M5→M6 指令已**预先授权**："Only permitted reason to look for a second multi-task
  landscape: AncSR1 fails the result-blind structural eligibility audit (**too few tasks**,
  disconnected space, no definable budgeted starting-point value)"；
* §7 的替代顺序（Moulana → Jalal2020 → 全新搜寻）**逐项执行完毕**，前两项各自因
  `OP-18`（>25% 缺失）与"只有 2 个任务"而失败；Wu2020 是穷尽筛选下**唯一**的合格者。

> **一句话**：**换数据不是"结果不好"，而是"数据本来就不够"** —— 且该判断在解盲之前作出。

---

## 3｜确认集的 provenance 记录（全部本项目实测）

| 项 | 值 |
|---|---|
| 论文 | Wu NC, Otwinowski J, Thompson AJ, Nycholat CM, Nourmohammad A, Wilson IA, Plotkin JB. **"Major antigenic site B of human influenza H3N2 viruses has an evolving local fitness landscape."** *Nature Communications* **11**:1233 (2020) |
| DOI | `10.1038/s41467-020-15102-5` |
| **license（Crossref API 实测）** | **CC-BY-4.0**（`content-version` = `tdm` **与** `vor`，`delay-in-days = 0`） |
| `source_type` | **`journal_source_data`**（期刊 Source Data，**非**第三方整理版） |
| 取数对象 | `41467_2020_15102_MOESM6_ESM.xlsx`，sheet **"Fitness and preference"** |
| URL | `https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-020-15102-5/MediaObjects/41467_2020_15102_MOESM6_ESM.xlsx` |
| 字节 / sha256 | `173,890` / 见 `M6_WU2020_PROVENANCE.json` |
| 原始测序 | SRA **BioProject PRJNA563320**（论文 Data availability 原文） |
| 代码 | `https://github.com/wchnicholas/site_B_landscape`（HEAD `4dad2576`，tag `v1.0`） |
| 重复结构 | 论文原文："**Two biological replicates** were performed for each experiment with a high correlation (**Pearson correlation = 0.92 to 0.97**) observed between replicates (Supplementary Fig. 2)" |

### 3.1 ⛔ 一次被抓住的"张冠李戴"（记录，防止复发）

第一次检索到的 Zenodo `10.5281/zenodo.11099316`（`nicwulab/H3N2_2020_RBS_epistasis`）
**md5 完全匹配**，但解包后是 **Italy/2020 毒株**的库（`Ita20HA_MultiMutLib.tsv`），
属同一实验室**另一篇 2024 论文** —— 与 Bei89/HK68/Mos99/NDako16 无关。

→ **教训**：命中摘要 ≠ 命中数据集。**必须打开文件核验内容**，而不是只看 DOI/标题/哈希。

### 3.2 ⛔ `GraphFLA` 整理版**不采用**

GraphFLA 把 `Bris07` 按 HA 194 位 L/P 多态拆成 `Bris07L194` / `Bris07P194` **两个文件**（共 7 个），
而**期刊 Source Data 只有 6 个背景**（`Bris07` 一个）。
→ 采用 GraphFLA 会把**同一个背景重复计一次**，凭空造出 6 个额外 task pair。
→ **采用期刊原表：6 个 task。**（GraphFLA 仅用于本轮的**结构筛选**，其数据**不进任何分析**。）

---

## 4｜E1–E6 重新判定（对 Wu2020）

| # | 判据 | 门槛 | 实测 | 判定 |
|---|---|---|---|---|
| **E1** | task 数 | ≥3 | **6**（`HK68, Bk79, Bei89, Mos99, Bris07, NDako16`） | ✅ PASS |
| **E2** | task pair 数 | ≥10 | **C(6,2) = 15** | ✅ PASS |
| **E3** | 空间可定义 | — | 完整乘积 **4·4·3·2·3·2 = 576**，观测 **576**，**3,456 行 = 576 × 6 完全平衡** | ✅ PASS |
| **E4** | AA Hamming-1 可定义 | — | 6 个残基位点；**每点度 = Σ(状态数−1) = 3+3+2+1+2+1 = 12** | ✅ PASS |
| **E5** | graph_eligible | — | 多任务 + 组合邻域俱在（见 §6 的 informativeness 说明） | ✅ PASS |
| **E6** | OP-21 下预算档 | ≥2 | `|space|/4 = 144` → 可用档 **`[24, 96]`**（384 剔除） | ✅ PASS |
| **OP-18** | 缺失率 | ≤10% 主 / >25% 排除 | **全部 6 个 task 缺失率 = 0.0000** → 全部进主分析 | ✅ PASS |

**→ 结构资格：PASS。可进入 §3 的解盲主检验。**

---

## 5｜任务与表型映射（**现在冻结，不得事后更改**）

| 概念 | 冻结定义 |
|---|---|
| **task** | **6 个 H3N2 遗传背景**之一：`HK68 / Bk79 / Bei89 / Mos99 / Bris07 / NDako16` |
| **主表型列** | **`Fitness`** —— 论文原文称其为 "replication fitness"，是该研究的**主量**（摘要与结果均以它陈述） |
| **辅表型列** | `Preference` = 论文定义的 "**normalized fitness** of individual variants such that the average preference in a given genetic background …" → **不是独立表型**，是 `Fitness` 的**逐背景归一化** |
| `value` | `Fitness` |
| `genotype` | `Variant`（6 残基字符串） |
| **`Preference` 的处置** | **只作为不变式核验**（见 §5.1），**不作为敏感性分支、不参与主检验** |

### 5.1 预指定不变式（写定，先于计算）

若 `Preference` 在每个 task 内是 `Fitness` 的**仿射变换**，则
* `f1_landscape_rho`（Spearman）、`ρ_rank`（Spearman）**逐位不变**；
* `greedy_ssm`（只比较大小）与 `mlde_ridge`（标准化 y + 岭）的搜索轨迹**不变**。

→ **预测：`Fitness` 与 `Preference` 两条路径给出完全相同的 `f1` 与 `ρ_rank`。**
若实测**不**相同，说明归一化不是仿射的，**必须记录并解释**（不得用于挑结果）。

---

## 6｜`informative` 与 SEM 的处置（**必须原样出现在报告的限制段**）

期刊 Source Data **不含逐变体的 SEM/SD**（SRA 有原始读数，重算成本超出本轮范围）。

因此：

1. **`informative` 定义**：按 `M1_SCHEMA_SPEC` v1.4 的**原始定义**（不引入 SEM）——
   `informative ⟺ measurement_state == 'exact' ∧ at_inferred_floor == False ∧ value_group 非 NaN`。
   该表**无删失语义、无缺失、且 576 个变体是作者预先设计的 "variants of interest"**
   → **全部 3,456 行 `measurement_state = exact`、`at_inferred_floor = False`、`informative = True`**。
2. **`CL-9` 的 SEM 分量不适用**：`informative_frac` 的 SEM 形式（`mean > floor + 2·SEM`）
   在本数据上**无法计算**。**本报告一律不引用 CL-9 的 SEM 形式**，
   只报 `missingness = 0.0000` 与"按 schema 定义的 `informative_frac = 1.0`"。
3. **本判据的实际效力**：它只影响**候选 parent 池**。此处池 = **全部 576 个变体**
   （不做任何预先筛选 —— 这也符合项目铁律"never drop genotypes from the Day-0 pool"）。
4. **噪声模型**：`M6` 主检验**不注入噪声**（噪声注入属 Exp2，不在 M6 范围）。
   论文报的重复间 Pearson `0.92–0.97` **仅作背景信息记录**，**不进入任何计算**。

---

## 7｜图与搜索（继承 M5，仅空间不同）

| 项 | 值 |
|---|---|
| 邻接 | **氨基酸 Hamming-1**（单残基替换）；完整乘积 ⇒ 每点度恒为 **12** |
| 层数 `R` | **3**（`OP-1` 冻结） |
| 预算语义 | `OP-1`：`B` = 唯一被测基因型数，起点不计；`b1=⌈B/2⌉`，其后 `b=⌈(B−b1)/2⌉`，再取余 |
| 策略 | `random` / `greedy_ssm` / `mlde_ridge`（`eov/search_sim.py`，唯一实现） |
| 预算档 | **`{24, 96}`**（`384` 因 `OP-21` 剔除；**这是 `AMENDMENT-017` §2 预先写定的处理**） |
| `u_τ` 尺度 | `OP-12` 无 clip 经验分位：`u_τ(z) = (z − q05)/(q95 − q05)` |
| 起点/候选池 | 全部 **576** 个基因型 |
| 计算规模 | 576 起点 × 6 task × 3 policy × 2 budget = **20,736 次搜索** |

### 7.1 coverage **必须显式标注**（用户指令）

| 预算 | Wu2020 coverage | 对照（M4 已报） |
|---|---|---|
| `B = 24` | **4.17%** | TEM-1 `B=384` **0.694%** |
| `B = 96` | **16.67%** | Phillips2023 `B=384` **0.586%** |

→ **Wu2020 的 coverage 比发现集高 6–28 倍**，`B=96` 时已远离"预算型搜索"体制。
**此差异必须在 M6 报告的摘要、结果与限制三处都出现，并与结论并列。**

---

## 8｜主检验（**与 `AMENDMENT-017` §3 逐字相同，未改任何阈值**）

| 项 | 值 |
|---|---|
| 主特征（唯一） | `f1_landscape_rho` |
| 主结局（唯一） | **pair 级 `ρ_rank`** = 6 个 `(policy × budget)` 格各自 Spearman 后取均值 |
| 方向 | **正**，单侧 |
| 成功阈值 | `Spearman(f1, ρ_rank)` **≥ 0.45** 且 95% bootstrap CI（按 pair 重采样 2,000 次）**排除 0** |
| 辅判据（同报，不参与判定） | pair 级 `ρ_rank` 的**中位数**（绝对迁移水平） |
| 判定 | 满足 → 确认成功，主线继续；不满足 → **停止 EOV 主线，不再寻找第三个数据集** |

**禁止事项（继承 `AMENDMENT-017` §5，全部有效）**：不得使用 `f6`/`f3`/`f2`/`f4`/`f5`；
不得引入新模型；不得执行 `D1`/`D3`；不得因结果更换数据集；不得改阈值；不得只报显著子组。

---

## 9｜不变式复核

| 冻结定义 | 是否改动 |
|---|---|
| `V` / `R_{B,π}` / `u_τ`(OP-12 无 clip) / `R=3` | **未改** |
| `eov/search_sim.py`（策略唯一实现） | **未改** |
| `OP-1` / `OP-2` / `OP-12` / `OP-18` / `OP-21` / `OP-25` | **未改** |
| `AMENDMENT-017` §3 的阈值（0.45）、§4 的判定规则、§5 的禁令、§8 的范围限制 | **一字未改** |
| M4 四实验、M5 discovery 结论与其 `discovery` 标签 | **未改** |
| `M1_SCHEMA_SPEC.md` v1.1 哈希 | **未改** |
| **唯一变更** | **确认集：AncSR1 → Wu2020**（经 `AMENDMENT-017` §7 路径 + 用户裁决） |

### 9.1 `AMENDMENT-017` §8 范围限制的**继续适用**

`f1_landscape_rho` 仍需两个 task 的景观值 → **不是**前瞻性特征。
成功时只能说 **"task transferability is predictable from task similarity, despite low
absolute transfer."**（诊断/设计层面），**不能**说"今天就能预测明天"。

---

## 10｜执行顺序

```
S1  本文件冻结                                  ← 完成
S2  Wu2020 结构资格 E1–E6 判定（§4）             ← 完成（全部 PASS）
S3  建统一测量表 + 空间/图，跑 20,736 次搜索，一次性跑主检验
S4  按 §8 判定；按 §7.1 标注 coverage；按 §6/§9.1 标注限制
```
