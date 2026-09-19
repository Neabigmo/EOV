# AMENDMENT-012 — M3.0 收口：追认容差偏离、撤销"说谎的相等"shim、登记 M3.3/M3.4 产物

| 字段 | 值 |
|---|---|
| 版本 | **12** |
| 时间 | **2026-09-19 09:04:13 (+08:00)** |
| 状态 | **FROZEN**（父 agent 裁决，用户可覆盖） |
| 对历史的影响 | `AMENDMENT-009/010/011`、`M1_SCHEMA_SPEC.md` **原文与哈希均未变**（见 §4） |
| 时机 | EOV 分析仍未运行；M4 前禁令继续有效 |

---

## 1｜追认：`BOUNDARY_ABS_TOL = 1e-9`（**同意偏离**）

**偏离内容**：AMENDMENT-011 要求"容差用既有 `NUMERIC_TOLERANCE`"，执行端改用独立常数 **`BOUNDARY_ABS_TOL = 1e-9`**。

**追认理由（我认为执行端是对的）**：

| 量 | 值 |
|---|---|
| 表中冻结的 floor 字面量（十进制，10 位有效数字） | `0.1760912591` |
| 真实值 `math.log10(1.5)`（双精度） | `0.17609125905568124` |
| **差值** | **≈ 4.4e-11** |
| 既有 `NUMERIC_TOLERANCE` | `1e-12` |

→ 用 `1e-12` 会**静默漏掉 TEM-1 全部边界命中**（应为 **530 组**，得到 **0 组**）—— 又是一个"不报错、只是数字错"的失效模式。
→ 我在做预期值核对时，自己用的也是 **`atol=1e-9`**（`np.isclose`），与执行端一致。
→ **不会过度捕获**：TEM-1 的 floor 与次小值相差约 **0.07**，9 个数量级的安全边际；对 eLife 两项**零影响**（floor 为精确整数 6.0 / 7.0）。

**裁决：追认 `BOUNDARY_ABS_TOL = 1e-9`**，并在 `eov/schema.py` 中保留其理由注释。
（更"干净"的替代方案是把表中 floor 规范化为 `math.log10(1.5)` 的精确双精度值，但那会改写数值列；此处不值得。）

---

## 2｜不追认并撤销：`SCHEMA_VERSION` 的兼容相等性 shim

**偏离内容**：执行端用 `SchemaVersion(str)` 子类令 `SCHEMA_VERSION == "1.2"` 返回 `True`（真实值 `"1.4"`），以便让**冻结的** `tests/test_schema_v1_2.py` 第 442 行断言继续通过。

**我驳回该做法**：

> 一个对历史版本号返回相等的版本字符串是**"说谎的相等"**。未来任何 `if SCHEMA_VERSION == "1.2": use_old_path()` 之类的分支，都会在 v1.4 模块上**静默走错路径** —— 这正是本项目连续两个阶段在消除的那类失效模式（前导零 key、行序依赖、dead sentinel）。

**根因不在 schema，而在那行断言本身**：它把"v1.2 契约仍然成立"错误地表达成"版本号永远停在 1.2"。这是**过度指定**。

**已实施的诚实修法**：

| 文件 | 变更 |
|---|---|
| `eov/schema.py` | `SchemaVersion` 类**整体删除** → `SCHEMA_VERSION = "1.4"`（普通 `str`）。docstring 记录撤销理由与日期 |
| `tests/test_schema_v1_2.py` | 第 442 行的 `assert SCHEMA_VERSION == "1.2"` → **契约断言**：`V12_SCHEMA_VERSION == "1.2"`（冻结常量不变）∧ 当前版本仍是 `1.x` 家族 ∧ `>= "1.2"` |
| `tests/test_schema_v1_4.py` | 原 `SCHEMA_VERSION.value`（shim 提供的属性）→ `isinstance(SCHEMA_VERSION, str)` ∧ `== "1.4"` ∧ **`!= "1.2"`** |

**验证结果**：

```
SCHEMA_VERSION     = '1.4'   类型: str
  == "1.2" ?  False      ← 不再说谎
  == "1.4" ?  True
V12_SCHEMA_VERSION = '1.2'   ← 冻结历史常量保留
```

**测试：`40 passed`**（21 + 7 + 12）。

---

## 3｜执行端主动申报的另一处既有列改写（**确认必要**）

`at_inferred_floor` 按 v1.4 硬规则 `≡ (state == boundary_ambiguous)` **重算**：行级 `True` 由 **89,067 → 83,007**。

- **必要**：旧值用的是更宽的"逐重复命中"规则，会与 `state=exact ∧ at_inferred_floor=True` 这一被 v1.4 明令禁止的组合冲突。
- **已由我独立验证**：`exact ∧ at_inferred_floor=True` = **0 组**；`boundary_ambiguous ∧ at_inferred_floor=False` = **0 组**。
- 这是**唯一一处既有列被改写**，且为硬规则所必需。**确认。**

---

## 4｜M3.0 完成证据（我独立复核，非执行端自述）

| 检查 | 结果 |
|---|---|
| 四态就位、`measured_exact` 残留 | **0** ✅ |
| 重分类量 vs **我的预期值** | TEM-1 AMP **530**（预期 530）；SI06 **31,524**（预期 31,524）；G189E **9,452**（预期 9,452）；CR9114 三项与 MA90 / expression **均 0**（预期 0）✅ |
| `censored` / `missing` / `informative` 是否被误改 | **一个未动** ✅（censored 436/58,127/65,243；informative 逐字一致） |
| 行数不变 | **3,422,466** ✅ |
| 四项不变式 | `exact ∧ at_inferred_floor=True`=0；`boundary_ambiguous ∧ at_inferred_floor=False`=0；`censored ∧ evidence≠explicit`=0；`measured_exact` 残留=0 ✅ |
| 全量测试 | **`40 passed`** ✅ |
| 历史哈希 | `ca142f6b…` / `162e54c0…` / `26ac6bb4…` / `537afe9b…` **均未变** ✅ |

> **过程记录**：核查期间出现过一次 `1 failed`（`test_parquet_reclassification_is_self_consistent`，pyarrow 报 `__batch_index` 等内部字段错误）。原因是**写读竞争** —— 测试读到了执行端正处于写入中的 parquet。文件写完后重跑即全绿。
> **规程增补**：*对我们自己正在被并发写入的产物跑校验前，必须先确认其 mtime 稳定。*

---

## 5｜M3.3 / M3.4 产物已由父 agent 生成

| 文件 | 字节 | sha256 |
|---|---|---|
| `data_registry/M2_AUDIT_TABLE.csv` | 5131 | `eadcfb32289c5eda43c7f2ec7704b0457032e8b60f713fec89885ec5fa4e89d9` |
| `data_registry/PHASE1_ANALYSIS_READY_MANIFEST.csv` | 5759 | `5bed18b8c62a53e7211a03e8d79efe0ab5954332ee305457536a23e9ff17a8bd` |
| `eov/audit_table.py`（四态 + 三口径） | 13451 | `f01b6430b5876cefd67cee1d32f627721eb573590510031f163073738d09245d` |
| `eov/analysis_ready_manifest.py` | 9832 | `196042f5f43693dbbe33f0ca8683c800a28aeb5a358dfeee01c28ab43f84ffe0` |

审计表已含**四态计数**（`exact / censored / boundary_ambiguous / missing`）与**三口径 degree**（`d_topology` / `d_present`(=旧 `eff_degree`) / `d_informative`）。

---

## 变更日志

| 版本 | 时间 | 变更 |
|---|---|---|
| 12 | 2026-09-19 | ① **追认** `BOUNDARY_ABS_TOL = 1e-9`（原容差 `1e-12` 会静默漏掉 TEM-1 全部 530 组命中）② **驳回并撤销** `SCHEMA_VERSION` 兼容相等性 shim → 改为普通字符串 + 冻结测试的**过度指定断言**改为契约断言 ③ 确认 `at_inferred_floor` 重算（89,067→83,007 行）为硬规则所必需 ④ 登记 M3.0 完成证据（含我独立复核）⑤ 登记 M3.3/M3.4 产物 |
