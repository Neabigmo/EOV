# AMENDMENT-002 — 最终枚举结果并入预注册（含两项实质修正）

| 字段 | 值 |
|---|---|
| 版本 | **2** |
| 时间 | **2026-09-19**（精确时间戳见 `data_registry/FREEZE_LEDGER.md`） |
| 状态 | **FROZEN** |
| 依据 | `data_registry/LANDSCAPE_HUNT_v0.md` **最终版（627 行 / 67.7 KB）** |
| **时机** | **任何分析均未运行** → 预注册期修订，**无需盲法重跑** |

## 修正范围

| 被修正对象 | 修正 |
|---|---|
| `AMENDMENT-001` A-1（H1 噪声阶梯） | **B-1**：新增档 A 的首选证据床 |
| `AMENDMENT-001` A-3（证据链角色） | **B-2 + B-3**：预算-空间硬规则 + 角色重排 |
| `AMENDMENT-001` A-9（Novelty 定位段） | **B-4**：补入比 GraphFLA 更近的对手 |
| `DATA_AUDIT.md` v2 §2.5（规模口径） | **B-5**：升级为硬规则 |
| `DATA_AUDIT.md` v2 §3（三条线索） | **B-6**：最终裁决 + 一处引用更正 |
| `AMENDMENT-001` A-7（M0 P0） | **B-8**：新增两项 |

---

## B-1｜判据 ④ 的满足者：AncSR1（**条件性**，需先验证数据可达性）

**对象**：Starr, Picton & Thornton, *Nature* 2017，`10.1038/nature23902`（PMC6214350）；后续 Metzger, Park, Starr & Thornton, *eLife* 2024，"Epistasis facilitates functional evolution in an ancient transcription factor"，`10.7554/eLife.88737`。

✅ **我已独立核实**：eLife 88737 的作者、标题、DOI、发表时间（2024-05-20，Version of Record）。
🔷 **子代理核实（引自原文）**：**160,000 = 20⁴**（4 个关键位点 × 全部 20 种氨基酸）× **{ERE, SRE} 两个 DNA 响应元件** × **独立转化两次**（replicate FACS-seq）× **可估 SEM**；共 **4 个条件** = {ERE, SRE} × {AncSR1, AncSR1+11P}。

**为什么重要**：
1. 它是**目前唯一同时满足全部 4 条判据**的候选（判据 ④ 的重复与误差**内建**，不需要回源抗体数据的 eLife/Desai 仓库）。
2. **任务语义比抗体逃逸干净**：同一蛋白（祖先转录因子）面对**两个不同的 DNA 靶标** —— 这在语义上更接近"底物/靶标切换"，而不是"免疫压力"。
3. 与 TrpB4/GB1 同为 **20 字母表 × 4 位点**（deg = 4×19 = 76），结构可比。

**修正 A-1**：H1 的 **档 A 首选 AncSR1**（若数据可取）；TEM-1 仍走档 A（triplicate 真实存在）。档 B/C 仅在 AncSR1 + TEM-1 都不可用时才启用。

⚠️ **未核实（本次的唯一阻塞）**：per-variant × per-element 荧光表的**可下载位置**未确认（PMC PDF 被拦，eLife API 拒绝无 Accept 头的请求，未找到 Dryad/Zenodo 记录）。
→ **新增 P0-0（最高 ROI）**：抓 Nature 补充材料 / eLife 88737 的 Data availability / 直接联系 Tyler Starr 索取 160k × 4 条件的逐变体表。
→ **在数据到手之前，AncSR1 一律标记为"条件性 L3"，不得作为主结论依据。**

---

## B-2｜新硬规则：**预算必须显著小于搜索空间**（OP-21）

**事实（子代理实测）**：`new_PTE` = 6 位点 / **64 个基因型**（完整 2⁶）；`Lunzer2005` = 6 位点 / **512 个基因型**（2×4×8×2×2×2）。

**问题（数学上致命）**：我们默认预算档位 `B ∈ {24, 96, 384}`。
- `B = 96 > 64` → 在 `new_PTE` 上"搜索"等于**把整个空间买下来**，`R_{B,π}` 退化为 oracle，**search policy 之间的差异被完全抹平**，H2/H3 中"策略能不能找到"这一维度消失。
- `B = 384` 已接近 `Lunzer2005` 的 512（coverage = 75%）。

**新增硬规则（OP-21，冻结默认）**：
1. **`B ≤ |space| / 4`**（coverage ≤ 25%）。任何数据集/任务违反此式时，该 `B` 档位**不得使用**。
2. 每个 `(landscape, B)` 组合必须报告 **coverage = B / |space|**。
3. 空间过小的 landscape **只能作 oracle-only 证据**（只算 `R_0`、`R_k^oracle`、adaptive-accessible），**不得参与任何预算型主张**。
4. 由此：`new_PTE` 上限 `B ≤ 16`；`Lunzer2005` 上限 `B ≤ 128`；`Mira2015_TEM_*`（16 个基因型）上限 `B ≤ 4` → **事实上只能是 oracle-only**。

> **这条修正直接推翻 AMENDMENT-001 A-3 里"`new_PTE`/`Lunzer2005` 作为第二例（酶，多条件）"的角色分配。** 该分配作废，按 B-3 重排。

---

## B-3｜证据链角色重排（取代 A-3 的表）

| 角色 | 数据 | 是否满足 4 条判据 | 回答什么 |
|---|---|---|---|
| **主数据** | **TEM-1**（AMP → AZT；triplicate 真实） | ①②③✓ ④✓（triplicate） | 严格 Tomorrow Test；酶-新底物 |
| **第二系统（条件性）** | **AncSR1**（20⁴ 完整 × 4 条件 × 2 重复） | ①②③✓ ④✓*（*待 P0-0 验证数据） | 跨系统的起点估值；TF-靶标切换 |
| **高密度多任务复制** | **Phillips2023**（16 位点 × 3 任务 × 65,536，缺失 0.01–0.04%） | ①②③✓ ④✗（阶梯 A/B/C） | "TEM-1 是不是特例" |
| **次选多任务复制** | `Moulana2023+2022`（15 位点 × 5 任务，CB6 缺失 49.6%） | ①②③✓ ④✗ + **MNAR** | 仅经 OP-18 门槛后进 sensitivity |
| **20 字母表 + 多任务** | **`Jalal2020`**（`NBS` / `parS`，各 160,000 / 0 缺失 / deg = 76） | ①②③✓ ④⚠️ | 与 TrpB4/GB1 同空间结构的第二例 |
| **同蛋白任务面板** | **`Mira2015_TEM_*`**（TEM-1 × 15 β-内酰胺，2⁴ = 16） | ①✗（空间过小） | `Corr(EOV_τ1, EOV_τ2)`；**oracle-only** |
| **oracle-only** | `new_PTE`、`Lunzer2005` | ①△ ②✓ ③✓ | 景观机会 `R_k^oracle`，**不做预算型主张** |
| **模态对照** | `Soo2021`（RNA，8 位点 × A/C/G/T，deg = 24，2 温度） | ①②③✓ ④⚠️ | 定义的普适性（L0，非蛋白证据） |
| **辅助环境轴** | MBE `msag106`（**就是 TEM-1**，≈11 环境，有真重复，但严格单突变） | ①✗ | TEM-1 的环境敏感性，**不做起点选择** |

### ⚠️ 对 INT-8 的决定性事实（请据此裁决）

**"第二个系统也必须是酶"这一选项在数据上基本不可行。** 理由：
- 酶的多任务**密集**景观，现存只有**小空间**（`new_PTE` 64、`Lunzer2005` 512、`Anderson2021` 32、`Frohlich21_OXA-48` 16）→ 按 B-2 无法承载预算型 DE；
- 大空间酶景观（TrpB4 160,000、GB1 149,361）**只有单一任务**。

→ 因此：
- **选项 (ii)（要求酶）** ⇒ 跨系统主张**只能**建立在"单任务、跨 landscape 的起点效应"上，**publication-level 的 multi-task 跨系统主张不成立**。
- **选项 (i)（接受，推荐）** ⇒ 第二系统用 AncSR1（TF）/ Phillips2023（病毒糖蛋白–抗体），结论限定为 **"protein starting-point option value（跨酶、转录因子与结合蛋白）"**。

---

## B-4｜🔴 Novelty：比 GraphFLA 更近的对手是 **TrpB 原文本身**

**主张（🔷 子代理核实，⚠️ 待我独立确认 —— 新增 P0-9）**：Johnston et al., *PNAS* 2024（我们计划用作第二主数据的 `10.1073/pnas.2400439121`）**已经发表**了在该 159,129 变体完整 20⁴ 景观上的：
- **从每一个起点出发的 max fitness ECDF**；
- 3 种 in-silico directed evolution；
- local-optima / accessible-path 分析；
- **注入噪声的 null model**。

**为什么这比 GraphFLA 更危险**：
> **"从每个起点出发的最大适应度分布"在数学上就是单任务下的 `R_{B,π}(x,τ)`。** GraphFLA 是"整张景观 × 随机起点取平均"，而 TrpB 原文是"**逐起点**"。后者与我们的分析单位**完全一致**。

**修正 A-9**：定位段必须增补下列表述（无论 P0-9 结果如何都要写）：

> 在单任务、单分布的条件下，**逐起点可达值的分布**已有先例（Johnston et al., PNAS 2024 在 TrpB 20⁴ 完整景观上的 ECDF 分析）。因此本文的增量**不在**"起点差异存在"或"给定预算下起点可达值不同"，而在于：(i) **任务维度的 holdout** —— 未来任务的任何测量都不进入特征、超参选择与排序；(ii) 以 **selection regret**（选错起点的决策损失）而非可达最大值分位数为主指标；(iii) 检验 **`Corr(EOV_τ1, EOV_τ2)`**，即起点价值是否跨任务稳定，从而区分"通用 option value"与"任务族条件化的 option value"。

**附带收益**：TrpB 原文的 **3 个 DE 基线 + 噪声 null model 可直接复用**，`search_policies.py` 少写一大块（与 SSMuLA 复用的决定一致）。

---

## B-5｜DATA_AUDIT 新硬规则：**规模一律以实际文件为准**

**事实（子代理实测，论文声明 vs 仓库实际）**：

| 文件 | 论文表格声明 | 仓库实际 | 实际/声明 |
|---|---|---|---|
| `Papkou2023_DHFR.csv` | 4⁹ = 262,144（99.7% 实测） | **135,178** | **51.6%** |
| `Westmann2024.csv` | 4⁸ = 65,536 | **17,765** | **27.1%** |
| `Kuo2020.csv` | 262,144 | 197,890 | 75.5% |

另有：`benchmarks/_datasets.py` 引用的 `Papkou2023_DHFR_RAW.csv` **返回 404**（仓库中不存在）；`Skwara2023_Butyrate.csv` **格式损坏**（表头 27 列，第 2 行仅 3 字段）。

**新增硬规则（写入 DATA_AUDIT §2.5/§4）**：
1. 一切**规模、完整性、缺失率**数字**只以实际文件的行数 / unique 序列数为准**；引用论文数字必须显式标注"**论文声明**"。
2. 每个纳入的数据集必须记录：`rows`、`unique_sequences`、`expected_space_size`、`completeness = unique / expected`、`fitness_missing`。
3. 自动校验脚本必须**对全部 163 个 CSV 跑一遍**（当前仅 28 个做了取值域、44 个做了行数），并记录失败文件。

---

## B-6｜三条线索的最终裁决（取代 DATA_AUDIT v2 §3 的相关推断）

| 线索 | 裁决 | 依据 |
|---|---|---|
| **FLIP2** | **排除，投入为 0** | 44 个 CSV 只有 `sequence,target,set,validation`，**无任何 condition 列**；`gb1/low_vs_high` 与 `gb1/one_vs_rest` 的 8,733 行序列**完全相同**、target **逐字节相同** → 是 distribution-shift 切分。License CC-BY-4.0 |
| **DHFR-TMP** | **判据 ① ✗** | 1,208 已组装 / ~1,136 回收（"416 个同源物"是过滤子集）；111,233 genotype 行；**每骨架中位仅 18 个随机突变**，跨骨架 Hamming 距离巨大 → 无组合邻域。9 个条件中 **6 个是同药不同浓度**（抗性同源物数 318→246→226→128→80→27 单调）→ 很弱的 future task 轴。数据 Figshare `10.6084/m9.figshare.30470525.v1`，MIT |
| **MBE `msag106`** | **判据 ① ✗**；作 TEM-1 辅助环境轴 | **研究的就是 TEM-1**；≈11 个真实环境（3 温度 × 2 培养基 + avibactam/tazobactam + M182T + Δss）；**有真重复**（"P<0.01 in both replica experiments"）；但**严格单突变**（Mehlhoff 2020 的 5,428/5,720 单密码子替换）。补充材料被 OUP Cloudflare 403，**未取得** |

⚠️ **引用更正**：DHFR-TMP 的**已发表版是 `PMC12346277`**；`PHASE1_DECISION` 讨论中我此前引用的 `PMC11785229` 是 **preprint**。后续引用一律用已发表版。

---

## B-7｜新增待签字条目

| ID | 内容 | 默认 |
|---|---|---|
| **OP-21** | 预算-空间硬规则 `B ≤ |space|/4`，coverage 必须报告；违规者降为 oracle-only | 见 B-2 |
| **OP-22** | AncSR1 是否作为**第二主系统**（条件：P0-0 数据可达） | 是（若数据可得） |
| **OP-23** | `Jalal2020` 的角色（20 字母表多任务第二例 vs 仅 robustness） | 纳入主 panel，但需先核 fitness 语义 |
| **INT-9** | 若 TrpB 原文确已做逐起点 ECDF，我们的增量边界如何表述 | 见 B-4 的定位段（任务 holdout + regret + 跨任务一致性） |
| **INT-8（更新）** | 结合/逃逸/TF 景观是否算跨系统证据 | 建议 (i)；新增决定性事实：**(ii) 在数据上基本不可行**（B-3） |

---

## B-8｜M0 P0 清单更新

| # | 动作 | 备注 |
|---|---|---|
| **P0-0（新，最高 ROI）** | **AncSR1 逐变体 × 4 条件荧光表的可达性**：Nature 补充材料 / eLife 88737 Data availability / 联系 Tyler Starr | 决定能否拿到唯一"判据 ④ 内建"的 L3 |
| **P0-9（新）** | **独立确认 TrpB 原文是否已做逐起点 max-fitness ECDF + 3 种 DE + 噪声 null model** | 决定 novelty 定位段与 `search_policies.py` 的复用范围 |
| P0-4（原） | 逐条独立复核子代理数据 | 范围扩大：改为**全部 163 个 CSV 自动校验**（见 B-5） |

（A-7 的其余 6 条 P0 动作保持有效。）

---

## 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| 2 | 2026-09-19（预注册期） | ① 新增 AncSR1 作为判据 ④ 的满足者（条件性，P0-0）② 新增预算-空间硬规则 `B ≤ |space|/4` 并**推翻** A-3 中 `new_PTE`/`Lunzer2005` 的角色 ③ 证据链角色重排 + INT-8 的决定性事实 ④ Novelty 定位段补入 TrpB 原文（P0-9）⑤ DATA_AUDIT 规模口径升级为硬规则 ⑥ 三条线索最终裁决 + PMC 引用更正 ⑦ 新增 OP-21…OP-23 / INT-9 / P0-0 / P0-9。**分析未运行，无需盲法重跑。** |
