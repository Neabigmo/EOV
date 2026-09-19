"""EOV Phase I — measurement schema（v1.1 冻结实现 + v1.2 metadata 增量）。

规范文档
--------
* ``prereg/M1_SCHEMA_SPEC.md``（**v1.1，只读冻结原文；sha256 不得变动**）
* ``prereg/AMENDMENT-009_schema_v1_2.md``（v1.1 → v1.2 的**唯一**变更说明）
* 上游约束：``prereg/AMENDMENT-008_m1_preconditions.md``、``PHASE1_DATA_GATE.md`` v3（C1–C9）

``SCHEMA_VERSION = "1.2"`` —— v1.2 只改 **metadata 语义与校验契约**：
``task_panel`` 角色、许可 provenance 五字段、replicate 三计数、boundary 来源、
measurement modality 分离、以及 graph eligibility 的代码级硬防守。
**v1.2 不改任何科学定义**（EOV / ``V_{B,pi}`` / regret 一律不动），
并且 **v1.1 的既有函数全部保持可用**（向后兼容）。

⛔ 本模块的边界（M1/M2 禁令，AMENDMENT-008 §5、AMENDMENT-009 §8）
------------------------------------------------------------------
本文件**只**做：枚举定义、行/组/表/数据集级校验、测量三态判定、informative 判定、
graph eligibility 判定与 QC 范围。
本文件**不含**且**禁止**加入：
``NO EOV   NO regret   NO parent ranking   NO Tomorrow-Test outcome``
—— 也不含搜索策略、预算模拟、可达性最大值（``R_k``）、模型拟合。
``classify_measurement_state`` 只读"重复值是否相同 / sem 是否为 0 / 值是否落在边界"，
不看 fitness 的大小、不做任何比较或排序。

只依赖标准库。
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    # v1.1（保持可用，向后兼容）
    "MeasurementState",
    "DatasetRole",
    "SourceType",
    "MEASUREMENT_COLUMNS",
    "DATASET_RECORD_COLUMNS",
    "GROUP_KEY_COLUMNS",
    "NUMERIC_TOLERANCE",
    "classify_measurement_state",
    "classify_informative",
    "group_key",
    "validate_row",
    "validate_measurement_group",
    "validate_measurement_table",
    "validate_dataset_record",
    "informative_fraction",
    # v1.2（AMENDMENT-009）
    "SCHEMA_VERSION",
    "V11_SCHEMA_VERSION",
    "BoundaryStatus",
    "BoundarySource",
    "MeasurementModality",
    "MEASUREMENT_COLUMNS_V12",
    "DATASET_RECORD_COLUMNS_V12",
    "PLACEHOLDER_BASIS",
    "MIN_BASIS_CHARS",
    "GRAPH_ELIGIBLE_ROLES",
    "GRAPH_ELIGIBLE_QC_FIELDS",
    "NON_GRAPH_QC_FIELDS",
    "graph_eligible",
    "allowed_qc_fields",
    "functional_task_ids",
    "auxiliary_task_ids",
    "validate_measurement_row_v12",
    "validate_measurement_group_v12",
    "validate_measurement_table_v12",
    "validate_dataset_record_v12",
    "migrate_dataset_record_v11_to_v12",
]


# --------------------------------------------------------------------------
# 1. 枚举（互斥）
# --------------------------------------------------------------------------
class MeasurementState(str, Enum):
    """measurement 状态。**v1.4 起为四态互斥**（AMENDMENT-011 §1.2）。

    ======================  ====================================================
    ``exact``               正常测得，未命中任何边界
    ``censored``            命中**明确文档化**的 assay floor，且满足 CL-7
    ``boundary_ambiguous``  命中 ``boundary_status = inferred`` 的**推断**边界
    ``missing``             无有效 measurement
    ======================  ====================================================

    * ``MEASURED_EXACT`` 是 ``EXACT`` 的**只读别名**（同一枚举成员，``is`` 比较为真）；
      **已作废**，仅供 v1.1/v1.2 冻结测试与历史行使用 —— **新写入一律用 ``exact``**。
    * ``boundary_ambiguous`` 是**独立状态**：不得计入 ``exact``，也不得计入 ``censored``。
    """

    EXACT = "exact"
    #: 已作废（deprecated）：与 ``EXACT`` 是同一成员，仅为历史兼容保留。
    MEASURED_EXACT = "exact"
    CENSORED = "censored"
    BOUNDARY_AMBIGUOUS = "boundary_ambiguous"
    MISSING = "missing"


class DatasetRole(str, Enum):
    """六个互斥角色（AMENDMENT-008 §3 + AMENDMENT-009 §1）。

    ``TASK_PANEL``（v1.2 新增）语义冻结为：同一蛋白背景下存在**多个 task/substrate
    measurement**，可用于 task holdout / readiness，但**不存在足够的 combinatorial
    genotype neighborhood**，因此**不得用于 budgeted graph adaptation**。
    硬性保证落在代码里：``graph_eligible()`` 对 ``task_panel`` 恒返回 ``False``。
    """

    STRICT_MULTI_TASK = "strict_multi_task"
    SINGLE_TASK_CONTROL = "single_task_control"
    ORACLE_ONLY = "oracle_only"
    MODALITY_CONTROL = "modality_control"
    CONDITIONAL = "conditional"
    TASK_PANEL = "task_panel"


class SourceType(str, Enum):
    """四种 provenance（AMENDMENT-008 §2.1，C8 按 provenance 判定再分发）。"""

    AUTHOR_DEPOSIT = "author_deposit"
    JOURNAL_SOURCE_DATA = "journal_source_data"
    SECONDARY_DISTRIBUTION = "secondary_distribution"
    DERIVED_AGGREGATE = "derived_aggregate"


# --------------------------------------------------------------------------
# 2. 列契约
# --------------------------------------------------------------------------
GROUP_KEY_COLUMNS: Tuple[str, ...] = (
    "protein",
    "dataset_id",
    "genotype_id",
    "task_id",
    "condition_id",
)

MEASUREMENT_COLUMNS: Tuple[str, ...] = GROUP_KEY_COLUMNS + (
    "replicate",
    "value",
    "value_sem",
    "value_sd",
    "measurement_state",
    "floor",
    "ceiling",
    "informative",
    "source_row_ref",
)

DATASET_RECORD_COLUMNS: Tuple[str, ...] = (
    "dataset_id",
    "protein_or_system",
    "source_type",
    "original_deposit_url",
    "fetched_url",
    "license",
    "analysis_allowed",
    "redistribution_allowed",
    "role",
    "theoretical_space_size",
    "complete_product",
    "observed_genotype_count",
    "notes",
)

#: "重复值完全相同" 的数值容差（防浮点表示噪声；规范 §2.1 要求严格相同）。
NUMERIC_TOLERANCE = 1e-12

#: v1.4：**边界命中**判定所用容差。**不等于** ``NUMERIC_TOLERANCE``，原因见下。
#:
#: 冻结在表里的 ``floor`` 是**十进制字面量**（如 TEM-1 写成 ``0.1760912591``，约 10 位有效
#: 数字），而测量值携带完整双精度。二者之差可达 **~4.4e-11**：
#:
#:     math.log10(1.5)      = 0.17609125905568124   ← 实际值
#:     表中 floor 字面量      = 0.1760912591          ← 差 4.4e-11
#:
#: 若用 ``NUMERIC_TOLERANCE = 1e-12`` 去比对，TEM-1 会**静默漏掉全部命中**
#: （实测：AMP 应为 530 组，用 1e-12 得到 **0 组**）。故边界命中使用独立的、
#: 明确记录在案的容差。eLife 两个数据集的 floor 是精确整数（6.0 / 7.0），
#: 三种容差下计数完全一致，因此本常数不会造成过度捕获。
BOUNDARY_ABS_TOL = 1e-9


def _at_boundary_v14(value: float, floor: Any, ceiling: Any) -> bool:
    """组代表值是否落在 floor / ceiling 上（v1.4 边界命中判定）。"""
    f = _as_float(floor)
    c = _as_float(ceiling)
    if f is not None and math.isclose(value, f, rel_tol=0.0, abs_tol=BOUNDARY_ABS_TOL):
        return True
    if c is not None and math.isclose(value, c, rel_tol=0.0, abs_tol=BOUNDARY_ABS_TOL):
        return True
    return False


# --------------------------------------------------------------------------
# 3. 小工具
# --------------------------------------------------------------------------
def _is_missing_number(x: Any) -> bool:
    if x is None:
        return True
    if isinstance(x, str):
        s = x.strip().lower()
        return s in ("", "na", "nan", "none", "null")
    try:
        return math.isnan(float(x))
    except (TypeError, ValueError):
        return True


def _as_float(x: Any) -> Optional[float]:
    if _is_missing_number(x):
        return None
    return float(x)


def _as_bool(x: Any) -> Optional[bool]:
    if isinstance(x, bool):
        return x
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return bool(x)
    if isinstance(x, str):
        s = x.strip().lower()
        if s in ("true", "1", "yes", "y", "t"):
            return True
        if s in ("false", "0", "no", "n", "f"):
            return False
    return None


def group_key(row: Mapping[str, Any]) -> Tuple[str, ...]:
    """返回 (protein, dataset_id, genotype_id, task_id, condition_id)。"""
    return tuple(str(row.get(c, "")) for c in GROUP_KEY_COLUMNS)


#: v1.4：历史字符串 "measured_exact" 仍可读入，统一归一化为 ``MeasurementState.EXACT``。
LEGACY_STATE_ALIASES: Dict[str, "MeasurementState"] = {
    "measured_exact": MeasurementState.EXACT,
}


def _coerce_state(x: Any) -> Optional[MeasurementState]:
    if isinstance(x, MeasurementState):
        return x
    if x is None:
        return None
    s = str(x).strip()
    if s in LEGACY_STATE_ALIASES:
        return LEGACY_STATE_ALIASES[s]
    try:
        return MeasurementState(s)
    except ValueError:
        return None


# --------------------------------------------------------------------------
# 4. 三态判定（核心，规范 §2.1）
# --------------------------------------------------------------------------
def _classify_state_v12(
    replicates: Optional[Iterable[Any]],
    sem: Any = None,
    value: Any = None,
    floor: Any = None,
    ceiling: Any = None,
    boundary_status: Any = None,
    n_expected: Any = None,
) -> MeasurementState:
    """按冻结规则判定一个 (genotype × task × condition) 组的测量状态。

    规则（M1_SCHEMA_SPEC §2.1；v1.2 契约见 AMENDMENT-009 §3.2）：

    * ``missing``        —— 无可用重复值，或代表值缺失；
    * ``censored``       —— 重复值**数值上完全相同** ∧ ``sem == 0`` ∧ 代表值**落在
      **已验证**边界上**；
    * ``measured_exact`` —— 其余情况。

    参数
    ----
    replicates : 该组的逐重复测量值（可含 None/NaN，将被剔除）
    sem        : 组级 SEM。**必须显式给出且等于 0** 才能判为 censored；
                 缺省（None）时**保守地不判 censored**。
    value      : 组代表值（用于判断是否落在边界）。
    floor, ceiling : 该 task×condition 的实测检测边界（可为 None）。
    boundary_status : v1.2 新增。``"unresolved"`` ⇒ **绝不判 censored**
                 （AMENDMENT-009 §3.3：证据不足时不得为了跑 CL-7 硬造 floor）。
                 **缺省（None）表示调用方未声明**，此时保持 v1.1 行为（向后兼容）；
                 v1.2 长表校验器总是显式传入该字段。
    n_expected : v1.2 新增。若给出且实际有效重复数 < ``n_expected``，
                 则该组存在**缺失重复** —— 按 §3.2「缺失重复 ≠ 删失」，**不判 censored**。

    v1.2 补充规则
    -------------
    * **仅一个有效重复** → 保留该 measurement（既不 missing 也不 censored），
      但**不得虚构 SEM**；``informative`` 由 :func:`classify_informative` 按保守规则判。
    * 缺失重复**不得**被记为 censored。

    ⛔ 本函数不比较 fitness 大小、不排序、不做任何分析。
    """
    reps = [float(r) for r in (replicates or []) if not _is_missing_number(r)]
    if not reps:
        return MeasurementState.MISSING

    v = _as_float(value)
    if v is None:
        # 有重复值但没有代表值：不能宣称精确
        return MeasurementState.MISSING

    # --- v1.2 门禁（只在调用方显式提供新元数据时生效，保证 v1.1 向后兼容） -----
    bs = _coerce_simple_enum(BoundaryStatus, boundary_status)
    if bs is BoundaryStatus.UNRESOLVED:
        # 边界未解决 ⇒ 不得产出 censored
        return MeasurementState.MEASURED_EXACT
    if n_expected is not None:
        try:
            if len(reps) < int(n_expected):
                # 缺失重复 ≠ 删失（§3.2）
                return MeasurementState.MEASURED_EXACT
        except (TypeError, ValueError):
            pass
    if len(reps) < 2:
        # 仅一个有效重复：保留 measurement，但"重复值一致"在此毫无信息量
        return MeasurementState.MEASURED_EXACT

    at_boundary = False
    f = _as_float(floor)
    c = _as_float(ceiling)
    if f is not None and math.isclose(v, f, rel_tol=0.0, abs_tol=NUMERIC_TOLERANCE):
        at_boundary = True
    if c is not None and math.isclose(v, c, rel_tol=0.0, abs_tol=NUMERIC_TOLERANCE):
        at_boundary = True

    identical = all(
        math.isclose(r, reps[0], rel_tol=0.0, abs_tol=NUMERIC_TOLERANCE) for r in reps
    )
    sem_value = _as_float(sem)
    sem_is_zero = sem_value is not None and sem_value == 0.0

    if identical and sem_is_zero and at_boundary:
        return MeasurementState.CENSORED
    return MeasurementState.MEASURED_EXACT


def classify_measurement_state(
    replicates: Optional[Iterable[Any]],
    sem: Any = None,
    value: Any = None,
    floor: Any = None,
    ceiling: Any = None,
    boundary_status: Any = None,
    n_expected: Any = None,
) -> MeasurementState:
    """**v1.4 四态判定**（AMENDMENT-011 §1.2）。

    判定表
    ------
    1. 无有效重复，或组代表值缺失 → ``missing``
    2. ``boundary_status = explicit`` ∧ 重复全等 ∧ ``SEM == 0`` ∧ 组代表值命中边界
       → ``censored``（真删失，依据明确文档化的 assay floor）
    3. ``boundary_status = inferred`` ∧ 组代表值命中该推断边界 → ``boundary_ambiguous``
       —— **不要求**重复全等 / ``SEM == 0``；判定只用**组代表值**
    4. ``boundary_status = unresolved`` → **绝不**产出 censored / boundary_ambiguous
    5. 其余 → ``exact``

    ``boundary_status`` **缺省（None）** 表示调用方未声明边界证据等级 → 走 v1.1/v1.2 的
    三态路径（:func:`_classify_state_v12`）。这是必要的兼容门禁：v1.1 的冻结 tripwire
    在不传该参数时期望得到三态语义，而 ``measured_exact`` 与 ``exact`` 在 v1.4 中是
    **同一个枚举成员**。

    ⛔ 本函数不比较 fitness 大小、不排序、不做任何分析。
    """
    reps = [float(r) for r in (replicates or []) if not _is_missing_number(r)]
    if not reps:
        return MeasurementState.MISSING

    v = _as_float(value)
    if v is None:
        return MeasurementState.MISSING

    bs = _coerce_simple_enum(BoundaryStatus, boundary_status)
    if bs is None:
        # 调用方未声明边界证据等级 → 保持 v1.1/v1.2 语义（兼容门禁）
        return _classify_state_v12(
            replicates=replicates, sem=sem, value=value, floor=floor, ceiling=ceiling,
            boundary_status=None, n_expected=n_expected,
        )

    if bs is BoundaryStatus.UNRESOLVED:
        # 证据不足 ⇒ 绝不把推断冒充事实，也不把可疑 floor 当精确值
        return MeasurementState.EXACT

    at_boundary = _at_boundary_v14(v, floor, ceiling)

    if bs is BoundaryStatus.INFERRED:
        # 只以**组代表值**是否落在推断边界上为准（不要求重复全等）
        return MeasurementState.BOUNDARY_AMBIGUOUS if at_boundary else MeasurementState.EXACT

    # bs is BoundaryStatus.EXPLICIT —— 走 CL-7 的严格条件
    if n_expected is not None:
        try:
            if len(reps) < int(n_expected):
                return MeasurementState.EXACT  # 缺失重复 ≠ 删失
        except (TypeError, ValueError):
            pass
    if len(reps) < 2:
        return MeasurementState.EXACT  # 单重复无法谈"重复一致"
    identical = all(
        math.isclose(r, reps[0], rel_tol=0.0, abs_tol=NUMERIC_TOLERANCE) for r in reps
    )
    sem_value = _as_float(sem)
    sem_is_zero = sem_value is not None and sem_value == 0.0
    if identical and sem_is_zero and at_boundary:
        return MeasurementState.CENSORED
    return MeasurementState.EXACT


def classify_informative(
    state: Any,
    value: Any,
    sem: Any = None,
    floor: Any = None,
    ceiling: Any = None,
) -> bool:
    """``informative`` 判定（CL-9 / 规范 §4）。

    informative := state == measured_exact
                   ∧ value > floor + 2·SEM
                   ∧ value < ceiling - 2·SEM

    SEM 缺省时对应一侧视为不满足（保守）。censored / missing 一律 False。
    """
    st = _coerce_state(state)
    if st != MeasurementState.MEASURED_EXACT:
        return False
    v = _as_float(value)
    s = _as_float(sem)
    if v is None or s is None:
        return False
    f = _as_float(floor)
    if f is not None and not (v > f + 2.0 * s):
        return False
    c = _as_float(ceiling)
    if c is not None and not (v < c - 2.0 * s):
        return False
    return True


# --------------------------------------------------------------------------
# 5. 行 / 组 / 表 / 数据集级校验
# --------------------------------------------------------------------------
def validate_row(row: Mapping[str, Any]) -> List[str]:
    """校验一行 measurement 长表。返回错误列表（空 = 合法）。"""
    errs: List[str] = []

    for col in MEASUREMENT_COLUMNS:
        if col not in row:
            errs.append(f"missing column: {col}")
    if errs:
        return errs

    for col in GROUP_KEY_COLUMNS + ("source_row_ref",):
        if row.get(col) in (None, ""):
            errs.append(f"empty required field: {col}")
    if row.get("replicate") in (None, ""):
        errs.append("empty required field: replicate")

    st = _coerce_state(row.get("measurement_state"))
    if st is None:
        errs.append(
            "invalid measurement_state: "
            f"{row.get('measurement_state')!r} (allowed: measured_exact/censored/missing)"
        )

    value = _as_float(row.get("value"))
    floor = _as_float(row.get("floor"))
    ceiling = _as_float(row.get("ceiling"))
    sem = _as_float(row.get("value_sem"))
    sd = _as_float(row.get("value_sd"))
    informative = _as_bool(row.get("informative"))

    if informative is None:
        errs.append(f"invalid informative flag: {row.get('informative')!r}")
    if sem is not None and sem < 0:
        errs.append("value_sem must be >= 0")
    if sd is not None and sd < 0:
        errs.append("value_sd must be >= 0")
    if floor is not None and ceiling is not None and floor > ceiling:
        errs.append("floor must be <= ceiling")

    if st is MeasurementState.MISSING:
        if value is not None:
            errs.append("state=missing requires value to be null")
        if informative is True:
            errs.append("state=missing requires informative=False")
    elif st is MeasurementState.CENSORED:
        if informative is True:
            errs.append("state=censored requires informative=False")
        if floor is None and ceiling is None:
            errs.append("state=censored requires floor and/or ceiling to be set")
        if value is None:
            errs.append("state=censored requires a (boundary) value")
        elif floor is None and ceiling is None:
            pass
        else:
            on_floor = floor is not None and math.isclose(
                value, floor, rel_tol=0.0, abs_tol=NUMERIC_TOLERANCE
            )
            on_ceiling = ceiling is not None and math.isclose(
                value, ceiling, rel_tol=0.0, abs_tol=NUMERIC_TOLERANCE
            )
            if not (on_floor or on_ceiling):
                errs.append("state=censored requires value to sit on floor or ceiling")
    elif st is MeasurementState.MEASURED_EXACT:
        if value is None:
            errs.append("state=measured_exact requires a value")

    return errs


def validate_measurement_group(rows: Sequence[Mapping[str, Any]]) -> List[str]:
    """校验同一 (genotype × task × condition) 组的内部一致性。

    * 所有行的 group key 必须相同；
    * 组级字段（state/floor/ceiling/informative）必须全组一致；
    * 声明的 state 必须等于 ``classify_measurement_state`` 从该组重复值算出的结果。
    """
    errs: List[str] = []
    if not rows:
        return ["empty group"]

    keys = {group_key(r) for r in rows}
    if len(keys) != 1:
        errs.append(f"rows in group have different group keys: {sorted(keys)}")

    for field in ("measurement_state", "floor", "ceiling", "informative"):
        vals = {str(r.get(field)) for r in rows}
        if len(vals) != 1:
            errs.append(f"group-level field {field!r} is not constant within group: {sorted(vals)}")

    declared = _coerce_state(rows[0].get("measurement_state"))
    reps = [r.get("value") for r in rows]
    # 组代表值：取第一个**非空**重复值。
    # 依据构造规则（M1_SCHEMA_SPEC §3）：未观测到的重复**不得**出现在长表里；
    # 若某单元格完全没有观测，只允许一条 state=missing 的行。
    # 因此对 censored 组（重复值完全相同）代表值必然等于该边界值；
    # 对 measured_exact 组，代表值用于边界检验——若某组恰好"重复全同 ∧ sem=0 ∧ 落在边界"
    # 却被声明为 measured_exact，本检查会（正确地）报出不一致。
    representative = None
    for r in rows:
        v = _as_float(r.get("value"))
        if v is not None:
            representative = v
            break
    recomputed = classify_measurement_state(
        replicates=reps,
        sem=rows[0].get("value_sem"),
        value=representative,
        floor=rows[0].get("floor"),
        ceiling=rows[0].get("ceiling"),
    )
    if declared is not None and declared != recomputed:
        errs.append(
            f"declared state {declared.value!r} != recomputed {recomputed.value!r} "
            "(check replicate values / sem / boundary)"
        )
    return errs


def validate_measurement_table(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """逐行 + 逐组校验整张表。返回统计字典（不抛异常）。"""
    rows = list(rows)
    row_errors: List[Tuple[int, List[str]]] = []
    for i, r in enumerate(rows):
        e = validate_row(r)
        if e:
            row_errors.append((i, e))

    groups: Dict[Tuple[str, ...], List[Mapping[str, Any]]] = {}
    for r in rows:
        groups.setdefault(group_key(r), []).append(r)

    group_errors: List[Tuple[Tuple[str, ...], List[str]]] = []
    for k, g in groups.items():
        e = validate_measurement_group(g)
        if e:
            group_errors.append((k, e))

    state_counts = {s.value: 0 for s in MeasurementState}
    for r in rows:
        st = _coerce_state(r.get("measurement_state"))
        if st is not None:
            state_counts[st.value] += 1

    return {
        "n_rows": len(rows),
        "n_groups": len(groups),
        "n_invalid_rows": len(row_errors),
        "n_invalid_groups": len(group_errors),
        "state_counts": state_counts,
        "row_errors": row_errors[:50],
        "group_errors": group_errors[:50],
        "ok": not row_errors and not group_errors,
    }


def validate_dataset_record(rec: Mapping[str, Any]) -> List[str]:
    """校验数据集级元数据（规范 §6）。"""
    errs: List[str] = []
    for col in DATASET_RECORD_COLUMNS:
        if col not in rec:
            errs.append(f"missing column: {col}")
    if errs:
        return errs

    if rec.get("dataset_id") in (None, ""):
        errs.append("dataset_id must be non-empty")

    try:
        SourceType(str(rec["source_type"]))
    except ValueError:
        errs.append(
            f"invalid source_type: {rec['source_type']!r} "
            f"(allowed: {[s.value for s in SourceType]})"
        )
    try:
        DatasetRole(str(rec["role"]))
    except ValueError:
        errs.append(
            f"invalid role: {rec['role']!r} (allowed: {[r.value for r in DatasetRole]})"
        )

    for flag in ("analysis_allowed", "redistribution_allowed", "complete_product"):
        if _as_bool(rec.get(flag)) is None:
            errs.append(f"{flag} must be boolean-like, got {rec.get(flag)!r}")

    tss = rec.get("theoretical_space_size")
    ogc = rec.get("observed_genotype_count")
    tss_i = None if tss in (None, "") else int(tss)
    ogc_i = None if ogc in (None, "") else int(ogc)
    if tss_i is not None and tss_i <= 0:
        errs.append("theoretical_space_size must be > 0")
    if ogc_i is not None and ogc_i <= 0:
        errs.append("observed_genotype_count must be > 0")
    if tss_i is not None and ogc_i is not None:
        declared_complete = _as_bool(rec.get("complete_product"))
        actually_complete = ogc_i == tss_i
        if declared_complete is not None and declared_complete != actually_complete:
            errs.append(
                "complete_product inconsistent with counts "
                f"(declared={declared_complete}, observed={ogc_i}, theoretical={tss_i})"
            )
    return errs


def informative_fraction(rows: Iterable[Mapping[str, Any]]) -> float:
    """``informative_frac`` = informative 行数 / 全部行数（任务准入用，CL-9）。

    仅统计;不做任何阈值判定（准入闸门在协议层，不在 schema 层）。
    """
    rows = list(rows)
    if not rows:
        return float("nan")
    n_inf = sum(1 for r in rows if _as_bool(r.get("informative")) is True)
    return n_inf / len(rows)


# ==========================================================================
# 6. schema v1.2 增量（AMENDMENT-009；**metadata-only**，不改任何科学定义）
# ==========================================================================
#: v1.2 只改 metadata 语义与校验契约；EOV / V_{B,pi} / regret 的定义一律不动。
#: v1.4 起 ``SCHEMA_VERSION`` 指向**当前**版本；它定义在文件末尾（§7），
#: 以便同时保留各历史版本的冻结常量。
V11_SCHEMA_VERSION = "1.1"
V12_SCHEMA_VERSION = "1.2"
V13_SCHEMA_VERSION = "1.3"


class BoundaryStatus(str, Enum):
    """边界判定的确定性（AMENDMENT-009 §3.3）。

    ⛔ 绝不能把 observed min/max 当作 assay floor/ceiling。
    证据不足时必须是 ``unresolved``，且此时**不得产出任何 censored**。
    """

    EXPLICIT = "explicit"
    INFERRED = "inferred"
    UNRESOLVED = "unresolved"


class BoundarySource(str, Enum):
    """边界值的来源（AMENDMENT-009 §3.3）。"""

    ASSAY_DETECTION = "assay_detection"
    TRANSFORMATION = "transformation"
    PLATE_CLIPPING = "plate_clipping"
    AUTHOR_STATEMENT = "author_statement"
    REPLICATE_PATTERN = "replicate_pattern"
    NONE = "none"


class MeasurementModality(str, Enum):
    """功能读数 vs 辅助读数（AMENDMENT-009 §4）。

    expression axis 是 **auxiliary**，不得悄悄当成第四个 functional task。
    """

    FUNCTIONAL = "functional"
    AUXILIARY = "auxiliary"


#: v1.2 数据集级列契约：单列 ``license`` 被五个字段取代（AMENDMENT-009 §2）。
DATASET_RECORD_COLUMNS_V12: Tuple[str, ...] = (
    "dataset_id",
    "protein_or_system",
    "source_type",
    "original_deposit_url",
    "fetched_url",
    "paper_license",
    "source_data_license",
    "code_license",
    "analysis_allowed",
    "redistribution_allowed",
    "redistribution_basis",
    "role",
    "theoretical_space_size",
    "complete_product",
    "observed_genotype_count",
    "notes",
)

#: v1.2 measurement 长表列契约（v1.1 的超集，向后兼容）。
MEASUREMENT_COLUMNS_V12: Tuple[str, ...] = GROUP_KEY_COLUMNS + (
    "replicate",
    "value",
    "value_sem",
    "value_sd",
    "n_expected",
    "n_observed",
    "n_missing",
    "measurement_state",
    "measurement_modality",
    "floor",
    "ceiling",
    "boundary_status",
    "boundary_source",
    "informative",
    "source_row_ref",
)

#: ``redistribution_basis`` 不得是这些占位串（AMENDMENT-009 §2：必填且必须说明实际依据）。
PLACEHOLDER_BASIS: frozenset = frozenset(
    {
        "",
        "-",
        "--",
        "?",
        "n/a",
        "na",
        "none",
        "null",
        "tbd",
        "todo",
        "unknown",
        "unspecified",
        "pending",
        "placeholder",
        "see notes",
    }
)

#: basis 必须是一句解释，而不是一个词。
MIN_BASIS_CHARS = 10

#: **只有**这两类角色允许进入 graph 平面（AMENDMENT-009 §5）。
GRAPH_ELIGIBLE_ROLES: Tuple[DatasetRole, ...] = (
    DatasetRole.STRICT_MULTI_TASK,
    DatasetRole.SINGLE_TASK_CONTROL,
)

#: graph-eligible 才允许输出的 QC；非 graph-eligible（含 ``task_panel``）**不得输出 degree**。
GRAPH_ELIGIBLE_QC_FIELDS: Tuple[str, ...] = ("degree_topology", "degree_effective")
NON_GRAPH_QC_FIELDS: Tuple[str, ...] = (
    "task_coverage",
    "measured_fraction",
    "censored_fraction",
    "informative_fraction",
    "uncertainty_completeness",
)


# --------------------------------------------------------------------------
# 6.1 枚举/布尔小工具
# --------------------------------------------------------------------------
def _coerce_role(x: Any) -> Optional[DatasetRole]:
    if isinstance(x, DatasetRole):
        return x
    if x is None:
        return None
    try:
        return DatasetRole(str(x).strip())
    except ValueError:
        return None


def _coerce_simple_enum(enum_cls: Any, x: Any) -> Any:
    if isinstance(x, enum_cls):
        return x
    if x is None:
        return None
    try:
        return enum_cls(str(x).strip().lower())
    except ValueError:
        return None


def _is_placeholder_basis(text: Any) -> bool:
    if text is None:
        return True
    s = str(text).strip().lower()
    if s in PLACEHOLDER_BASIS:
        return True
    return len(str(text).strip()) < MIN_BASIS_CHARS


# --------------------------------------------------------------------------
# 6.2 graph eligibility 与 QC 范围（AMENDMENT-009 §5）
# --------------------------------------------------------------------------
def graph_eligible(
    role: Any,
    *,
    complete_product: Any = None,
    observed_genotype_count: Any = None,
    theoretical_space_size: Any = None,
) -> bool:
    """**代码级硬防守**：``task_panel``（及 oracle_only / modality_control / conditional）永不 graph-eligible。

    冻结公式（AMENDMENT-009 §5）::

        graph_eligible = (role ∈ {strict_multi_task, single_task_control})
                         ∧ 完整/密集乘积空间
                         ∧ observed_genotype_count == theoretical_space_size

    角色检查**排在最前**：即使空间完整、计数相等，``task_panel`` 也一律返回 ``False``。
    缺少显式证据（``complete_product`` 未声明或为假、计数缺失）时一律返回 ``False``（保守）。
    """
    r = _coerce_role(role)
    if r not in GRAPH_ELIGIBLE_ROLES:
        # task_panel / oracle_only / modality_control / conditional → 一律不可入图
        return False
    if _as_bool(complete_product) is not True:
        return False
    if observed_genotype_count is None or theoretical_space_size is None:
        return False
    try:
        return int(observed_genotype_count) == int(theoretical_space_size)
    except (TypeError, ValueError):
        return False


def allowed_qc_fields(role: Any, **kwargs: Any) -> Tuple[str, ...]:
    """按角色返回**允许输出**的 QC 字段（AMENDMENT-009 §5）。

    graph-eligible → degree 类字段 + 非图类字段；
    否则 → **只有**非图类字段（task coverage / fractions / uncertainty）。
    """
    if graph_eligible(role, **kwargs):
        return GRAPH_ELIGIBLE_QC_FIELDS + NON_GRAPH_QC_FIELDS
    return NON_GRAPH_QC_FIELDS


# --------------------------------------------------------------------------
# 6.3 modality 分离（AMENDMENT-009 §4）
# --------------------------------------------------------------------------
def _modality_of(row: Mapping[str, Any]) -> Optional[MeasurementModality]:
    return _coerce_simple_enum(MeasurementModality, row.get("measurement_modality"))


def functional_task_ids(rows: Iterable[Mapping[str, Any]]) -> Tuple[str, ...]:
    """**functional** modality 覆盖的 task 集合（auxiliary **不计入**）。"""
    return tuple(
        sorted({str(r.get("task_id")) for r in rows if _modality_of(r) is MeasurementModality.FUNCTIONAL})
    )


def auxiliary_task_ids(rows: Iterable[Mapping[str, Any]]) -> Tuple[str, ...]:
    """**auxiliary** modality 覆盖的 task 集合（如 Phillips2023 的 expression axis）。"""
    return tuple(
        sorted({str(r.get("task_id")) for r in rows if _modality_of(r) is MeasurementModality.AUXILIARY})
    )


# --------------------------------------------------------------------------
# 6.4 measurement 行 / 组 / 表校验（v1.2）
# --------------------------------------------------------------------------
def _counts_triplet(row: Mapping[str, Any]) -> Tuple[Optional[int], Optional[int], Optional[int], List[str]]:
    errs: List[str] = []
    vals: List[Optional[int]] = []
    for col in ("n_expected", "n_observed", "n_missing"):
        raw = row.get(col)
        if raw in (None, ""):
            vals.append(None)
            continue
        try:
            vals.append(int(raw))
        except (TypeError, ValueError):
            errs.append(f"{col} must be an integer, got {raw!r}")
            vals.append(None)
    ne, no, nm = vals
    if ne is not None and ne < 1:
        errs.append("n_expected must be >= 1")
    if no is not None and no < 0:
        errs.append("n_observed must be >= 0")
    if nm is not None and nm < 0:
        errs.append("n_missing must be >= 0")
    if ne is not None and no is not None and no > ne:
        errs.append(f"n_observed ({no}) must be <= n_expected ({ne})")
    if ne is not None and no is not None and nm is not None and nm != ne - no:
        errs.append(f"n_missing ({nm}) must equal n_expected - n_observed ({ne} - {no})")
    return ne, no, nm, errs


def validate_measurement_row_v12(row: Mapping[str, Any]) -> List[str]:
    """v1.2 行级校验 = v1.1 行级校验 + 新字段（replicate 计数 / modality / boundary）。"""
    errs: List[str] = []
    for col in MEASUREMENT_COLUMNS_V12:
        if col not in row:
            errs.append(f"missing column: {col}")
    if errs:
        return errs

    errs.extend(validate_row(row))
    _, _, _, c_errs = _counts_triplet(row)
    errs.extend(c_errs)

    if _coerce_simple_enum(MeasurementModality, row.get("measurement_modality")) is None:
        errs.append(
            f"invalid measurement_modality: {row.get('measurement_modality')!r} "
            f"(allowed: {[m.value for m in MeasurementModality]})"
        )

    bs = _coerce_simple_enum(BoundaryStatus, row.get("boundary_status"))
    bsrc = _coerce_simple_enum(BoundarySource, row.get("boundary_source"))
    if bs is None:
        errs.append(
            f"invalid boundary_status: {row.get('boundary_status')!r} "
            f"(allowed: {[b.value for b in BoundaryStatus]})"
        )
    if bsrc is None:
        errs.append(
            f"invalid boundary_source: {row.get('boundary_source')!r} "
            f"(allowed: {[s.value for s in BoundarySource]})"
        )

    if bs is not None and bsrc is not None:
        if bs is BoundaryStatus.UNRESOLVED and bsrc is not BoundarySource.NONE:
            errs.append("boundary_status=unresolved requires boundary_source=none")
        if bs in (BoundaryStatus.EXPLICIT, BoundaryStatus.INFERRED) and bsrc is BoundarySource.NONE:
            errs.append(f"boundary_status={bs.value} requires a concrete boundary_source")

    st = _coerce_state(row.get("measurement_state"))
    if st is MeasurementState.CENSORED and bs is BoundaryStatus.UNRESOLVED:
        errs.append(
            "state=censored is forbidden when boundary_status=unresolved "
            "(AMENDMENT-009 3.3: never fabricate a floor to run CL-7)"
        )
    return errs


def validate_measurement_group_v12(rows: Sequence[Mapping[str, Any]]) -> List[str]:
    """v1.2 组级校验。

    在 v1.1 组规则之上追加：计数三元组自洽、组内字段恒定、boundary 一致性、
    「只有一个有效重复时不得虚构 SEM」、以及**用 v1.2 契约重算 state**。
    """
    errs: List[str] = []
    if not rows:
        return ["empty group"]

    for i, r in enumerate(rows):
        e = validate_measurement_row_v12(r)
        if e:
            errs.extend(f"row[{i}]: {msg}" for msg in e)

    keys = {group_key(r) for r in rows}
    if len(keys) != 1:
        errs.append(f"rows in group have different group keys: {sorted(keys)}")

    for field in (
        "measurement_state",
        "measurement_modality",
        "boundary_status",
        "boundary_source",
        "n_expected",
        "n_observed",
        "n_missing",
        "floor",
        "ceiling",
        "informative",
    ):
        vals = {str(r.get(field)) for r in rows}
        if len(vals) != 1:
            errs.append(f"group-level field {field!r} is not constant within group: {sorted(vals)}")

    ne, no, nm, _ = _counts_triplet(rows[0])
    values = [r.get("value") for r in rows]
    n_value_rows = sum(1 for v in values if _as_float(v) is not None)
    reps = [v for v in values if _as_float(v) is not None]

    # 构造规则（M1_SCHEMA_SPEC §3）：未观测到的重复不得发射成行。
    if no is not None and n_value_rows != no:
        errs.append(
            f"n_observed ({no}) must equal the number of rows carrying a value ({n_value_rows}); "
            "unobserved replicates must not be emitted as rows"
        )

    bs = _coerce_simple_enum(BoundaryStatus, rows[0].get("boundary_status"))
    declared = _coerce_state(rows[0].get("measurement_state"))

    # 硬性禁令：unresolved ⇒ 不得出现 censored
    if bs is BoundaryStatus.UNRESOLVED and declared is MeasurementState.CENSORED:
        errs.append("boundary_status=unresolved forbids censored (task-level rule)")

    # 「仅一个有效重复不得虚构 SEM/SD」
    if no is not None and no < 2:
        if any(_as_float(r.get("value_sem")) is not None for r in rows) or any(
            _as_float(r.get("value_sd")) is not None for r in rows
        ):
            errs.append(
                "value_sem/value_sd must be null when fewer than 2 replicates were observed "
                "(a spread cannot be derived from a single replicate)"
            )

    representative = None
    for v in values:
        fv = _as_float(v)
        if fv is not None:
            representative = fv
            break

    recomputed = _classify_state_v12(
        replicates=reps,
        sem=rows[0].get("value_sem"),
        value=representative,
        floor=rows[0].get("floor"),
        ceiling=rows[0].get("ceiling"),
        boundary_status=rows[0].get("boundary_status"),
        n_expected=ne,
    )
    if declared is not None and declared != recomputed:
        errs.append(
            f"declared state {declared.value!r} != recomputed {recomputed.value!r} "
            "(v1.2: check replicate values / sem / boundary_status / n_expected)"
        )
    return errs


def validate_measurement_table_v12(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """v1.2 表级校验：逐行 + 逐组 + **逐 task 的 boundary 一致性**。返回统计字典。"""
    rows = list(rows)
    row_errors: List[Tuple[int, List[str]]] = []
    for i, r in enumerate(rows):
        e = validate_measurement_row_v12(r)
        if e:
            row_errors.append((i, e))

    groups: Dict[Tuple[str, ...], List[Mapping[str, Any]]] = {}
    for r in rows:
        groups.setdefault(group_key(r), []).append(r)

    group_errors: List[Tuple[Tuple[str, ...], List[str]]] = []
    for k, g in groups.items():
        e = validate_measurement_group_v12(g)
        if e:
            group_errors.append((k, e))

    # 逐 (dataset_id, task_id)：boundary_status 必须在 task 内恒定；
    # unresolved 的 task **一条 censored 都不许有**。
    task_errors: List[Tuple[str, List[str]]] = []
    tasks: Dict[Tuple[str, str], List[Mapping[str, Any]]] = {}
    for r in rows:
        tasks.setdefault((str(r.get("dataset_id")), str(r.get("task_id"))), []).append(r)
    for (ds, task), g in tasks.items():
        terr: List[str] = []
        statuses = {str(r.get("boundary_status")) for r in g}
        if len(statuses) != 1:
            terr.append(f"boundary_status not constant within task: {sorted(statuses)}")
        if statuses == {"unresolved"}:
            n_cens = sum(
                1
                for r in g
                if _coerce_state(r.get("measurement_state")) is MeasurementState.CENSORED
            )
            if n_cens:
                terr.append(
                    f"boundary_status=unresolved forbids censored, found {n_cens} censored row(s)"
                )
        if terr:
            task_errors.append((f"{ds}/{task}", terr))

    state_counts = {s.value: 0 for s in MeasurementState}
    for r in rows:
        st = _coerce_state(r.get("measurement_state"))
        if st is not None:
            state_counts[st.value] += 1

    return {
        "schema_version": V12_SCHEMA_VERSION,
        "n_rows": len(rows),
        "n_groups": len(groups),
        "n_tasks": len(tasks),
        "n_invalid_rows": len(row_errors),
        "n_invalid_groups": len(group_errors),
        "n_invalid_tasks": len(task_errors),
        "state_counts": state_counts,
        "functional_task_ids": functional_task_ids(rows),
        "auxiliary_task_ids": auxiliary_task_ids(rows),
        "row_errors": row_errors[:50],
        "group_errors": group_errors[:50],
        "task_errors": task_errors[:50],
        "ok": not row_errors and not group_errors and not task_errors,
    }


# --------------------------------------------------------------------------
# 6.5 数据集级校验（v1.2）
# --------------------------------------------------------------------------
def validate_dataset_record_v12(rec: Mapping[str, Any]) -> List[str]:
    """v1.2 数据集记录校验（AMENDMENT-009 §2）。

    ⛔ ``redistribution_allowed`` **不得**由 ``source_data_license`` 机械推导：
    完全可能存在 "primary deposit = CC0 但 third-party repackaged file = license unclear"。
    因此本函数**不含**任何"许可 vs 布尔"的一致性规则；判定依据只能是
    ``redistribution_basis`` 里写明的 provenance 事实。
    """
    errs: List[str] = []
    for col in DATASET_RECORD_COLUMNS_V12:
        if col not in rec:
            errs.append(f"missing column: {col}")
    if errs:
        return errs

    if rec.get("dataset_id") in (None, ""):
        errs.append("dataset_id must be non-empty")

    if _coerce_simple_enum(SourceType, rec.get("source_type")) is None:
        errs.append(
            f"invalid source_type: {rec.get('source_type')!r} (allowed: {[s.value for s in SourceType]})"
        )
    if _coerce_role(rec.get("role")) is None:
        errs.append(f"invalid role: {rec.get('role')!r} (allowed: {[r.value for r in DatasetRole]})")

    for flag in ("analysis_allowed", "redistribution_allowed", "complete_product"):
        if _as_bool(rec.get(flag)) is None:
            errs.append(f"{flag} must be boolean-like, got {rec.get(flag)!r}")

    basis = rec.get("redistribution_basis")
    if basis is None or str(basis).strip() == "":
        errs.append("redistribution_basis is required (must cite the provenance fact relied on)")
    elif _as_bool(rec.get("redistribution_allowed")) is True and _is_placeholder_basis(basis):
        errs.append(
            f"redistribution_basis looks like a placeholder ({str(basis)[:40]!r}); "
            "redistribution_allowed=True requires a concrete provenance basis"
        )

    tss = rec.get("theoretical_space_size")
    ogc = rec.get("observed_genotype_count")
    tss_i = None if tss in (None, "") else int(tss)
    ogc_i = None if ogc in (None, "") else int(ogc)
    if tss_i is not None and tss_i <= 0:
        errs.append("theoretical_space_size must be > 0")
    if ogc_i is not None and ogc_i <= 0:
        errs.append("observed_genotype_count must be > 0")
    if tss_i is not None and ogc_i is not None:
        declared_complete = _as_bool(rec.get("complete_product"))
        actually_complete = ogc_i == tss_i
        if declared_complete is not None and declared_complete != actually_complete:
            errs.append(
                "complete_product inconsistent with counts "
                f"(declared={declared_complete}, observed={ogc_i}, theoretical={tss_i})"
            )

    # 角色/空间与 graph eligibility 的自洽提示（不阻断，属于元数据卫生）
    if _coerce_role(rec.get("role")) is DatasetRole.TASK_PANEL:
        if ogc_i is not None and tss_i is not None and ogc_i == tss_i and _as_bool(rec.get("complete_product")) is True:
            pass  # 允许：task_panel 仍可标注空间完整，但 graph_eligible() 恒为 False
    return errs


def migrate_dataset_record_v11_to_v12(
    rec: Mapping[str, Any],
    *,
    paper_license: str = "",
    source_data_license: str = "",
    code_license: str = "",
    redistribution_basis: str = "",
) -> Dict[str, Any]:
    """把 v1.1 数据集记录迁移为 v1.2 结构（单列 ``license`` → 五字段）。

    ``license`` 原值**保留在 notes 中**（不丢历史），但不再作为 v1.2 的字段。
    """
    out: Dict[str, Any] = {}
    for col in DATASET_RECORD_COLUMNS_V12:
        if col in ("paper_license", "source_data_license", "code_license", "redistribution_basis"):
            continue
        out[col] = rec.get(col, "")
    out["paper_license"] = paper_license
    out["source_data_license"] = source_data_license
    out["code_license"] = code_license
    out["redistribution_basis"] = redistribution_basis
    legacy = rec.get("license")
    if legacy not in (None, ""):
        out["notes"] = f"{out.get('notes', '')} | v1.1 license field = {legacy}".strip(" |")
    return out


# ==========================================================================
# 7. schema v1.4 增量（AMENDMENT-011；**metadata-only**）
# ==========================================================================
#: v1.4 的核心变化：measurement state 由三态升为**四态**；新增 ``censoring_evidence``；
#: 新增 ``d_present`` / ``d_informative`` 两个**分离**的邻域口径。
#: EOV / V_{B,pi} / regret 的定义一律不动。


#: 当前版本（真实值 "1.4"）。
#:
#: ⚠️ **曾经的兼容相等性 shim 已被移除（AMENDMENT-012）**。
#: v1.4 首次落地时，为了让**冻结资产** ``tests/test_schema_v1_2.py`` 的断言
#: ``SCHEMA_VERSION == "1.2"`` 继续通过，曾用一个 ``SchemaVersion(str)`` 子类令
#: ``SCHEMA_VERSION == "1.2"`` 返回 ``True``。**该做法已被撤销**：
#: 一个会对历史版本号返回相等的版本字符串是"说谎的相等"，会让未来任何
#: ``if SCHEMA_VERSION == "1.2": ...`` 的分支在 v1.4 模块上**静默走错路径** ——
#: 这正是本项目一路在消除的那类静默失效。
#: 现在 ``SCHEMA_VERSION`` 是**普通字符串**，相等性只有一种含义。
#: 相应地，冻结测试中那一行**过度指定**的断言已改为契约断言（见
#: ``tests/test_schema_v1_2.py`` 的 v1.2 版本检查），并记录在 FREEZE_LEDGER 批次 #18。
SCHEMA_VERSION = "1.4"

#: 冻结的 v1.2 三态判定入口（v1.2 校验器仍在使用；不得改动其语义）。
classify_measurement_state_v12 = _classify_state_v12


class CensoringEvidence(str, Enum):
    """该组被判为"边界删失"所依据的**证据等级**（AMENDMENT-011 §2）。"""

    EXPLICIT = "explicit"  #: 明确文档化的 assay floor（⇒ 可产出真 censored）
    INFERRED = "inferred"  #: 推断边界（⇒ 只能产出 boundary_ambiguous）
    NONE = "none"  #: 未命中任何边界


#: v1.4 measurement 长表列契约（v1.2 的超集；新增 3 列）。
MEASUREMENT_COLUMNS_V14: Tuple[str, ...] = MEASUREMENT_COLUMNS_V12 + (
    "censoring_evidence",
    "at_inferred_floor",
    "value_group",
)

#: v1.4 数据集级列契约沿用 v1.2。
DATASET_RECORD_COLUMNS_V14: Tuple[str, ...] = DATASET_RECORD_COLUMNS_V12


def _coerce_evidence(x: Any) -> Optional[CensoringEvidence]:
    return _coerce_simple_enum(CensoringEvidence, x)


def evidence_for_state(state: Any) -> CensoringEvidence:
    """canonical state → 其应携带的 ``censoring_evidence``（v1.4 硬规则）。"""
    st = _coerce_state(state)
    if st is MeasurementState.CENSORED:
        return CensoringEvidence.EXPLICIT
    if st is MeasurementState.BOUNDARY_AMBIGUOUS:
        return CensoringEvidence.INFERRED
    return CensoringEvidence.NONE


def classify_group_v14(
    rows: Sequence[Mapping[str, Any]],
    *,
    representative: Any = None,
) -> Tuple[MeasurementState, CensoringEvidence]:
    """**组级** v1.4 判定：返回 ``(state, censoring_evidence)``。

    ``representative`` 缺省时依次尝试 ``row["value_group"]`` → 第一个非空 ``value``。
    （组代表值必须是**规范化的组级量**，绝不能依赖某一行的位置 —— AMENDMENT-010 §1。）
    """
    if not rows:
        return MeasurementState.MISSING, CensoringEvidence.NONE
    r0 = rows[0]
    reps = [r.get("value") for r in rows if _as_float(r.get("value")) is not None]
    if not reps:
        return MeasurementState.MISSING, CensoringEvidence.NONE

    rep = representative
    if rep is None:
        rep = r0.get("value_group")
    if _as_float(rep) is None:
        rep = reps[0]

    st = classify_measurement_state(
        replicates=reps,
        sem=r0.get("value_sem"),
        value=rep,
        floor=r0.get("floor"),
        ceiling=r0.get("ceiling"),
        boundary_status=r0.get("boundary_status"),
        n_expected=r0.get("n_expected"),
    )
    return st, evidence_for_state(st)


def _v14_structural_errors(row: Mapping[str, Any]) -> List[str]:
    """v1.4 三条**硬规则**（AMENDMENT-011 §2）。"""
    errs: List[str] = []
    st = _coerce_state(row.get("measurement_state"))
    ev = _coerce_evidence(row.get("censoring_evidence"))
    aif = _as_bool(row.get("at_inferred_floor"))

    if ev is None:
        errs.append(
            f"invalid censoring_evidence: {row.get('censoring_evidence')!r} "
            f"(allowed: {[e.value for e in CensoringEvidence]})"
        )
    if aif is None:
        errs.append(f"at_inferred_floor must be boolean-like, got {row.get('at_inferred_floor')!r}")

    if st is not None and ev is not None:
        if st is MeasurementState.CENSORED and ev is not CensoringEvidence.EXPLICIT:
            errs.append("state=censored requires censoring_evidence=explicit")
        if st is MeasurementState.BOUNDARY_AMBIGUOUS and ev is not CensoringEvidence.INFERRED:
            errs.append("state=boundary_ambiguous requires censoring_evidence=inferred")
        if ev is CensoringEvidence.NONE and st not in (
            MeasurementState.EXACT,
            MeasurementState.MISSING,
        ):
            errs.append("censoring_evidence=none is only valid with state=exact or state=missing")
        if ev is CensoringEvidence.EXPLICIT and st is not MeasurementState.CENSORED:
            errs.append("censoring_evidence=explicit is only valid with state=censored")
        if ev is CensoringEvidence.INFERRED and st is not MeasurementState.BOUNDARY_AMBIGUOUS:
            errs.append("censoring_evidence=inferred is only valid with state=boundary_ambiguous")

    if aif is True and st is MeasurementState.EXACT:
        errs.append(
            "state=exact forbids at_inferred_floor=True (v1.4: an inferred-floor hit must be "
            "classified as boundary_ambiguous, not as exact)"
        )
    if st is MeasurementState.BOUNDARY_AMBIGUOUS and aif is False:
        errs.append("at_inferred_floor must be True when state=boundary_ambiguous")
    return errs


def validate_measurement_row_v14(row: Mapping[str, Any]) -> List[str]:
    """v1.4 行级校验 = v1.2 行级校验 + 四态/证据硬规则。"""
    errs: List[str] = []
    for col in MEASUREMENT_COLUMNS_V14:
        if col not in row:
            errs.append(f"missing column: {col}")
    if errs:
        return errs
    errs.extend(validate_measurement_row_v12(row))
    errs.extend(_v14_structural_errors(row))
    return errs


def validate_measurement_group_v14(rows: Sequence[Mapping[str, Any]]) -> List[str]:
    """v1.4 组级校验：v1.2 组规则 + 组级字段恒定 + **用 v1.4 契约重算 state**。"""
    errs: List[str] = []
    if not rows:
        return ["empty group"]
    for i, r in enumerate(rows):
        e = validate_measurement_row_v14(r)
        if e:
            errs.extend(f"row[{i}]: {msg}" for msg in e)

    for field in ("censoring_evidence", "at_inferred_floor", "value_group"):
        vals = {str(r.get(field)) for r in rows}
        if len(vals) != 1:
            errs.append(f"group-level field {field!r} is not constant within group: {sorted(vals)}")

    # 与 v1.2 组规则共用的部分（计数三元组、缺失重复、unresolved 禁令、字段恒定）
    errs.extend(validate_measurement_group_v12(rows))

    declared = _coerce_state(rows[0].get("measurement_state"))
    declared_ev = _coerce_evidence(rows[0].get("censoring_evidence"))
    recomputed, recomputed_ev = classify_group_v14(rows)
    if declared is not None and declared != recomputed:
        errs.append(
            f"declared state {declared.value!r} != recomputed {recomputed.value!r} (v1.4: "
            "check boundary_status / 组代表值 value_group / sem / n_expected)"
        )
    if declared_ev is not None and declared_ev is not recomputed_ev:
        errs.append(
            f"declared censoring_evidence {declared_ev.value!r} != recomputed {recomputed_ev.value!r}"
        )
    return errs


def validate_measurement_table_v14(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """v1.4 表级校验：逐行 + 逐组 + 逐 task 一致性。返回统计字典。"""
    rows = list(rows)
    row_errors: List[Tuple[int, List[str]]] = []
    for i, r in enumerate(rows):
        e = validate_measurement_row_v14(r)
        if e:
            row_errors.append((i, e))

    groups: Dict[Tuple[str, ...], List[Mapping[str, Any]]] = {}
    for r in rows:
        groups.setdefault(group_key(r), []).append(r)

    group_errors: List[Tuple[Tuple[str, ...], List[str]]] = []
    for k, g in groups.items():
        e = validate_measurement_group_v14(g)
        if e:
            group_errors.append((k, e))

    task_errors: List[Tuple[str, List[str]]] = []
    tasks: Dict[Tuple[str, str], List[Mapping[str, Any]]] = {}
    for r in rows:
        tasks.setdefault((str(r.get("dataset_id")), str(r.get("task_id"))), []).append(r)
    for (ds, task), g in tasks.items():
        terr: List[str] = []
        statuses = {str(r.get("boundary_status")) for r in g}
        if len(statuses) != 1:
            terr.append(f"boundary_status not constant within task: {sorted(statuses)}")
        if statuses == {"unresolved"}:
            bad = sum(
                1
                for r in g
                if _coerce_state(r.get("measurement_state"))
                in (MeasurementState.CENSORED, MeasurementState.BOUNDARY_AMBIGUOUS)
            )
            if bad:
                terr.append(
                    f"boundary_status=unresolved forbids censored/boundary_ambiguous, found {bad} row(s)"
                )
        if "inferred" in statuses:
            # 只允许 boundary_ambiguous（或 exact / missing）—— 绝不允许真 censored
            bad = sum(
                1 for r in g if _coerce_state(r.get("measurement_state")) is MeasurementState.CENSORED
            )
            if bad:
                terr.append(
                    f"boundary_status=inferred forbids censored (must be boundary_ambiguous), "
                    f"found {bad} row(s)"
                )
        if terr:
            task_errors.append((f"{ds}/{task}", terr))

    state_counts = {s.value: 0 for s in MeasurementState}
    evidence_counts = {e.value: 0 for e in CensoringEvidence}
    for r in rows:
        st = _coerce_state(r.get("measurement_state"))
        if st is not None:
            state_counts[st.value] += 1
        ev = _coerce_evidence(r.get("censoring_evidence"))
        if ev is not None:
            evidence_counts[ev.value] += 1

    return {
        "schema_version": str(SCHEMA_VERSION),
        "n_rows": len(rows),
        "n_groups": len(groups),
        "n_tasks": len(tasks),
        "n_invalid_rows": len(row_errors),
        "n_invalid_groups": len(group_errors),
        "n_invalid_tasks": len(task_errors),
        "state_counts": state_counts,
        "evidence_counts": evidence_counts,
        "row_errors": row_errors[:50],
        "group_errors": group_errors[:50],
        "task_errors": task_errors[:50],
        "ok": not row_errors and not group_errors and not task_errors,
    }


def validate_dataset_record_v14(rec: Mapping[str, Any]) -> List[str]:
    """v1.4 数据集记录校验：v1.4 **未改**数据集级字段，故沿用 v1.2 契约。"""
    errs: List[str] = []
    for col in DATASET_RECORD_COLUMNS_V14:
        if col not in rec:
            errs.append(f"missing column: {col}")
    if errs:
        return errs
    return validate_dataset_record_v12(rec)

