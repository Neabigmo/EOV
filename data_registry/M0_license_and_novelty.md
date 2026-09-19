# M0 — License 回源 & TrpB Novelty 核验

| 字段 | 值 |
|---|---|
| 任务 | M0 数据核验的纯文献/网络类子任务（Task A / B / C） |
| 执行时间 | 2026-09-19 |
| 执行者 | 子代理（父代理：Phase I M0） |
| 纪律 | 只读元数据/LICENSE/Data availability/README；**未下载任何数据集本体**；项目目录内只写本文件 |
| 环境限制 | `<PYTHON_BROKEN>` 损坏（`ModuleNotFoundError: No module named 'encodings'`）→ 改用具 `<PYTHON>`（3.12.3）与 PowerShell 完成全部解析 |

> **判定口径**：✅ 已核实 = 我直接读取了原始来源并附原文片段与 URL；🔷 继承 = 由父代理/其他代理先前核实，本次未复算；⚠️ 未核实 = 找不到或无法读取，**不作推断**。

---

# Task A — License 回源（6 项）

## A0. 继承的已核实结论（未复算）

🔷 **TEM-1CML GPL-3.0-or-later｜TrpB CC0-1.0（数据 deposit）｜TEV CC-BY-4.0｜Kosterlitz CC-BY-4.0｜DAOx CC-BY-4.0｜amiE CC-BY-4.0｜glmS CC-BY-4.0｜DHFR MIT｜Hsp90 EMPIRIC CC-BY**

## A1. PTE 磷酸三酯酶

| 项 | 结论 |
|---|---|
| 仓库 LICENSE | ❌ **不存在**（仓库树 15 个文件，无 LICENSE；`raw .../LICENSE` 与 `LICENSE.md` 均 **HTTP 404**） |
| 论文许可 | ✅ **CC BY** |
| 能否再分发 | 论文内容 ✅ 可（署名）；**仓库代码/数据文件许可未声明**（默认保留所有权利）→ ⚠️ **数据文件再分发存疑** |

- 证据 URL（论文）：`https://api.biorxiv.org/details/biorxiv/10.64898/2026.07.02.736193`
- 原文片段：`"title":"Substrate-dependent epistasis probes active site intramolecular wiring","authors":"Buda, K.; Miton, C. M.; Vogt, C.; Tokuriki, N.",...,"date":"2026-07-03","version":"1","type":"new results","license":"cc_by"`
- 摘要佐证规模：`"we profile all 64 combinations of six key mutations in a phosphotriesterase across nine substrates"`
- 证据 URL（无 LICENSE）：`https://raw.githubusercontent.com/karolbuda/rba-error-propagation/main/LICENSE` → 404
- 实测仓库内容：`github/un-normalized-processed/` 下 **9 个底物 CSV**：`2NH, DHC, POE, POM, PTE, PTM, acetate, butyrate, tbbl`（与 arXiv 表/摘要一致）
- 置信度：**高**
- 备注：**同行评审状态** = 仍为 bioRxiv preprint（`type: new results`, v1, 2026-07-03）。Tokuriki 组通常后续发 Nat Commun/PNAS，届时条款会明确。

## A2. CTX-M-14（Palzkill lab）

| 项 | 结论 |
|---|---|
| 仓库 LICENSE | ❌ **不存在**（仓库树 9 个文件，无 LICENSE；`raw .../LICENSE` → 404） |
| 论文许可 | ✅ **CC BY-NC-ND** |
| 能否再分发 | ✅ 可再分发（**署名**），但 **NC（禁商用）＋ ND（禁演绎）** → ⚠️ **我们若发布任何"派生表/改写后的数据"即落入 ND 限制** |

- 证据 URL：Europe PMC `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1073/pnas.2313513121%22&resultType=core&format=json`
- 原文片段：`"title":"Network of epistatic interactions in an enzyme active site revealed by large-scale deep mutational scanning."` ｜ `"pmcid":"PMC10962969"` ｜ `"isOpenAccess":"Y"` ｜ `"license":"cc by-nc-nd"`
- 置信度：**高**
- 备注：README 明确这些文件是 "published in Judge et al." 的配套数据，`fitness_data/` 含每双突变的 counts + fitness + **sigma**。

## A3. Bank2016

| 项 | 结论 |
|---|---|
| 是什么 | **Hsp90**（热激蛋白）上的大内含子适应度景观；**640 个工程突变体**＝6 位点 13 个氨基酸改变突变的全部组合 |
| 论文 | **Bank C, Matuszewski S, Hietpas RT, Jensen JD (2016), "On the (un)predictability of a large intragenic fitness landscape", PNAS 113(49):14085–14090** |
| DOI / ID | `10.1073/pnas.1612676113`｜PMID 27864516｜PMCID PMC5150413 |
| 论文许可 | ❌ **未找到开放许可**：Europe PMC `isOpenAccess = N`，`license` 字段**为空** |
| 能否再分发 | ⚠️ **不可假定可再分发**（无可见许可；GraphFLA 的 MIT 不覆盖该数据） |

- 证据 URL（引文，权威）：GraphFLA arXiv 源码 `icml2024.bib` 与 `main.bbl`
- 原文片段（bib）：`@article{BankMHJ16, author = {Bank, C. and Matuszewski, S. and Hietpas, R. T. and Jensen, J. D.}, title = {On the (un)predictability of a large intragenic fitness landscape}, journal = {Proc. Natl. Acad. Sci. U. S. A.}, volume = {113}, number = {49}, pages = {14085--14090}, year = {2016}}`
- 原文片段（蛋白与规模）：`"640 engineered mutants that represent all possible combinations of 13 amino acid-changing mutations at 6 sites in the heat-shock protein Hsp90"`
- 证据 URL（许可）：Europe PMC（同上 DOI）→ `"isOpenAccess":"N"`, `"license":""`
- 实测文件：`Bank2016a.csv` = `sequences,pos1..pos9,fitness`（640 行量级）；`Bank2016b.csv` = `sequences,F583H,W585L,S586T,A587P,N588A,M589A,fitness`（**2⁶ = 64**，二元）
- 置信度：**高**（引文与蛋白）；**高**（无开放许可）

## A4. Mira2015 TEM（15 个 β-内酰胺 × 2⁴ = 16）

| 项 | 结论 |
|---|---|
| GraphFLA 表中的引文键 | **`MiraCGMSB15`** = Mira, **C**rona, **G**reene, **M**eza, **S**turmfels, **B**arlow |
| 因此对应论文 | ✅ **PLoS One 2015 `10.1371/journal.pone.0122283`**（"Rational design of antibiotic treatment plans…"）—— **不是** MBE 那篇 |
| 该文许可 | ✅ **CC BY**（PMC4422678，isOpenAccess=Y） |
| ⚠️ DOI 更正 | 任务书中标注为"错的" `10.1093/molbev/msad237` **确实不是 Mira 2015**：它 = **Kosterlitz et al. 2023, "Evolutionary 'Crowdsourcing': Alignment of Fitness Landscapes Allows for Cross-species Adaptation of a Horizontally Transferred Gene", MBE 40, PMC10657783, `cc by`**。Mira 2015 的 MBE 那篇真实 DOI 是 **`10.1093/molbev/msv146`**（"Adaptive Landscapes of Resistance Genes Change as Antibiotic Concentrations Change", MBE 32(10), PMID 26113371） |
| MBE `msv146` 许可 | ❌ `isOpenAccess = N`，无 PMCID，`license` 空 → **无开放许可** |
| **底层数据许可是否可见** | ⚠️ **在本项目实际取用路径上不可见**：15 个 CSV **只经 GraphFLA 二次分发**，作者处无 deposit；GraphFLA 的 MIT 只覆盖其仓库，**不覆盖第三方数据** |

- 证据 URL（引文键与规模）：arXiv 源码附录长表：`Mira2015 & \cite{MiraCGMSB15} & TEM-AMP & Mutation & $2^4=16$ ...`（共 15 行，对应 15 个 `Mira2015_TEM_*.csv`，文件名已实测：AM, AMC, AMP, CAZ, CEC, CPD, CPR, CRO, CTT, CTX, CXM, FEP, SAM, TZP, ZOX）
- 证据 URL（PLoS One 许可）：Europe PMC DOI `10.1371/journal.pone.0122283` → `"license":"cc by"`
- 证据 URL（MBE msv146）：Europe PMC → `"isOpenAccess":"N"`, `"license":""`
- 置信度：**高**（归属为 PLoS One，依据 = 引文键作者首字母与 PLoS One 作者列表完全吻合）；**中**（"15 个文件的数值来自该文而非 MBE 文"—— 由引文键推定，未逐值回溯）
- 建议动作：从 **PLoS One 补充材料**取原始数据（CC BY），不要以 GraphFLA 副本作为许可依据。

## A5. MaveDB score sets（VIM-2 等）

| 项 | 结论 |
|---|---|
| 各 score set 的 license 字段 | ✅ **CC0 1.0 (Public domain)**，逐条可见 |
| MaveDB 站点自身条款 | ⚠️ `/docs/terms/`、`/docs/faq/`、首页返回 200 但为 SPA，HTML 中 **0 处** 匹配 `CC0/Creative Commons/license` → **站点级条款未能以文本形式取得** |
| 能否再分发 | ✅ 可（CC0 = 放弃一切权利，无需署名） |
| API 关键更正 | experiment URN = `urn:mavedb:00000073-a`；**score set URN 必须带后缀 `-1`**（`urn:mavedb:00000073-a-1`），否则 404 |

- 证据 URL：`https://api.mavedb.org/api/v1/score-sets/urn:mavedb:00000073-a-1`
- 原文片段：`"license":{"longName":"CC0 (Public domain)","shortName":"CC0","active":true,"link":"https://creativecommons.org/publicdomain/zero/1.0/","version":"1.0","id":1,"recordType":"ShortLicense"}`
- 已逐条确认 CC0 的 score sets：`00000073-a-1`（VIM-2 128 µg/mL AMP 25C）、`00000073-f-1`（VIM-2 4 µg/mL CTX 37C）、`00000040-a-1`（"Deep mutational scan of HSP90, 30C no salt"）、`00000053-a-1`（"Pairwise mutations in PSD95 PDZ3"）
- ⚠️ **对既有记录的更正**：VIM-2 不是"3 β-内酰胺 × 2 温度"，实测 9 个 score set 标题为：128 / 16 / 2 µg/mL AMP @25C、128 / 16 / 2 µg/mL AMP @37C、4 / 0.5 µg/mL CTX @37C、0.031 µg/mL MEM @37C
- 置信度：**高**

## A6. CR9114 数据文件本身（eLife 71393）

| 项 | 结论 |
|---|---|
| eLife 71393 许可 | ✅ **CC BY**（isOpenAccess=Y, PMC8476123） |
| 因此 CDN 源数据 | ✅ 推断同一许可 → **可再分发（署名）** |
| 版本差异注意 | 本次未发现需要区分的版本差异：**71393（2021）与 83628（2023）在 Europe PMC 均报 `cc by`**；88737（2024）亦为 `cc by` |

- 证据 URL：Europe PMC DOI `10.7554/eLife.71393` → `"license":"cc by"`；`10.7554/eLife.83628` → `"license":"cc by"`；`10.7554/eLife.88737` → `"license":"cc by"`
- 置信度：**高**（文章许可）；**中**（"CDN 上 `fig1-data1` 文件随文章 CC BY"—— eLife 的 source data 属文章组成部分，且 `fig1-data1-v3.xlsx` 由文章页面提供，但**未找到 eLife 关于 source data 单独许可的明文**）
- 建议：在再分发声明中写"数据取自 eLife 文章 83628/71393 的 source data，文章许可 CC BY 4.0"

## A7. 汇总（可直接填入 DATA_AUDIT 的 license 列）

| 数据集 | 论文许可 | 数据文件许可 | 可再分发 |
|---|---|---|---|
| TEM-1CML | (Nat Commun) | GPL-3.0-or-later 🔷 | ✅ |
| Phillips2023 (eLife 83628) | **CC BY** ✅ | 随文章（CC BY，置信中） | ✅ 署名 |
| CR9114 (eLife 71393) | **CC BY** ✅ | 随文章（CC BY，置信中） | ✅ 署名 |
| TrpB | **CC BY-NC-ND** ✅ | CC0-1.0 🔷 | ✅ |
| DAOx / TEV / Kosterlitz / amiE / glmS | CC-BY-4.0 🔷 | 同 | ✅ 署名 |
| **PTE** | **CC BY** ✅（preprint） | ❌ 仓库无 LICENSE | ⚠️ 存疑 |
| **CTX-M-14** | **CC BY-NC-ND** ✅ | ❌ 仓库无 LICENSE | ⚠️ 禁商用/禁演绎 |
| **Bank2016** | ❌ 无开放许可 ✅ | ❌ 未见 | ⚠️ 不可假定 |
| **Mira2015 TEM** | **CC BY** ✅（PLoS One） | ❌ 作者无 deposit；仅 GraphFLA 二次分发 | ⚠️ 需回源 PLoS One 补充材料 |
| **MaveDB score sets** | — | **CC0 1.0** ✅ | ✅ |
| DHFR / Hsp90 EMPIRIC | MIT / CC-BY 🔷 | 同 | ✅ |

---

# Task B — TrpB Novelty 核验（P0-9）

**论文**：Johnston et al., PNAS 2024, `10.1073/pnas.2400439121`，"A combinatorially complete epistatic fitness landscape in an enzyme active site"，PMID 39074291，**PMC11317637**。
**取得方式**：Europe PMC 全文 XML（`isOpenAccess=Y`, `inEPMC=Y`）→ `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11317637/fullTextXML`（154,590 B，已解析 78,217 字符纯文本）。
**论文许可**：`cc by-nc-nd`（Europe PMC）。

## 四条主张逐条裁决

| # | 主张 | 结论 | 原文片段 |
|---|---|---|---|
| **1** | 从每一个起点基因型出发的 max fitness ECDF/分布 | ✅ **已确认** | "**(E) The max fitness achieved from each starting point is plotted as a violin and ECDF for each of the three directed evolution simulation methodologies. We show the results for the 4-site-saturation landscape on TrpB and on GB1.**" |
| **2** | 3 种 in-silico directed evolution 模拟 | ✅ **已确认** | "**Method 1) site-saturation mutagenesis (SSM) at each of the four sites in parallel followed by recombination of the best variants at each site; Method 2) single-step sequential SSM, using the best variant at one site as the parent for the next until all four sites have been examined, starting from any of the sites; and Method 3) SSM at each site in parallel followed by direct synthesis of the top N additivity-predicted variants—96 variants in this case**" ｜ "**( D ) Three different baselines of directed evolution methodologies.**" |
| **3** | local-optima / accessible-path 分析 | ✅ **已确认** | "**For TrpB, there are 520 total optima (5.3% of the active variants), one of which is the global optimum, AIKG**" ｜ "**if no deleterious steps are allowed, ~20% of the starting points cannot reach the global optimum, AIKG, via any single-step path**" ｜ "**( C ) An empirical cumulative distribution function (ECDF) built from all possible starting points and displaying the fraction of paths reaching the top, given a specified cutoff.**" |
| **4** | 注入噪声的 null model | ✅ **已确认**（且**对 null model 也跑了同一套 DE 模拟**） | "**compared all of these effects to a null model built from an additive landscape injected with noise based on that of the TrpB landscape ( Construction of a Null Model )**" ｜ "**Construction of a Null Model. … we fit an exponential distribution to the distribution of differences in fitness between the two replicates of the TrpB landscape and sampled from it, randomly adding or subtracting the value from the fitness.**" ｜ "**The same simulations were run for the null model … ( SI Appendix , Fig. S31 and Table S15 )**" |

## 可直接复用的实现细节（他们要我们复用的部分）

| 要素 | 已核实内容 |
|---|---|
| **起点集合** | **每一个被判定为 active 的变体**；TrpB 中 = **9,783 个**（"starting from one of the top 9,783 variants in either landscape (the number of active variants in the TrpB landscape)"） |
| **Method 1** "SSM combine best" | 对每个 active 变体，在四个位点各自独立做全部 19 种替换 → 每位点取最佳氨基酸 → 构建重组序列；报告 {初始序列, 全部单位点变体, 重组件} 中的最佳值 |
| **Method 2** "Single-step SSM greedy walk" | 对每个 active 变体 × **每一种位点采样顺序（M! = 4! = 24）**，迭代 M 轮 SSM；报告末态变体 fitness |
| **Method 3** "SSM calculate and test top N" | 每个 active 变体做 M×19+1 个数据点 → 加性模型预测全部 20^M 组合 → **直接合成 top N（N = 96）**；报告最大值。**N 被扫描过**（SI Fig. S32：增大 N 略有改善） |
| **随机性/重复** | ⚠️ **无随机初始化重复**：采样是**穷举式**（"Because we enforced the sampling of every single substitution during the SSM steps"）。这与"多次随机初始化求平均"是不同设计 |
| **附加对照** | 同一套 Method 1/2/3 也在 **GB1** 上跑过（Fig. 3F） |
| **数据/代码可得性** | "**Data and analysis software have been deposited in CaltechDATA (software and processed data are available at https://doi.org/10.22002/h5rah-5z170) and the NCBI Sequence Read Archive (raw fastq files are available at SRA Accession No. PRJNA1127511)**" |
| 实验重复 | "two replicate flasks"；"159,129 variants (99.45% of the total library) had sufficient sequencing coverage for quantification in **both replicate experiments**" |

## 对 Phase I novelty 定位的直接影响（供父代理裁决）

- 他们已发布的是：**单任务**下、**逐起点**、在 **3 种确定性策略**下的 **max fitness 分布**，外加 **noise null model 的同一套模拟**。
- 因此"逐起点的 `R_{B,π}(x,τ)`"本身 **已不再是新增量**；我们的可辩护增量收窄为：**(i) 任务维度 holdout**、**(ii) selection regret（决策损失）而非 max fitness 分位数**、**(iii) `Corr(EOV_τ1, EOV_τ2)` 的跨任务稳定性**、**(iv) 预算 B 作为估值轴的系统扫描（他们只对 N 做了有限扫描，且不跨任务）**。
- ⚠️ 他们的**可及性分析**（0–100% 允许下降步长的扫描 + 全体起点的路径 ECDF）与我们 `R_k^adaptive` 概念**高度重叠**，必须显式列为 baseline。

---

# Task C — AncSR1 数据入口

## C1. 已找到的部分 ✅

| 项 | 结论 | 证据 |
|---|---|---|
| 数据托管 | ✅ **Dryad `10.5061/dryad.jsxksn0hk`** | Metzger 2024 eLife Data availability 原文："**Initial and intermediate data files can be found at dryad ( https://doi.org/10.5061/dryad.jsxksn0hk )**" |
| 代码托管 | ✅ `https://github.com/JoeThorntonLab/DBD.GeneticArchitecture`（README 复述同一 Dryad 链接） | 同上 + README 原文 |
| Dryad 记录元数据 | 标题 "Epistasis facilitates functional evolution in an ancient transcription factor"；作者 Metzger / Park / Starr / Thornton；**version 3**；`versionStatus = submitted`；**20 个文件** | `https://datadryad.org/api/v2/versions/272141/files` |
| 数据集本体与重复 | ✅ 原文确认：**"all 160,000 combinations of 20 amino acids at four sites"**；**"transformed into yeast strains carrying either an ERE- or SRE-driven GFP reporter and functionally characterized using a FACS-based Sort-seq assay"**；**"concordance in the activation class assigned to each variant between replicates was >97% … (R²=0.62 for functional variants)"** | eLife 88737 全文（CC BY） |
| 文章许可 | ✅ eLife 88737 = **CC BY** | Europe PMC |

## C2. 未找到的部分 ⚠️（不作推断）

| 项 | 状态 |
|---|---|
| **per-variant × per-element 的整洁荧光表（CSV/TSV）** | ⚠️ **未找到机器可读 deposit**。Dryad 的 20 个文件全部是 **R `.rda` 对象与 1 个 `.gexf` 图**，例如 `DT.JOINT.rda`（15.9 MB）、`DT.11P.CODING.rda`（18.0 MB）、`AA.SEQ.rda`、`EFFECT.TABLE.TE.rda`、`ALL.ACT.gexf`。**没有 CSV**。 |
| 能否确认 `.rda` 内含逐变体逐元件的均值/SEM | ⚠️ **无法确认**：读取 `.rda` 需要 R，本机 **未安装 R**（`Rscript` NOT FOUND）。**未下载该数据集本体**（遵守任务约束） |
| Starr 2017 原始 deposit 位置 | ⚠️ **未找到**。Nature `10.1038/nature23902`：Europe PMC `isOpenAccess=Y` 但 **`license` 字段为空**；fullTextXML 请求返回 **HTTP 500**（作者手稿不提供全文）；nature.com 与 link.springer.com 均被 `idp` 重定向拦截 |
| 该 Dryad 是否等同 Starr 2017 的原始表 | ⚠️ **不等同（按标题与文件形态判断）**：它是 **Metzger 2024** 的"initial and intermediate data files"，eLife 原文只说这些数据"**come from** a previously published deep mutational scan of AncSR1 (Starr et al., 2017)" |
| Dryad 版本状态 | ⚠️ `versionStatus = submitted`（非 `published`）——含义未核实 |

## C3. 一条对建模有直接影响的实测发现

eLife 88737 原文对"序列空间"的定义是：

> "**The RH sequence space consists of all 160,000 possible sequences … with edges connecting nodes that can be directly interconverted by a single nucleotide change given the standard genetic code.**"

→ **AncSR1 的网络是"单核苷酸可互换"，不是氨基酸 Hamming-1。** 这与 TEM-1（18 个替换事件）和 Phillips2023（2¹⁶ 二元）都不同。若纳入 AncSR1，`N_k(x)` 的定义必须另立一套（或至少显式声明用核苷酸邻接）。

## C4. 索取邮件草稿（可直接发送）
> **说明（release 版已删除草拟外发邮件原文）**：
> 当时的动作是「拟向作者索取 per-variant 表」。原文含第三方个人邮箱，按 release 隐私规则移除；
> 该动作的**科学结论**（数据入口与许可的核验结果）不受影响，见本节其余部分。
---

# 仍未解决 / 需人工动作

| # | 事项 | 为什么阻塞 | 建议动作 |
|---|---|---|---|
| 1 | **AncSR1 逐变体逐元件表**（`.rda` 内容或 CSV） | 决定 AncSR1 能否作为"判据 ④ 内建"的 L3 | 发 C4 邮件；或在本机装 R 后读取 Dryad `.rda`（需下载约 130 MB，**当前约束下未做**） |
| 2 | **PTE / CTX-M-14 / Bank2016 / Mira2015 的底层数据再分发权** | 三个仓库**无 LICENSE**，Bank2016 论文无开放许可，Mira2015 仅 GraphFLA 二次分发 | ① Mira2015 → 改用 PLoS One 补充材料（CC BY）；② Bank2016 → 视为"仅内部使用，不再分发"；③ PTE/CTX-M-14 → 联系作者或等正式发表 |
| 3 | **eLife source data 是否随文章 CC BY 的明文** | 影响 Phillips2023/CR9114 的再分发措辞 | 查 eLife 的 "Terms and conditions / source data" 页面（本轮未取得） |
| 4 | **MaveDB 站点级条款文本** | SPA 渲染，HTML 无文本 | 用浏览器打开 `/docs/terms/` 人工确认；或只依赖逐 score set 的 `license` 字段（已确认 CC0） |
| 5 | **TrpB 论文 CC BY-NC-ND vs 数据 CC0-1.0 的并存** | 影响"能否再分发其处理后的数据" | 数据用 CaltechDATA 的 CC0 声明；论文文本引用遵循 NC-ND |

## 附：本次对既有冻结记录的两条更正（**未改动任何冻结文件**）

1. **Jalal2020 不是"同一蛋白 × 2 个任务"**：GraphFLA 论文表格中该引文键 `JalalTSCLTNLL20` 的两行，subject 分别是 **ParB** 与 **Noc**（两个不同的 DNA 结合蛋白，各自 20⁴ = 160,000）。文件名为 `Jalal2020_parS.csv` 与 `Jalal2020_NBS.csv`（指 DNA 靶标而非同一空间）。实测两文件的 fitness 数值不同（同为 `AAAA`：NBS = −11.051，parS = −10.772）。→ 应作为**两个单任务 20⁴ 景观**，不可计入"dense × multi-task"集合。
2. **`10.1093/molbev/msad237` 不是错的 DOI，而是另一个数据集**：它 = Kosterlitz et al. 2023（"Evolutionary 'Crowdsourcing'…", MBE, **CC BY**）。Mira 2015 的 MBE 论文真实 DOI 为 `10.1093/molbev/msv146`（**无开放许可**）；而 GraphFLA 的 15 个 `Mira2015_TEM_*` 对应的是 **PLoS One `10.1371/journal.pone.0122283`（CC BY）**。
