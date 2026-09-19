# Phase-I Decision Report — **MODIFY**

| 字段 | 值 |
|---|---|
| 阶段 | **M0–M4 收口** |
| 裁决 | **MODIFY**（不是 GO，也不是"整个想法彻底死掉"的 NO-GO） |
| 依据 | 用户 2026-09-19 的签字裁决（逐字见 `M4_SIGNATURE_REQUEST.md` 顶部签署记录） |
| 参数状态 | `OP-1…OP-16` / `INT-1…INT-5` **已按用户裁决生效**；裁决资格已恢复 |
| 验证状态 | 报告数值核验 **746 项全通过**；测试套件 **86 项全通过** |

---

## 1｜正式结论（用户给定措辞，逐字采用）

> **English**
> **Budget-constrained starting-point value is real and reproducible, but our Phase-I evidence
> does not support a strong task-general evolutionary option value distinct from readiness
> and existing informed heuristics.**
>
> **中文**
> **预算约束下的起点价值是真实且稳定的，但现阶段没有证据支持一种独立于 readiness/已有 heuristic、
> 并可跨未来任务泛化的"通用 EOV 属性"。**

---

## 2｜**必须删除**的一句话

> ~~"EOV is a general, distinct protein property that can be prospectively predicted."~~

**Phase I 不支持它。** 具体地：

- "general"（跨任务）—— 跨任务只**部分**稳定；
- "distinct"（区别于 readiness）—— `readiness` 与 `EOV` **不可区分**；
- "prospectively predicted"（可提前预测）—— 对**最强非随机 heuristic** 24/24 不显著。

---

## 3｜成立的部分

### 3.1 起点价值是**真实且预算结构化**的 landscape quantity

泄漏修正（不变量 5）之后，Exp 1 的跨预算 Spearman 相关**变强**为

$$\rho = 0.833,\; 0.929,\; 0.994$$

（原单值场口径 0.665/0.860/1.000；`OP-4` 补算 20 条轨迹后 median 0.966）。
配合 TrpB / GB1 两个独立景观上的外部模拟器校验，可以支撑：

> **在固定 landscape / search setup 下，不同 starting point 的预算后价值不是噪声，
> 且随预算具有相当强的结构稳定性。**

### 3.2 四层分解：一个可理解的预算刻度

$$R_0,\quad R_k^{oracle},\quad R_k^{adaptive},\quad R_{B,\pi}$$

三个 Phillips landscape 上，`B = 384` 的贪心搜索都恰好落在
**2 跳与 3 跳 oracle 之间**（k=2 搜索差距为负、k=3 转为正）：

> **`B = 384` 大致对应 2–3 个突变半径的穷举 oracle 尺度。**

附带结论：`R_k^oracle − R_k^adaptive` 的最大差仅 0.24，仅 **0.13%** 的 parent 出现正差
→ **"有好邻居但走不过去"这个失败模式在 Phillips2023 上几乎不存在**。

---

## 4｜没站住的三个大主张

### 4.1 "存在 task-general EOV" —— 证据不足

跨预算很稳定，**跨任务只部分稳定**（`greedy_ssm` median ρ = 0.396；
Kendall τ = 0.213–0.309；`SI06~G189E` 仅 0.16–0.31）。

**必须区分**：

$$\boxed{\text{starting-point value is structured}} \;\not\Rightarrow\;
\boxed{\text{there exists a task-general protein EOV trait}}$$

> 一个蛋白"在这个 landscape 上很值得进化"，目前**不能**可靠升级成"它普遍更有未来选择权"。

### 4.2 "今天的信息可以提前选出明天更好的 parent" —— 主判据 FAIL

**容易骗到人的地方**：frozen selector 相对 `random` 有
**44.6%–61.8%** 的 regret reduction，三个预算 CI 全部排除 0，`top-k` 下也稳健。

**这是一个真实正结果。** 但预注册判据从来不是"比 random 好就赢"，而是
**相对最强非随机 heuristic 还要有增量**：

$$\text{对非随机 heuristic：} \; 24/24 \; \text{个单元 CI 跨 0}$$

而且 `top-k` 敏感性显示这是**判据本身在本样本量下不可满足**（不是"未观察到效应"）：
把决策规则从 argmax 放宽到 top-20，可分辨格子由 8/180 升到 34/180，
**但判据仍然 0/180** —— 因为 CI 收窄与效应缩小同步发生。

正确结论不是"模型成功预测 EOV"，而是：

> **Today information contains useful signal beyond random choice, but the tested frozen
> selector does not establish incremental prospective value beyond simple informed heuristics.**

### 4.3 `readiness ≠ EOV` —— 当前没有被证明

⚠️ **注意：A3 之后此节的标注已改变**（原先主条件是 `AZT@0.44`，签字后恢复登记默认 `AZT@36.0`）。

| 条件（A2 严格容差下） | greedy B24 | B96 | B384 |
|---|---|---|---|
| **主条件 `AZT@36.0`**（登记默认） | FAIL (p = 0.497) | **PASS (p = 0.0088)** | **PASS (p = 0.0106)** |
| sensitivity `AZT@0.44` | FAIL | FAIL (p = 0.089) | FAIL (p = 0.097) |

**两个统计量在主条件上指向不同侧重，必须并列报告**：

- **方向性（`Readiness`）**：B96/B384 的命中率 **0.654 / 0.646**，p < 0.05，CI 排除 0
  → **有弱但显著的预测方向**；
- **幅度（方差压缩比）**：B96/B384 的 `sd_ratio` = **0.951 / 1.027**，CI 覆盖 1
  → **今天的信息并不压缩未来的离散度**，即"同一个现在、不同的未来"**成立**。

→ 合起来是：**方向上有微弱信息，幅度上不受约束**；
且**该方向性在主条件上成立、在 sensitivity 上不成立**（两条件仍不一致）。

**无论取哪个条件，"readiness 与 EOV 不可区分"这一强主张都不成立** —— 这正是 §1 的正式结论。
**不能写**："我们发现了一个独立于 promiscuity/readiness 的新 protein property。"

---

## 5｜H1 / H2 的最终状态

| 项 | 状态 | 依据 |
|---|---|---|
| **H1 — 严格读法**（A1 保守分母 `2×median(value_sd)`） | **FAIL** | 仅 1 个 landscape 满足"≥2 策略 × ≥2 预算" |
| H1 — 宽松读法 | PASS | 3 landscape × 3 预算 × 3 策略 |
| H1 — 限定 `greedy_ssm` | PASS（两口径均） | 9/9；ICC 0.53–0.83、effect/noise 1.06–2.19、permutation p 8/9 < 0.05（例外 `G189E@B24`，p = 0.90） |
| **H2 — 判据 (A)** `ΔCV-R² ≥ 0.05` | **FAIL（定量）** | 最大 **0.0149**，**18/18 格低于阈值**，最差为负 |
| **H2 — 判据 (B)** regret 降低 ≥ 20% | **FAIL** | `argmax` / top-5 / top-20 三种决策规则下**全部 0/180** |
| **H2 — 对照完整 proxy set** | **incomplete / unresolved** | `conservation` 与 `frozen zero-shot score` **未算**（`D3`）。用户裁决：**论文若要写"independent of known proxies"，这两个 baseline 必须存在**；否则标为 unresolved |

---

## 6｜下一阶段的研究问题（用户给定，收窄后）

**不要**立刻造一个 Transformer 去"救结果"。课题不停，但问题收窄为：

$$\boxed{\text{What makes starting-point value transferable across tasks?}}$$

即从"**预测 EOV**"转为"**解释什么时候 starting-point value 可以跨任务迁移，什么时候不可以**"。

已有的、天然指向这个问题的一组事实：

| 已观测事实 | 出处 |
|---|---|
| **budget 轴：稳定** | Exp 1 跨预算 ρ = 0.833 / 0.929 / 0.994 |
| **task 轴：不完全稳定** | Exp 1 跨任务 median ρ = 0.396；Kendall τ = 0.21–0.31 |
| **current / readiness heuristic 很强** | §4.3：方向命中率 0.65，p ≈ 0.01 |
| **frozen selector 没能稳定超过它** | §4.2：24/24 不显著 |

→ 指向的核心张力：$$\text{budget invariance} \quad\text{vs}\quad \text{task dependence}$$

---

## 7｜引用外部校验时的口径（用户给定）

> Across two independent landscapes, the fixed-budget simulator recovered approximately
> **82–93%** of the corresponding exhaustive/published search value at `B = 384`.

**不能只写 93.1%**（那只是 TrpB；GB1 上只有 0.823）。且必须紧跟一句：

> performance depends on landscape geometry and the imposed three-step search horizon.

支撑：`M4_TRPB_EXTERNAL_CHECK.csv`、`M4_GB1_BASELINE_AND_EXTERNAL.csv`、`M4_TRPB_LOCAL_OPTIMUM_CHECK.csv`
（残差归因：`OP-1` 的 `R=3` 上限 + 最陡上升 vs 固定顺序坐标扫描的算法差异）。

---

## 8｜D1 / D3 的执行条件（用户裁决要点）

| 项 | 条件 |
|---|---|
| **D1**（DAOx/TEV 无图策略） | **授权但降为非阻塞 exploratory**；**不得用来翻转 Phase-I 主裁决**；必须明确标为 **post-decision exploratory** |
| **D3**（conservation + frozen zero-shot） | **不阻塞本轮 MODIFY**。论文若要写"EOV 不能被已有 proxy 解释" → **必须补**；否则 H2 标为 *incomplete/unresolved against full proxy set*。**禁止 finetune** |
| **D4′**（`R=3`） | **维持 `R=3`**；`R>3` 后续做 sensitivity，**不能回写主分析** |

理由（用户原话）：

> "现在再发明一个策略，然后发现它恰好能把 readiness 和 EOV 分开，会非常像：
> **看完答案以后继续试方法直到成功。** 这个风险比少一个实验严重得多。"

> "就算 ESM/EVmutation/conservation 全部很差：**强版 EOV 故事依然不会自动复活。**"

---

## 9｜永久工作规程（本报告新增，第 26 条）

> ### **Evidence before explanation**
> **凡报告中出现"没有 / 未做 / 未物化 / 需要授权 / 代码不存在"这类否定性事实，
> 必须先 grep / ledger / filesystem check，再写解释。**

**为什么需要它**：本项目的两次同类错误都发生在我**为某件事找理由**而不是**去查它**的时候：

| # | 错误 | 性质 |
|---|---|---|
| 1 | 把 TrpB 当成 "novelty 风险" 而非**交付物** | 把它归错了类，于是它从未进入"要交"的清单 |
| 2 | 写"DAOx / TEV **从未物化**" | 这是从"M2 长表里没有"**推断**出来的，而 M2 本来就不该装 `task_panel`。实测它们早在 `M3_taskpanel_measurements.parquet` 里（DAOx 5×6,417 **全 informative**；TEV 163×62,220） |

第 2 条的代价很具体：一个**便宜的授权项**（写一个无图策略）被包装成了
一个**昂贵且与用户指令冲突的授权项**（新增数据集）。

---

## 10｜本轮之后的项目状态

**已冻结的能力（可复用于下一阶段）**

| 资产 | 内容 |
|---|---|
| 数值核验 | `eov/m4_verify_report.py` —— **746 项**，含跨文档计数一致性 |
| 回归测试 | `tests/` —— **86 项**（含 `test_search_sim.py` 41、`test_tis.py` 7） |
| 泄漏防护 | `eov/tis.py`（L39 接口级隔离）+ `M4_LEAKAGE_AUDIT.md`（独立审计，28 PASS / 5 VIOLATION，全部闭环） |
| 策略唯一实现 | `eov/search_sim.py`（**已获两个独立景观的外部校验**） |
| 复现性 | `experiments/M4/*/{TIS_MANIFEST,config,seeds}.json` + `data/manifests/*.sha256`（端到端重跑逐字节相同） |
| 失效登记 | `FREEZE_LEDGER.md` 批次 #1–#41（**11 个静默失效 + 9 个漏交的强制交付物，全部闭环**） |

**下一步的两个选项（用户裁决）**

1. **研究 task-transferability 的边界**（§6 的问题）；
2. **接受 Phase I 的负结果，转去另一个方向**。

---

## 附：正式结论的一句话版本

> **Starting-point value is strongly budget-structured, while its transfer across future
> tasks — and its distinction from readiness — remains the real unsolved problem.**
>
> 起点价值是强预算结构化的；而它**能否跨未来任务迁移**、以及**它与 readiness 的区别**，
> 才是真正尚未解决的问题。
