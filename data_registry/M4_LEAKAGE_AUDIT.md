# M4 泄漏审计（`leakage_audit.md`）

| 字段 | 值 |
|---|---|
| 依据 | `PHASE1_PROTOCOL.md` **L41**："泄漏审计（M7 前）：由第二人/第二个 agent 独立复查代码路径，出具 `leakage_audit.md`" |
| 审计者 | **独立子 agent**（非 M4 执行者；结论从代码自行得出，未采信执行方的叙述） |
| 时间 | 2026-09-19 |
| 范围 | M4 四个实验 + 7 个辅助脚本 + 4 份 `TIS_MANIFEST.json` + `M4_REPORT.md` |
| 构造 | 对每一条禁止项**先尝试构造违规**，再判定；未能构造出的攻击也逐条登记（§4） |
| 运行环境 | `<PYTHON>`（3.12.3） |

## 0｜被审文件与哈希（sha256 前 16 位）

| 文件 | sha256[:16] | bytes |
|---|---|---|
| `eov/exp1_stability.py` | `44a0d28220a6f9d9` | 10980 |
| `eov/exp2_baselines.py` | `fa7ffc0f0c0a8729` | 18697 |
| `eov/exp3_tomorrow_test.py` | `159a9796ad0b9e94` | 18796 |
| `eov/exp4_readiness_vs_eov.py` | `40398cf2960f49ff` | 13853 |
| `eov/search_sim.py` | `1b99ba66b8c5ecff` | 9091 |
| `eov/landscape.py` | `77435b8794084ee1` | 20619 |
| `eov/m4_gates.py` | `4e2c3eac505a0371` | 9250 |
| `eov/m4_h1_auxiliary.py` | `8aa6c70550ad6eb9` | 8879 |
| `eov/m4_layer_decomposition.py` | `63d251ef4b495440` | 8770 |
| `eov/m4_int1_int3_diagnostic.py` | `b243d4872a5bb53a` | 9985 |
| `eov/m4_exp3_topk_sensitivity.py` | `6d5a9822b9a191e5` | 9090 |
| `eov/m4_openparam_sensitivity.py` | `315ff5bcdb7188c5` | 11108 |
| `eov/m4_op4_rep_sensitivity.py` | `531954643dd66a54` | 7782 |
| `eov/m4_emit_manifests.py` | `57b15cd0cd295f3e` | 10073 |
| `data_registry/M4_REPORT.md` | `5117cf485b51691b` | 72880 |
| `PHASE1_PROTOCOL.md`（冻结） | `668ce6169643b1db` | 16714 |
| `PHASE1_DECISION.md`（冻结） | `0a70444b483f3326` | 11995 |

## 1｜判定汇总

| 清单 | PASS | VIOLATION | CANNOT_DETERMINE |
|---|---|---|---|
| A｜PROTOCOL §14（8 项） | 7 | **1**（A.2，scoped） | 0 |
| B｜DECISION §2.4 不变量（5 项） | 4 | **1**（不变量 5） | 0 |
| C｜DECISION §6 禁止事项（13 项） | 13 | 0 | 0 |
| D｜PROTOCOL §1.2 明确禁止进入 TIS（5 项） | 4 | **1**（§1.2.2，同 A.2） | 0 |
| E｜PROTOCOL L39 接口级要求 | — | **1** | 0 |
| F｜PROTOCOL L40 TIS_MANIFEST 完整性 | — | **1** | 0 |
| **合计** | **28** | **5** | **0** |

> **审计过程中的一次自我纠错**：我最初的 A.8 判定为"部分违规"，依据是"Exp 2 应有 12 选择器 × 18 格 = 216，
> 而 CSV 只有 198 行"。**该判定是错的**：`exp2_baselines.py:72-74` 的 `SELECTORS` 只有 **11** 项，
> 11 × 2 futures × 3 policies × 3 budgets = **198**，与行数**完全相符，没有缺口**。
> 我在提交前用 `groupby` 逐格核对，确认 18 个格子每个都有 11 个选择器。
> **A.8 因此改判 PASS。** 记在这里是因为审计者的假阳性与假阴性同样有害。

**没有发现任何"未来任务的 fitness 值进入了 Day-0 特征/选择器/归一化常数"的泄漏。**
最强的一条正面证据是 §3 的**扰动复现测试**：8 个 Day-0 特征全部可由 **AMP-only** 数据
逐位精确复现（`max|diff| = 0.000e+00`）。

已发现的 6 条 VIOLATION **全部是"程序性 / 记录性 / 期望取值"性质的**，
没有一条会改变"今天的信息能不能预测明天"这一实质结论的**方向**；
但其中 B-5（不变量 5）与 F（manifest 不完整）**会改变读者对结果强度的判断**，必须修。

---

## 2｜Checklist A — `PHASE1_PROTOCOL.md` §14「禁止的泄漏模式」

| # | 条目 | 判定 | 证据 | 理由 |
|---|---|---|---|---|
| **A.1** | 用 withheld task 的 fitness 做特征标准化（均值/方差/分位） | **PASS** | `exp2_baselines.py:135-144`（`u_fn` 只读 `arrs[key][0]`，key=今天）；`:196-204`（`u_today` 与 6 个 AMP 条件）；`exp3:105-111`；`exp4:92-98` | 所有特征侧分位数都取自 **AMP** 条件自身的 informative 分布。`m4_int1_int3_diagnostic.py:65-68` 的 CV 内标准化用 **训练折** 的 `Xtr.mean/std`，测试折用训练统计量 —— 这是 A.1 唯一真正适用之处，写法正确。**§3 的 AMP-only 逐位复现**是决定性证据 |
| **A.2** | 用 withheld task 的数据做特征选择或超参搜索 | **VIOLATION（scoped）** | `exp4_readiness_vs_eov.py:221`：`best = min(dirs.items(), key=lambda kv: kv[1][1])`，其中 `kv[1][1]` 是**用未来 `V` 算出的二项 p 值**（`:211-216`） | 这是在 4 个预测器里**按未来数据的 p 值挑一个**，字面命中 §14.2。**缓解事实**：(i) 只写入 `exploratory_best_*` 三列；(ii) 冻结判据用的是**预指定**的 `known_family_mean`（`:224`），未受影响；(iii) 代码注释 `:223` 自认有 4 重比较偏倚。**未缓解**：CSV 里这三列一旦被当成结果引用即是选择偏倚产物。→ 建议把这三列改名为 `exploratory_*_DO_NOT_QUOTE` 或删除 |
| **A.3** | 用全库（含 withheld）算 PLM score 的归一化常数 | **PASS（不适用）** | `grep -i "torch\|transformers\|esm\|finetune\|PLM"` 在 `eov/*.py` 只命中一处文件名 `MOESM4_ESM.xlsx`（`m3_taskpanel_closeout.py:210`） | M4 全程未使用任何 PLM / 零样本分数，故无此通道 |
| **A.4** | 用 `Readiness`（未来任务量）作为预测特征 | **PASS** | 特征侧只有 `known_family_mean` = `E_{τ'∈AMP}[u_{τ'}(F_{τ'}(x))]`（`exp2:200-204`、`exp3:267-274`） | 全部 9 个特征只依赖 **AMP**（今天）条件。**未来任务上的** `u_τ(R_0(x,τ))` 未出现在任何特征里。与 §1.2.3 一致 |
| **A.5** | 用未来任务的"任务身份"做 one-hot 或路由 | **PASS** | `exp3:306` `F = feats_full()` 在 `for key in FUTURES`（`:307`）**之前**调用一次；`exp2:222-233` 特征块无 `ft/fc` 引用 | 特征构造不接收、不分支于任务身份。`exp2:281` 与 `exp3:314-316` 虽在 future 循环内，但只引用 `TODAY_PRIMARY` 与 `(si,bi)`，**与 `key` 无关** |
| **A.6** | 在发现 matched pair 之后才定义匹配变量或容差 | **PASS** | `exp4:104` 定义 `eps`；`:146-152` 定义 `TOL`；`:164-166` 定义匹配列；`:171-172` **才**枚举 pairs | 顺序严格为 **容差 → 匹配变量 → pairs**。且 `PROXIES`（`:60-61`）是模块级常量、`eps` 只由 AMP@781 的 `value_sem` 导出（`:99-104`），均与 pair 无关 |
| **A.7** | 用 confirmation 半集的信息去调整 discovery 半集的 pair 搜索规则 | **PASS** | `exp4:64-66` `split_of` 是 `genotype_id` 的纯哈希函数；`:139-142` 只取 confirmation；`half == "discovery"` 仅出现在 `:140` 的**计数打印** | discovery 半区**完全没有被使用**。既无调整，也无泄漏。**但见 §5 观察 O-2**：discovery 未被使用意味着该切分在本实验中不承担任何功能 |
| **A.8** | 报告时省略被检验的 pair / 特征 / 模型总数 | **PASS** | `M4_EXP2_LADDER.csv` **198 行** = 11 选择器（`exp2:72-74`）× 2 futures × 3 policies × 3 budgets —— 我逐格核对，**18 个格子每个都有 11 个选择器，无缺口**；`M4_REPORT §8` 明列 "198 行"。Exp 3：`§5.3` 明列 **180 个单元**（= 10 对手 × 18 格）、`§5.2` 明列 **405 行 / 45 个单元 / 9 个选择器**。Exp 4：`§6.4` 明列 **54–104 对**、`§8` 明列 18 行 | §14.8 要求的总数（pair / 特征 / 模型）在报告中均可找到。**唯一可挑剔处**：`§4.4` 的展示表只列了 11 个选择器中的 7 个（display 选择），完整集合在 CSV 里 —— 不构成"省略总数"，因为 198 与 11 都在报告/产物中可得 |

---

## 3｜决定性正面证据：AMP-only 逐位复现测试

为把 A.1/A.4/A.5 从"读代码觉得没问题"提升为**可检验事实**，我做了一个独立复现：
**只用 AMP 六个条件的测量**（完全不加载任何 AZT 行）重新构造 8 个 Day-0 特征，
与 `M4_EXP2_V.npz` 中落盘的 `feat_*` 逐位比对。

| 特征 | 逐位相同？ | max\|diff\| | 落盘 sd |
|---|---|---|---|
| `current_fitness` | **YES** | 0.000e+00 | 0.278656 |
| `known_family_mean` | **YES** | 0.000e+00 | 0.221490 |
| `known_family_worst` | **YES** | 0.000e+00 | 0.229314 |
| `local_robustness` | **YES** | 0.000e+00 | 0.175858 |
| `neighbor_informative_frac` | **YES** | 0.000e+00 | 0.067248 |
| `dist_to_best` | **YES** | 0.000e+00 | 1.763381 |
| `n_better_neighbors` | **YES** | 0.000e+00 | 4.917062 |
| `local_ruggedness` | **YES** | 0.000e+00 | 0.287172 |

**`ALL 8 FEATURES REPRODUCED FROM AMP-ONLY DATA: True`**

**推理**：AZT 与 AMP 行同在 `M2_measurements.parquet` 中。若任一特征曾读过 AZT 值，
那么一个**只加载 AMP** 的重实现必然无法逐位复现（浮点运算不会凑巧相等）。
8/8 精确相等 ⇒ 落盘的 Day-0 特征**不含任何 AZT 信息**。
这条证据覆盖 Exp 2/3/4 的特征侧（Exp 3 的 `feats_full`、Exp 4 的 `feats` 都源自同一构造）。

---

## 4｜Checklist B — `PHASE1_DECISION.md` §2.4「不变量（违反即结果作废）」

| # | 不变量 | 判定 | 证据 | 理由 |
|---|---|---|---|---|
| **B-1** | `u_τ` 必须与候选 `x` 无关，只由 τ 与预注册参照点决定 | **PASS** | `search_sim.py:185` `utility_from_values(values, scale, ref)`；全部调用点：`exp1:77,78`、`m4_h1_auxiliary.py:86`、`m4_op4_rep_sensitivity.py:80`、`exp2:135-144`、`exp3:105-108`、`exp4:92-96`。**`ref=` 参数在所有 M4 调用中均未被使用** | 每个 `u_τ` 都由**整张景观**（`raw[t]` / `vals[t]` / `arrs[key][0]`）算一次分位数得到，是 τ 的函数，与任何候选 `x` 无关。`ref` 通道存在但未被任何 M4 代码使用 |
| **B-2** | `u_τ` 单调非降，且每个 task family 内形式固定 | **PASS** | `search_sim.py:185-215`：`q05q95` 分支为 `(z−q05)/(q95−q05)`（仿射递增，**无 clip**）；`scale2max` 分支为 `z/vmax`。`exp1` 两尺度并列；TEM-1 全栈只用 `q05q95` | 两分支均严格单调非降；同一 task family 内形式固定。`AMENDMENT-013 §1` 已恢复无 clip 形式，我用 `M4_EXP1_RAW_V.csv` 核对：`scale2max` 与 `q05q95` 的 108 行 Spearman **逐一相等**，符合"仿射 ⇒ 秩不变" |
| **B-3** | 选择永远优化 EOV，永不优化 `AdaptationPremium` | **PASS** | 全树 `grep -i "premium"` 在 `eov/*.py` **只命中 1 处**：`exp2_baselines.py:20`，且位于模块 docstring，内容是"二者必须同尺度"的**论证**，非计算 | M4 代码中**不存在** `AdaptationPremium` / `EOV − Readiness` 的任何变量、函数或排序键。Exp 2/3 的选择器全部是 Day-0 特征（`:222-233`、`:293-304`）；Exp 4 的选择是对内预测器比较。另核对：`M4_REPORT.md` 全文亦无以 `AdaptationPremium` 为目标的表述 |
| **B-4** | Ground truth 与预测侧不对称：ground-truth `V`/`EOV` 用已揭晓 τ 的 utility（oracle 侧）；Day-0 预测侧只能用 TIS | **PASS** | 预测侧：`exp2:222-233` + `:281`、`exp3:293-304` + `:314-316`、`exp4:164-166` —— 全部 AMP-only（§3 已逐位证实）。Ground-truth 侧：`exp2:271` `u = us[key]`、`exp3:308` `u_f = mk_u(load_raw(*key))`、`exp4:110` `u_f = scale(key)[0]` —— 全部用未来条件自身的 utility | 不对称性是**按设计存在**且方向正确的：oracle 侧用未来尺度，预测侧只用今天。**注意**：未来侧 `u_f` 的分位数取自未来景观全分布（含 CV 测试折），但这 (i) 不属 §14.1（该条只管**特征**标准化），(ii) 为 B-4 明文要求，(iii) 对线性模型的 CV-R² 是**仿射不变**的（`m4_int1_int3_diagnostic.py:69-71` 另行标准化 y），故对报告的 CV-R² **完全无害** |
| **B-5** | `R_{B,π}` 的期望必须对**测量噪声**取（不得用单次 max 的点估计充数） | **VIOLATION** | **exp1**：`exp1_stability.py:92` `a = raw[t]`（单一干净值场），`:99-102` 每个 (policy,budget,parent) **只调用一次** `simulate_search` —— 无任何噪声重复。**exp3 S1**：`exp3:182` `v = arrs[("AMP", c)]`、`:188` 单次 `simulate_search` —— 同样无噪声重复。**§3.8**：`m4_op4_rep_sensitivity.py:95` 用 `raw[t]`（干净场），20 次重复全是**策略**重复，无测量噪声重复 | 对照：`exp2:183` `vals = [v] + [perturbed(...)*2]`（3 个值场，取均值）✓；`m4_h1_auxiliary.py:59-60,100-105` `N_NOISE=3 × N_POLICY=7` ✓。**未满足的三处**恰好是 Exp 1 的招牌 ρ（§3.1/§3.2）、Exp 3 的冻结选择器（S1）、以及 §3.8 的 OP-4 补算。见 §5 的 S-1/S-2 |

---

## 5｜Checklist C — `PHASE1_DECISION.md` §6「禁止事项（冻结）」13 项

| # | 条文 | 判定 | 证据 |
|---|---|---|---|
| C.1 | 不做生成式 protein design | **PASS** | 全树无生成模型/采样代码；无 `torch`/`transformers` |
| C.2 | 不重新训练 / 不 finetune protein foundation model | **PASS** | `grep -i "torch\|transformers\|finetune"` 在 `eov/*.py` 无实质命中 |
| C.3 | 不声称"发现了通用 evolvability" | **PASS** | `M4_REPORT §7.1/§7.3` 明确写"**不得声称 task-general EOV**"；§3.3 主动收窄为"搜索可及性条件化的"起点价值 |
| C.4 | 不使用 predicted future-task fitness（含 PLM 预测的未来任务表现） | **PASS** | 未来的 `V` 全部来自 `M2_measurements.parquet` 的实测 `value_group`；无任何预测型 future fitness |
| C.5 | 不拿 DAOx 单突变数据伪装多轮 evolution | **PASS（不适用）** | DAOx 未进入 M4 任何脚本（`M4_REPORT §6.5` 已声明未物化） |
| C.6 | 不把 task-specific latent activity 叫 EOV | **PASS（不适用）** | M4 未使用 latent activity 概念 |
| C.7 | 不把 imputed fitness 当 experimental truth | **PASS** | 无插补：缺失一律 `NaN`（`exp2:90`、`exp3:97`、`exp4:86`）。且 `exp2:97-99` 明确把 `state != exact` 或 `at_inferred_floor` 的行标为**不可扰动**，噪声注入不掩盖删失 |
| C.8 | 不为得到 positive result 修改 EOV 定义或任何阈值 | **PASS（有披露）** | `AMENDMENT-013/014/015/016` 逐条登记改动。**值得注意**：AMENDMENT-013 §1 **恢复**了被误加 clip 的原文公式（这是"改回冻结值"，不是改阈值）；AMENDMENT-014 把尺度选择写成显式准入判据。四处改动**没有一处放宽**判据 —— 013 §1 与 §3、014 的 A1/A2 都使判据**更严**或**更明确** |
| C.9 | 不用 `AdaptationPremium` 作为选择目标 | **PASS** | 同 B-3：全树唯一命中是 docstring |
| C.10 | 不用 random 作为 Tomorrow Test 的唯一对照（必须对最强 heuristic） | **PASS** | `exp3:325` `for sel, r in list(cell.items()) + [("random", r_rnd)]` —— **9 个 heuristic + random 全部并列**；`M4_EXP3_TOMORROW.csv` 180 行 = 10 对手 × 2 futures × 3 policies × 3 budgets。冻结判据的对手方是 heuristic，random 另列 |
| C.11 | 不报 p 值而不报 effect size / 不报 absolute terminal value | **PASS** | Exp 2 每行同报 `v_oracle`/`v_robust_worst`/`v_selected`/`regret` 与 NR（`exp2:325-332`）；Exp 4 同报 `direction_rate`/`effect`/CI（`:219-220`）；Exp 3 同报 `NR_frozen`/`NR_opponent`/`reduction_pct`（`:358-360`） |
| C.12 | 不在 concentration/条件上事后择优 | **PASS（有披露，见 S-3）** | 主未来条件由 `AZT@36.0` 改为 `AZT@0.44`（AMENDMENT-013 §4）。披露充分：`M4_REPORT §4.1/§7.5-O4` 明写这一张力，且**两个条件的完整结果并列报告**（180 行含两者）。**未缓解之处**：该改动的依据（锚点可分辨性、G-FTI ratio）是**在看到门控输出之后**才形式化的 |
| C.13 | 不用二手镜像数据（合并了 imputed 值的副本） | **PASS** | M4 只读 `M2_measurements.parquet`（源自作者 deposit，见 M0 审计）；无镜像路径 |

---

## 6｜Checklist D — `PHASE1_PROTOCOL.md` §1.2「明确禁止进入 TIS（泄漏）」5 项

| # | 条文 | 判定 | 证据 |
|---|---|---|---|
| D.1 | 未来任务 τ 的任何 fitness、标签、排序、统计量、分布分位、上界/下界 | **PASS** | §3 逐位复现证实 Day-0 特征不含 AZT 值。**但见 S-4**：AZT 的 **reachability**（`R_AZT_*`）确实存在于 exp3/exp4 读入的 NPZ 中，用途是 oracle 侧 ground truth |
| D.2 | 由未来任务数据训练/选择的任何模型、超参、特征筛选结果 | **VIOLATION（同 A.2）** | `exp4:221`。其余无：`m4_int1_int3_diagnostic.py:56-57` 固定 `lam=1.0`、`N_FOLD=5`，注释 `:17-18` 明示"不做内层调参"；`exp2/exp3` 无超参 |
| D.3 | 由未来任务算出的 `Readiness`（`u_τ(R_0(x,τ))`）进入预测模型或选择规则 | **PASS** | 特征中的 `known_family_mean` 是对 **AMP** 的期望，不是对未来任务的 `u_τ(R_0(x,τ))`。`exp2:200-202`、`exp3:267-272` 的键集合只含 `"AMP"` |
| D.4 | 未来任务的"任务身份"本身（模型须在不知道 τ 的前提下输出排序） | **PASS** | `exp3:306` 一次构造、无 `key` 分支；冻结选择器 `current_fitness` 由 **AZT 盲**的 S1 产出（`M4_EXP3_S1_MODEL_SELECTION.csv` 的 5 个 holdout 全为 `AMP@*`，我核验 `holdout.str.contains("AZT").any() == False`；9 个选择器 × 45 格，与 `M4_EXP3_FROZEN_SELECTOR.md` 表一致） |
| D.5 | 任何跨任务 pooling 的 statistic 若其计算包含了 withheld task 的数据 | **PASS** | Exp 4 的 `known_family_mean` pool 的是 6 个 AMP 条件（全为今天）；Exp 1 的跨任务 ρ 两侧均为 ground truth 且 Phillips 无 today/future 切分；无包含未来条件的 TIS 侧 pooling |

---

## 7｜「我主动尝试构造但未能成立的违规」

审计强度体现在攻击失败，而非攻击成功。以下每条我都尝试构造，均**未能成立**：

| # | 我尝试的攻击 | 结果 | 为什么失败 |
|---|---|---|---|
| **X-1** | **Exp 1 用"每个任务自己的测量"跑搜索 = 泄漏吗？** | **不成立** | Exp 1 **没有任何预测侧**：它不构造特征、不选起点、不做 Day-0/Tomorrow 切分。`V_{B,π}(x,τ)` 按定义就是 τ 景观上的 oracle 侧量；跨任务比较是 **ground-truth 对 ground-truth**。没有"用未来信息预测未来"这回事。**我的结论：不是泄漏。**（`exp1:92,95,102`） |
| **X-2** | **用未来景观自身分位数做 `u_f` = A.1 违规吗？** | **不成立** | A.1 字面只管**特征**标准化。且 B-4 **要求** ground truth 用已揭晓 τ 的尺度。而且对线性模型的 CV-R²，y 的仿射变换**恒等不影响**（`m4_int1_int3_diagnostic.py:69-71` 另外把 y 标准化），故对 `M4_INT1_CV_DIAGNOSTIC.csv` 的数值**零影响**。我专门核对了 CV 内标准化（`:65-68`）用的是**训练折**统计量 |
| **X-3** | **Exp 3 的 S1 是否偷偷看过 AZT？** | **不成立（但见 S-2）** | `exp3:103` `arrs = {("AMP", c): load_raw("AMP", c) for c in AMP_CONDITIONS}` —— 字典里**没有 AZT 键**；`us`（`:110`）与 `R_amp`（`:180-190`）同样只遍历 `AMP_CONDITIONS`。S1 的 405 行结果里 holdout 全为 `AMP@*`。虽然 `:84-85` 把整个 TEM-1（含 AZT 行）读进了 `df`，但 AZT 行**从未进入 `arrs`** |
| **X-4** | **`proxy_eov_today` 会不会随 future 变化（即偷偷用了未来）？** | **不成立** | 静态：`exp2:281`、`exp3:314-316`、`exp4:161-163` 全部只引用 `TODAY_PRIMARY` 与 `(si,bi)`，**函数体内无 `key`/`ft`/`fc`**。虽位于 future 循环内，但每次算出的是**同一个数组**。Exp 2 的 `exp4`/`exp3` 都从 `R_AMP_781.0` 读 |
| **X-5** | **Exp 4 的匹配容差是否依赖已发现的 pair？** | **不成立** | `exp4:104` 在**所有循环之外**、配对之前算好；输入只有 AMP@781 的 `value_sem`。`:146-152` 的 `TOL`、`:164-166` 的匹配列均在 `:171` 枚举 pairs 之前 |
| **X-6** | **discovery 半集是否影响了 confirmation 的配对？** | **不成立** | discovery 从未被读取（除 `:140` 的计数打印）。没有可被影响的通道 |
| **X-7** | **`AdaptationPremium` 是否在某个辅助脚本里被最大化/排序？** | **不成立** | 全仓 `grep -i premium` 在 `eov/*.py` 仅 1 处、位于 docstring。我另外检查了 `argmax`/`argmin`/`sort`/`best`/`select` 的每个调用点：全部作用于 Day-0 特征、NR、或 Kendall τ，**没有一个作用于 `EOV − Readiness`** |
| **X-8** | **噪声扰动是否把删失行"洗白"成实测值？** | **不成立** | `exp2:97-99` 把 `state != "exact"` 或 `at_inferred_floor` 标为不可扰动；`exp2:174-178` 的 `perturbed` 只在 `pert` 为真处注入。删失行的值被**固定**在 floor 值上，不会被噪声掩盖 |
| **X-9** | **`MeasurementIndex` 是否可能携带 fitness？** | **不成立** | `landscape.py:254` `__slots__ = ("_present", "_informative", "_n_rows")` —— **结构上无法存放 fitness**。这是真正的类型级防护，且它是 M4 唯一一处真正的类型级防护 |
| **X-10** | **top-k 敏感性脚本是否重新挑选了冻结选择器？** | **不成立** | `m4_exp3_topk_sensitivity.py:96-101` 从 S2 冻结记录**解析**出 `frozen` 并断言其存在；`:117-118` 直接用它，不重挑。`:121` 遍历**全部** `CANDIDATES + ["random"]`，无选择 |
| **X-11** | **报告是否用"最好的 policy/budget"冒充全体结论？** | **不成立** | `M4_REPORT §3.1/§3.2` 把 3 policies × 3 budgets 全列；`random`/`mlde_ridge` 的 ρ ≈ 0 被**显著地**报出来（§3.3 还用它们推出了结构性结论）。`greedy_ssm` 的突出被明写为**条件化**结论 |
| **X-12** | **TIS_MANIFEST 的 sha256 是否造假？** | **不成立** | 我独立重算 4 份 manifest × 4 个输入 = 16 个哈希，**全部 OK**。且 `m4_emit_manifests.py:11` 明示"派生而非手写"。**但文件的"集合"是错的** —— 见 F |

---

## 8｜发现的问题（不软化）

### S-1｜**不变量 5 在 Exp 1 与 Exp 3-S1 上未被满足**（最严重）

- **性质**：`PHASE1_DECISION.md` §2.4 标注"**违反即结果作废**"。
- **事实**：`exp1_stability.py:92,99-102` 与 `exp3_tomorrow_test.py:182,188` 每个
  (parent, policy, budget) 只用**一个干净值场**调用一次 `simulate_search`，没有任何测量噪声重复。
- **受影响的结果**：
  1. **`M4_REPORT §3.1/§3.2` 的全部跨预算/跨任务 ρ**（生死问题 #1/#2 的直接证据）；
  2. **`M4_REPORT §3.8` 的 OP-4 补算**（`m4_op4_rep_sensitivity.py:95` 同样只用干净场，
     20 次重复全是**策略**重复）；
  3. **Exp 3 的 S1 模型选择**（决定冻结选择器 `current_fitness` 的那 405 格）。
- **未受影响**：§3.4 的 H1（来自 `m4_h1_auxiliary.py`，`N_NOISE=3 × N_POLICY=7` ✓）、
  Exp 2 的 ladder、Exp 3-S3 的 V、Exp 4（后三者都读经噪声平均的 `M4_EXP2_V.npz`）。
- **我的判断（不软化）**：这不是形式问题。(a) Exp 1 的 ρ 与 §3.8 的"下界"叙述**只考虑了策略噪声**，
  遗漏了测量噪声这一项，故 §3.8 关于"真实 ρ = 0.966"的说法**其下界性质被低估**；
  (b) 更严重的是 **S1**：9 个选择器的平均 NR 极差仅 **0.029**，而逐单元 sd 达 **0.19–0.22**，
  再加测量噪声后，**`current_fitness` 之所以被"冻结"，很可能由噪声决定**。
  → §5.2 已自认"选择器之间差异比自身波动小一个数量级"，但**没有把这一点连到"冻结选择器可能是噪声产物"**。
- **建议**：在 `M4_REPORT §3.1/§3.2/§3.8/§5.2` 各加一句显式声明；
  若要恢复 §2.4 的合规性，需在干净场 + 2 个噪声场上重跑 Exp 1（成本约 3×480 s）
  与 Exp 3-S1（约 3×1500 s）。

### S-2｜**§1.2.2 / §14.2：Exp 4 用未来数据挑选要报告的预测器**

- `exp4_readiness_vs_eov.py:221` `best = min(dirs.items(), key=lambda kv: kv[1][1])`，
  `kv[1][1]` 是用**未来 V** 算出的二项 p 值。
- **缓解**：冻结判据用预指定的 `known_family_mean`（`:224`），`best` 只进 `exploratory_best_*` 三列。
- **未缓解**：`M4_EXP4_MATCHED_PAIRS.csv` 的这三列是选择偏倚产物。建议改名加 `DO_NOT_QUOTE` 或删除。

### S-3｜**主未来条件的选择依据在看到门控输出之后才形式化**

- `m4_gates.py:143-149` 用 AZT 各条件**自身**的 `signal/uncertainty` 与 `informative_frac` 选出 future condition。
  这是 `PHASE1_DATA_GATE.md:50`（C9）**明文预注册**的规则，故**不构成 §14 违规**。
- 但事实是：**"未来任务"不是盲选的**。它由未来条件的**边际测量质量**决定（与任何 parent 排序无关，故不传递价值信息）。
- AMENDMENT-013 §4 把主条件从 36.0 改到 0.44 时用的是**同类判据**（A1 锚点可分辨性 + G-FTI）。
  报告 §7.5-O4 已登记该张力，但**未点明"条件选择权本身是一次事后自由度"**。

### S-4｜**TIS_MANIFEST 的输入集合既不完整也不准确（L40 违规）**

这是**具体、可核验**的记录性违规：

| 实验 | 实际读取（`np.load` / `read_parquet` / `open`） | manifest 声明 | 差异 |
|---|---|---|---|
| exp1 | `M2_measurements.parquet` | 4 个文件 | **3 个幻影输入** |
| exp2 | `M2_measurements.parquet` (+`M4_EXP2_V.npz` in `--report-only`) | 4 个文件 | 3 幻影 + 1 遗漏 |
| exp3 | `M2_measurements.parquet`, **`M4_EXP2_V.npz`**, `M4_EXP3_S1_R.npz`, `M4_EXP3_S1_MODEL_SELECTION.csv` | 4 个文件 | **3 个幻影 + 3 个遗漏** |
| exp4 | **`M4_EXP2_V.npz`**, `M2_measurements.parquet` | 4 个文件 | 3 幻影 + 1 遗漏 |

- 根因：`m4_emit_manifests.py:143` `for rel in (MEAS, MEAS3, AUDIT, MANIFEST):` —— 一份**与实验无关的硬编码清单**，
  对所有 4 个实验写同样的 4 个输入；而 `M3_taskpanel_measurements.parquet`、`M2_AUDIT_TABLE.csv`、
  `PHASE1_ANALYSIS_READY_MANIFEST.csv` **没有任何一个 M4 脚本读过**。
- **最要命的一处**：**`M4_EXP2_V.npz` 含 `R_AZT_0.44` 与 `R_AZT_36.0`**，被 exp3(`:252`) 与 exp4(`:73`) 读取，
  却**不在任何 manifest 里**。一个只读 manifest 的复核者**不会知道未来任务的 reachability 流进了 exp3/exp4**。
  （实质判定：该读取是 oracle 侧、B-4 允许；但**声明遗漏本身就是 L40 要防的事**。）
- 另：manifest 是 UTF-8，而 `json.load(open(p))` 在本机默认 GBK 下会抛 `UnicodeDecodeError`
  （我实测命中）——下游工具会被绊住，建议 manifest 一律 ASCII 或调用方显式 `encoding="utf-8"`。

### S-5｜**manifest 的 `feature_interface_note` 对 exp2 说了假话**

- 4 份 manifest 都写："`arrs` 只装 AMP 族的键"。
- **我实测**（`exp2_baselines.build_inputs()`）：exp2 的 `arrs` 有 **8 个键，其中 2 个是 AZT**：
  `('AZT','0.44')`、`('AZT','36.0')`。→ 该句**对 exp2 为假**。
- 对 exp3 为真（`:103` 只装 AMP）。
- **含义**：exp2 的特征侧**没有**数据级防火墙，只有**约 40 行代码中不引用未来键**的编程纪律。
  执行方"只在数据层满足"的自述，实际上**在 exp2 连数据层都不成立**。
  §3 的逐位复现证明纪律**被执行了**，但那与"结构上做不到"是两件事。

### S-6｜**（已撤回）** —— 这是我的一次假阳性，保留记录以示审计过程

- 我最初写：Exp 2 应有 12 选择器 × 18 格 = 216，实际 198 行，差 18 格且报告未解释。
- **核对结果：该指控不成立。** `exp2_baselines.py:72-74` 的 `SELECTORS` 只有 **11** 项
  （`random`, `current_fitness`, `known_family_mean`, `known_family_worst`, `local_robustness`,
  `neighbor_informative_frac`, `dist_to_best`, `n_better_neighbors`, `local_ruggedness`,
  `proxy_eov_today`, `oracle`），11 × 2 × 3 × 3 = **198**，与 `M4_EXP2_LADDER.csv` 行数**完全相等**。
  我另外用 `groupby(["future","policy","budget"]).size()` 逐格核实：**18 个格子全部为 11，无一缺口**。
- **A.8 改判 PASS**，本条目撤回。根因是我在数 `SELECTORS` 时把 9 个特征误当作 10 个（多算一个），
  得到 12 而非 11。记录于此，因为**审计者的假阳性会浪费执行方的时间、并侵蚀审计的可信度**，
  与假阴性同样有害。

### S-7｜观察（非违规，但应向读者交代）

| # | 观察 |
|---|---|
| **O-1** | `m4_exp3_topk_sensitivity.py:148` `a = nr_b(F[frozen][pidx] if sel != "random" else F[frozen][pidx])` —— **三元表达式两个分支完全相同**，是无效代码。不影响结果，但属应清理的写法 |
| **O-2** | Exp 4 的 discovery 半区**完全未被使用**。DECISION 的 matched-pair 判据提到 discovery/confirmation 切分，但此处切分不承担任何功能（既不选变量也不选容差）。这**更保守**，但读者会以为存在一个"发现阶段" |
| **O-3** | `exp2_baselines.py` 的 `config.json` 写 `"n_noise_reps": 3`，而脚本里 `N_NOISE_REPS = 2`（+1 干净场 = 3 个值场）。命名口径不一致，易误读为"3 个噪声实现" |
| **O-4** | Exp 2/3/4 的选择器候选集被 `fin = np.isfinite(col) & ok`（`ok` 来自**未来** `V`）掩蔽（`exp2:293`、`exp3:70`、`exp3:341`）。**当前不活跃**：两个 future 都是 `parents 可评估 1000/1000`、池损失 `0.000%`，故掩蔽不改变任何数值。但这是一条**结构性的潜在通道** —— 若某个 future 有缺测，选择器的 argmax 就会在一个由**未来可评估性**决定的集合上取得。建议改为只按 Day-0 有限性掩蔽（`fin = np.isfinite(col)`），把未来可评估性仅用于评分 |
| **O-5** | Exp 3 S1 的 `feats_for` 对**邻域类特征**（`current_fitness`/`local_robustness`/`n_better_neighbors`/`dist_to_best`/`local_ruggedness`/`neighbor_informative_frac`）始终用固定的 `AMP@781`（`:136`），只有 `known_family_mean/worst` 排除了 holdout 条件（`:201,147`）。**这是正确的**（AMP@781 恒为今天条件，且 holdout ≠ 781.0 由 `:199` 保证），但**代码里没有注释说明为何前者不需要 leave-one-out**，容易被误读为漏做 LOO |

---

## 9｜「L39 的接口级要求」

`PHASE1_PROTOCOL.md` **L39** 原文：

> TIS 的构造代码必须放在 `eov/` 下并被 `experiments/` 引用；所有特征函数签名只接受 `τ₀` 数据对象，**在类型/接口层面就无法访问 `τ`**。

**执行方的主张**：该要求"只在数据层满足，未在类型层满足"。

### 我的核查结果：**主张方向正确，但对 exp2 而言连"数据层"都不成立**

| 层面 | 是否满足 | 证据 |
|---|---|---|
| **类型/接口层** | **❌ 不满足** | `exp3:134` `def feats_for(today_keys, P)` —— 参数是**调用方给的键列表**，不是受约束的 τ₀ 对象；`exp2` 的特征块更是直接写在 `main()` 内、闭包捕获了整个 `arrs`。没有任何类型、类或接口能阻止特征代码写 `arrs[("AZT","0.44")]` |
| **数据层（exp3）** | **✅ 满足** | `exp3:103` `arrs = {("AMP", c): ...}` —— AZT 键**不在字典里**，写 AZT 键会立刻 `KeyError`。这是一个有效（虽非类型级）的防火墙 |
| **数据层（exp2）** | **❌ 不满足** | 我实测 `build_inputs()` 返回的 `arrs` **含 2 个 AZT 键**；`all_ids`（`:117`）显式把 `FUTURES` 并入。故 exp2 的保护**纯粹是编程纪律** |
| **数据层（exp4）** | **n/a** | exp4 的特征从 NPZ 读入（已由 §3 证实为 AMP-only），且不构造新特征 |
| **行为层（全部）** | **✅ 满足** | §3 的 AMP-only 逐位复现（8/8，`max|diff| = 0`）证明**实际执行的特征构造没有读过 AZT** |

**我的独立判定**：

1. **L39 未满足。** 4 份 `TIS_MANIFEST.json` 自己也承认（`feature_interface_note`：
   "**尚无类型级强制**（缺少一个只接受 τ₀ 对象的 TIS 类）"）——这是诚实的自我披露，
   但它等于**书面承认冻结要求未被满足**，而 L41 的审计正是要独立确认这一点。
2. **执行方对"满足到哪一层"的自述不准确。** 它说"在数据层满足"；
   实际是 **exp3 在数据层满足、exp2 不满足**。manifest 里"`arrs` 只装 AMP 族的键"
   这句话对 exp2 是**假的**（S-5）。
3. **实际风险等级：低但非零。** 因为 (a) §3 的逐位复现证明当前代码没有泄漏；
   (b) 但 (b') 保护的强度依赖于**审计者读代码的能力**，而不是结构。
   M7 前若要名副其实，最小修法是引入一个 `TIS` 类：
   ```python
   class TIS:
       def __init__(self, today_keys): self._a = {k: load(k) for k in today_keys}
       def field(self, key): assert key in self._a; return self._a[key]
   ```
   并把 `feats_for(tis, P)` 的签名改为只接受 `TIS` 实例。这样 exp2 也会获得 exp3 已有的 `KeyError` 级保护。

---

## 10｜结论

1. **没有任何"未来任务 fitness 值进入 Day-0 特征/选择器/归一化常数"的实质泄漏。**
   最强证据是 §3 的 AMP-only 逐位复现（8/8 特征，`max|diff| = 0.000e+00`）。
   `AdaptationPremium` 从未被当作目标（全树 1 处 docstring 命中）。
   不变量 1/2/3/4 与 §6 的 13 条禁止事项**全部通过**。
2. **5 条 VIOLATION，全部是程序性/记录性/期望取值性质**：
   B-5（不变量 5 未对测量噪声取期望，影响 Exp 1 招牌 ρ、§3.8、及 Exp 3-S1 的冻结选择器）、
   A.2=D.2（Exp 4 用未来 p 值挑探索性预测器）、
   F=L40（TIS_MANIFEST 输入集合既不完整也不准确，且漏报了含 AZT 的 NPZ 这个通道）、
   L39（无类型级强制，且 exp2 连数据级也没有）。
   （原第 6 条 A.8 经自查为**假阳性**，已撤回，见 §8-S-6。）
3. **其中只有 S-1 会实质影响科学判断**：它使 Exp 1 的 ρ 与 §3.8 的"下界"叙述不完整，
   并使 Exp 3 冻结选择器的身份**可能是噪声产物**（选择器间极差 0.029 vs 逐单元 sd 0.19–0.22）。
   **建议 M7 前补做**：干净场 + 2 个噪声场上重跑 Exp 1 与 Exp 3-S1，报告 ρ 与 S1 排序是否稳定。
4. **两条与执行方叙述不一致、我按代码判定的事实**：
   - manifest 的"`arrs` 只装 AMP 族的键"对 **exp2 为假**（实测 8 键含 2 个 AZT）；
   - TIS_MANIFEST 的输入清单是**硬编码的全局 4 文件**，"派生而非手写"（`m4_emit_manifests.py:11`）
     这句话**只对 sha256 成立，对文件集合不成立**。
5. **本审计未修改任何被审文件**；仅新建本文件 `data_registry/M4_LEAKAGE_AUDIT.md`。
