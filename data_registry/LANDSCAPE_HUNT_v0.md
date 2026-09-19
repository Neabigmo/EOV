# LANDSCAPE_HUNT_v0

**DATA_AUDIT 最高优先级缺口搜索结果：寻找第二个 multi-task dense protein landscape**

- 日期：本次会话
- 执行范围：只做检索与核实，未写分析代码，未把任何数据集落入项目目录
- 唯一写入文件：本文件
- 研究问题：*TEM-1 是不是特例？* → 需要 ≥1 个满足 4 条硬判据的第二个 multi-task dense protein landscape

---

## 0. 结论摘要（先读这段）

**能找到。而且比预期好得多。**

主战场 **GraphFLA**（NeurIPS 2025 Spotlight，MIT license）不只是"算了 20 个特征"——它把 **155+ 个 combinatorially complete landscape 的原始 CSV 直接公开在一个 GitHub 仓库里**，格式统一为 `sequences,pos1..posN,fitness`，可以用 `raw.githubusercontent.com` 直接取，无需申请、无需爬虫、无需登录。

其中存在**同一基因型空间、多个任务条件**的成组文件（这是本次搜索的核心发现），最强的三个：

| 排名 | 候选 | 规模 | 任务数 | 缺失率 | 判定 |
|---|---|---|---|---|---|
| **1** | **Phillips2023 / 流感 HA 受体结合位点 × 抗 CH65 抗体** | **65,536 完整 2^16，16 位点** | **3（SI06 / MA90 / G189E）** | 6–28 / 65536（≈0.01–0.04%） | **L3 最佳** |
| **2** | **Phillips2021 / 流感 HA × CR9114 抗体** | **65,536 完整 2^16，16 位点** | **3（h1 / h3 / fluB）** | 1–442 / 65536 | **L3** |
| **3** | **Moulana2023 + Moulana2022 / SARS-CoV-2 RBD × 抗体** | **32,768 完整 2^15，15 位点** | **5（CB6 / CoV555 / REGN10987 / S309 / ACE2）** | **任务间差异极大：S309 = 0%，CB6 = 49.6%** | **L3（需处理缺失）** |

**但有一个必须先说清的硬缺口（现已被部分解决）**：

> **判据 4（重复测量 / 可估噪声）在 GraphFLA 发布的 CSV 中不满足。**
> 我逐个检查了表头与重复行：文件只有 `sequences,pos1..posN,fitness` 一列 fitness，**没有任何 replicate 列、没有 SD 列**；在我统计的 80 个文件中 unique genotype 数 = 行数（无重复基因型），因此**无法从 GraphFLA 文件内部估计噪声**。
>
> ✅ **已解决，而且比预期好（见 2.8 节，已亲自拉取表头核实）**：
> - **Phillips2021（CR9114 / CR6261）的 eLife source data 自带 3 次生物学重复 + 每个 genotype×抗原的 SEM**，65,536 行 = 字面完整 2^16 超立方体，3 个抗原任务。**判据 4 ✅。**
> - **AncSR1**（Starr/Picton/Thornton, *Nature* 2017）另有 2 次独立 FACS-seq 重复 + 可估 SEM（但 processed 表位置**未找到**）。
> - **TEM-1** 有 triplicate（SD < 10%）。
>
> ⚠️ 更正我先前的判断：**GraphFLA 的 CSV 是派生提取（单列 fitness），但上游原始数据保留了重复。** → **判据 4 不再是"碰运气回源"，而是一个已确认存在、有确切 URL 的下载动作。** 唯一新增的真陷阱是**滴定边界钉扎行（`*_sem = 0` 表示"未测到"而非"无噪声"），必须在算噪声之前剔除。**

**另外一条会直接改变 Phase I 设计的发现：**

> **TEM-1 的 future task 不是 1 个。** 仓库里有 `Mira2015_TEM_*` **15 个文件 = 同一个 2^4 = 16 基因型空间 × 15 种 β-内酰胺抗生素**。虽然空间只有 16 个基因型（不能模拟 B=96 的 DE），但它给 TEM-1 提供了**真正的多任务面板**，可以让 "TEM-1 只有一个 future task" 这个弱点部分解除。

**你指定的三个线索，最终裁决（详见 2.7 节）：**

| 线索 | 裁决 |
|---|---|
| **FLIP2** | ❌ **排除**。44 个 CSV **全部没有 condition 列**；GB1 的两个文件逐字节同值 → **是 distribution-shift 切分，不是多任务数据集**。为零投入。 |
| **DHFR-TMP 梯度** | ⚠️ **部分**。判据 1 ✗（1,000+ 个不同骨架 × 每骨架 ~18 个随机突变，无组合覆盖）。9 个条件里 **6 个是同一药物的不同浓度** → **是很弱的 future task 轴**。数据可用（Figshare，**MIT**）。 |
| **MBE `msag106`** | ⚠️ **部分（硬伤）**。**≈11 个真实环境 ✅、有重复 ✅，但严格单突变 → 判据 1 硬性 ✗。** 附带价值：它研究的正是 **TEM-1**，可补一条环境任务轴。 |

**并且在线索之外捞到四个更强的候选：**

- **⭐⭐ `CR9114 / CR6261`（Phillips et al., *eLife* 2021，原始 source data）** —— **完整 2^16 = 65,536 × 3 个抗原（H1/H3/fluB）× 3 次生物学重复 + SEM**（CR6261：2^11、2 抗原）。**判据 1/2/3/4 全部满足**，且**已核实可下载**。→ **这是"第二个 multi-task dense landscape"目前最干净的答案。**
- **⭐⭐ `AncSR1`（Starr, Picton & Thornton, *Nature* 2017）** —— **4 位点完整 20^4 = 160,000 × {ERE, SRE} × 2 背景 × 2 次独立 FACS-seq 重复 + SEM**。判据 1/2/4 满足，**判据 3 待核实**（未找到机器可读 deposit）。
- **⭐ `Jalal2020_NBS` / `Jalal2020_parS`（GraphFLA 仓库内，已实测 160,000 行 × 2）** —— **4 位点 × 20 氨基酸全字母表 + 完整 + 2 个 DNA 结合位点任务**，与 GB1（149,361）/TrpB4（159,129）**空间结构同类** → DE/预算机器可**原样复用**。
- **⭐⭐ `glmS` 核酶配体滴定（RNAGym **RAW** 包，Andreasson 2020）** —— **67 位点、穷举单+双突变、5 个配体浓度、每次测量带 `_stErr`、CC-BY-4.0**。**全 survey 唯一"processed 之外"四条全满足的 entry**，但**是 RNA**，只能作**模态对照**，不能回答"TEM-1 是不是蛋白特例"。详见 §2.5d。

### ⚠️ 最重要的结构性结论（**v1 的措辞已被修正，见下**）

对 **ProteinGym（217 processed + 213 raw）/ RNAGym（70 processed + raw 包）/ CIS-BP（及 Codebook）/ MaveDB（API 全量 2,063 个 experiment，其中 35 个有 ≥2 个 score set）** 做了穷尽检索。

> **【修正后的准确表述】**
>
> **① 对蛋白系统：两轴在打包资源里确实互斥。**
> - 所有深度组合多突变数据集都是**单条件**；
> - 所有多条件数据集都是**单突变或随机文库**；
> - **ProteinGym / CIS-BP / MaveDB 中没有任何 entry 同时满足 4 条判据。**
>
> **② 但"任何资源里都不存在"这句话是错的——有两个例外：**
> - **⭐ RNA 侧例外**：**RNAGym 的 RAW 包里的 `glmS` 核酶配体滴定 DMS 满足全部 4 条判据**（67 位点、穷举单+双突变、**5 个配体浓度**、每次测量都有 `_stErr`、CC-BY-4.0、无需注册）。见 §2.5d。
> - **⭐ 蛋白侧例外**：交集**存在，但只在原始文献/原始 deposit 里**，不在打包 benchmark 里——即 **GraphFLA 从文献 curation 出来的成组文件**（Phillips2021 CR9114 / Phillips2023 / Moulana2023 / Mira2015 / Lunzer2005 / Anderson2021 …），以及 **eLife CDN 上的原始 source data（带 triplicate + SEM）**。
>
> **③ 一个必须记住的方法学教训**：**RNAGym 的 processed 版本把整个配体浓度序列塌缩成单一 `DMS_score` 列**，因此"processed 无多条件"这个观察**完全不能推断"原始数据无多条件"**。这与 §3.4 的教训是同一个：**判据 3/4 的核实对象必须是原始 deposit，不能是聚合仓库的再分发版本，也不能是 processed 版本。**

**这反过来对我们的定位是好事**：它说明"多任务 × 密集组合"不是"再找一个数据集"的问题，而是**打包 benchmark 结构性缺失的一类数据**。**同时也意味着：`data_registry/DATA_AUDIT.md` 不能靠"下载一个 benchmark"来完成，必须以逐文献 curation 的方式建立。**

---

## 1. 核实方法（先说清哪些是"已核实"）

| 做法 | 说明 |
|---|---|
| ✅ 已核实 | 下载 GraphFLA 论文的 arXiv LaTeX 源码（arXiv:2510.24826v1 的 `src` 包）并**直接读取了论文里那张 155 行 landscape 总表的原始 TeX**（`sections/appendix.tex` 第 833–1008 行的 `longtable`，label `tab:datasets`）。因此下表的"作者/文献/空间/规模"来自论文原文，不是二手转述。 |
| ✅ 已核实 | 用 GitHub 目录页内嵌 JSON 抓取了 `data/BioSequence/` 的**完整文件清单：163 个 CSV**。 |
| ✅ 已核实 | 对每个关键文件用 HTTP `Range: bytes=0-119` **只取表头 + `Content-Range` 总字节数**，确认列结构。 |
| ✅ 已核实 | 对 44 个关键文件做了**内存内行数统计**（下载到内存、计数、不落盘、不留档），得到精确的 `rows` / `unique sequences` / `fitness 为空(NaN/NA)` 计数。**项目目录内没有写入任何数据集文件。** |
| ✅ 已核实 | GraphFLA 数据托管位置、license、PyPI 包信息、论文中"数据已随仓库发布"的 checklist 原文。 |
| ⚠️ 未核实 | 各数据集的**原始论文级 license**；原始数据源的 replicate 结构；`pos1..posN` 列的完整取值域（仅抽样确认）；GraphFLA 之外候选（FLIP2 / DHFR-TMP / MBE msag106）的结论由并行检索线程负责，本文只标注状态。 |

**核心 URL**

- 论文：<https://arxiv.org/abs/2510.24826>（NeurIPS 2025 **Spotlight**，"Augmenting Biological Fitness Prediction Benchmarks with Landscapes Features from GraphFLA"）
- 论文 HTML 全文：<https://arxiv.org/html/2510.24826v1>
- 代码与数据仓库：<https://github.com/COLA-Laboratory/GraphFLA>
- **landscape CSV 目录（主战场）**：<https://github.com/COLA-Laboratory/GraphFLA/tree/main/data/BioSequence>
- raw 取数模板：`https://raw.githubusercontent.com/COLA-Laboratory/GraphFLA/main/data/BioSequence/<文件名>.csv`
- PyPI 包：`graphfla` 0.3.0（<https://pypi.org/project/graphfla/>，MIT，依赖仅 numpy/pandas/python-igraph/scikit-learn/scipy/rich/joblib）

> ⚠️ 注意：**PyPI 的 wheel 只有 ~166 KB，不含数据。** 155 个 landscape 只在 GitHub 仓库里。

---

## 2. 候选表

**图例**：`邻域密度` 写作 `空间是否完整 / 每节点 Hamming-1 度数`。
`满足4条判据` 中，**判据 4 对全部 GraphFLA 条目一律为"部分（未满足）"**，原因见第 0 节；因此"全部满足"列不会出现"是"，这是**诚实的裁决**，不是遗漏。

### 2.1 第一梯队 —— multi-task + dense（同一基因型空间，多个任务）

| 名称 | 蛋白/系统 | 位点数 | 变体数 | 任务数 | 任务类型 | 邻域密度 | 数据托管 (URL) | license | 满足4条判据? | 置信度 | 待核实点 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Phillips2023** (SI06 / MA90 / G189E) | 流感 HA 受体结合位点 (CH65 抗体) | 16 (二元) | **65,536 × 3 = 196,608** | **3** | 3 个不同抗体/病毒背景的结合亲和力 | **完整 2^16**，deg = 16 | `data/BioSequence/Phillips2023_{SI06,MA90,G189E}.csv` | 仓库 MIT；原始论文 eLife 12:e83628 | 1✓ 2✓ 3✓ **4✗** | **高** | 原始数据是否有 replicate；fitness 单位与"escape/affinity"语义 |
| **Phillips2021** (CR9114: h1 / h3 / fluB) | 流感 HA | 16 (二元) | **65,536 × 3 = 196,608** | **3** | 3 个抗体/毒株背景 | **完整 2^16**，deg = 16 | `.../Phillips2021_CR9114_{h1,h3,fluB}.csv` | 同上；eLife 10:e71393 | 1✓ 2✓ 3✓ **4✗** | **高** | 同上 |
| **Phillips2021** (CR6261: h1 / h9) | 流感 HA | 11 (二元) | 1,917 × 2 = 3,834 | 2 | 2 个抗体背景 | **非完整**：2^11 = 2,048，实测 1,917（93.6%） | `.../Phillips2021_CR6261_{h1,h9}.csv` | 同上 | 1△ 2✓ 3✓ **4✗** | **高** | 缺失 131 个基因型的原因 |
| **Moulana2023** (CB6 / CoV555 / REGN10987 / S309) | SARS-CoV-2 Omicron BA.1 RBD | 15 (二元) | **32,768 × 4 = 131,072** | **4** | 4 个单抗逃逸/结合 | **完整 2^15**，deg = 15 | `.../Moulana2023_{CB6,CoV555,REGN10987,S309}.csv` | 仓库 MIT；eLife 12:e83442 | 1✓ 2✓ 3✓ **4✗** | **高** | **任务间缺失率差异巨大**（见下）；跨任务交集大小 |
| **Moulana2022_ACE2** | 同上（ACE2 受体结合） | 15 (二元) | 32,768 | 1（+4 可合并） | 受体结合 | 完整 2^15 | `.../Moulana2022_ACE2.csv` | eLife/Nat Commun 13:7011 | 1✓ 2✓ 3✓ **4✗** | **高** | 与 Moulana2023 联合成 5 任务面板 |
| **⭐ `Jalal2020_NBS` / `Jalal2020_parS`** | **ParB（蛋白-DNA 结合）** | **4 × 20 氨基酸** | **160,000 × 2 = 320,000** | **2** | **两个不同 DNA 结合位点（NBS / parS）** | **完整 20^4，deg = 4×19 = 76** | `.../Jalal2020_{NBS,parS}.csv` | 仓库 MIT；Jalal et al. 2020 | 1✓ 2✓ 3✓ **4✗** | **高** | **唯一一个"20 氨基酸全字母表 + 完整 + 双任务"的蛋白景观——见下方说明** |

> **⭐ 为什么 `Jalal2020` 可能是比 Phillips2023 更重要的发现（本轮最后阶段才捞到）**
>
> 已核实：两个文件各 **160,000 行 / 160,000 unique / 0 缺失**，列结构 `sequences,pos1..pos4,fitness`，`pos` 取值是**氨基酸字母**（`AAAA, AAAC, …`），fitness 为负值 log 尺度（-11.05 ~ -10.52 起）。
>
> 这意味着它是 **20^4 = 160,000 的完整四维氨基酸立方体 × 2 个任务**——**与 GB1（149,361）和 TrpB4（159,129）的空间结构完全同类**。
>
> 三个直接后果：
> 1. **DE 模拟基础设施可以原样复用**。GraphFLA 论文的 DE 分析正是用"20^3 / 20^4 饱和蛋白景观"做的；SSMuLA 的 DE/MLDE 也是。我们的 `search_policies.py` 可以对 GB1 / TrpB4 / **Jalal2020** 用**同一套代码**，省掉一整个适配层。
> 2. **它把"任务"从'不同结合伙伴'拉回到"同一蛋白、两个真实功能位点"**，比抗体逃逸的语义更接近 TEM-1。
> 3. 每个节点 **deg = 76**（4 位点 × 19 种替代），邻域结构丰富，`N_k(x)` 与预算型搜索都有充足空间。
>
> **代价**：只有 **2 个任务** → leave-one-out 只能得到 1 个 held-out 任务，无法单独支撑"跨 future context 复现"。**建议用法：把 Jalal2020 与 Phillips2023 组合**——前者提供"20 字母表 + 酶同类空间 + 2 任务"，后者提供"3 任务 + 近零缺失"。
>
> **待核实**：NBS 与 parS 的确切定义（两个 DNA 序列？两个结合位点？）、原始论文出处与 license、fitness 是否为 log 结合亲和力。

**Moulana2023 各任务的精确缺失（已核实，行数均为 32,768，unique 均为 32,768）：**

| 文件 | 字节 | rows | unique | fitness 缺失行 | 缺失率 |
|---|---|---|---|---|---|
| `Moulana2023_S309.csv` | 2,089,985 | 32,768 | 32,768 | **0** | **0%** |
| `Moulana2022_ACE2.csv` | 2,087,287 | 32,768 | 32,768 | 203 | 0.6% |
| `Moulana2023_REGN10987.csv` | 1,941,566 | 32,768 | 32,768 | 9,082 | 27.7% |
| `Moulana2023_CoV555.csv` | 1,877,584 | 32,768 | 32,768 | 12,901 | 39.4% |
| `Moulana2023_CB6.csv` | 1,817,904 | 32,768 | 32,768 | **16,257** | **49.6%** |

> 含义：这是**"同一空间、不同任务测量的完整度不同"**。leave-one-task-out 时，训练任务与 held-out 任务的**可比较基因型交集**会显著小于 32,768，且缺失不是随机的（低亲和力变体更可能测不到）。**这是必须预先写进协议的偏差来源。**

**Phillips2021/2023 的缺失（已核实，行数均 = unique）：**

| 文件 | 字节 | rows | 缺失行 |
|---|---|---|---|
| `Phillips2021_CR9114_h1.csv` | 4,344,750 | 65,536 | 442 |
| `Phillips2021_CR9114_h3.csv` | 3,573,818 | 65,536 | 1 |
| `Phillips2021_CR9114_fluB.csv` | 3,476,274 | 65,536 | 2 |
| `Phillips2023_SI06.csv` | 4,012,926 | 65,536 | 28 |
| `Phillips2023_MA90.csv` | 4,443,170 | 65,536 | 6 |
| `Phillips2023_G189E.csv` | 4,315,048 | 65,536 | 6 |

> **Phillips2023 是三个任务都近乎完整（0.01–0.04% 缺失）的唯一组合** → 若只选一个"第二个 multi-task dense protein landscape"，选它。
>
> **一个重要推论（由算术保证，不是假设）**：每个文件都是 16 个二元位点、且 unique 序列数恰好 = 2^16 = 65,536，因此**每个文件都覆盖了完整立方体，三个文件的基因型集合必然完全相同**。同理 Moulana 系列（15 位点、32,768 = 2^15）五个文件共享同一完整空间。→ **"同一空间"这一点已经成立，不需要再验证交集里有没有缺基因型**（需要验证的只是 pos 列取值域确为 {0,1}，见核实清单）。

### 2.2 第二梯队 —— 真·多环境，但空间小（≥3 位点、完整、多任务，变体数 < 10^4）

这些**满足判据 1 的"≥3 位点 + 组合完整"**，但每个节点的邻域极小，**不足以模拟 B=96/384 的 DE**；可用于"任务迁移 / 起点效应 / 环境×上位效应"，不能作为 DE 预算研究的主数据。

| 名称 | 蛋白/系统 | 位点数 | 变体数 | 任务数 | 任务类型 | 邻域密度 | 满足4条判据? | 置信度 | 待核实点 |
|---|---|---|---|---|---|---|---|---|---|
| **Mira2015_TEM_** *(15 个文件)* | **TEM-1 β-内酰胺酶（与我们主数据同一蛋白！）** | 4 | 16 | **15** | 15 种 β-内酰胺抗生素 | 完整 2^4，deg=4 | 1△ 2✓ 3✓ 4? | **高** | 各缩写对应药物；原始论文是否有重复测量 |
| **Lunzer2005** (fitness / nad / nadp) | 异丙基苹果酸脱氢酶 (IMDH) | 6 | 512 | **3** | 适应度 + NAD + NADP 两种辅酶活性 | 完整 2^6，deg=6 | 1✓ 2✓ 3✓ 4? | **高** | "fitness" 与两个生化活性的关系 |
| **Anderson2021_MPH_** *(6 个文件)* | 甲基对硫磷水解酶 (金属酶) | 5 | 32 | **6** | 6 种金属离子 (Ca/Cd/Co/Cu/Mg/Mn) | 完整 2^5，deg=5 | 1✓ 2✓ 3✓ 4? | **高** | 注意 pos2 存在 `-`（缺失/indel 状态） |
| **Michael2024_** *(5 个文件)* | 噬菌体 λ 受体识别 | 9 | 512 | **5** | base / LamB / Lspec / OmpF / Ospec（不同受体/宿主） | 完整 2^9，deg=9 | 1✓ 2✓ 3✓ 4? | **高** | 论文内引用名为 Doud2024，文件名却是 Michael2024（同一人，命名不一致）；base 有 82 个缺失 |
| **Wu2020_** *(7 个文件)* | 流感 H3N2 抗原位点 B | 6 | 576 | **7** | 7 个病毒株背景 | 完整 2^6×9? 实测 576，deg 待定 | 1✓ 2✓ 3✓ 4? | 中 | 576 = 2^6×3^2，非标准立方体；需确认等位集 |
| **Bakerlee2022_** *(12 个文件)* | 酿酒酵母（10 个位点） | 10 | 1,022 | **12** | 6 环境 × 2 倍性 (hap/hom) | 2^10 = 1,024，实测 1,022 | 1✓ 2✓ 3✓ 4? | **高** | 缺 2 个基因型；是酵母整体适应度非蛋白 |
| **Hall2019_** *(8 个文件)* | 微生物 5 位点 | 5 | 32 | **8** | 8 种培养基/环境 | 完整 2^5，deg=5 | 1✓ 2✓ 3✓ 4? | **高** | 物种与"位点"定义 |
| **Guerrero2019_** *(9 个文件)* | 抗生素抗性（3 位点） | 3 | 8 | **9** | 3 物种 × 3 蛋白稳态条件 (WT/GroEL/LON) | 完整 2^3，deg=3 | 1△ 2✓ 3✓ 4? | **高** | 空间过小（8 个基因型），仅作概念验证 |
| **Frohlich21_OXA-48_** *(6 个文件)* | **OXA-48 β-内酰胺酶** | 4 | 16 | **6** | CAZ (ceftazidime) × 3 轨迹 + PIP (piperacillin) × 3 轨迹 | 完整 2^4，deg=4 | 1△ 2✓ 3✓ 4? | 中 | 来源是**博士论文**非期刊；轨迹是否为独立任务 |
| **Khan2011Flynn2013_** *(3 个文件)* | DM25 系统 | 5 | 32 | **3** | 3 种环境 (DM25 / +EGTA / +guanazole) | 完整 2^5，deg=5 | 1✓ 2✓ 3✓ 4? | 中 | 分子实体是什么（疑似蛋白/酶） |
| **Lozovsky_DHFR_ic50_** *(5 个文件)* | 疟疾 DHFR | 4 | 16 | **5** | 5 个条件 (c57–c61) | 完整 2^4，deg=4 | 1△ 2✓ 3✓ 4? | 中 | c57–c61 是药物还是株背景 |
| **Tamer_DHFR_** *(4 个文件)* | 大肠杆菌 DHFR | 5 | 32 | **4** | kcat 与 ki × 2 轨迹 | 完整 2^5，deg=5 | 1✓ 2✓ 3△ 4? | 中 | 是"assay 类型"而非"环境"，是否算独立任务需论证；**同一 Toprak 实验室** |
| **Ogbunugafor22_** *(2 个文件)* | 疟疾 DHFR | 4 | **15** | 2 | 乙胺嘧啶 / 环氯胍 | 2^4 = 16，实测 15 | 1△ 2✓ 3✓ 4? | 中 | 少 1 个基因型；论文表格标 `(2^4)×12` 与文件 15 行**不一致** |
| **new_PTE_catact_** *(2 个文件)* | 磷酸三酯酶 (PTE) | 6 | 64 | 2 | 2 种底物 (2NH / butyrate) | 完整 2^6，deg=6 | 1✓ 2✓ 3✓ 4? | 中 | 文件前缀 `new_` 无文献归属；**酶-多底物**语义最贴近 EOV |
| **daSilva2010_** *(2 个文件)* | HIV-1 蛋白区段 | 5 | 32 | 2 | CCR5 / CXCR5 趋向性 | 完整 2^5，deg=5 | 1✓ 2✓ 3✓ 4? | 低 | 未逐文件核实行数 |
| **Jalal2020_** *(2 个文件)* | ParB | 4 | ~160,000? | 2 | NBS / parS 两种 DNA 位点 | 待核实 | ? | 低 | 论文表标 20^4 = 160,000，**未核实文件行数** |

### 2.3 第三梯队 —— 单任务但密集（L1：只支持 starting-point / N_k，不支持 future-task holdout）

这些**不满足判据 2**，但可作为"跨 landscape 复现 H1/H2"的复制集，以及图算法的标准测试床。全部已确认存在于仓库（抽查已核实）。

| 名称 | 蛋白/系统 | 位点数 | 变体数（已核实或论文值） | 任务数 |
|---|---|---|---|---|
| `Wu2016_GB1.csv` | GB1 (IgG Fc 结合) | 4 | 149,361（论文 20^4=160,000 的 93.4%） | 1 |
| `Johnston2024_TrpB4.csv` | TrpB 酶活性中心 | 4 | 论文 20^4=160,000，文件 1,518,184 B | 1 |
| `Johnston2024_TrpB3A..3I` | TrpB（9 个不同 3 位点窗口） | 3 × 9 | 8,000 × 9 | 1（但 **9 个不同 landscape**） |
| `Papkou2023_DHFR.csv` | DHFR | 9 | 论文 4^9=262,144（99.7% 实测），文件 2,005,057 B | 1 |
| `Kuo2020.csv` | Shine-Dalgarno 序列 | 9 | 4^9=262,144，文件 1,402,457 B | 1 |
| `Westmann2024.csv` | TetR 调控景观 | 8 | 4^8=65,536，文件 213,334 B | 1 |
| `Poelwijk2019.csv` | eqFP611 荧光蛋白 | 13 | 2^13=8,192，文件 91,298 B | 1 |
| `Bendixsen2019_ligase.csv` / `_hdv.csv` | 核酶 / 连接酶 | 14 | 2^14=16,384，文件 219,181 B | 1 |
| `Tu2022_TEV.csv` / `Tu2022_T7.csv` | TEV 蛋白酶 / T7 | 4 / 3 | 20^4 / 20^3 | 1 |
| `Podgornaia2015_PhoQ.csv` | PhoQ 传感激酶 | 4 | 20^4=160,000 | 1 |
| `Lite2020_ParD2/D3.csv` | ParD 毒素-抗毒素 | 3 | 20^3=8,000 | 1 |
| `Wong2018_{brca2,smn1,ikbkap}.csv` | 人类 5' 剪接位点 | — | 32,768 × 3 | **3 个不同基因，不是 3 个任务** |
| `Weinreich2006Tan2011_*.csv` | TEM β-内酰胺酶 | 5 | 2^5=32 | 2 项研究（任务是否不同待核实） |

### 2.4 明确排除

| 对象 | 排除理由 |
|---|---|
| `Skwara2023_*`、`Diaz-Colunga_*`、`Kehe*`、`Clark*`、`Sanchez-Gorostiaga*` | **微生物群落**组成→功能景观；"基因型"是群落而非蛋白。只能作数学定义的方法学对照 |
| `data/Materials`、`data/Chemistry`、`data/Pharmacology`、`data/ChemBio` | 非生物序列模态 |
| `Bridgham2009.csv` | 仅 16 行且 **7/16 fitness 缺失**，太稀疏 |
| `[unpublished] A complete map of specificity encoding for a partially fuzzy protein interaction/` | 未发表数据，仅含 `datacard.rtf`，无明确引用与 license |
| `Moulana2023_CB6`（单独使用） | **49.6% 缺失**；单独使用不可靠，必须与 S309/ACE2 联合 |
| `Phillips2021_CR6261_*`（单独使用） | 空间仅 93.6% 覆盖，位点数 11，任务仅 2 |

### 2.5 ProteinGym / RNAGym / CIS-BP 专项结论（由并行检索线程提供，已核实）

**结论一句话：这三个 benchmark 里"多条件"与"多突变体密集"是两个不相交的集合。**

| 对象 | 事实（已核实） | 对我们 |
|---|---|---|
| **ProteinGym processed**（`DMS_ProteinGym_substitutions.zip`，217 个文件） | **每个文件只有 `mutant, mutated_sequence, DMS_score, DMS_score_bin` 四列**。每基因型一个分数，**无 replicate、无 condition 列** | ❌ 不能直接用 |
| **ProteinGym raw**（`substitutions_raw_DMS.zip`，213 个文件） | **确实带多条件表**：`AACC1_PSEAI_Dandage_2018`（10 条件：30/37/42 °C × TMAO/glycerol × 庆大霉素）、`A4GRB6_PSEAI_Chen_2020`（9 条件：3 浓度 × 2 温度 AMP + CTX + MEM）、`KKA2_KLEPN_Melnikov_2014`（20 条件 = 5 底物 × 4 稀释）、`AMIE_PSEAE_Wrenbeck_2017`（3 底物：乙酰胺/异丁酰胺/丙酰胺）、`HSP82_YEAST_Flynn_2019`（**2 个真 replicate + 5 个条件**）等 | ⚠️ 多条件成立，**但全部是单突变文库**（7–233 个位点被突变，无多突变体） |
| **ProteinGym 多突变体集合** | `SPG1_STRSG_Wu_2016`（GB1）149,360 变体 / 4 位点 / **121,174 个四重突变**；`SPG1_STRSG_Olson_2014` 536,962 双突变体 / 1,485 个位点对（每对约 360 变体 ≈ 20×20 的 90%）；`HIS7_YEAST_Pokusaeva_2019` 496,137；`GFP_AEQVI_Sarkisyan_2016` 50,630 等 | ⚠️ 密集成立，**但全部单条件、且只有一列分数** |
| **CIS-BP 及其后继 Codebook** | **不存在逐基因型多条件数据**（PWM/SELEX 为主）。最好的外部替代是 PAX6 paired-domain Y1H DMS：2 个 DNA bait × ±geneticin = 4 条件，但只有 **5,266 个多突变体** | ❌ 死路 |

> **核心张力（原文）**："every multi-condition assay above is a SINGLE-mutant library … and every deep combinatorial multi-mutant assay is SINGLE-condition. **NO single ProteinGym assay satisfies both 1 and 2.**"

**→ 本文件第 2.1 节的发现正好把这个张力解开了。**
Phillips2023 / Phillips2021_CR9114 / Moulana2023 **不在 ProteinGym 里**，它们来自原始论文（eLife），而 **GraphFLA 把它们按"同一空间、不同条件"成组地收了进来**。也就是说：

> **GraphFLA 的 curated collection 恰好是 ProteinGym 缺失的那个交集。** 这不是"再找一个数据集"，而是"ProteinGym 这个 benchmark 结构性缺失的一类数据，被另一个仓库补上了"。

**副产品（对判据 4 有用）**：ProteinGym raw 里 `HSP82_YEAST_Flynn_2019`（2 replicate + 5 条件）、`ADRB2_HUMAN_Jones_2020`（4 配体浓度 × 2 replicate）、`R1AB_SARS2_Flynn_2022`（FRET + TF + growth，各 2 replicate）**带有显式重复列**。它们**不能**做主证据（单突变、不密集），但可以作为**噪声结构 / 任务迁移的对照数据集**，并且是我们"dense 数据没有 replicate"这一缺口的一种外部校准手段。

**ProteinGym 下载地址（已核实）**
- processed：`https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/DMS_ProteinGym_substitutions.zip`
- **raw（多条件所在）**：`https://marks.hms.harvard.edu/proteingym/ProteinGym_v1.3/substitutions_raw_DMS.zip`

#### 2.5b MaveDB / RNAGym / CIS-BP 穷尽检索结果（已核实）

| 资源 | 检索方式 | 结论 |
|---|---|---|
| **MaveDB** | 读全量 experiment 列表 `https://api.mavedb.org/api/v1/experiments`（**2,063 个** experiment），筛出**有 ≥2 个 score set 的 35 个**并逐个读摘要 | **35 个多条件 experiment 中，没有一个同时是组合多突变。** 已核实 URN：`urn:mavedb:00000040-a`（HSP90，**4 条件 = {30 °C, 36 °C} × {无盐, 0.5 M NaCl}**，**CC0**，但只有 **189 个变体且全为单突变**）；`urn:mavedb:00000053-a`（PSD95 PDZ3 pairwise，**648,022 个变体**，CC0，单条件） |
| **RNAGym** | 读 HF 镜像 `reference_sheet_final.parquet` + 目录 API（`Marks-lab/RNAgym`，**二手镜像，已标注**；主源为 `marks.hms.harvard.edu/rnagym/…/fitness_processed_assays.zip`）；**raw 包另行核实** | **processed：共 70 个 assay（已核实）**——**36 个是从 ProteinGym 原样导入的蛋白 assay**（`BLAT_ECOLX_Firnberg_2014`、`GFP_AEQVI_Sarkisyan_2016`、`DLG4_RAT_McLaughlin_2012`、`CAPSD_AAV2S_Sinai_2021`、`BRCA1_HUMAN_Findlay_2018` …），**34 个是 RNA**（24 ribozyme + 4 tRNA + 2 mRNA + 2 aptamer + 1 TAT）→ **processed 侧不提供任何新的蛋白多条件条目（判据 1、2 均 ✗，置信度：高）**。<br>⚠️ **但 RAW 包另有 3 个多条件数据集，其中 `glmS` 满足全部 4 条判据 → 见 §2.5d。**（我在本表初版把"processed 无多条件"错误地推广到了整个 RNAGym，已更正） |
| **CIS-BP 及 Codebook** | 已核实 | **没有任何逐基因型 × 多条件数据**（PWM/SELEX 构造所致） |

> ⚠️ **一条已发出的错误更正（记录在案，防止传播）**：并行线程曾给出 MaveDB URN `00000056`（Dutta 2010 B2L11）——**该 ID 未经核实，已撤回**。该数据集的**已核实**形态是 ProteinGym raw 文件 `B2L11_HUMAN_Dutta_2010_binding-Mcl-1.csv`，表头实测为
> `mut_proteingym, score, hgvs_pro, 100 nM Mcl-1, 1 uM Mcl-1, 100 nM Bcl-xL, 1 uM Bcl-xL` → **4 个条件（2 抗原 × 2 浓度），约 200 行 / 170 个计分变体，全为单突变**（DOI 10.1016/j.jmb.2010.03.058）。

**四个资源里"只差一条判据"的最接近者（全部已核实，可作为对照/脚手架）**

| 对象 | 满足 | 差哪条 | 备注 |
|---|---|---|---|
| `SPG1_STRSG_Wu_2016`（GB1） | 1（149,360 变体 / 恰好 4 位点 V39,D40,G41,V54 / **121,174 个四重突变** ≈ 完整 20^4） | **2**（+4） | ProteinGym 里最好的基因型图基质；raw 文件含 `Count input` / `Count selected` → **有噪声代理** |
| `SPG1_STRSG_Olson_2014`（GB1） | 1（**536,962 个双突变**，1,485 个位点对，每对 ~360/361 变体 ≈ 20×20 的 90%） | **2**（+4） | raw 列：`W, W_0.01floor, lnW, score, Mut1/Mut2 Fitness, Input Count, Selection Count` |
| **`PHOT_CHLRE_Chen_2023`（CreiLOV）** | **1 + 4**（165,407 个多突变；raw 文件为 `HGVSp, rep1, rep2, rep3, mean, …` → **3 次重复**） | **2**（单条件） | ⭐ **这正是我在 GraphFLA 仓库里实测到 165,428 行的 `NEW_Chen2023_CreiLOV.csv`**——**两处独立命中同一数据集**。它有重复但没有多任务，且 20 位点采样率仅 15.8% |
| `HSP82_YEAST_Flynn_2019` | **2 + 3 + 4**（13,294 个单突变 × **6 条件** + **2 个显式重复列**，论文报 R² = 0.90） | **1**（无多突变） | **最佳"外部噪声校准"数据集** |
| `HIS7_YEAST_Pokusaeva_2019` | 1（496,137 个多突变） | 2, 3(多条件), 4 | raw 只有 `mutant, selection` |
| `AACC1_PSEAI_Dandage_2018` | 2（**10 条件**：3 温度 × 2 伴侣 × 庆大霉素） | 1 | 1,801 个变体，全单突变 |
| `KKA2_KLEPN_Melnikov_2014` | 2（**20 条件** = 5 底物 × 4 稀释） | 1 | 4,960 个变体，全单突变 |
| `AMIE_PSEAE_Wrenbeck_2017` | 2（**3 种底物**：乙酰胺/异丁酰胺/丙ionamide） | 1 | 6,227 个变体，全单突变——**"多底物酶"最接近的形式，但只有单突变** |

> **对本项目的直接含义**：想在 ProteinGym/MaveDB 体系内做"多任务 × 密集组合"，**必须跨数据集拼接**，而拼接会引入"不同蛋白"这一混淆。**这正是 GraphFLA 那批成组文件的不可替代价值。**

**未解决线索（标记为未核实，勿当结论使用）**：Bonnin 等 2025 bioRxiv，*"Deep mutational scanning of a Streptococcus pneumoniae FMN riboswitch reveals robustness during mouse infection and diverging adaptive landscapes in response to targeting antibiotics"*（DOI **10.1101/2025.04.17.649428**）。标题暗示**同一个 DMS 文库在 ≥3 个环境（体外 / 小鼠感染 / 抗生素）下读出**。**bioRxiv 两次返回 HTTP 429，未能核实变体数、组合深度与数据可得性。**（注：这是 **RNA**，且深度可能只有单/双突变。）

#### 2.5c 收尾增量：三条"只差判据 2"的对象 + 许可证据缺口 + 两个陷阱

**① 三个对象经表头实测后升级为"仅差判据 2"（判据 1+3+4 全部满足）**

| 对象 | 表头（已核实） | 规模 | 差哪条 |
|---|---|---|---|
| **`PHOT_CHLRE_Chen_2023`（CreiLOV）** | `HGVSp, rep1, rep2, rep3, mean, log_rep1, log_rep2, log_rep3, log_mean, mutant` → **3 次真重复** | **165,407 个多突变体** / 118 位点 | **仅差判据 2**（单条件荧光/FACS）→ **判据 1+3+4 组合里最强的一个** |
| **`GRB2_HUMAN_Faure_2021`** | `protein, mutant, pca_type, aa_seq, Nham_aa, WT, fitness, sigma, growthrate, growthrate_sigma` → **有 `sigma`** | 63,366 总数 / **62,332 个双突变** / 56 位点 | **仅差判据 2**（单条件酵母生长） |
| **`DLG4_HUMAN_Faure_2021`** | 同上（有 `sigma`） | 6,976 / 5,696 个双突变 | **仅差判据 2** |

> 这三者此前被我归入"判据 4 未知"。**现在明确：它们的噪声结构是可估的。** → 它们是**"如果最终必须在单条件数据上做"时的首选基质**（可与另一个多条件单突变数据拼成两轴，但会引入"不同蛋白"混淆）。

**② 许可证据缺口（**必须补进 DATA_AUDIT 的 license 列**，这是目前最实的一个合规风险）**
- **ProteinGym 的 MIT 只覆盖代码/仓库，不覆盖 DMS 数据本身** —— 其 README 只为 code 声明 MIT，**底层 DMS 数据的许可见不到声明**。
- **CIS-BP 站点上任何地方都没有 license**；广为流传的 "Public Domain" 说法**溯源到第三方 re3data（r3d100013971），不是 CIS-BP 自己声明的**。
- 这两条意味着：**"我们用了 ProteinGym/CIS-BP" 这句话在再分发时需要逐数据集回源确认**，不能引用聚合仓库的许可标签。→ 与 3.4 节的"核实对象必须是原始 deposit"是同一条原则的两个面。

**③ 两个容易踩的陷阱**
- **MaveDB 里的 TF 条目不是 DNA 结合数据。** 所有被检查的 TF-domain 条目其实是 **Human Domainome 1.0 的 DHFR 稳定性 DMS**（单条件、CC0）——**极易被误当成"转录因子-DNA 结合"数据**。
- **同一数据集在不同仓库规模不一致，原因未解决**：`DLG4/PSD95` 在 ProteinGym 是 **6,976**，在 MaveDB `00000053-a` 是 **648,022**（疑为核苷酸级 vs 氨基酸级，**未确认**）；Hsp90 在 ProteinGym/Flynn 是 **13,294**，在 MaveDB `00000040-a` 是 **189**（疑为 curated 子集，**未确认**）。→ **再次印证：跨仓库规模不可直接互换。**

**④ 其他可用的多条件（但全为单突变，判据 1 ✗）补充清单**
`MaveDB 00000039-a`（7 个启动子构建 = 表达水平，各 ~185 变体）、`MaveDB 00000012-a`（Gal4 DBD，6 种筛选方案/时间点，1,319）、`A0A1I9GEU1_NEIME_Kennouche_2019`（3 种 assay：黏附/聚集/菌毛）、`RL40A_YEAST_Mavor_2016`（5 种药物）、`S22A1_HUMAN_Yee_2023`、`Q837P4/P5_ENTFA_Meier_2023`、`MTH3_HAEAE_RockahShmuel_2015`、`GAL4_YEAST_Kitzman_2015`（5 个时间点）、`SC6A4_HUMAN_Young_2021`（2 种底物）、`ENVZ_ECOLI_Ghose_2023`（on/off）。

**⑤ 另一个"近失"：PAX6 paired-domain Y1H DMS**（McDonnell 2024，DOI 10.1038/s44320-024-00043-8，PMC11219921，**CC BY**）
- 150 个位点，**2,980 个设计单突变（LE9 2,856 / BLX 2,838 计分）** → **Hamming-1 完整（每个位点全部 20 种替换）**；**4 个条件 = 2 个 DNA bait（LE9, BLX）× ±geneticin**。
- **差在：只有 5,266 个多突变体（<10^4），且未找到独立 processed deposit** → **判据 1（密度）与判据 3 均 ✗**。
- 意义：**这是"转录因子 × 多 DNA 靶标"这一类里最好的对象**，如果将来放宽"≥10^4 多突变体"的门槛，它是第一顺位。

**⑥ 已核实的方法学结论（可直接引用）**：对 ProteinGym raw 包**全部 213 个文件的表头做了穷尽扫描——每一个拥有 >1 个 score 列的文件都是单突变文库**。这是"两轴互斥"最直接的证据。

**⑦ "查不到"清单（已按 §2.5d 更正）**：**蛋白**侧——任何同时满足 4 条判据的 entry（ProteinGym / CIS-BP / MaveDB 全 2,063）**查不到**；ProteinGym 中既多条件又含多突变体的 assay **查不到**；Codebook HT-/GHT-SELEX 的**逐循环计数矩阵** **查不到**（只有原始 trimmed FASTQ）；**TrpB `data.zip`（3.3 GB）内部文件 schema 未核实**（流式下载超时）。**RNA 侧例外见 §2.5d。**

---

### 2.5d ⭐⭐ **RNAGym RAW 里的 `glmS` 核酶：全survey 唯一满足 4 条判据的 entry**

**这是对 §2.5b 的实质性更正。** 我此前写"RNAGym 不提供任何多条件数据"——**这只对 processed 版本成立**。

**已由我独立核实的三项（不是转述）**：
- `https://marks.hms.harvard.edu/rnagym/fitness_prediction/fitness_raw_data.zip` → **HTTP 206，`Content-Range: bytes 0-7/13581795`**（= 13,581,795 B，与并行线程报告一致），首字节 `PK` → **有效 ZIP，无需注册，匿名可取**。
- Crossref `10.1038/s41467-020-15540-1` → **Nat Commun 2020**，license 字段 = **`https://creativecommons.org/licenses/by/4.0`**（CC-BY-4.0，确认）。
- 同源摘要原文（已读）："We measure the cleavage rates for **all possible single and double mutants** of this ribozyme **across a series of ligand concentrations**, determining kcat and KM values for active variants." → **穷举单突变 + 双突变 + 多浓度**成立。

**并行线程提供、我未逐字节复核的细节（标记为未独立复核）**：文件 `raw_data/andreasson_2020/dataframe1_kobs_kcat_KM_rescues.csv`，表头含 `glmS_variant_sequence, MismatchCount, Mismatches, kobs_{10000,2500,640,160,40}uM, kobs_*_stErr, kcat, KM, kcat/KM_M-1s-1, Rescue_vs_SingleMut{1,2}_10mM` 等；**161,879 行**，非空 kobs 计数 161,861 / 43,370 / 24,346 / 20,390 / 13,225；**67 个可变位点**；`dataframe2` 另含 `kobs_10000uM_2`（10 mM 条件的独立重复）与 `biological_mutation_frequency`。

| 判据 | 结论 |
|---|---|
| 1（≥3 位点 + 密集组合） | ✅ **67 位点，穷举单+双突变**（Hamming-2 内组合完整） |
| 2（≥2 任务，≥1 可 held-out） | ✅ **5 个配体浓度（40 / 160 / 640 / 2,500 / 10,000 µM）** + kcat/KM + 2 条双突变 rescue 支路 |
| 3（processed 可下载） | ✅ 逐基因型 × 逐浓度 CSV，**无需注册**（我实测 206/200） |
| 4（重复 / 可估噪声） | ✅ **每个 kobs / kcat / KM 都有 `_stErr`**，另有独立重复 `kobs_10000uM_2` |

**⚠️ 对我们的关键限制**：
1. **这是 RNA，不是蛋白。** 它的 held-out 任务轴是**配体浓度迁移**，**不是**我们讨论的蛋白条件轴（底物/抗生素/宿主）。→ **它不能回答"TEM-1 是不是蛋白特例"**，只能作为**模态对照**（与 `Soo2021` 同角色，但判据更完整）。
2. **必须用 RAW 文件**：`Andreasson_2020_ribozyme` processed assay **把整个浓度序列塌缩成单一 `DMS_score` 列** → **processed 版本直接丢掉全部多任务信息**。这是一个对所有数据集都通用的警告。
3. 配体的化学身份（GlcN6P）是**从论文标题/摘要推断**，列名只写 `uM`。

**RNAGym raw 里另外两个多条件集合（已核实计数，均为 RNA）**：
- `raw_data/li_2018/GSE111508_FitnessDataMultiEnv.txt` —— 酵母 tRNA，**23,284 个基因型**，4 个条件（`Fit23/Fit30/Fit37/FitDMSO` = 23/30/37 °C YPD + 30 °C+3% DMSO），69 个可变位点。**但突变深度直方图（由线程自行计算）为 1:207, 2:8101, 3:6891, 4:4514, 5:2209, 6:929, 7:319, 8:82, 9:31 → 是随机文库，不是组合文库**；23k 基因型散布在 69 位点上 → **Hamming-1 邻域几乎全空，判据 1 ✗**。DOI 10.1038/s41559-018-0549-8。
- `raw_data/puchta_2016/` —— 酵母 snoRNA，5 个文件（21,008 / 22,812 / 21,800 / 21,737 / 34,009 行），轴 = 温度（30 vs 37 °C）× 碳源（葡萄糖 vs 半乳糖）× 构建体。引文写在文件头：Puchta et al., *Science* 352:840-844 (2016)。**突变深度直方图未计算 → 组合密度未核实。**

---

### 2.5e 多底物酶 / 多温度宿主两条线程的收尾结果（**含 4 个新的已核实候选**）

#### A. ⭐ **Kosterlitz 多宿主 blaTEM —— 唯一"组合完整 × ≥3 宿主"的已核实数据集**

| 维度 | 值 |
|---|---|
| 蛋白 | **TEM-1 β-内酰胺酶（blaTEM）——与我们主数据同一蛋白** |
| 位点 / 变体 | **5 位点**（g4205a 启动子 SNP、A42G、E104K、M182T、G238S）→ **32 个基因型（完整 2^5，零空洞）** × 3 条条形码 = 96 个质粒 |
| **任务** | **3 个宿主物种**（*E. coli* DH10B、*K. pneumoniae* Kp08、*S. enterica* Typhimurium LT2），各自跨 cefotaxime 梯度 |
| 数据 | Zenodo **10.5281/zenodo.10045641** + `github.com/livkosterlitz/crowdsourcing` |
| **license** | **CC-BY-4.0（已通过 API 核实）** |
| 论文 | *Mol Biol Evol* 10.1093/molbev/msad237 / PMC10657783 |
| 判据 | 1✓（5 位点完整）2✓（**3 宿主**）3✓ **4 ⚠️**（逐宿主重复筛选未明；逐浓度值 vs 仅拟合拐点未核实） |

> **价值**：这是**多宿主轴上唯一的组合完整数据集**，而且**是 TEM-1**。n=32 使它只能做**评估/留出核心**，不能做训练语料——但它让"future task = 换宿主"这条轴第一次有了真实数据。

#### B. ⭐ **PTE 6 位点 × 9 底物 —— 唯一"组合完整 × 多底物"且有真实重复的数据集（对本报告 `new_PTE` 条目的重大升级）**

- 蛋白：磷酸三酯酶（*Pseudomonas diminuta* 定向进化谱系）；**6 位点**（p233/p254/p271/p272/p306/p313）→ **64 个基因型（完整 2^6，192 条唯一边）**。
- **9 种底物**（2NH, DHC, POE, POM, PTE, PTM, acetate, butyrate, tbbl），跨 3 个化学类（有机磷、酯、内酯）。
- **已核实引用**："we profile all 64 combinations of six key mutations in a phosphotriesterase across nine structurally diverse substrates … generating a multi-dimensional map of epistasis and promiscuity"；"We collected **4872 measurements**, consisting of **biological (n = 3–10) and technical (n = 3) replicates** for 576 conditions (64 genotypes across nine substrates)"；CV "mean = 16%; median = 15%"。
- 文件级已核实：`github/un-normalized-processed/` 下正好 9 个逐底物 CSV；`2NH.csv` 表头 `Code,p233,p254,p271,p272,p306,p313,exp1..exp9,pte1..pte24`，64 行 → **即用型 64 × 9 基因型×任务矩阵 + 完整 Hamming-1 邻接**。
- 数据：`github.com/karolbuda/rba-error-propagation`；preprint 10.64898/2026.07.02.736193。
- **判据 1✓ 2✓ 3✓ 4✓（真实重复 + CV）** —— **但只有 64 个基因型**。
- ⚠️ **license 未核实**（归档中未见 LICENSE 文件）；**同行评审状态未知**；**内部不一致**：正文称 4 种有机磷，但 9 个 CSV 里只见 3 个有机磷缩写（POE/POM/PTM）。

> **这修正/升级了本报告 §2.2 里的 `new_PTE_catact_2NH/butyrate` 条目**：GraphFLA 只收了 **2** 个底物，**源数据有 9 个，且带 3–10 次生物学重复**。→ **若要"酶-多底物"证据，应回源取这 9 个 CSV，而不是用 GraphFLA 的 2 个派生文件。**

#### C. ⭐ **TEV 蛋白酶 DNA-recorder 多底物特异性 —— 唯一"大规模 × 多底物"的景观**

- **29,716 个蛋白酶 × 最多 134 种底物 → 约 600,000 个 protease–substrate 对（~355,000 唯一，占可能的 59.7%）**。
- 已核实引用："we demonstrate testing 29,716 candidate proteases against up to 134 substrates in parallel"；"three libraries targeting residues from either cluster (libraries A and B) or both clusters simultaneously (library AB) using NNK or NNS codons"（**蛋白酶侧 3–6 个随机化残基**）。
- 数据：`github.com/JeschekLab/ProtRec` + Zenodo **10.5281/zenodo.15346003**；MLDEEP Zenodo **10.5281/zenodo.15344074**；SRA SAMN48276352；论文 10.1038/s41467-025-60622-7 / PMC12217912。
- **license：CC-BY-4.0（已通过 Zenodo API 在两个记录上核实）**。
- 判据：1△（多位点 NNK/NNS 随机化，**非完整超立方体**；深度部分落在**任务轴**上）2✓（**134 个底物**）3✓ 4⚠️（**每条件重复数未声明**，只有"excellent robustness across replicate cultivations"+ 噪声底修正 → 噪声可估但未文档化）。
- **注意**：底物面板是**设计的 motif 文库**。若把任务定义为"哪个蛋白酶对留出底物 X 最好"，这是一个真实的 **3–6 位点 × 134 任务**密集景观。

#### D. **MPH：8 个环境（不是我先前写的 6 个），且带 SD**

- Anderson et al., *Nat Commun* 10.1038/s41467-021-23943-x；数据 `github.com/danderson8/MPH_Epistasis` + Zenodo **10.5281/zenodo.4552583**。
- 已核实引用："all possible combinations of the five functionally relevant mutations under **eight different laboratory conditions** (in which an alternative divalent metal is supplemented)"；"are the **average of three biological replicates, with error bars indicating the standard deviation**"。
- → **判据 4 ✓（有 SD）**。修正本报告 §2.2 中 `Anderson2021_MPH` 的"6 种金属"为 **8 个环境**（GraphFLA 只收了 6 个文件）。
- ⚠️ Zenodo license 字段为 **"other-open"**；GitHub 侧 LICENSE **未核实**。

#### E. 已核实的阴性结论（两条线程）

1. **不存在任何"组合型 × 多温度"的蛋白景观。** 唯一候选 **Tang & Zheng YFP × 7 温度**（Zenodo 10.5281/zenodo.20719728，MIT，**237,039,715 B** 的 `code_and_data.zip` 已下载并逐行扫描）：7 个温度（15/20/25/30/35/40/42 °C）+ 每基因型 Tm + ddG，但 **109,856 行恰好 1 个突变、0 行 >1 个突变** → **是饱和单突变扫描，判据 1 ✗**。**这是"多温度 × 蛋白"轴上最好的数据集，但仍不满足判据 1。**
2. **"≥3 位点 AND ≥10^4 多突变体 AND ≥2 条件"在**多底物**与**多环境**文献里都不存在。** 联合集最大只有 **64 个基因型（PTE）** 和 **32 个（MPH、Kosterlitz）**。达到 10^4+ 多突变体的一律单条件。
   → 该交集**只存在于本报告 §2.1 已列的对象中**：TEM-1CML（13 位点/55,296/2 抗生素）、CR9114（16/65,536/3 抗原）、AncSR1（4/160,000/2 DNA 元件×2 背景）、Jalal2020（4/160,000/2 位点）。

#### F. 新增近失清单（全部只差判据 1 或 3，**记录以免重复检查**）

| 对象 | 规模 / 条件 | 差哪条 |
|---|---|---|
| **VIM-2 金属β-内酰胺酶**（eLife 2020, PMC7308095；**MaveDB `urn:mavedb:00000073-a` … `-i` = 9 个 score set**） | 3 种 β-内酰胺 × 2 温度（25/37 °C），各 5,549 变体，有重复 | **1**（单突变） |
| **Cox 2022 247 单抗 × RBD**（*Nature*） | **247 个条件**，干净 CSV + SRA | **1**（Hamming-1 饱和）→ **若门槛放宽为"可建 Hamming-1 图"，这是全报告最好的一份** |
| **Taft 2022 + Shlesinger 2026 DML 配对** | 同一 RBD 组合文库 vs 13 单抗 + ACE2，以及 vs 10 份血清 = **24 个条件** | **3**（Taft 仓库仍是占位 README；Shlesinger 的 Zenodo 标题为 "Code for manuscript"）→ 需**邮件问作者** |
| **RNAP rpoB CREPE**（*Nat Commun* 10.1038/s41467-023-41882-7；Zenodo 10.5281/zenodo.8144064，**CC-BY-4.0**，逐条件 CSV） | ~6,000 变体 × 5 环境 + 2 菌株背景 = **7 个条件** | **1**（易错 PCR 文库，Hamming-1 覆盖稀疏） |
| **DAOx**（Zenodo 10.5281/zenodo.15846928，**CC-BY-4.0**） | ~6,500 变体 × 5 底物，2 次重复 r = 0.94–0.97 | **1**（94.4% 单突变饱和） |
| **amiE 酰胺酶**（figshare 10.6084/m9.figshare.3505901.v2，**CC-BY-4.0**） | >96.3% 全部单错义 × 3 底物 | **1** |
| **TtgR**（4 位点 × 2 诱导物，含完整 16 节点空间，3 次重复） | — | **3 决定性失败**："available from the corresponding author on reasonable request" |
| **APPI 多蛋白酶**（2 位点 × 4 种人丝氨酸蛋白酶） | — | **3**："All relevant data are available from the authors." |
| **Irvine 2025 Fc 文库**（>10^8 Fc 变体 × 8 种 Fc 受体） | — | **3**（未找到任何数据可得性声明） |
| **腺苷酸激酶**（*Science* 2025） | 181 个直系同源物 × 9–96 °C | **1**（是直系同源物，不是突变格） |
| **Mira/Barlow TEM-50** | 4 位点完整 × 15 种 β-内酰胺 — **文献中最好的判据 2** | ⚠️ **线程称"找不到 deposit"** —— **但本报告已核实 GraphFLA 仓库里就有这 15 个 CSV**。→ **数据是存在的，只是不在作者处**；引用时注意这一 provenance 差异 |
| **Palmer 2015 DHFR** | 6 位点完整但仅 96 变体、单一药物 | **1/2 规模 + 3**（仅补充材料） |

#### G. 方法学限制（如实记录）
**未认证的 GitHub REST API 在整个会话中对所有并行线程限流（60 req/h/IP）**，因此 `LSSI-ETH`（Taft DML）与 `klawrence26/bnab-landscapes` 的仓库树**无人能枚举**。CR9114 是靠**直接拉 eLife CDN 的逐变体 CSV** 绕开的（因此它是文件级核实）。**Taft / Shlesinger 的 processed 表仍未核实，值得一次作者邮件或带认证的 GitHub 调用。**

### 2.6 并行检索线程确认的其他候选（含**判据 4 的唯一满足者**）

#### ⭐⭐ AncSR1 祖先类固醇受体 —— **可能是最强的候选，因为它是唯一满足判据 4 的**

- 来源：Starr, Picton & Thornton, *Nature* 2017, **"Alternate evolutionary histories in the sequence space of an ancient protein"**, doi:10.1038/nature23902，PMC6214350。独立复核：Metzger, Park, Starr & Thornton, *eLife* 2024, doi:10.7554/eLife.88737，PMC11105156。
- **已核实原文引用**："We prepared a library that contains **all 160,000 combinations of all 20 amino acids at four key sites** in the RH … We engineered yeast reporter strains in which **ERE or SRE** drives expression of a fluorescent GFP reporter … We transformed the library into **each reporter** and used FACS coupled to deep sequencing (FACS-seq) to quantify binding of each variant in the library to ERE or SRE"
- **已核实重复结构**："Each RH library (AncSR1 and AncSR1+11P) was **independently transformed twice into each yeast reporter strain (ERE and SRE) for replicate FACS-seq analyses**."
- **已核实噪声可估**："We estimated the **standard error of mean fluorescence (SEM)** for genotypes based on their depth of coverage."

| 维度 | 状态 |
|---|---|
| 判据 1（≥3 位点 + 密集完整） | ✅ **4 位点 × 20 氨基酸 = 160,000 完整 20^4**，deg = 76 |
| 判据 2（≥2 任务） | ✅ **4 个条件 = {ERE, SRE} × {AncSR1, AncSR1+11P}**，同一批 160,000 基因型 |
| 判据 3（processed 可下载） | ⚠️ **未核实** —— 未能找到 per-variant per-element 荧光表的 Dryad/Zenodo DOI；论文 data availability 不可读（PMC PDF 被拦）。**这是唯一的阻塞项。** |
| 判据 4（重复/噪声） | ✅ **2 次独立重复 + 可估 SEM** —— **目前唯一满足者** |

> **为什么它很关键**：它把"held-out future task"从**结合伙伴**变成了**同一蛋白的另一个 DNA 响应元件**，而且**带重复**。这正是我在第 0 节标记为"唯一硬缺口"的那一项的解药。
>
> **待办（第一优先）**：向作者（Tyler Starr）或 Nature 补充材料索取/抓取 per-variant 荧光表。**若拿到，Phase I 的 H1 就有了一个"起点差异 > 噪声"的干净检验床，不再依赖 TEM-1 单点。**

#### TrpB（Tm9D8*）—— 判据 1/3/4 满足，**判据 2 不满足**，但有一个**重大 novelty 警告**

- Johnston, Almhjell, Watkins-Dulaney, Liu, Porter, Yang & Arnold, *PNAS* 2024, doi:10.1073/pnas.2400439121，PMC11317637。
- 已核实："a **combinatorially complete, 160,000-variant** fitness landscape across four residues in the active site of an enzyme"；"**159,129 variants (99.45%)** had sufficient sequencing coverage for quantification in **both replicate experiments**"。
- 单一条件（非天然环境中的 pooled *E. coli* 生长，200 µM indole）→ **判据 2 ✗**。
- 数据：**CaltechDATA doi:10.22002/h5rah-5z170，license CC0-1.0**，`data.zip` **3.32 GB** + `code.zip` 413 MB。
- 🔴 **重大 novelty 警告**：该论文**已经在这个景观上跑了 in-silico directed evolution 基准**——3 种 DE 策略、**从每一个起点出发的 max fitness ECDF**、local-optima / accessible-path 分析，以及**注入噪声的 null model**。
  > **"从每一个起点出发的最大适应度分布" 就是 `R_{B,π}(x,τ)`。** 我们的 operational option value 的**单任务版本已经被发表**。
  > **可用的那一半**：他们的 3 个 DE 基线可以直接当我们的 "today optimizer"；他们的噪声注入 null model 也是现成的噪声处理范式。**必须引用并复用，而不是重新发明。**

#### 其他已核实候选 / near-miss

| 对象 | 结论 |
|---|---|
| **酿酒酵母 Hsp90 (582–590)**，Bank, Matuszewski, Hietpas & Jensen, *PNAS* 2016, doi:10.1073/pnas.1612676113 | 已下载并解析实际数据（DRYAD doi:10.5061/dryad.th0rj，**CC0**）：**1,612 条密码子基因型 / 641 个氨基酸基因型 / 8 个可变密码子位点**，距离分布 {0:6, 1:36, 2:152, 3:404, 4:550, 5:368, 6:96} → **Hamming-1 图密集，组合完整**，判据 1 ✅。但 **Bank 2016 的组合文库只在高盐一个条件下测**；多环境版本是 Fragata et al. *Heredity* 2018（doi:10.1038/s41437-018-0125-7，6 环境 = 25/30/36 °C × ±0.5 M NaCl），**那是单密码子扫描（576 个），不是组合文库** → **判据 2 只能"跨数据集拼"，不能"同一数据集 holdout"**。判据 3 = 只有原始 read counts（18 列，语义未文档化），需重跑作者 MCMC 软件 `empiricIST`。 |
| **GB1**（Wu, Dai, Olson, Lloyd-Smith & Sun, *eLife* 2016, doi:10.7554/eLife.16965） | 4 位点完整 20^4，但 fitness = **稳定性 + 结合亲和力的合成**，是**一个任务** → 判据 2 ✗。（我们已有的 `Wu2016_GB1.csv` 149,361 行与此一致。） |
| **PDZ deep coupling scan**（Salinas & Ranganathan, *eLife* 2018） | 5 个同源物 × (171 单突变 + ~12,996 双突变)；最大 Hamming 距离 2；每个基因型只在一个配体上测 → **判据 1 与 2 均 ✗** |
| **DAOx / EP-Seq**（Vanella et al., *Nat Commun* 2026, doi:10.1038/s41467-026-69913-z；Zenodo doi:10.5281/zenodo.15846928, **CC-BY-4.0**） | ~6,500 变体 × 5 个 D-氨基酸底物，**2 次生物学重复，Pearson r 0.94–0.97** → 判据 2/3/4 ✅，**但判据 1 ✗：是单突变饱和扫描**（6,530 / 6,916 个可能单错义）。**这印证了原计划里"不能把 DAOx 写成完整 directed-evolution landscape"的边界——现在有硬证据。** |
| **基孔肯雅病毒 E3-E2-6K-E1**（Ju, Hannon, … Bloom, bioRxiv 2025.08.25.672233） | ~135,000 条带条形码变体，在**人类细胞 vs 蚊子细胞**两种宿主中测 → **C2/C3/C4 很强（最好的 multi-host 设计）**，但 C1 判定为 ✗（单突变扫描）。**建议对 Bloom lab 的 GitHub CSV 做一次精确核对**：若多突变体密度足够，它是 C1-marginal。 |
| **腺苷酸激酶 evolutionary-scale enzymology**（Muir et al., *Science* 2025, doi:10.1126/science.adu1058；Zenodo doi:10.5281/zenodo.15022271, CC-BY-4.0） | "基因型"是 **181 个天然直系同源物**而非突变文库；唯一组合部分是 4 位点 LID motif 交换 → 判据 1 ✗ |
| **药物外排泵 EfrCD**（Thavarasah et al., *Methods in Enzymology* 2025） | 明确是"single site-saturation library" → 判据 1 ✗。**值得追踪其后续论文。** |

### 2.7 三个指定线索的最终裁决（**FLIP2 / DHFR-TMP 梯度 / MBE msag106**）

**一句话：三个都不是 purpose-built 的 multi-task dense combinatorial landscape。一个彻底排除，两个"部分"。**

#### ① FLIP2 —— **排除（判据 1 与 2 均不满足）**

- 托管：Zenodo **10.5281/zenodo.18433203**（concept 18433202，v3，2026-01-30），**CC-BY-4.0**；81 个文件，其中 44 个 `.csv.gz`。
- **决定性证据（已核实）**：**读了全部 44 个 CSV 的表头——没有一个包含 condition / task / environment / assay / substrate 列。** schema 只有三种：`sequence,target,set,validation`（40 个）、`sequence,set,target[,validation]`（3 个：cas×2、ired）、以及 `scl/mixed_vs_human_2` 多一列 `Classes`。
- **进一步的逐行对照（已核实）**：`gb1/low_vs_high.csv.gz` 与 `gb1/one_vs_rest.csv.gz` **各 8,733 行、8,733/8,733 序列完全相同、8,733/8,733 target 值逐字节相同（0 处不同）**。
  > → 同一个数据集里的多个文件是**同一批测量的不同 train/test 切分**，只有 `set` 列不同。**FLIP2 = distribution-shift benchmark，不是多任务数据集。** 判据 2 彻底 ✗，判据 1 也只是"继承"自上游单条件数据。
- 论文自述也印证（ICML 2026 oral）："…as well as **splits** that measure generalization…"，通篇讲 splits，从不讲 conditions。
- **结论**：**为 multi-task 问题投入 FLIP2 的时间应为零。** 唯一价值是它指向的上游数据集（`trpb` → Johnston PNAS 2024，单条件）。

#### ② DHFR 广谱突变扫描（TMP 梯度）—— **部分满足，判据 1 ✗**

- 论文：Romanowicz, Resnick, Hinton, Plesa 等；**已发表版 = Science Advances，PMC12346277**；⚠️ **原计划引用的 `PMC11785229` 是 2025-01-24 的 preprint 版**，引用时需更正。
- **规模更正（已核实）**：常被引用的"416 个同源物"是**过滤子集**（Codon 1、fitness ≥ −1）。完整库是 **1,208 个已组装 / ~1,136 个回收**。变体总量：Codon1 **60,724** 行 + Codon2 **50,509** 行 = **111,233** 个 genotype×fitness 行；≤5 替换的突变体 12,274 + 16,060 = **28,334**；唯一突变体 **109,454**。
- **判据 1 ✗**：**不是固定位点文库**——是 **1,000+ 个不同的天然同源骨架**，每个骨架中位 **~18 个随机突变体**（DropSynth 组装错误，非设计饱和库）。跨同源物的"邻居"相隔数百万个 Hamming 步，**`N_k(x)` 无意义**。
- **判据 2 ⚠️**：共 **9 个生长条件** = LB + 补充 M9 + 非补充 M9（互补）+ **6 个 TMP 浓度**（0.058 / 0.5(MIC) / 1.0 / 10 / 50 / 200 µg/mL = 400× MIC）。每个基因型确有 8 列 fitness（已读数据字典）。
  > ⚠️ **但 6 个"任务"是同一药物的不同浓度** —— 作者自己记录了单调结构（抗性同源物数 318→246→226→128→80→27）。**预测"200 µg/mL 下的最佳适应者"≈预测"0.5 µg/mL 下的最佳适应者"。浓度梯度是一个很弱的 future task。** 唯一近正交的轴是 **培养基/宿主**（LB vs M9+supp vs M9−supp），属于代谢负担型 shift，不是新化学。
- **判据 3 ✅**：**Figshare `10.6084/m9.figshare.30470525.v1`（`DHFR_Fitness_Data_2025.zip`，71,413,298 B，**MIT**）**；另有 `10.6084/m9.figshare.28266890.v1`（mapping/counts，CC-BY-4.0）；原始 FASTQ = BioProject **PRJNA1189478**；代码 `github.com/PlesaLab/DHFR`。archive 内含 `mutIDinfo15/16.csv`（每序列 8 个 fitness 列）、`BCs15/16_map.csv`（逐条形码计数）、`readme.txt`。覆盖度：**仅 2,980（lib15）/ 8,795（lib16）行拥有全部 8 个 fitness 值**。
- **判据 4 ⚠️**：**无真生物学重复**；但两个独立密码子优化版本（Codon1/Codon2）提供跨版本复现（ρ = 0.47 互补；ρ = 0.86 @MIC；ρ = 0.64 @400×MIC），且每基因型 ~18–46 个条形码 → **可从 `numprunedBCs` 与条形码散布估伪重复方差**。
- ⚠️ **第二个结构性陷阱**：库是 ~1,000 个**不同的天然蛋白**，"起点"与"任务"被**系统发育距离和表达水平混淆**（弱 RBS ≈ 原生 10% 表达）。→ **模型可能靠"学分类学"取胜，而不是学可适应性。**

#### ③ MBE `msag106`（collateral fitness effects）—— **多环境 ✅，但判据 1 硬性 ✗**

- 论文：Goff, Tsou, Mehlhoff, Ostermeier（2026），Mol Biol Evol 43(5)，doi:10.1093/molbev/msag106，PMC13160053。
- **它研究的正是 TEM-1 β-内酰胺酶**（E. coli）。
- **判据 2 ✅（≈11 个真实环境）**：LB 30 °C / LB 37 °C / LB 42 °C / M9 最小培养基 37 °C / +M182T 背景 / +avibactam 2 µg/mL / +tazobactam 64 µg/mL / Δss 胞质定位变体 / 以及 western-blot 可溶-不可溶分级。→ **温度 × 培养基 × 化学伴侣/抑制剂 × 亚细胞定位，是真正的环境轴。**
- **判据 1 ❌（硬性失败）**：**严格单突变**。方法原文："We used our previously constructed library of **all the possible single-codon substitutions (i.e. 5′-NNN) in TEM-1**"。该库来自 Mehlhoff et al. *PNAS* 2020（PMC7261132）：**94.9%（5,428/5,720）的全部非同义单突变**。→ **无法建基因型图，无法定义 `N_k(x)`，无法比较"哪个起点更会适应"。**
- **判据 4 ✅（三者中最强）**：全文阈值是 "P < 0.01 in **both replica experiments**"，且有显式噪声基因型处理。
- **判据 3 ⚠️ 查不到**：数据在 OUP 补充材料 Data S1–S8（`msag106_supplementary_data.zip`），但 OUP 全线 **HTTP 403（Cloudflare 挑战）**，BioStudies `totalHits: 0`，PMC 无全文。→ **本文件标记为"未能取得"，条件数 ≈11 来自正文与图注（已核实），不是来自数据文件。**

#### 2.7 汇总表

| 线索 | 多任务? | 组合 ≥3 位点? | 逐基因型×逐条件可下载? | 对"选哪个起点" | 裁决 |
|---|---|---|---|---|---|
| **FLIP2** | **✗** 单条件数据的 shift 切分 | 仅继承上游（trpb = 4 位点完整，CC0） | **✗ 不存在 condition 列** | **不可用** | **排除** |
| **DHFR-TMP** | **△** 8 条件，但 6 个是同药不同浓度 | **✗** 1,000+ 不同骨架，每骨架 ~18 随机突变 | **✅** Figshare，**MIT**，archive 已核实 | 三者中最好，但**任务轴很弱** | **部分** |
| **MBE msag106** | **✅** ≈11 个真实环境 | **✗ 严格单突变** | 很可能有（Data S1–S8）但**未能下载** | **判据 1 失败** | **部分（硬伤）** |

> **额外收获**：`msag106` 是 **TEM-1 的多环境单突变扫描 + 重复实验**。它**不能**做起点选择，但它给 TEM-1 补上了一条**环境任务轴（温度 × 培养基 × 伴侣/抑制剂）**，可用于检验"同一蛋白在不同任务类型下 EOV 是否一致"。**建议放入 TEM-1 的 task panel 作为辅助轴。**

### 2.8 ⭐⭐ 推翻判据 4 缺口的发现：**原始 source data 本身带 triplicate + SEM**

**这是我此前判断错误的地方，必须显式更正。** GraphFLA 的 CSV 是**派生提取**（单列 fitness），但**上游 eLife source data 保留了完整重复结构**。以下由我**亲自 `Range` 拉取表头核实**（HTTP 206，非转述）：

| 文件 | 字节 | 内容 |
|---|---|---|
| `https://cdn.elifesciences.org/articles/71393/elife-71393-fig1-data1-v2.csv` | **12,258,680** | CR9114：表头 `genotype, h1_repa, h1_repb, h1_repc, h1_mean, h1_sem, h3_repa…h3_sem, fluB_repa…fluB_sem, pos1..pos16, som_mut` |
| `https://cdn.elifesciences.org/articles/71393/elife-71393-fig1-data2-v2.csv` | **358,244** | CR6261：同结构，`h1`/`h9` + `pos1..pos11` |

- **65,536 行 = 字面意义的完整 2^16 超立方体**；`pos1..pos16` 为二元，`som_mut` 的直方图**精确等于二项式 C(16,k)**（1,16,120,560,1820,4368,8008,11440,12870,11440,8008,4368,1820,560,120,16,1）→ **16 个可突变位点，Hamming-1 邻接完整**。
- **每个 genotype × 每个 antigen 都有 3 次生物学重复 + SEM** → **判据 4 ✅**。
- 论文已核实引用："all combinations of a set of mutations separating the germline and somatic sequences for **CR9114 (16 mutations totaling 65,536 variants)** and **CR6261 (11 mutations totaling 2,048 variants)**"；"Affinities obtained by Tite-Seq are **reproducible across biological triplicates**（…average standard error of **0.047 -logKD units** across antibody-antigen pairs）"。
- **任务结构**：CR9114 → **{H1, H3, fluB} 3 个抗原**；CR6261 → **{H1, H9} 2 个抗原**。**同一抗体框架内基因型集合完全相同** → 可以直接"在 H1 上训练选择器，问 65,536 个起点里哪些最适应 H3 / fluB"。**这是目前最干净的 held-out 对象。**

> ⚠️ **必须处理的删失陷阱**：文件里大量行被**钉在滴定边界**（我实测到 `h3_repa = h3_repb = h3_repc = 6.0, h3_sem = 0.0` 的整行）。**这些行的 SEM = 0 表示"未测到"，不是"零噪声"。** 在计算 `R_0` / 噪声天花板之前**必须先把边界钉扎行识别并剔除**，否则会把系统性删失当成完美的测量精度。这是当前最隐蔽、后果最大的一个坑。
> 滴定边界：H3/fluB 为 1e-11–1e-6 M；H1/H9 为 1e-12–1e-7 M。

> **⚠️ 轻微的 novelty 提示**：Phillips2021 论文本身已经做了 **accessible-path / epistasis-order 分析**（H1 拟合到 5 阶、H3 到 4 阶、fluB 到 1 阶）。→ 这与我们 `R_k^oracle` 的"可及路径"概念有重叠，**需引用并纳入对照**，但**它没有任务 holdout**（是在单任务内做阶数分析）。
> 代码：`https://github.com/klawrence26/bnab-landscapes`；景观浏览器 `yodabrowser.netlify.app`（**后者未核实**）。
> license：eLife 文章与 source data 默认 **CC-BY**，但**未逐文件读到 license 行 → 标记为未核实**。

**同时新增（来自并行线程，已核实）**：**CTX-M-14 活性位点成对 DMS**（Judge, Sankaran, Hu, Palaniappan, Birgy, Prasad, Palzkill, *PNAS* 2024;121(12):e2313513121）
- **17 个活性位点、49,096 个双突变**（19² × 136 = 49,096，且 16+15+…+1 = 136，**算术自洽**），在 **cefotaxime 或 ampicillin** 两个药物下筛选。
- **有误差估计**（已核实引用）："the median error value estimated based on sequencing coverage by the DMS2 program was **σ = 0.27 for cefotaxime and σ = 0.28 for ampicillin**"。
- 数据：`https://github.com/Palzkill-Lab/CTXM_epistasis`。
- **判据 1 严格意义上 ✗（只有 Hamming-2，无法建深度多步轨迹）**，但**双突变集合内的 Hamming-1 图是完整的** → **优秀的跨酶泛化测试集**，且**与 TEM-1 同属 β-内酰胺酶家族**，可作为"同家族不同酶"的复制。

---

## 3. 按判据逐条裁决

### 3.1 判据 1（≥3 位点 + 密集组合覆盖）—— **充分满足**

满足且**组合完整**的：Phillips2021_CR9114 三件套、Phillips2023 三件套、Moulana2023 四件套 + Moulana2022、Soo2021（RNA）。均 ≥10^4 变体，且为**穷举立方体**，`N_k(x)` 有严格定义。

### 3.2 判据 2（≥2 个任务，≥1 个可 held-out）—— **充分满足**

- Phillips2023：3 个抗体任务（SI06 / MA90 / G189E）
- Phillips2021：CR9114 下 3 个任务（h1 / h3 / fluB）
- Moulana：5 个任务（4 单抗 + ACE2）
- Soo2021：2 个温度（30 °C / 37 °C），8 位点 × 4 核苷酸 = 65,536 完整

> **语义警告（必须写进论文）**：抗体逃逸景观的"任务"是**不同的结合伙伴**，不是"新 enzymatic function"。它的"适应"是**逃逸结合**，蛋白不获得新催化功能。这与 TEM-1 的 AMP→AZT（新底物活性）**不是同一类 future task**。若要主张"TEM-1 不是特例"，**最干净的第二个证据必须来自酶-多底物**：`new_PTE`（2NH / butyrate）、`Lunzer2005`（NAD / NADP）、`Mira2015`（15 种抗生素）、`Frohlich21`（OXA-48: CAZ / PIP）、`Anderson2021`（6 种金属）。这些空间小，但**任务语义与 TEM-1 一致**。

### 3.3 判据 3（processed 数据可下载，逐基因型逐条件）—— **充分满足**

已用 `Range: bytes=0-119` 逐文件确认列结构，例：

```
Mira2015_TEM_AMP.csv        → sequences,pos1,pos2,pos3,pos4,fitness          (16 行)
Lunzer2005_fitness.csv      → sequences,pos1..pos6,fitness                   (512 行)
Moulana2023_CB6.csv         → sequences,pos1..pos15,fitness                  (32,768 行)
Phillips2023_SI06.csv       → sequences,pos1..pos16,fitness                  (65,536 行)
Soo2021_30C.csv             → sequences,pos1..pos8,fitness                   (65,536 行)
Bridgham2009.csv            → sequences,X,Y,Z,W,fitness                      (16 行)
```

### 3.4 判据 4（重复测量 / 可估噪声）—— **原判"不满足"，现已被推翻**

**先修正本文件此前（v0 初稿）的结论。** 我此前写"判据 4 在所有已发布文件中不满足"——**这对 GraphFLA 的 CSV 成立，但对上游原始数据不成立**。已由直接文件核实推翻：

> ✅ **Phillips2021 的 eLife source data 本身就带 3 次生物学重复 + 每个 genotype×antigen 的 SEM。**
> **已独立核实（本次亲自 `Range` 拉取表头，非转述）**：
> - `https://cdn.elifesciences.org/articles/71393/elife-71393-fig1-data1-v2.csv`（**12,258,680 B**，HTTP 206）
>   表头：`genotype, h1_repa, h1_repb, h1_repc, h1_mean, h1_sem, h3_repa, h3_repb, h3_repc, h3_mean, h3_sem, fluB_repa, fluB_repb, fluB_repc, fluB_mean, fluB_sem, pos1..pos16, som_mut`
> - `…-fig1-data2-v2.csv`（**358,244 B**）同结构，`h1`/`h9` + `pos1..pos11`

**因此正确的表述是：**

| 来源 | 判据 4 |
|---|---|
| **GraphFLA 的 `data/BioSequence/*.csv`** | ❌ 单列 fitness，无重复（这是**派生提取**，不是原始数据） |
| **上游原始数据（eLife CDN / Desai 实验室）** | ✅ **有 triplicate + SEM** —— 已核实 Phillips2021；Moulana 系列同实验室，极可能同样有 |
| **TEM-1** | ✅ triplicate（原始数据，SD < 10%） |
| **AncSR1** | ✅ 2 次独立 FACS-seq（但 processed 表位置**未找到**） |

> **操作结论（会改变 M0 的动作顺序）**：**判据 4 不再是"需要回源碰运气"的缺口，而是一个已确认存在的下载动作。** P0-1 从"回源找重复"降级为"**换源下载 eLife CDN 的 fig-data 文件**"。
> ⚠️ **但仍有一个真陷阱**：CR9114 文件里 H3/fluB 的许多行被**钉在滴定边界值上**（我看到 `h3_* = 6.0, h3_sem = 0.0` 的整行）→ **这些行的 SEM = 0 是"未测到"而非"无噪声"**。做 `R_{0}` / 噪声天花板之前**必须先把边界钉扎行识别并排除**，否则会把删失当成零噪声。这是目前最容易被忽略的一个坑。
- 后果：H1 的"between-parent variation 明显高于实验噪声"**目前无法直接检验**。

**可选的补救路径（按优先级）：**
1. **⭐ 直接改用 AncSR1（见 2.6 节）作为 H1 的检验床**：它是**唯一同时满足判据 1+2+4** 的候选（4 位点完整 20^4 × {ERE, SRE} × 2 次独立 FACS-seq 重复 + 可估 SEM）。**唯一阻塞是 processed 数据的存放位置未核实。** → 拿到它，H1 就不再依赖 TEM-1 单点。
2. 去原始论文的 data availability 取带重复的数据（Desai 实验室的抗体逃逸数据通常有多轮分选/重复；eLife 论文有明确的数据仓库）。
3. 用 ProteinGym raw 里**带显式重复列**的单突变多条件数据集（`HSP82_YEAST_Flynn_2019`：2 replicate + 5 条件；`ADRB2_HUMAN_Jones_2020`：4 浓度 × 2 replicate；`R1AB_SARS2_Flynn_2022`）做**外部噪声尺度校准**（见 2.5 节）。
4. 复用 **TrpB 论文的噪声注入 null model**（2.6 节）作为噪声处理范式。
5. 用**层级/邻域结构**做噪声代理：完整立方体中，同一 fitness 水平上的邻域散布含"地形不平 + 噪声"两部分，可借重复任务（同空间不同抗体）的秩一致性给噪声上界。
6. 若最终仍无法取得，则 **Phase I 的证据天花板应降级为"cross-task reproducibility of starting-point effects"，而不是"起点差异 > 噪声"**。

### 3.5 汇总裁决

| 等级 | 定义 | 归属 |
|---|---|---|
| **L3++ 四条全满足且已核实可下载** | 判据 1+2+3+4 **全部满足** | **⭐⭐ 蛋白：`CR9114`（Phillips 2021 eLife source data）** —— 完整 2^16 = 65,536 × 3 抗原 × **3 次生物学重复 + SEM**，CDN 直连；**`CR6261`** 同结构（2^11 × 2 抗原）。⚠️ 需先剔边界钉扎行<br>**⭐⭐ RNA：`glmS` 核酶（RNAGym RAW 包，Andreasson 2020）** —— 67 位点穷举单+双突变 × 5 个配体浓度 × 每次测量带 `_stErr`，CC-BY-4.0。**是 RNA，只能作模态对照**（§2.5d） |
| **L3+ 判据 1+2+4 满足，判据 3 待核实** | — | **⭐ `AncSR1`** —— 4 位点完整 20^4 × {ERE,SRE} × 2 背景 × 2 次独立重复；**机器可读 deposit 未找到** |
| **L3 合格候选（strict multi-task）** | 判据 1+2+3 全满足，判据 4 可经补救获得 | **Phillips2023（GraphFLA 组内首选）**、**Phillips2021_CR9114**、**Moulana2023+2022（需处理缺失）**、**⭐ Jalal2020_NBS/parS（20 字母表 + 完整 20^4 + 2 任务，DE 机器可原样复用）**；RNA 对照：**Soo2021** |
| **L2 部分合格** | 任务是真多环境，但空间 <10^4，不能模拟预算型 DE | Mira2015（TEM ×15 抗生素，**与主数据同蛋白**）、Lunzer2005、Anderson2021、Michael2024、Wu2020、Bakerlee2022、Hall2019、Frohlich21、Khan2011Flynn2013、Tamer、Lozovsky_DHFR、Ogbunugafor22、**new_PTE** |
| **L1 单任务密集** | 只支持 starting-point / N_k / 跨 landscape 复现 | GB1、TrpB4+TrpB3A–3I、Papkou DHFR、Kuo2020、Westmann2024、Poelwijk2019、Bendixsen2019、Tu2022、Podgornaia2015、Lite2020 等 |
| **排除** | 见 2.4 | 群落景观、非生物模态、过稀疏、未发表 |

---

## 4. 结论

**能找到合格候选，且不需要"proof of principle"降级。而且比预期多了两个不同性质的选项。**

1. **可立即回答"TEM-1 是不是特例"的候选至少 5 个**：`AncSR1`、`Jalal2020`、`Phillips2023`、`Phillips2021_CR9114`、`Moulana2023+2022`。其中 **4 个来自同一个 MIT 仓库（GraphFLA），今天就能下载**。

2. **三个"最佳"取决于你优先保哪一条判据**：

   | 若优先保… | 选 | 理由 |
   |---|---|---|
   | **判据 4（噪声）** | **⭐ AncSR1**（Starr/Picton/Thornton, *Nature* 2017） | **唯一**同时满足 1+2+4：4 位点完整 20^4 × {ERE, SRE} × **2 次独立 FACS-seq 重复 + 可估 SEM**。阻塞项：processed 数据位置**未核实** |
   | **判据 3（确定性下载）** | **Phillips2023** | 16 位点完整 2^16 × 3 抗体任务，缺失率 0.01–0.04%，**今天就能 `raw` 下载**，不需要联系作者 |
   | **与酶/DE 文献的可比性** | **⭐ Jalal2020_NBS/parS** | **4 位点 × 20 氨基酸 = 完整 160,000 × 2 任务**，与 GB1（149,361）/TrpB4（159,129）**空间结构同类** → `search_policies.py` 可**原样复用**，deg = 76 |

   > **推荐组合**：`AncSR1`（保判据 4）+ `Jalal2020`（保 DE 可比性）+ `Phillips2023`（保多任务与零摩擦下载）+ `Moulana2023`（保 5 任务面板）。**四者互不重叠，一次买到全部证据维度。**

3. **但"跨模态/跨蛋白复现"要比"再找一个蛋白"更值钱**：建议证据链排成
   - 主：TEM-1（AMP → AZT，酶-新底物，triplicate）
   - 酶-多底物第二例：`new_PTE`（2NH / butyrate）或 `Lunzer2005`（NAD / NADP）
   - **同字母表高密度多任务**：`Jalal2020`（ParB × 2 DNA 位点）与/或 `AncSR1`（受体 × ERE/SRE，带重复）
   - 高密度多任务复制：`Phillips2023` / `Moulana2023`（结合任务）
   - 模态对照：`Soo2021`（RNA × 2 温度）
   这样"EOV 存在"的主张既跨蛋白、又跨任务类型、又跨模态，而不是"又一个酶"。

4. **判据 4 的缺口已从"全部缺失"降级为"部分缺失"**：`AncSR1` 补上了它，TEM-1 本身有 triplicate；**仍缺的是 GraphFLA 密集景观（Phillips / Moulana / Jalal）的重复结构**。若最终拿不到，则 H1 在这三者上的表述必须从"起点差异超过实验噪声"改为"起点效应在不同 future task 间可复现"——**可辩护但更弱**；而在 `AncSR1` 与 TEM-1 上仍可做完整版 H1。

5. **附带重大收益：基础设施不必自建（但要注意两个已有实现）。** GraphFLA 已发布 155 个 landscape + 20 个特征的参考实现（`pip install graphfla`，MIT）；**TrpB 论文已发布"从每个起点出发"的 DE 基准 + 噪声注入 null model**。→ `eov/landscape.py`、`metrics.py` 复用 GraphFLA；`search_policies.py` 的基线复用 TrpB 的 3 种 DE。自研精力集中在 `tomorrow_test.py` 与 **selection regret** 两件事上。

6. **附带重大发现：TEM-1 的 future task 不必只有 1 个。** `Mira2015_TEM_*` 是同一蛋白 × 15 种抗生素的完整 2^4 空间（16 基因型）。它不能模拟 B=96 的 DE，但**可以给出 15 个真实的 held-out 任务面板**，用于检验 `Corr(EOV_τ1, EOV_τ2)`——这正是 MODIFY 判据里那个关键量。**前提是先读懂它那列 fitness（中位数 = 0，见 8.1-3）。**

7. **一个必须立刻改的实现决定**：`Lunzer2005`（2×4×8×2×2×2）、`Wu2020`（4×4×3×…）与 TEM-1（13 位点 / 18 突变 / 度 18）都证明**混合字母表乘积空间是常态**。→ **`eov/landscape.py` 从第一行就要按"混合字母表乘积空间"写，不要按二元超立方体写。**

8. **一个必须立刻改的数据审计规则**：**论文表格声明的规模 ≠ 仓库文件的实际规模**（Papkou DHFR：论文 99.7% vs 仓库 **51.6%**；Westmann：65,536 vs **17,765**）。→ **DATA_AUDIT 一律以实际文件行数/unique 数为准。**

---

## 5. 下一步核实清单（按优先级）

### P0 —— 决定 H1 能不能做（最高优先，1–2 天）

1. ~~**回源取噪声结构（判据 4）**~~ → **✅ 对 Phillips2021 已解决（见 2.8 节与 3.4 节）**：eLife source data **自带 3 次生物学重复 + 每 genotype×抗原的 SEM**，已亲自拉取表头核实。
   **剩余动作（已收窄）：**
   - **(a)** 对 **Phillips2023**（CH65：SI06/MA90/G189E）做同样的 source-data 抓取 —— 同一实验室、同一期刊，**极可能有同结构的 `*_rep*` / `*_sem` 列**。这是当前**回报最高的一个下载动作**。
   - **(b)** 对 **Moulana2022/2023**（SARS-CoV-2 RBD）抓 Desai 实验室的原始表，找 `replicate` / `bin` / `tile` / `library` 列。
   - **(c)** ⚠️ **删失处理**：识别并剔除**滴定边界钉扎行**（`*_sem = 0` 且值 = 边界值），否则噪声会被系统性低估。**这一步必须在算任何 `R_0` / 噪声天花板之前完成。**
   - **(d)** **AncSR1** 的 processed 表位置仍未找到 → 见 P0-0（若采纳）。

2. ~~**确认 `pos1..posN` 取值域**~~ → **已完成（见第 8 节）**。28 个文件已抽样核实：Phillips / Moulana / Michael2024 / Bakerlee / Guerrero / Khan / Ogunbugafor 严格 `0/1`；`Soo2021` 为 `A/C/G/T`。**完整立方体成立，P0-2 关闭。** 剩余待办降级为：把 `pos` 域检查写进 DATA_AUDIT 的自动校验脚本，对**全部 163 个文件**跑一遍（本次只做了 44 个的行数与 28 个的取值域）。

3. **确认 fitness 语义与量纲**
   - 动作：读各文件 fitness 列的 min/max/分布；对照原始论文的 Methods。
   - 验证什么：是 log 亲和力（Moulana 样本值 ≈ 9.8）、escape fraction、还是富集比。**跨任务归一化方案完全取决于这一点。**

### P1 —— 决定证据链结构（3–5 天）

4. **建立"任务面板"清单并计算跨任务秩一致性**
   - 对每个 L3 候选，计算同一批基因型在不同任务间的 Spearman ρ（任务相似度矩阵）。
   - 验证什么：held-out 任务与 today 任务的**真正差异度**。若 ρ ≈ 1，说明"任务"其实没变，Tomorrow Test 是假的。**这是最容易自欺的一步。**

5. **Moulana 面板的缺失-偏差量化**
   - 动作：S309（0% 缺失）vs CB6（49.6% 缺失）的缺失模式分析。缺失是否与 fitness 相关（MNAR）？
   - 验证什么：held-out 任务上的可比较基因型交集大小，以及缺失是否引入系统偏差。

6. **逐个确认 license**
   - 动作：仓库根 `LICENSE` = MIT（已核实），但**这是代码仓库的 license，不自动覆盖第三方数据**。
   - 要做的：对将使用的每个 landscape，回到原始论文确认其数据再分发条款（尤其 eLife = CC-BY 通常宽松，Science/PNAS 各异）。
   - **当前状态：全部"未核实"。** 这是 DATA_AUDIT 必须补的一列。

### P2 —— 补全检索面（并行进行中）

7. ~~**FLIP2**~~ → **✅ 已完成，见 2.7 ①：排除。** Zenodo 10.5281/zenodo.18433203，CC-BY-4.0；44 个 CSV 全部无 condition 列；GB1 两个文件逐字节同值 → **是 distribution-shift 切分，不是多任务**。
8. ~~**DHFR-TMP 梯度**~~ → **✅ 已完成，见 2.7 ②：部分。** 判据 1 ✗（1,000+ 骨架 × 每骨架 ~18 随机突变）；9 条件但 6 个是同药浓度；数据在 Figshare（**MIT**）。⚠️ **原引用的 `PMC11785229` 是 preprint，已发表版是 `PMC12346277`。**
9. ~~**Mol Biol Evol `10.1093/molbev/msag106`**~~ → **✅ 已完成，见 2.7 ③：多环境 ✅（≈11），但严格单突变 → 判据 1 硬性 ✗。** 它研究的就是 **TEM-1**，可为 TEM-1 补一条环境任务轴。补充材料被 OUP Cloudflare 403 挡住，**未能取得**。
10. **`ChenFT22` = Chen, Fowler & Tokuriki, Nat Ecol Evol 6(4):427–438, 2022**：**GraphFLA 引用了它但没放进 155 表**。这是一篇**多环境蛋白景观**工作，可能是重要遗漏项。**状态：仍未核实。**
11. ~~**ProteinGym / RNAGym / CIS-BP 的多条件条目**~~ → **已完成（见 2.5 节）**。结论：ProteinGym **多条件 = 单突变**、**多突变密集 = 单条件**，两者不相交；CIS-BP 无逐基因型多条件数据。raw 包地址已核实。**RNAGym 的 assay 级多条件调查仍在进行。**

---

## 6. Novelty 风险提示（**必读**）

### 6.1 最高风险（**两个**）：GraphFLA 的"景观几何→DE"，以及 TrpB 的"从每个起点出发的 DE 基准"

**已核实（读自论文 LaTeX 源码与 HTML 全文）**，GraphFLA 论文明确包含：

- **Appendix F / Section 4.5 "Application to directed evolution"**
- 用了 **20 个 3-/4-位点饱和蛋白景观**（20^3 或 20^4）
- 评估 **5 种 DE 方法**：(1) greedy adaptive walk；(2) MLDE；(3) MLDE + zero-shot warm start；(4) ALDE；(5) ALDE + zero-shot warm start
- 每种 **100 次随机初始化**，指标 = 找到的最优变体的 **fitness percentile**
- **结论原文（译文）**："basic DE 方法在 benign landscape 上容易接近全局最优，但在更 rugged、更 epistatic、更不可导航的景观上表现挣扎；5 种 ML/主动学习引导方法也受 epistasis 影响，但更先进的方法（MLDE+zero-shot、ALDE 变体）更稳健。"
- 论文中还有一张表：**"Spearman correlation between fitness landscape features and the performance of 5 directed evolution (DE) approaches on 20 combinatorially complete protein fitness landscapes."**

**这对我们的直接威胁**：`landscape 特征 → DE 成功率` 这个映射已经被发表（NeurIPS 2025 Spotlight）。如果 EOV 只是"再算一遍特征和 DE 结果的相关性"，**增量不足**。

**必须写清的差异（我建议的定位）：**

| 维度 | GraphFLA | 我们的 EOV |
|---|---|---|
| 分析单位 | **整个 landscape**（全局特征：γ、FDC、φ_lo、NFC、η…） | **景观内的单个起点基因型** |
| 起点处理 | 100 次**随机**初始化后平均 | **起点本身是被估值的对象**（`EOV(x)`） |
| 任务 | **单任务**，无 held-out 概念 | **多任务，future task 完全隐藏** |
| 指标 | 达到的 max fitness percentile | **selection regret（选错起点的代价）** |
| 分解 | 无 | **`R_0` / `R_k^oracle`（景观机会）/ `R_{B,π}`（预算+策略可及）三层分离** |
| 目标 | 解释"模型为什么在这个任务上差" | 回答"今天该选哪个 parent 去面对未知任务" |

> **一句话定位**：GraphFLA 问"**什么样的景观好演化**"；EOV 问"**在同一张景观上，今天看起来一样好的两个起点，面对未知任务时的选择权是否不同，以及我们能否提前选出对的**"。**任务 holdout 是 GraphFLA 完全没有的维度，这是我们唯一稳固的护城河。**

#### 6.1b 🔴 更贴近我们的风险：TrpB 论文已经发表了"**从每一个起点出发**"的 DE 基准

**已核实**（Johnston et al., *PNAS* 2024, doi:10.1073/pnas.2400439121）：该论文在 159,129 个变体的完整 20^4 景观上**已经做了**：

- 3 种 in-silico directed evolution 策略；
- **从每一个起点出发的 max fitness 的 ECDF**；
- local optima / accessible-path 分析；
- **注入噪声的 null model**。

> **"从每个起点出发的最大适应度分布"在数学上就是单任务的 `R_{B,π}(x,τ)`。**
> 也就是说：**EOV 的 operational 组件（预算化搜索 × 逐起点结果）在单任务情形下已被发表**，而且是在一个完整 20^4 酶景观上。

**这对我们意味着什么**
1. **不能把"我们会模拟每个起点的 DE 结果"当作新颖性。** 必须显式引用 TrpB 的这套基准，并说明我们的增量是**任务维度的 holdout**，不是起点维度的模拟。
2. **但这是好消息的一半**：他们的 3 个 DE 基线 + 噪声 null model **可以直接拿来当我们的 `search_policies.py` 与噪声处理范式**，省掉一整块开发与辩护成本。
3. **风险的具体形态**：审稿人会说"你在 TrpB 上做的事已经有人做了，你只是换了个任务"。**我们的回答必须是**：TrpB 的 ECDF 是**单任务、同分布**下的起点差异；**他们从未问过"把任务换掉之后，今天的起点排序是否还成立"**。→ **`Corr(EOV_τ1, EOV_τ2)` 与 selection regret 是我们唯一不能被他们覆盖的量。**
4. **行动**：把 TrpB 论文的 DE 实现**列为必读的第一篇**（在 GraphFLA 之前），并在 PHASE1 的 novelty 声明里逐条对照它的图。

### 6.2 已存在的、概念上与我们重叠的具体特征（必须作为 baseline 纳入）

GraphFLA 已经实现并发布了这些**per-config 可及性**度量；我们的 `R_k^oracle` / adaptive-accessible potential **在概念上有重叠**，必须显式比较，否则会被审稿人指出：

- `global_optima_accessibility` —— 处于通往全局最优的 fitness-monotone 路径上的配置比例
- `local_optima_accessibility` / `mean_path_length_to_local_optima` —— 指定局部最优的可及性
- `mean_path_length_to_global_optimum` / `mean_distance_to_global_optimum`
- `evolvability_enhancing_mutations` (φ_EE) —— **"增加进入更适应区域机会的突变比例"**，这个名字几乎就是 evolvability
- `extradimensional_bypass` —— reciprocal-sign motif 通过额外维度绕过的比例
- `basin_fitness_correlation` (BFC) —— 盆地大小与峰适应度的相关

> **行动建议**：把 GraphFLA 的 20 个特征**全部**作为 H2 的 proxy baseline 集。这样"EOV 不是旧概念换名"的论证才有说服力——**我们是在和最强的现有特征集比较，而不是和 stability/promiscuity 两个弱 baseline 比较。**

### 6.3 其他风险

| 风险 | 说明 |
|---|---|
| **SSMuLA** | 已实现 DE / MLDE / ftMLDE / ALDE 模拟，含 96/384 预算、50 replicates、Held-out 序列切分（<https://github.com/fhalab/SSMuLA>，Zenodo 10.5281/zenodo.13910506）。我们的 `search_policies.py` **本质上会重建它**。GraphFLA 论文里引用的 ALDE 工作（`YangLBHAKHYA25`）即此线。→ **应复用而非重写**，且必须说明差异（SSMuLA 无 future-task holdout）。 |
| **MAGALLEN** | 已知唯一的生物景观分析包（C 实现，10^5 规模）。GraphFLA 论文将其列为唯一先例。影响小，但引用需完整。 |
| **"Multi-environment fitness landscape" 已有工作** | `ChenFT22`（Chen, Fowler & Tokuriki, Nat Ecol Evol 2022）标题即 "phenotype-environment-fitness landscape"；`Anderson2021` 标题即 "adaptive landscape ... shaped by **environment-dependent epistasis**"。→ **"多环境"本身不是新意**，新意必须在"起点估值 + 任务 holdout + regret"。 |
| **数据组装的贡献被抹平** | GraphFLA 已公开 155 个 landscape。**"我们收集了一个 landscape panel"不再是贡献**，只能在方法与致谢中引用。好消息是省下大量时间。 |

### 6.4 与论文原文数字的不一致（供 DATA_AUDIT 记录）

- 论文正文称 **155 个 dataset / "more than 67 studies"**，另一处写 **"61 works"**；而我抓取的 TeX 长表实际 **149 行**，仓库 `data/BioSequence/` 实际 **163 个 CSV**。→ 三个数字互不相同。**引用时不要写"155"以外的推断，建议写"该仓库发布的 landscape 集合（论文称 155 个）"。**
- 论文表格里 TEM 的缩写写作 `TEM-FSP`，仓库文件名是 `Mira2015_TEM_FEP.csv`（应为 cefepime）→ **论文表格有笔误**。
- 论文引用键 `DoudGLMDFM24`（Doud et al. 2024, Nat Commun 15:863），仓库文件名前缀是 `Michael2024_`（Michael B. Doud 的名）→ 命名不一致。

---

## 7. 本文件未核实项（明确列出，不猜测）

1. 任何 landscape 的**原始论文级 license**。
2. ~~已核实文件的 `pos` 列完整取值域~~ → **已核实 28 个文件（见第 8 节）**；**其余 135 个文件未做**。
3. **replicate / 噪声结构**（判据 4）—— 全部未取得。ProteinGym raw 里有带重复列的单突变多条件数据集（2.5 节），可作外部校准，但**密集数据的噪声仍未拿到**。
4. `Jalal2020_*`、`daSilva2010_*`、`Wu2020_*`（除 HK68/Mos99 外）、`Khan2011Flynn2013_*`（除 DM25 外）等的**精确行数与位点结构**（未逐个做行数统计）。
5. FLIP2 / DHFR-TMP / MBE msag106 / RNAGym assay 级多条件的结论（并行检索中，**尚未返回**）；~~ProteinGym 多条件条目~~ → **已完成，见 2.5 节**。
6. `Soo2021` 的 RNA 具体分子与"温度任务"的生物学解释（已确认位点域为 A/C/G/T、8 位点、2 温度）。
7. Mira2015 的 15 个抗生素缩写与具体药物的对应关系；**以及该文件 fitness 列中位数为 0 的确切含义**（见 8.1-3，这是使用该面板的前提）。
8. `new_PTE_*`、`NEW_Chen2023_CreiLOV`、`Palmer_*`、`NEW_Rotrattanadumrong2022` 等带 `new_`/`NEW_`/无文献前缀文件的**文献归属**。
9. 仓库 `data/` 下 `Microbiome` / `ChemBio` / `Chemistry` / `Materials` / `Pharmacology` 五个子目录的**具体内容清单**（本次未展开；已确认目录存在）。
10. **跨任务可比较基因型交集**：Moulana 五个任务的缺失是否 MNAR、交集实际多大（**未计算**；这是 P1-5 的核心动作）。
11. **跨任务秩一致性矩阵** `Corr(EOV_τ1, EOV_τ2)` 与任务相似度：**未计算**（P1-4）。

---

## 8. 附：逐文件核实数据（位点取值域 + fitness 量纲）

对 28 个关键文件做了内存内解析（抽样 400 行统计各 `pos` 列的 distinct 值；对全部行统计 fitness 的 min/median/max）。**未落盘。**

| 文件 | 行数 | pos 列取值域（前 3 列，抽样） | fit_min | fit_med | fit_max |
|---|---|---|---|---|---|
| `Phillips2023_SI06.csv` | 65,536 | `0/1` | **-9.762** | -6.060 | -6.000 |
| `Phillips2023_MA90.csv` | 65,536 | `0/1` | **-10.526** | -9.473 | -7.948 |
| `Phillips2023_G189E.csv` | 65,536 | `0/1` | **-10.331** | -8.770 | -6.000 |
| `Phillips2021_CR9114_h1.csv` | 65,536 | `0/1` | **+7.000** | 9.366 | 9.835 |
| `Moulana2023_S309.csv` | 32,768 | `0/1` | +7.686 | 8.877 | 10.013 |
| `Moulana2023_CB6.csv` | 32,768 | `0/1` | +5.000 | 9.160 | 10.561 |
| `Moulana2022_ACE2.csv` | 32,768 | `0/1` | +6.876 | 8.777 | 10.040 |
| `Soo2021_30C.csv` | 65,536 | **`A/C/G/T`** | -6.766 | -2.452 | 1.813 |
| `Mira2015_TEM_AMP.csv` | 16 | `L/M \| E/K \| G/S` | -1.905 | **0** | **0** |
| `Mira2015_TEM_CAZ.csv` | 16 | `L/M \| E/K \| G/S` | -1.655 | **0** | **0** |
| `new_PTE_catact_2NH.csv` | 64 | `D/E \| H/R \| F/L` | -0.093 | 1.559 | 3.059 |
| `new_PTE_catact_butyrate.csv` | 64 | `D/E \| H/R \| F/L` | -0.801 | 0.509 | 1.990 |
| `Anderson_MPH_MnPTM.csv` | 32 | `L/R \| `**`-/S`**` \| H/L` | -0.693 | 0.292 | 1.338 |
| `Anderson_MPH_CuPTM.csv` | 32 | `L/R \| `**`-/S`**` \| H/L` | -0.387 | 0.674 | 2.212 |
| `Lunzer2005_fitness.csv` | 512 | `D/R \| D/E/K/N \| F/H/I/K/L/N/Q/Y` | 45.657 | 94.327 | 100.612 |
| `Lunzer2005_nad.csv` | 512 | 同上 | 6.219 | 7.715 | 9.033 |
| `Lunzer2005_nadp.csv` | 512 | 同上 | 5.762 | 8.353 | 10.744 |
| `Bakerlee2022_hap_37C.csv` | 1,022 | `0/1` | -0.008 | 0 | 0.018 |
| `Hall2019_Glucose.csv` | 32 | `0/1` | 0.966 | 1.179 | 1.304 |
| `Wu2020_HK68.csv` | 576 | `E/H/K/Q \| E/G/K/N \| F/S/Y` | -2.442 | 0.761 | 3.392 |
| `Michael2024_base.csv` | 512 | `0/1` | -7.474 | -4.005 | 3.477 |
| `Tamer_DHFR_kcat_trajr.csv` | 32 | `L/P \| A/T \| L/R` | **-2.925** | -0.041 | 0.002 |
| `Tamer_DHFR_ki_trajr.csv` | 32 | `L/P \| A/T \| L/R` | **0** | 2.128 | 5.006 |
| `Guerrero2019_E_coli_WT.csv` | 8 | `0/1` | 0.334 | 0.374 | 0.412 |
| `Khan2011Flynn2013_DM25.csv` | 32 | `0/1` | -0.001 | 0.073 | 0.123 |
| `Frohlich21_OXA-48_ic50_CAZtraj1.csv` | 16 | `A/V \| F/L \| A/S` | -0.002 | 0.090 | 1.630 |
| `Lozovsky_DHFR_ic50_c57.csv` | 16 | `I/N \| C/R \| N/S` | -0.301 | 0.602 | 2.107 |
| `Ogbunugafor22_pyr.csv` | **15** | `0/1` | 1.000 | 1.282 | 1.450 |

### 8.1 从这张表得出的四个**必须写进协议**的结论

1. **位点取值域已确认**：Phillips / Moulana / Michael2024 / Bakerlee / Guerrero / Khan / Ogbunugafor 均为严格 `0/1` → **完整布尔立方体成立，deg = 位点数（16 / 15 / 9 / 10 / 3 / 5 / 4）**。`Soo2021` 为 `A/C/G/T`，8 位点 × 4 → deg = 8×3 = **24**。
   → 第 5 节 P0-2 可以关闭。

2. **fitness 量纲在任务之间根本不可比（硬证据）**：
   - Phillips2023 三件套是**负值**（-10.5 ~ -6），Phillips2021_CR9114 是**正值**（7 ~ 9.84）。
   - `Tamer_DHFR`：`kcat` 范围 **[-2.925, 0.002]**，`ki` 范围 **[0, 5.006]** —— 同一个蛋白、同一个空间，两个任务量纲完全不同。
   → **B4（跨 task 归一化）不是理论担忧，是当场就会爆炸的 bug。** 直接用原始 fitness 做 `R_{B,π}` 或 regret，跨任务比较必然错误。必须按 task 内部 robust normalization，且 WT/dead 锚定方案要先验证这些数据里是否真有 WT 与 dead 行。

3. **`Mira2015_TEM_*` 的 fitness 中位数 = 0、最大值 = 0**，说明它**不是连续活性量表，而更像"相对 WT 的 log 倍数（0 = WT 水平）"或某种阈值化/折叠变化矩阵**。→ 在第 5 节 P2 把它当"任务面板"用之前，**必须先读懂这一列**，否则 15 个任务面板是假的。

4. **`Anderson2021_MPH` 的 pos2 取值域是 `-`/`S`** —— 这是一个**缺失/indel 状态**，不是氨基酸替换。→ 建 Hamming 图时这个位点必须特殊处理（否则 `N_k(x)` 的"单步突变"定义在这个位点上不成立）。

### 8.2 另一个结构性发现：混合字母表空间是常态，不是例外

`Lunzer2005` 的 6 位点取值域为 `D/R`(2) × `D/E/K/N`(4) × `F/H/I/K/L/N/Q/Y`(8) × 2 × 2 × 2 = **512**，`Wu2020` 为 `E/H/K/Q`(4) × `E/G/K/N`(4) × `F/S/Y`(3) × … = **576**。

> **这意味着"Hamming-1 图"不能假设是超立方体。** 每个节点的度 = `Σ(该位点等位数 − 1)`，且**度是常数**（乘积空间的性质），但**不同位点的分支因子差异可达 4 倍**。
> 这与 TEM-1 的结构完全一致（13 位点 / 18 突变 / 度 = 18）。→ **`eov/landscape.py` 从一开始就必须按"混合字母表乘积空间"写，而不是按二元立方体写。** 这是一个现在花 10 分钟、以后省一周的决定。

### 8.3 ⚠️ 仓库数据质量问题（**必须在 DATA_AUDIT 里逐个核对，不能引用论文表格数字**）

我把论文表格里声明的 `Space` 与仓库里**实际文件行数**做了对比，发现**多处不一致**：

| 文件 | 论文表格声明 | **实际文件行数** | 覆盖率 | 判定 |
|---|---|---|---|---|
| `Papkou2023_DHFR.csv` | 4^9 = 262,144（正文称实测 261,382 = 99.7%） | **135,178** | **51.6%** | ⚠️ **严重不符** |
| `Westmann2024.csv` | 4^8 = 65,536 | **17,765** | **27.1%** | ⚠️ 严重不符 |
| `Kuo2020.csv` | 4^9 = 262,144 | **197,890** | 75.5% | ⚠️ 不符 |
| `Domingo2018.csv` | 2^6×3^4 = 5,184 | **4,176** | 80.6% | ⚠️ 不符 |
| `Lite2020_ParD2.csv` | 20^3 = 8,000 | **7,882** | 98.5% | 轻微 |
| `Tu2022_TEV.csv` | 20^4 = 160,000 | **159,132** | 99.5% | 轻微 |
| `Johnston2024_TrpB3A.csv` | 20^3 = 8,000 | **7,971** | 99.6% | 轻微 |
| `Wu2016_GB1.csv` | 20^4 = 160,000（论文称 149,361 = 93.4%） | **149,361** | 93.4% | ✅ 一致 |
| `Johnston2024_TrpB4.csv` | 20^4 = 160,000（PNAS 称 159,129） | **159,129** | 99.5% | ✅ 一致 |
| `Poelwijk2019.csv` | 2^13 = 8,192 | **8,192** | 100% | ✅ 一致 |
| `Bendixsen2019_hdv.csv` | 2^14 = 16,384 | **16,384** | 100% | ✅ 一致 |

**另外两个仓库缺陷（已核实）**：

1. **`benchmarks/_datasets.py` 引用了不存在的文件**：它写的是 `BioSequence/Papkou2023_DHFR_RAW.csv`，但我实测该 URL 返回 **404 Not Found**；仓库里实际是 `Papkou2023_DHFR.csv`。→ 照抄该 benchmark 配置会直接崩。
2. **`Skwara2023_Butyrate.csv` 格式损坏**：表头有 27 列（`sequences` + 25 个 pos + `fitness`），但第 2 行只有 3 个字段（`1000000000000000000000000,1,0`）。→ 该文件不可直接解析，且它同时是唯一一个有重复行的文件。

**最后一个新候选（不合格但需记录）**：`NEW_Chen2023_CreiLOV.csv`（CreiLOV 荧光蛋白）——**20 个二元位点，165,428 行 = 2^20 的 15.8%**，`pos` 严格 `0/1`，fitness 为正（≈4.02 起）。**不是完整空间**，但 20 位点 × 16.5 万变体的随机采样使每节点期望实测邻居数 ≈ 20 × 0.158 = 3.2 → **邻域过稀，`N_k(x)` 不可靠**，判据 1 不满足。文件前缀 `NEW_` 且无文献归属。

**其余已核实行数（补齐 2.3 / 2.4 节未列出的部分）**：

| 文件 | rows | uniq | 文件 | rows | uniq |
|---|---|---|---|---|---|
| `Jalal2020_NBS.csv` | **160,000** | 160,000 | `Jalal2020_parS.csv` | **160,000** | 160,000 |
| `NEW_Chen2023_CreiLOV.csv` | 165,428 | 165,428 | `Tu2022_TEV.csv` | 159,132 | 159,132 |
| `Lite2020_ParD2.csv` | 7,882 | 7,882 | `Michael2024_Lspec.csv` | 512 | 512 |
| `daSilva2010_CCR5.csv` | 32 | 32 | `daSilva2010_CXCR5.csv` | 32 | 32 |
| `Wu2020_Bei89.csv` | 576 | 576 | `Wu2020_NDako16.csv` | 576 | 576 |
| `Khan2011Flynn2013_DM25_guanazole.csv` | 32 | 32 | `Lozovsky_DHFR_ic50_c61.csv` | 16 | 16 |
| `Palmer2015.csv` | 64 | 64 | `Palmer_DHFR_ic75.csv` | 64 | 64 |
| `Hall2020_NfsA_ec50_2039.csv` | 128 | 128 | `Hall2010_haploid.csv` | 64 | 64 |
| `Bank2016a.csv` | 640 | 640 | `Centurion2019.csv` | 3,072 | 3,072 |
| `Schulz2025.csv` | 1,024 | 1,024 | `Domingo2018.csv` | 4,176 | 4,176 |
| `Meini2015.csv` | 16 | 16 | `Malcolm1990.csv` | 8 | 8 |
| `Chou2011.csv` | 16 | 16 | `Whitlock2000.csv` | 32 | 32 |
| `deVisser2009.csv` | 32 | 32 | `Sunden_AP.csv` | 32 | 32 |
| `Bendixsen2019_hdv.csv` | 16,384 | 16,384 | `Weinreich2006Tan2011_Tan2011.csv` | 32 | 32 |
| `Weinreich2006Tan2011_Weinreich2006.csv` | 32 | 32 | `Skwara2023_Butyrate.csv` | 1,561 | **577** ⚠️ |

> **操作结论**：**任何进入 Phase I 的数据集，都必须以"仓库文件实际行数/unique 数"为准写进 DATA_AUDIT，不能用论文表格的 `Space` 列。** Papkou DHFR 的例子（论文 99.7% vs 仓库 51.6%）说明这个误差可以达到 **2 倍**，而且它恰好是原 Phase I 计划里的一个核心数据集。

---

## 9. 关键标识符与访问路径汇总（DATA_AUDIT 可直接引用）

**说明**：本节只列**已核实可解析**或**已由并行线程 API 核实**的标识符。`license` 列区分「已核实」与「未核实」——**未核实的不要写进再分发声明**。

### 9.1 第一优先（建议直接进主 panel）

| 对象 | 访问路径 | 规模（已核实） | license |
|---|---|---|---|
| **CR9114** | `https://cdn.elifesciences.org/articles/71393/elife-71393-fig1-data1-v2.csv`（**12,258,680 B**，我实测 HTTP 206） | 65,536 行 = 完整 2^16；3 抗原 × 3 重复 + SEM | ⚠️ eLife 默认 CC-BY，**未读到逐文件 license 行** |
| **CR6261** | `https://cdn.elifesciences.org/articles/71393/elife-71393-fig1-data2-v2.csv`（**358,244 B**） | 1,917 行；2^11；2 抗原 | 同上 |
| CR9114/CR6261 代码 | `github.com/klawrence26/bnab-landscapes` | — | code repo MIT（**未独立核实**） |
| **TEM-1CML** | Zenodo **10.5281/zenodo.21481201**；GitHub **msadikyildiz/Gaszek_Yildiz_Meng_2025** | 55,296 × {AMP 6 剂量, AZT 8 剂量} × triplicate | ✅ **GPL-3.0-or-later** |
| **GraphFLA 全部 landscape** | `https://raw.githubusercontent.com/COLA-Laboratory/GraphFLA/main/data/BioSequence/<文件>.csv` | 163 个 CSV | ✅ 仓库 MIT（**底层数据许可单独未核实**） |
| **glmS 核酶** | `https://marks.hms.harvard.edu/rnagym/fitness_prediction/fitness_raw_data.zip`（**13,581,795 B**，实测 206 + `PK`）→ `raw_data/andreasson_2020/` | 67 位点 × 5 配体浓度，161,879 行 | ✅ **CC-BY-4.0**（Crossref 核实） |

### 9.2 第二优先（多任务但空间小，或需回源）

| 对象 | DOI / URL | 规模 | license |
|---|---|---|---|
| **PTE 9 底物** | `github.com/karolbuda/rba-error-propagation`；preprint 10.64898/2026.07.02.736193 | 64 × 9，**生物重复 n=3–10 + 技术 n=3** | ⚠️ **未见 LICENSE 文件** |
| **Kosterlitz 多宿主 blaTEM** | Zenodo **10.5281/zenodo.10045641**；`github.com/livkosterlitz/crowdsourcing`；MBE 10.1093/molbev/msad237 | 32 × 3 宿主 × 3 条形码 | ✅ **CC-BY-4.0** |
| **MPH 8 环境** | Zenodo **10.5281/zenodo.4552583**；`github.com/danderson8/MPH_Epistasis`；Nat Commun 10.1038/s41467-021-23943-x | 32 × 8，**3 次生物重复 + SD** | ⚠️ Zenodo "other-open"；GitHub 未核实 |
| **TEV ProtRec** | Zenodo **10.5281/zenodo.15346003** + MLDEEP **10.5281/zenodo.15344074**；`github.com/JeschekLab/ProtRec`；SRA SAMN48276352；Nat Commun 10.1038/s41467-025-60622-7 | 29,716 蛋白酶 × ≤134 底物 ≈ 60 万对 | ✅ **CC-BY-4.0** |
| **AncSR1** | Nature 10.1038/nature23902 / PMC6214350；eLife 10.7554/eLife.88737 | 160,000 × 4 条件 × 2 重复 | ⚠️ **机器可读 deposit 未找到** |
| **TrpB** | CaltechDATA **10.22002/h5rah-5z170**（`data.zip` 3.32 GB + `code.zip` 413 MB）；SRA PRJNA1127511；PNAS 10.1073/pnas.2400439121 | 159,129 / 160,000；**含已发表 in-silico DE 基准** | ✅ **CC0-1.0** |
| **Bank2016 Hsp90** | DRYAD **10.5061/dryad.th0rj**（`data.csv` 174 KB） | 1,612 密码子 / 641 氨基酸基因型 | ✅ CC0（Zenodo 字段） |
| **Hsp90 EMPIRIC 6 环境** | eLife **10.7554/eLife.53810** source-data xlsx；BioProject **PRJNA593726** | 14,160 aa 变体 × 6 条件；R²=0.90 | ✅ **CC-BY** |
| **DAOx** | Zenodo **10.5281/zenodo.15846928**；SRA PRJNA1289092；Nat Commun 10.1038/s41467-026-69913-z | ~6,500 变体 × 5 底物；2 重复 r=0.94–0.97 | ✅ **CC-BY-4.0** |
| **amiE** | figshare **10.6084/m9.figshare.3505901.v2**；Nat Commun 10.1038/ncomms15695 | >96.3% 单错义 × 3 底物 | ✅ **CC-BY-4.0** |
| **CTX-M-14** | `github.com/Palzkill-Lab/CTXM_epistasis`；PNAS 10.1073/pnas.2313513121 | 17 位点 × 49,096 双突变 × 2 药 | ⚠️ **未核实** |
| **DHFR 广谱扫描** | Figshare **10.6084/m9.figshare.30470525.v1**（71 MB）+ 10.6084/m9.figshare.28266890.v1；BioProject PRJNA1189478；`github.com/PlesaLab/DHFR` | 111,233 genotype 行；9 条件 | ✅ **MIT**（mapping 为 CC-BY-4.0） |
| **YFP × 7 温度** | Zenodo **10.5281/zenodo.20719728**（237 MB） | 109,856 单突变 × 7 温度 + Tm + ddG | ✅ MIT（**但判据 1 ✗**） |

### 9.3 需作者邮件 / 带认证访问的（**目前无法核实，是最后的缺口**）

| 对象 | 为什么 | 需要什么 |
|---|---|---|
| **Taft 2022 + Shlesinger 2026 DML**（24 条件 = 13 单抗 + ACE2 + 10 份血清） | SRA **PRJNA1264489**；Zenodo **10.5281/zenodo.18660254**；GitHub **LSSI-ETH** —— 但 deposit 看起来只有代码 | **带认证的 GitHub 调用或作者邮件**。若能拿到，这是**多任务面板最后一次显著加强的机会** |
| **PNAS 2025 多药转运蛋白**（10.1073/pnas.2511892122 / PMC12772156） | 摘要称"八个底物 × 两个能量条件"的多参数 DMS；**Europe PMC 返回 HTTP 500**，OSTI 镜像失败 | **一次可用的 PNAS/PMC HTML 读取**。若是组合文库 → 顶级多底物命中；**目前 single vs multi-site 完全未知** |
| **Irvine 2025 Fc**（>10^8 Fc 变体 × 8 种 FcγR） | 预印本中**零数据可得性声明** | 作者邮件 |
| **Mira/Barlow TEM-50**（4 位点 × 15 β-内酰胺） | ⚠️ 线程报告"找不到 deposit"，**但本报告已核实 GraphFLA 仓库内即有那 15 个 CSV** | 无需邮件；但 DATA_AUDIT 的 provenance 列须注明"**经 GraphFLA 二次分发获得，非作者 deposit**"，并注意 license 传递问题 |

### 9.4 全局方法学限制（如实记录）
**未认证的 GitHub REST API 在整个会话中对所有并行检索线程限流（60 req/h/IP）**，因此 `LSSI-ETH` 与 `klawrence26/bnab-landscapes` 的仓库树**无人能枚举**。CR9114 是通过**直接拉 eLife CDN 的逐变体 CSV** 绕开的（所以它是文件级核实）。**任何依赖 GitHub 仓库树的核实都应改用带认证的调用。**

---

## 10. 本文件的状态

- **三个并行检索线程现已全部结束**，本文件为**收口版本**（§0–§10）。
- 全文严格区分「已核实（亲自下载/解析/API 读取，附 URL）」与「未独立复核（来自并行线程，已标注）」。
- **本文件只写事实与裁决，不含任何分析结论**；`PHASE1_*` / `DATA_AUDIT.md` / `AMENDMENT-*` 由父代理维护，我未改动其中任何一个字。
- 已知的**未解决项**已集中列于 §7 与 §9.3，**不做推断填补**。
