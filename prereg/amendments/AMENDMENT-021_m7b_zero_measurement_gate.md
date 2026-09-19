# AMENDMENT-021 — M7-B 预注册：Zero-measurement transferability gate

| 字段 | 值 |
|---|---|
| 版本 | **21** |
| 时间 | **2026-09-19** |
| 状态 | **FROZEN**（写入时点：**尚未计算任何 `S_0` 与 `T` 的关系**；`S_0` 的公式常数已定稿，见 §3） |
| 依据 | 用户 2026-09-19 的 M7-B 完整设计（hypothesis / input / predictor / outcome / statistic / success / secondary / forbidden） |
| 标签 | **EXPLORATORY / design characterisation**（新问题；不是确认检验） |

---

## 1｜假设（与 M7 同构，只把"16 次测量"换成"0 次测量"）

$$
H:\quad S_0(\tau_s,\tau_t)\uparrow \;\Longrightarrow\; T(\tau_s\to\tau_t)\uparrow
$$

**目标措辞（保守版，用户指定）**：

> **Can task descriptors identify task changes for which transferring an existing
> starting-point ranking is unlikely to be useful?**

**主用途 = negative-transfer filter**，**不是**"找到一定可以迁移的未来任务"。
（依据：M7 的高相似度档 `ρ_rank` 中位也只有 **+0.0906**。）

---

## 2｜数据（**全部已冻结，无新表型数据**）

| 系统 | task 轴 | task 数 | pair 数 | `T = ρ_rank` 来源 |
|---|---|---|---|---|
| `TEM-1CML` | (药, 浓度) | **8** | **18** | `M5_TRANSFER_MAP.csv` 逐格均值（已冻结） |
| `Wu2020_H3N2_siteB` | H3N2 毒株背景 | **6** | **15** | `M6_WU2020_RESULT.json::rho_pair_level`（已冻结） |
| **合计（主分析）** | | **14** | **33** | |

### 2.1 被排除的系统：`Phillips2023_HA_CH65`（3 对）—— **本轮不可评估**

该数据集的 task 轴是"**哪一个 H1 抗原**"。据 Phillips et al. *eLife* 83628
（PMC9995116，CH65 抗体 × 不同 H1 抗原），`MA90` / `SI06` / `G189E` 是**抗原**，
不是抗体；要定义零测量相似度就需要**抗原序列**，而该序列**不在本工作区**。

> 按用户第 4 条原则（"不同系统不要硬拼一套奇怪的 descriptor"），
> **本轮将其排除并登记为 `not evaluable`**，而不是用"抗体/抗原身份"编一个序数相似度。
> 若日后取得抗原序列，可按同一套 §4 判据单独补做。

---

## 3｜`S_0` 的冻结公式（**逐系统定义，不做跨系统拼接**）

所有 `S_0 ∈ [0,1]` 由构造保证，**无需再缩放**。

### 3.1 `TEM-1CML`

$$
S_0 \;=\; S_{\text{chem}} \times S_c
$$

* **`S_chem`** = ECFP4（Morgan, radius 2, 2048 bit）Tanimoto：
  * 同药：`1.0`
  * `AMP ↔ AZT`：**`0.109756`**（本项目实测并冻结；SMILES 取自 PubChem
    CID 6249 / CID 35370；RDKit `2025.03.4`）
* **`S_c = exp(−|log10 c_s − log10 c_t|)`**（浓度单位 = 该数据集原始单位，`d_c` 以 **log10** 计）
  * **若两个浓度恰有一个为 0**：`S_c = 0` —— 即 `d_c → ∞` 的**极限**，
    "无药选择" 与 "任何加药条件" 视为**最大不相似**（**无自由参数**）
  * 若两者皆为 0：`S_c = 1`
* 约定（用户指定）：**用乘积，不用几何平均**（任何一项不相似 ⇒ 整体明显下降）。**已冻结，不得事后改。**

**8 个 task 的浓度**：`AMP@{0.0, 3.1, 12.2, 48.8, 195.0, 781.0}`、`AZT@{0.44, 36.0}`。

### 3.2 `Wu2020_H3N2_siteB`

$$
S_0 \;=\; \exp\!\left(-\,\frac{|y_s - y_t|}{10}\right)
$$

`y` = 毒株**分离年份**，取自论文原文（**非记忆**）：

| task | 毒株 | 年 |
|---|---|---|
| HK68 | A/Hong Kong/1/1968 | 1968 |
| Bk79 | A/Bangkok/1/1979 | 1979 |
| Bei89 | A/Beijing/353/1989 | 1989 |
| Mos99 | A/Moscow/10/1999 | 1999 |
| Bris07 | A/Brisbane/10/2007 | 2007 |
| NDako16 | A/North Dakota/26/2016 | 2016 |

尺度 **10 年 = 1 单位**，与 `S_c` 的"1 log10 单位"在形式上对齐。**λ 固定为 10，不拟合、不调参。**

---

## 4｜主统计量与不确定性（**用户 §6：task pair 不是独立样本**）

**主统计量**：

$$
\boxed{\;\rho_{\text{zero}} \;=\; \operatorname{Spearman}\!\left(S_0,\; T\right)\;}
\quad\text{over the 33 pairs}
$$

### 4.1 主不确定性：**task-cluster bootstrap**

按 **task**（14 个）有放回重采样 → 取**去重后**被抽中的 task → 保留原 pair 集中**两端都被抽中**的 pair
→ 若去重后 task 数 ≥ 4 且 pair 数 ≥ 6，则重算 `Spearman`。
2,000 次重复，取 2.5% / 97.5% 分位。**种子 `20260919+211`。**

> 同时报告**朴素 pair bootstrap**（2,000 次）用于对照 —— 预期 cluster 版 CI **更宽**。
> 若两者几乎相同，说明 pair 依赖在本数据上不严重（如实报告）。

### 4.2 置换检验（**保留 pair 依赖**）

**在系统内部**随机置换 `task ↔ descriptor` 的对应关系（TEM-1 内置换 8 个 (药,浓度)；
Wu2020 内置换 6 个年份），重算全部 `S_0` 与池化 `Spearman`。**20,000 次**，种子 `20260919+217`。

$$
p = \frac{1 + \#\{\text{null} \ge \rho_{\text{zero}}\}}{1 + B}
$$

> **为什么在系统内部置换**：descriptor 是逐系统定义的，跨系统置换会产生
> "TEM-1 的任务拿到一个年份"这类无意义组合；系统内置换才对应正确的零假设。

---

## 5｜成功判据（**用户 §7，逐字冻结**）

| 档位 | 条件 | 允许的措辞 |
|---|---|---|
| **Primary GO** | `ρ_zero ≥ 0.45` **且** task-cluster bootstrap 95% CI 下界 `> 0` | zero-measurement gate 成立 |
| **Conditional GO** | `0.25 ≤ ρ_zero < 0.45`，**且**方向正确，**且** permutation `p < 0.05`，**且** bottom tertile 能稳定筛出低-transfer pair | "metadata contains useful signal for **negative-transfer screening**"；**不得**写强版 zero-shot predictability |
| **NO-GO** | `ρ_zero < 0.25` **或** CI 大幅跨零 | **停止**。**不得**再加 descriptor、不得上 Transformer、不得上 LLM embedding 去救它 |

---

## 6｜辅助分析（**必须同报**）

1. **`S_0` 三分位 → `T` 的 median / mean / IQR / max**（沿用 M7 做法，**不新造阈值**）。
   核心检查：`S_0 low ⇒ T ≈ 0` 是否成立。
2. **预指定稳健性 A**：剔除**所有涉及零浓度条件**（`AMP@0.0`，5 对）后重算。
   ⚠️ 必须报，因为 `AMP@0.0` 按 §3.1 被钉在 `S_0 = 0`，可能**机械地**推高相关。
3. **预指定稳健性 B**：`S_0` 在**系统内**rank 归一化后重算池化相关，
   用于检查结论是否由**系统间偏移**（而非系统内梯度）驱动。
4. **逐系统** `Spearman(S_0, T)`（TEM-1 n=18；Wu2020 n=15）。
5. **朴素 pair bootstrap**（§4.1 对照）。

---

## 7｜禁止事项（**用户 §10/§11，逐字**）

1. ❌ 用**表型导出**的特征做 descriptor（否则退回 M7）；
2. ❌ 蛋白语言模型（future task 是 task，不是 protein sequence）；
3. ❌ 复杂神经网络（有效独立 task 数太少）；
4. ❌ 几十个化学 descriptor + feature selection（必然过拟合）；
5. ❌ 事后调参（`λ=10` 年、`S_c` 的 log10 尺度、乘积形式**全部冻结**）；
6. ❌ 看结果后再挑 learned embedding；
7. ❌ `D1` / `D3` 倒灌进主检验；
8. ❌ 把 **concentration 当作无关 metadata** —— TEM-1 已证明同药只换浓度 transfer 也可能塌，
   故剂量**必须**进入 task 定义。

---

## 8｜范围限制（**必须与结论同现**）

1. **仅 2 个系统 / 14 个 task / 33 个 pair** —— 样本小，**不得**声称普适。
2. `Phillips2023` 本轮 **not evaluable**（§2.1）；因此"三个独立系统"的说法**不成立**，只能说**两个**。
3. `S_0` 是**粗粒度、可解释**的描述符（指纹 × 剂量；年份差），
   它**不是**"任务相似度的真值"，只是**零测量可得**的一个代理。
4. **M7-B 成功 ≠ 完整前瞻解**：它给出的是**负向筛除**能力；
   非 low 档仍应走 M7 的 `m ≈ 16` 校准（两级 gate）。
5. **不改变绝对迁移结论**：M6 pair 级中位 `0.0021`、M5 `0.0599`、M7 high 档 `+0.0906` 一律不变。

---

## 9｜不变式复核

| 冻结定义 | 是否改动 |
|---|---|
| `T = ρ_rank` 的全部已冻结值（M5 / M6） | **未改** |
| `AMENDMENT-017` §3 阈值 `0.45` | **未改**（M7-B 直接沿用） |
| `AMENDMENT-019` 退化格规则、`AMENDMENT-020` 的 M7 结论 | **未改** |
| `V` / `u_τ` / `search_sim.py` / `R=3` | **未改** |
| **唯一新增** | **M7-B 的 descriptor 公式与判据** |

---

## 10｜执行顺序

```
S1  本文件冻结（含 S_chem = 0.109756 常数）        ← 完成
S2  组装 33 对（18 TEM-1 + 15 Wu2020）与 S_0，打印描述性统计（不看与 T 的关系）
S3  主检验 rho_zero + task-cluster bootstrap + 系统内置换检验
S4  §6 的五项辅助分析
S5  按 §5 判档，按 §8 附范围限制
```
