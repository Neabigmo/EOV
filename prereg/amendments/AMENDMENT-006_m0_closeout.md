# AMENDMENT-006 — M0 收口：两处对 DATA_AUDIT v3 的更正

| 字段 | 值 |
|---|---|
| 版本 | **6** |
| 时间 | **2026-09-19** |
| 状态 | **FROZEN** |
| 起因 | `DATA_AUDIT.md` v3 定稿**之后**，M0 又清掉两个尾巴（记录于 `data_registry/M0_verification_log.md` §M0-1b） |
| **时机** | **任何 EOV 分析均未运行** → 预注册期修订，无需盲法重跑 |

## 更正 1｜GraphFLA 全量校验：**162/163 → 163/163**；完整空间 **58 → 59**

`DATA_AUDIT.md` v3 §2.5/§8 记"**162/163，`learning.csv` 404**"与"**58 个精确完整乘积空间**"。

**事实更正**：`learning.csv` **根本不是仓库里的文件**。git tree 中真实存在的是那个**含空格与 `*`** 的长文件名：

```
data/BioSequence/NEW_Rotrattanadumrong2022_F1*U(m)_Experimental exploration of a ribozyme
neutral network using evolutionary algorithm and deep learning.csv
```

我最初的扫描脚本用 `git ls-tree … .split()` **按空白切分输出**，于是这个长文件名被切碎，只有末片 `…learning.csv` 落进列表 → 404。**是解析 bug，不是仓库缺文件。**

**补扫结果（HTTP 200，10,624,365 B）**：

| 项 | 值 |
|---|---|
| 行数 | **65,536 = 4⁸（完整 RNA 空间）** |
| 列数 / schema | 16 列；`Sequences, Ligated_1, Unligated_1, FL_1, RA_1, Ligated_2, Unligated_2, FL_2, RA_2, TR_1, …`；**无 `pos*`、无 `fitness` 列** |
| 重复结构 | `Ligated_1/2`、`Unligated_1/2`、`FL_1/2`、`RA_1/2` → **2 个生物学重复 + 派生比值** |

→ **它是第 59 个精确完整乘积空间**，且是**带重复结构的 RNA 8 位点完整景观**（完整性优于 `Soo2021`）。
→ 定位：**L0 模态对照候选**（非蛋白，不参与蛋白侧主张）。
→ 同一文件也是 **Windows `git checkout` 失败**的原因（文件名含 `*`）。

**被本更正取代的 v3 表述**：§2.5 的"162/163"、"58 个精确完整乘积空间"、§8 中把 `learning.csv` 404 列为未完成项。

---

## 更正 2｜MPH 源数据结构**已澄清**（从"未完成项"移出）

`DATA_AUDIT.md` v3 §8 把 **MPH 的基因型行数与位点结构**列为唯一残留的数据结构缺口。

**已解决**：`MPH Pt-methyl Recalculated.xlsx` =

| 项 | 值 |
|---|---|
| 环境 | **8 个 sheet**（Mg/Cu/Ca/Mn/Zn/Cd/Ni/Co）= 8 种金属 ✅ |
| 每 sheet 基因型行 | **202**（不是 32） |
| 位点数分布（标签 `193/258/271/273` 式） | 1 位点 48 / 2 位点 63 / 3 位点 61 / **4 位点 30** |
| 重复 | 每 sheet 3 个重复列（`1/2/3`）✅ |

→ **源数据是"最多 4 位点的 ~202 个变体集"，不是干净的乘积空间。**
→ 而 **GraphFLA 的 `Anderson_MPH_*` 只有 32 行 / 5 位点** → **派生版是源数据的子集，且位点编码方式不同**。
→ 这是 **CL-8（`processed ≠ raw`）的第五次复现**。
→ **裁决不变**：MPH 为 **oracle-only**，但 **M1 不得直接使用 GraphFLA 的 32 行版本**，必须先回源定义位点与基因型编码。

---

## M0 状态（本修正案生效后）

| 项 | 状态 |
|---|---|
| M0-1 GraphFLA 全量校验 | ✅ **163/163**，59 个精确完整空间 |
| M0-2 fitness 语义与 floor | ✅ 全部完成（MPH 结构一并澄清） |
| M0-3 Mira2015 语义 | ✅ |
| M0-4 PTE/MPH/Kosterlitz 原始 deposit | ✅（三者**均无 LICENSE 文件**） |
| M0-9 TEM-1 完整性 + Kosterlitz 宿主 | ✅ |
| M0-10 `PHASE1_DATA_GATE.md` | ✅（GO 有条件） |
| M0-5 license 回源（6 项） | 🟡 后台 agent `28c077ea` |
| M0-6 TrpB novelty（P0-9） | 🟡 同上 |
| M0-7 AncSR1 入口（P2） | 🟡 同上 |
| M0-8 `DATA_AUDIT.md` v3 | ✅ 已产出（sha256 见台账批次 #8） |

**→ M0 除 license/novelty/AncSR1 三项（同一后台 agent）外全部完成。**

## 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| 6 | 2026-09-19（预注册期） | 更正 v3 的两处：GraphFLA 校验 163/163 与 59 个完整空间（原 404 系我方解析 bug）；MPH 源数据 202 行 / 最多 4 位点已澄清（GraphFLA 32 行为派生子集，CL-8 第五次复现） |
