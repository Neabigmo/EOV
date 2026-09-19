# PHASE1_DATA_GATE.md — M0 出口裁决（data go / no-go）

| 字段 | 值 |
|---|---|
| 版本 | **v3**（并入 AMENDMENT-008；变更见 §6） |
| 时间 | **2026-09-19** |
| 状态 | **FROZEN** |
| 依据 | `M0_verification_log.md`、`M0_csv_sweep_v2.csv`、`M0_license_and_novelty.md`、AMENDMENT-001…008 |
| 裁决 | ## 🟢 **GO（有条件）** —— **用户已裁决 M0 = GO**，并批准进入 M1 |

---

## 1. 角色分类（**互斥**，M1 冻结 `dataset_role`）

| 角色 | 数据 | 依据 |
|---|---|---|
| **strict dense + multi-task** | **TEM-1CML**、**Phillips2023** | TEM-1：55,296 = 4×3³×2⁹（实测）、AMP→AZT；Phillips2023：2¹⁶、3 任务 informative 93.7/82.6/43.0% + 表达轴 |
| **dense single-task control** | **CR9114-h1** | h1 96.0%；**h3 10.9% / fluB 0.3% 已排除** → **不得作 multi-task evidence**（AMENDMENT-008 §3） |
| **conditional / pending** | **AncSR1** | Dryad `.rda`（无 CSV，需 R）；**单核苷酸邻接**定义 → `N_k(x)` 须另立（C7）；用户决定暂不索取 |
| oracle-only | Mira2015 TEM、Kosterlitz blaTEM、PTE、MPH | 空间 ≤ 64 → `B ≤ |space|/4` |
| L1 任务面板 | TEV ProtRec（134 底物）、DAOx | 非组合空间 |
| modality control（L0） | glmS、Soo2021、Rotrattanadumrong | RNA |

> `dataset_role ∈ {strict_multi_task, single_task_control, oracle_only, modality_control, conditional}`

---

## 2. M0 产生的四条新事实

1. **噪声实测**：AMP 781 median SD **0.321**（相对 **14.7%**）；AZT 36 **0.242**（**10.5%**）。原文"SD < 10%"**偏乐观**。
2. 🔴 **AZT 36 的 IQR 仅 1.07 × 噪声 SD**（AMP 2.09）→ 见 §3 的 **G-FTI**。
3. **删失普遍**：全语料仅 4 个文件地板占比 >30%，最高 **99.7%**（↔ 我实测可用率 0.3%，逐位吻合）。
4. 🔴 **TrpB 原文已发表逐起点 `R_{B,π}`（单任务、3 种确定性策略）+ 可及路径 + 噪声 null** → 增量只剩四项：**任务 holdout / selection regret / `Corr(EOV_τ1,EOV_τ2)` / 预算轴**。

---

## 3. 条件（违反即回退 NO-GO）

| # | 条件 |
|---|---|
| C1 | 噪声/量纲引用一律以**实测值**为准 |
| C2 | 任务准入用 **`informative_frac`**（≥50% 主 / 20–50% 敏感 / <20% 排除）；删失 ≠ 缺失 ≠ 精确值 |
| C3 | 判据 ②/③/④ 的核实对象只能是**原始 deposit**（CL-8，已五次复现） |
| C4 | **预算 `B ≤ \|space\|/4`**；小空间数据集只能 oracle-only |
| C5 | 主 Tomorrow Test（Phillips2023）= **MA90 → G189E**，**并强制共同报告 0.8 闸门下两条**（OP-25 披露义务） |
| **C6a** | **published-search / reproduction baseline gate**：TrpB 的 3 种 DE、可及路径扫描、local optima、噪声 null → **M4 前必须满足 `our reproduction ≈ published outputs`**，之后才可宣称增量。**复用其实现，不得重写。** |
| **C6b** | **prospective-selector baselines**（与 C6a 分开）：current fitness、robustness、known-task activity、**GraphFLA 全部 20 特征**、PLM zero-shot、linear/RF/XGB。H2 增量须**同时**相对 C6a 与 C6b 成立 |
| C7 | AncSR1 若启用，`N_k(x)` 必须**另立定义**（该文用单核苷酸邻接） |
| **C8** | **再分发政策按 provenance 判定，不按数据集名判定**：① 原始 deposit 有明确开放许可 → 按许可；② 第三方 repack / 无 LICENSE 的 GitHub artifact → **local-only + fetch instruction**；③ 含 **ND** 条款者 → **不得发布派生表** |
| **C9** | **G-FTI（future-task identifiability gate，M4 前，不阻塞 M1）**：对**全部 AZT 浓度**计算 `between-genotype signal / measurement uncertainty`，按**预注册规则**选 future condition，**不得默认 AZT 36** |

**措辞禁令**：不得写"我们首次逐 starting point 研究 fixed-landscape adaptation outcome"。

---

## 4. 许可：**两个状态必须分列**

```
analysis_allowed        # 科学分析能否进行
redistribution_allowed  # release 能否带原始文件
```

两者**不得互相阻塞**。当前状态：

| 数据 | analysis | redistribution |
|---|---|---|
| TEM-1CML | ✅ | ✅（GPL-3.0） |
| Phillips2023 / CR9114 | ✅ | ✅（eLife **CC BY**，署名） |
| TrpB | ✅ | ✅（CC0） |
| **Bank2016（Hsp90, 640 突变体）** | ✅ | ✅ **回源 Dryad `10.5061/dryad.th0rj` = CC0-1.0（我实测）**；GraphFLA 整理版 🔴 不得再打包 |
| **CTX-M-14（woson2020 / MBE 2022）** | ✅ | ⚠️ 论文 CC BY 4.0；**GitHub artifact local-only** |
| **CTX-M-14（Palzkill / PNAS 2024）** | ✅ | 🔴 **CC BY-NC-ND → 不得发布派生表** |
| PTE / MPH / Kosterlitz | ✅ | ⚠️ 仓库无 LICENSE → **local-only** |
| Mira2015（15 CSV） | ✅ | ⚠️ 须回源 PLoS One **CC BY** 补充材料 |
| AncSR1 | ⚠️ P2 | ⚠️ 未核 |
| MaveDB | ✅ | ✅（逐 score set **CC0 1.0**） |

---

## 5. 结论

> **M0 = GO（用户裁决）。** 证据天花板：**strict dense + multi-task = {TEM-1CML, Phillips2023}**；CR9114-h1 为 dense single-task control；AncSR1 条件性。
>
> **进入 M1**：**只构建统一 schema、provenance ledger 与无权 genotype graph；不得计算 EOV、regret、parent ranking 或任何 Tomorrow-Test 结果。M4 前分析禁令继续有效。**

---

## 6. 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| v1 | 2026-09-19 | 初版：GO（有条件），3 条新事实 + 6 条条件 |
| v2 | 2026-09-19 | Jalal2020 更正；TrpB novelty 并入；license 定案；AncSR1 陷阱；C8 v1 |
| **v3** | 2026-09-19 | ① **C6 拆为 C6a/C6b** ② **C8 改为 provenance 原则** + Bank2016 = **CC0（实测）** + **CTX-M-14 更正为两个数据集** ③ **CR9114-h1 移出 dense×multi-task** ④ 新增 **C9 = G-FTI** ⑤ 新增 `analysis_allowed` / `redistribution_allowed` 分列 ⑥ 角色分类互斥化 |
