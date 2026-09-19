# AMENDMENT-007 — M0 文献核验并入：TrpB novelty 确证、Jalal2020 更正、license 定案

| 字段 | 值 |
|---|---|
| 版本 | **7** |
| 时间 | **2026-09-19** |
| 状态 | **FROZEN** |
| 依据 | `data_registry/M0_license_and_novelty.md`（22,974 B，子代理交付）+ `data_registry/M0_csv_sweep_v2.csv`（全仓库 195 CSV，0 错误） |
| **时机** | **任何 EOV 分析均未运行** → 预注册期修订，无需盲法重跑 |

---

## 1｜🔴 TrpB novelty **全部确证**，定位段必须按此收紧（最高优先）

来源：Europe PMC 全文 XML（`https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11317637/fullTextXML`，`isOpenAccess=Y`；论文许可 `cc by-nc-nd`）。

| 主张 | 结论 | 证据（原文） |
|---|---|---|
| 逐起点 max fitness 分布 | ✅ **已发表** | "**(E) The max fitness achieved from each starting point is plotted as a violin and ECDF for each of the three directed evolution simulation methodologies.**" |
| 3 种 in-silico DE | ✅ **已发表** | Method 1 = 各位点并行取最优后重组；Method 2 = 单步贪心，遍历**全部 4! = 24 种位点顺序**；Method 3 = 加性模型预测全部 20^M 后**直接合成 top N = 96** |
| local optima / 可及路径 | ✅ **已发表** | TrpB 共 **520** 个局部最优（占 active 的 5.3%）；0% 容忍下降时 **~20% 的起点无法到达全局最优**，50% 容忍度下仍有 **6.8%** |
| 噪声 null model | ✅ **已发表** | "additive landscape injected with noise"，噪声由**两次重复间 fitness 差的指数分布**拟合；**并对 null model 跑了同一套 DE**（SI Fig. S31 / Table S15） |

**实现细节（可复用）**：起点集合 = **9,783 个 active 变体**；采样是**穷举式确定性**（"we enforced the sampling of every single substitution"），**无随机初始化重复**；同一套方法也跑过 **GB1**。

**→ 冻结的定位（取代 AMENDMENT-001 A-9 / 002 B-4 / 004 D-10 的措辞）**

> 逐起点的 `R_{B,π}(x,τ)`（**单任务**、3 种策略）**已被发表**；其"允许下降步长 0–100% 扫描 + 全体起点路径 ECDF"与我们的 `R_k^adaptive` **高度重叠**。
> **我们可辩护的增量只剩四项**：
> **(i) 任务维度的 holdout**（future task 的任何测量都不进入特征/超参/排序）；
> **(ii) selection regret**（决策损失，而非达到的 fitness 分位数）；
> **(iii) `Corr(EOV_τ1, EOV_τ2)`**（起点价值是否跨任务稳定 → 区分通用 vs 任务族条件化）；
> **(iv) 预算 `B` 作为估值轴的系统扫描**（他们固定策略、我们的问题是"给定预算该选哪个起点"）。
>
> **他们的 3 种 DE 实现 + 可及性扫描 + 噪声 null model 必须全部列为 H2 baseline 并复用代码**（避免重写）。

---

## 2｜⚠️ 更正：`Jalal2020` **不是"同一蛋白 × 2 任务"** → 移出 dense × multi-task 集合

**证据**（子代理核实）：GraphFLA 论文表中该引文键两行的 subject 分别是 **ParB** 与 **Noc** —— **两个不同的 DNA 结合蛋白**（各 20⁴ = 160,000）；实测两文件中同一 genotype（`AAAA`）的 fitness 不同（NBS **−11.051** / parS **−10.772**）。

**更正**：
- `Jalal2020_NBS` 与 `Jalal2020_parS` = **两个单任务、完整 20⁴、deg = 76 的密集景观**，**不是一个多任务景观**。
- **从"dense × multi-task 蛋白集合"中移除**（它们跨的是**蛋白**，不是**任务**）。
- 它们仍可用作：① 两个独立密集景观的 H1 复现点；② 若视 ParB/Noc 为同源对，可作**跨蛋白**而非跨任务的对照（须显式声明语义）。

**受影响的既有文档**：`DATA_AUDIT.md` v3 §2.6 证据链表、`PHASE1_DATA_GATE.md` v1 §1 —— **均需按本修正案更正**（gate 出 v2）。

---

## 3｜License 定案（6 项全部回源）

| 数据 | 结论 | 可再分发 |
|---|---|---|
| **CR9114（eLife 71393）** | **CC BY** ✅ | ✅（署名） |
| **Phillips2023（eLife 83628）** | **CC BY** ✅ | ✅（署名） |
| PTE | 论文（bioRxiv）**CC BY**，但 `karolbuda/rba-error-propagation` **无 LICENSE** | ⚠️ 数据文件存疑 |
| CTX-M-14 | PNAS 2024 **CC BY-NC-ND**；仓库无 LICENSE | 🔴 **ND → 发布派生表受限，仅作内部 robustness** |
| **Bank2016**（身份确证） | **Bank, Matuszewski, Hietpas & Jensen, PNAS 2016, `10.1073/pnas.1612676113`**；蛋白 = **Hsp90**，6 位点、**640 个突变体**；Europe PMC `isOpenAccess=N`、`license` 为空 | 🔴 **无开放许可，不可假定可再分发** |
| **Mira2015**（归属更正） | GraphFLA 引文键 `MiraCGMSB15` → **PLoS One `10.1371/journal.pone.0122283`，CC BY** ✅（其 MBE 篇真实 DOI = `10.1093/molbev/msv146`，`isOpenAccess=N`） | ⚠️ 15 个 CSV **只经 GraphFLA 二次分发**，再分发须回源 PLoS One 补充材料 |
| MaveDB | **逐 score set CC0 1.0**（4 条已核实）；API 注意：score set URN **必须带 `-1`** 后缀 | ✅ |
| PTE/MPH/Kosterlitz 仓库 | **三者均无 LICENSE 文件** | ⚠️ 不得进入再分发声明 |

**附带更正**：`VIM-2` **实为 9 个 score set**（128/16/2 µg/mL AMP@25 °C、128/16/2 µg/mL AMP@37 °C、4/0.5 µg/mL CTX@37 °C、0.031 µg/mL MEM@37 °C），**不是"3 β-内酰胺 × 2 温度"**。
**DOI 消歧**：`10.1093/molbev/msad237` = **Kosterlitz 2023（CC BY）**，是正确归属（AMENDMENT-005 无误）；Mira 的 MBE 篇为 `msv146`。

---

## 4｜AncSR1：入口找到，但**没有整洁表**，并带一条建模陷阱

- **托管**：**Dryad `10.5061/dryad.jsxksn0hk`**（Metzger/Park/Starr/Thornton，version 3，`versionStatus = submitted`）；代码 `github.com/JoeThorntonLab/DBD.GeneticArchitecture`。
- **形态**：**20 个文件全部是 R `.rda` 对象 + 1 个 `.gexf`，没有任何 CSV**（如 `DT.JOINT.rda` 15.9 MB、`DT.11P.CODING.rda` 18.0 MB）。读取需 **R**（本机未装）。
- **正文已确认**：160,000 = 20⁴ 全组合、ERE/SRE 双 GFP 报告、FACS Sort-seq、**replicate concordance > 97%**、**R² = 0.62（functional variants）**。
- ⚠️ **建模陷阱（必须记录）**：该文对序列空间的定义是 "**edges connecting nodes that can be directly interconverted by a single nucleotide change**" —— **不是氨基酸 Hamming-1**。若纳入 AncSR1，`N_k(x)` 必须**另立定义或显式声明**，不得与其它数据集的 Hamming-1 图混用。
- 报告内含**可直接发送的英文索取邮件草稿**（收件人 Tyler Starr，抄送 Thornton）。

**裁决**：AncSR1 保持 **P2 / 条件性**，**不阻塞** Phase I。（用户已决定暂不发邮件。）

---

## 5｜M0 全量校验达到**全仓库覆盖**

`M0_csv_sweep_v2.csv`（NUL-safe 文件枚举）：**整个 GraphFLA 仓库 195 个 CSV，全部成功（0 错误）**。

| 范围 | 数量 | 状态 |
|---|---|---|
| `data/BioSequence/`（**本项目范围**） | **163** | ✅ 全部已校验（含先前因文件名含空格而被漏扫的那 1 个） |
| 其余目录（`ChemBio / Chemistry / Materials / Microbiome / Pharmacology`） | 32 | ✅ 已校验，**均为非蛋白模态，不在本项目范围** |

---

## 6｜最终证据链（**本表取代 AMENDMENT-005 §E-8**）

| 角色 | 数据 | 空间 | 任务 | 判据 ④ | 判定 |
|---|---|---|---|---|---|
| **主数据** | **TEM-1CML** | 55,296 = 4×3³×2⁹（实测），deg 18 | AMP → AZT（**唯一 strict future**） | ✅ triplicate（实测 SD 0.321/0.242） | **L3** |
| **第二系统** | **Phillips2023** | 65,536 = 2¹⁶ | MA90 / G189E / SI06 + 表达轴 | ✅ rep×2 + SEM | **L3** |
| 噪声校准床 | CR9114（h1） | 65,536 | **单任务**（96.0%） | ✅ rep×3 + SEM | L2 |
| 条件性 | AncSR1 | 160,000 = 20⁴ | ERE/SRE × 2 背景 | ✅ 2 重复 + SEM | **P2（.rda，需 R；邻接定义不同）** |
| 同蛋白药物轴 | Mira2015 TEM | 16（2⁴） | 15 种 β-内酰胺 | ❌ 无重复 + 地板裁剪 | oracle-only |
| 同蛋白宿主轴 | Kosterlitz blaTEM | 32（2⁵） | ×3 宿主 × ~29 CTX 浓度 | ⚠️ | oracle-only |
| 密集单任务（**已更正**） | **`Jalal2020_NBS` / `Jalal2020_parS`** | 各 160,000 = 20⁴ | **各 1 个任务（ParB / Noc 两个蛋白）** | ⚠️ 待回源 | **H1 复现点（非多任务）** |
| 酶-多底物 | PTE | 64（2⁶） | 9 底物 | ✅ 9 exp 重复 | oracle-only（B ≤ 16） |
| 酶-多环境 | MPH | **202 变体 / 最多 4 位点** | 8 金属 | ✅ 3 重复 | oracle-only |
| L1 任务面板 | TEV ProtRec | 29,716 × ≤134 底物 | 134 | ⚠️ | L1 |
| 模态对照 | glmS（RNA）/ Soo2021 / NEW_Rotrattanadumrong（RNA 4⁸） | — | 5 / 2 / 2 | ✅ | L0 |

**→ `dense × multi-task` 蛋白集合（最终）= { TEM-1CML, Phillips2023, CR9114(h1) }**，外加条件性的 AncSR1。**Jalal2020 已移除。**

---

## 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| 7 | 2026-09-19（预注册期） | ① TrpB novelty 四条主张全部确证 → 定位收紧为 (i)–(iv) 四项增量，其 DE 实现/可及性扫描/噪声 null model 列为强制 baseline ② **Jalal2020 更正为两个不同蛋白的单任务景观，移出 dense×multi-task 集合** ③ license 六项定案（含 Bank2016 身份、Mira2015 归属更正、VIM-2 条件更正）④ AncSR1 = Dryad `.rda`（无 CSV，需 R）+ **单核苷酸邻接陷阱** ⑤ M0 CSV 校验达**全仓库 195/195** ⑥ 最终证据链表更新 |
