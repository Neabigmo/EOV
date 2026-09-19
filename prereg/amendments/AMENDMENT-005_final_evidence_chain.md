# AMENDMENT-005 — 最终证据链、二次分发 provenance 规则、以及阈值放宽观察名单

| 字段 | 值 |
|---|---|
| 版本 | **5** |
| 时间 | **2026-09-19**（精确时间戳见 `data_registry/FREEZE_LEDGER.md`） |
| 状态 | **FROZEN** |
| 依据 | 子代理 FINAL DELTA（三条并行线程全部结束）+ 我的 DOI 核验 |
| **时机** | **任何 EOV 分析均未运行** → 预注册期修订，无需盲法重跑 |

> **本文件包含 §E-8 的"最终证据链表"，它取代 AMENDMENT-001 A-3、AMENDMENT-002 B-3、AMENDMENT-004 D-10。** 其余修正案继续有效。

---

## E-1｜🆕 Kosterlitz 多宿主 blaTEM —— 与主数据**同一蛋白**的宿主轴

- **结构**：5 位点（g4205a 启动子 SNP、A42G、E104K、M182T、G238S）→ **32 基因型完整 2⁵，零空洞** × 3 条形码 = 96 质粒
- **3 个真实宿主物种**：*E. coli* DH10B / *K. pneumoniae* Kp08 / *S. enterica* Typhimurium LT2，各自跨 cefotaxime 梯度
- **托管**：Zenodo **`10.5281/zenodo.10045641`** ✅ 我核实 DOI 解析 200（→ `zenodo.org/records/10045641`）+ `github.com/livkosterlitz/crowdsourcing`；论文 *Mol Biol Evol* `10.1093/molbev/msad237`（OUP 侧 403，DOI 存在）
- **License**：🔷 CC-BY-4.0（子代理经 API 核实）
- **判据**：①✓ ②✓ ③✓ **④⚠️**（逐宿主重复筛选未明；逐浓度原值 vs 仅拟合拐点未核实）

**裁决**：空间仅 32 → 按 **OP-21**（`B ≤ |space|/4 = 8`）为 **oracle-only**。但它的价值不在预算型 DE，而在于：**给"任务轴"增加一个此前完全没有的维度 —— 换宿主**，且**与 TEM-1 同蛋白**，叙事上比抗体逃逸更贴合主线。
**新增用途**：`Corr(EOV_τ1, EOV_τ2)` 的宿主轴验证（与 `Mira2015` 的抗生素轴并列）。

---

## E-2｜⚠️ 更正：GraphFLA 只收了源数据的**子集**（第四次复现 CL-8）

| 对象 | GraphFLA 派生版 | **源数据** | 差异后果 |
|---|---|---|---|
| **PTE**（磷酸三酯酶） | **2** 个底物（2NH、butyrate） | **9** 个底物（2NH, DHC, POE, POM, PTE, PTM, acetate, butyrate, tbbl；跨 3 个化学类）；6 位点完整 2⁶ = 64；**biological n = 3–10 + technical n = 3 次真实重复**（4,872 次测量，CV 中位 15%） | 判据 ④ **由 ⚠️ 变 ✓**；我此前在 B-3 写的"new_PTE 仅 2 底物"**是错的** |
| **MPH**（甲基对硫磷水解酶） | **6** 个金属条件 | **8** 个环境，**明确三次生物学重复 + SD** | 判据 ④ **✓** |
| **Mira2015 TEM** | 15 个 CSV | **作者处无 deposit**（见 E-5） | 反方向：派生版是唯一来源 |

**PTE 数据入口**：`github.com/karolbuda/rba-error-propagation`；preprint `10.64898/2026.07.02.736193`。⚠️ license 未核实、同行评审状态未知。
**MPH 数据入口**：`github.com/danderson8/MPH_Epistasis` + Zenodo `10.5281/zenodo.4552583` ✅ 我核实解析 200。

**对裁决的影响**：两者空间仍 ≤ 64 → 预算型结论不变（oracle-only）。但**它们现在是"带真实重复的酶-多底物/多环境"证据**，是 H1 噪声问题在小空间酶景观上的**独立复现点**。
⚠️ **要"酶-多底物"证据必须回源取 PTE 的 9 个 CSV，不得用 GraphFLA 的 2 个派生文件。**

---

## E-3｜🆕 TEV 蛋白酶 DNA-recorder —— 任务面板最丰富（134 个底物），但不是组合空间

- **规模**：**29,716 个蛋白酶 × 最多 134 种底物 ≈ 600,000 个 protease–substrate 对**（约 355,000 唯一，占可能组合 59.7%）；蛋白酶侧为 3–6 个 NNK/NNS 随机化残基
- **托管**：`github.com/JeschekLab/ProtRec` + Zenodo **`10.5281/zenodo.15346003`** ✅ 与 `10.5281/zenodo.15344074` ✅（我核实均解析 200）；*Nat Commun* `10.1038/s41467-025-60622-7` ✅ 解析 200；🔷 CC-BY-4.0
- **判据**：①**✗**（多位点随机化，**非完整超立方体**，Hamming-1 邻域稀疏）②✓（**134 个底物**）③✓ ④⚠️（仅声明 "robustness across replicate cultivations"）

**裁决**：**不作组合景观使用**。但它把 **L1（readiness / task-transfer）的天花板从 DAOx 的 5 个底物抬到 134 个**。
**新增 OP-28**：L1 的"task uncertainty 对照"用 TEV（134 任务）还是继续用 DAOx（5 任务）？—— 若用 TEV，"预测明天一来就能干什么"这一侧的统计功效会大幅提高。

---

## E-4｜✅ 干净的穷尽性阴性结论：**不存在"组合型 × 多温度"的蛋白景观**

唯一候选 **Tang & Zheng YFP × 7 温度**（Zenodo `10.5281/zenodo.20719728` ✅ 我核实解析 200，MIT）已被完整下载（237,039,715 B）并逐行扫描：7 个温度（15–42 °C）+ 每基因型 Tm + ddG，但**109,856 行恰好 1 个突变、0 行 > 1 个突变** → **饱和单突变扫描，判据 ① ✗**。

**联合门槛**（≥3 位点 ∧ ≥10⁴ 多突变体 ∧ ≥2 条件）在多底物与多环境文献里**均不存在**；该交集里的最大空间只有 **64（PTE）** 与 **32（MPH、Kosterlitz）**。
→ **真正满足"密集 × 多任务"的对象集合 = { TEM-1CML, CR9114, AncSR1（条件性）, Jalal2020, Phillips2023 }**，与 §E-8 表一致。
→ 该声明可直接写入 `DATA_AUDIT.md` §3 作为**穷尽性方法学结论**。

---

## E-5｜Provenance 新规则：**二次分发（secondary distribution）必须标注**

**更正**：并行线程曾报告 "Mira/Barlow TEM-50（4 位点 × 15 种 β-内酰胺）找不到 deposit" —— **这是错的**：数据存在，**但只存在于 GraphFLA 仓库**（子代理逐个核实过表头/行数/缺失），**作者处无 deposit**。

**新增规则（写入 DATA_AUDIT 的 provenance 列）**：
1. 每个数据集必须标注来源类型：`author_deposit` / `journal_source_data` / **`secondary_distribution`** / `derived_aggregate`。
2. `secondary_distribution`（如 GraphFLA 的 `Mira2015_TEM_*`）必须写明："**经 <聚合仓库> 二次分发获得，非作者 deposit**"。
3. **License 不具传递性**：GraphFLA 的 MIT **不覆盖**其二次分发的底层数据；底层数据许可必须单独回源（与 D-6 的 ProteinGym / CIS-BP 同源）。
4. 本项目 **不重分发**任何第三方数据；只保存 URL/DOI + sha256 + 获取时间。

---

## E-6｜阈值放宽观察名单（**当前一律不纳入主分析**）

| 对象 | 已核实优势 | 卡在哪条判据 |
|---|---|---|
| **Cox 2022：247 个单抗 × SARS-CoV-2 RBD**（*Nature*） | **247 个条件**；干净 CSV + SRA | ①（Hamming-1 饱和） |
| **VIM-2**（MaveDB `00000073-a`…`-i`，9 个 score set = 3 β-内酰胺 × 2 温度，各 5,549 变体） | 有重复；6 条件 | ① |
| **PAX6 paired-domain Y1H**（McDonnell 2024, CC BY） | 150 位点、Hamming-1 完整、4 条件 = 2 DNA bait × ±geneticin | ①（仅 5,266 多突变体）+ ③（无独立 processed deposit） |
| **Taft 2022 DML / Shlesinger 2026 血清面板** | "同一 RBD 组合文库 vs 13 单抗 + ACE2" / "vs 10 份血清" = **24 个条件**，C1/C2 成立 | **③ 未核实**（GitHub API 全会话限流） |

**新增 OP-27**：是否发作者邮件索取 Taft 2022 DML / Shlesinger 2026 的 processed 表？这是**最后一个可能显著加强多任务面板的机会**（24 个条件 × 组合文库）。

---

## E-7｜本次 survey 的方法学限制（如实记录）

1. **未认证 GitHub REST API 在全会话对并行线程限流（60 req/h/IP）** → Taft 2022 DML 与 Shlesinger 2026 的 processed 表**无人能核实**；这一限制必须在 DATA_AUDIT 里写明（否则会被读成"查过但没有"）。
2. 因此 **"查不到" ≠ "不存在"**：本 survey 已出现 4 次"派生版本丢失信息"的反例（GraphFLA↔eLife、RNAGym processed↔raw、ProteinGym processed↔raw、GraphFLA 只收 PTE 2/9 底物）。所有阴性结论都必须写成"**在已核实的检索范围内未发现**"。

---

## E-8｜**最终证据链（operational，取代 A-3 / B-3 / D-10）**

| 角色 | 数据 | 空间 | 任务 | 噪声 | 判定 | 来源类型 |
|---|---|---|---|---|---|---|
| **主数据** | **TEM-1CML** | 55,296（13 位点/18 突变，deg 18） | AMP → AZT（唯一 strict future） | triplicate ✓ | **L3** | journal + GitHub + Zenodo |
| **第二系统（实测合格）** | **Phillips2023** | 65,536（2¹⁶，deg 16） | MA90 / SI06 / G189E + **表达轴** | rep×2 + SEM ✓ | **L3** | journal source data |
| **噪声校准床** | CR9114（Phillips2021） | 65,536 | h1 **96.0% informative**（h3 10.9% / fluB 0.3% → 排除） | rep×3 + SEM ✓ | **L2** | journal source data |
| 同蛋白宿主轴 | Kosterlitz blaTEM | 32（2⁵） | ×**3 宿主** × cefotaxime 梯度 | ⚠️ | oracle-only | Zenodo（CC-BY-4.0） |
| 同蛋白药物轴 | Mira2015 TEM | 16（2⁴） | **15 种 β-内酰胺** | ⚠️（fitness 语义未解） | oracle-only | **secondary_distribution（GraphFLA）** |
| 20 字母表多任务 | Jalal2020 | 160,000（20⁴） | NBS / parS | 0 缺失，重复未核 | 待核 fitness 语义 | secondary_distribution |
| 条件性 L3 | AncSR1 | 160,000（20⁴） | ERE/SRE × 2 背景 | 2 重复 + SEM | 🔶 数据入口未找到 → **P2** | 待定 |
| 酶-多底物（小空间） | **PTE（源数据）** | 64（2⁶） | **9 底物** | **n=3–10 + tech n=3 ✓** | oracle-only（B ≤ 16） | 作者 GitHub |
| 酶-多环境（小空间） | **MPH（源数据）** | 32（2⁵） | **8 环境** | **三次生物学重复 + SD ✓** | oracle-only | 作者 GitHub + Zenodo |
| 多底物任务面板（L1） | **TEV ProtRec** | 29,716 × ≤134 底物 | **134 底物** | ⚠️ | L1（非组合空间） | Zenodo（CC-BY-4.0） |
| 多底物单突变（L1） | DAOx / AMIE-Wrenbeck | — | 5 / 3 底物 | — | L1 | Zenodo |
| 同家族复制 | CTX-M-14 | 49,096 双突变（17 位点） | CAZ / AMP | σ = 0.27 / 0.28 | robustness | 作者 GitHub |
| oracle-only 其他 | Lunzer2005 / Michael2024 / Wu2020 / Bakerlee2022 / Hall2019 / … | 16–1,022 | 2–12 | 多为 ⚠️ | oracle-only | secondary_distribution |
| 档 B 外部校准集 | HSP82 / CreiLOV / GRB2 / DLG4 | — | 6 / 1 / 1 / 1 | 有 rep / sigma ✓ | 校准 | 聚合 raw |
| 模态对照（L0） | **glmS（RNA）** / Soo2021 | 161,879 行 / 67 位点 | 5 配体浓度 / 2 温度 | stErr + 1 重复 ✓ | L0 | RNAGym raw（CC-BY-4.0） |

**结论**：`dense × multi-task` 的蛋白集合 = **{TEM-1CML, Phillips2023, CR9114(h1), Jalal2020, AncSR1(条件性)}**；酶侧的密集多任务**不存在**，酶的多任务只存在于 ≤64 基因型的小空间。

---

## E-9｜新增待签字条目

| ID | 内容 | 默认 |
|---|---|---|
| **OP-27** | 是否发作者邮件索取 Taft 2022 DML / Shlesinger 2026 serum panel（24 条件 × 组合文库） | 建议发（唯一可能显著加强多任务面板的动作） |
| **OP-28** | L1 的 readiness 对照用 TEV（134 任务）还是 DAOx（5 任务） | TEV 为主、DAOx 保留为最小对照 |
| **OP-29** | Kosterlitz 宿主轴是否纳入 `Corr(EOV_τ1, EOV_τ2)` 分析 | 纳入（oracle 层） |

---

## 状态

- **三条并行检索线程全部结束**；`LANDSCAPE_HUNT_v0.md` 已自包含（§0–§8 + §2.5b–2.5e），除用户要求外不再改动。
- **搜索阶段正式关闭。** 后续任何增量只能来自：① M0 的逐条独立复核 ② OP-27 的作者回信。

## 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| 5 | 2026-09-19（预注册期） | ① 新增 Kosterlitz 多宿主 blaTEM（同蛋白宿主轴）② 更正 PTE 为 9 底物 + 真实重复、MPH 为 8 环境 + 三次重复 ③ 新增 TEV ProtRec（134 底物，L1）④ 穷尽性阴性结论（无组合型多温度蛋白景观）+ 联合交集的最大空间 ⑤ 新增二次分发 provenance 规则与 license 非传递性 ⑥ 阈值放宽观察名单（Cox 2022 / VIM-2 / PAX6 / Taft / Shlesinger）⑦ survey 方法学限制（GitHub API 限流，"查不到 ≠ 不存在"）⑧ **§E-8 最终证据链表（取代 A-3 / B-3 / D-10）** ⑨ 新增 OP-27 / OP-28 / OP-29。**未运行任何 EOV 分析。** |
