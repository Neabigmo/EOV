"""schema v1.4 测试（AMENDMENT-011）。

覆盖：
1. 四态枚举完整、``measured_exact`` 不再是写入值
2. ``boundary_status=inferred`` + 命中边界 → ``boundary_ambiguous``（**不要求重复全等**）
3. ``boundary_status=explicit`` + CL-7 → ``censored``
4. 无 floor（MA90 / expression 风格）→ 永不产生 censored / boundary_ambiguous
5. ``state=exact ∧ at_inferred_floor=True`` → 必须报错
6. ``censored ∧ censoring_evidence≠explicit`` → 必须报错
7. ``degree_informative`` 与 ``degree_present`` 必然不同（CR9114 h3 风格小型合例）
8. 边界命中容差：**十进制圆整的 floor 字面量**不得静默漏判（TEM-1 实况）
9. 真实 parquet 的重分类结果自洽（无 measured_exact、无 exact+at_inferred_floor）
10. 回归：v1.1 / v1.2 两个冻结测试文件仍全部通过（不改动它们）

⛔ 本文件不涉及任何 EOV / regret / parent ranking / Tomorrow-Test 逻辑。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eov.landscape import (  # noqa: E402
    GenotypeGraph,
    MeasurementIndex,
    MixedAlphabetSpace,
)
from eov.schema import (  # noqa: E402
    BOUNDARY_ABS_TOL,
    SCHEMA_VERSION,
    CensoringEvidence,
    MeasurementState,
    classify_group_v14,
    classify_informative,
    classify_measurement_state,
    evidence_for_state,
    validate_measurement_group_v14,
    validate_measurement_row_v14,
)

PARQUET = ROOT / "data" / "processed" / "M2_measurements.parquet"
V11_TEST = ROOT / "tests" / "test_tem1_topology.py"
V12_TEST = ROOT / "tests" / "test_schema_v1_2.py"

#: TEM-1 的真实推断边界：log10(1.5)。
LOG10_1P5 = 0.17609125905568124
#: 表里冻结的**十进制字面量**（约 10 位有效数字）。
TEM1_FLOOR_LITERAL = 0.1760912591


def _row(**overrides: Any) -> Dict[str, Any]:
    """一条合法的 v1.4 measurement 行。"""
    row: Dict[str, Any] = {
        "protein": "TEM-1",
        "dataset_id": "TEM-1CML",
        "genotype_id": ".............",
        "task_id": "AMP",
        "condition_id": "781.0",
        "replicate": "1",
        "value": 8.0,
        "value_sem": 0.1,
        "value_sd": 0.17,
        "n_expected": 3,
        "n_observed": 3,
        "n_missing": 0,
        "measurement_state": "exact",
        "measurement_modality": "functional",
        "floor": 6.0,
        "ceiling": 10.5,
        "boundary_status": "explicit",
        "boundary_source": "assay_detection",
        "informative": True,
        "source_row_ref": "row1",
        "censoring_evidence": "none",
        "at_inferred_floor": False,
        "value_group": 8.0,
    }
    row.update(overrides)
    return row


# ==========================================================================
# 1. 四态枚举
# ==========================================================================
def test_four_state_enum_and_legacy_alias():
    values = [s.value for s in MeasurementState]
    assert values == ["exact", "censored", "boundary_ambiguous", "missing"], values
    # 旧名已是同一成员的别名（只读兼容），其 value 必须是 "exact"
    assert MeasurementState.MEASURED_EXACT is MeasurementState.EXACT
    assert MeasurementState.MEASURED_EXACT.value == "exact"
    # 真实版本是 1.4（AMENDMENT-012 起 SCHEMA_VERSION 是**普通字符串**；
    # 曾经的 SchemaVersion shim 已被移除，不再有 .value 属性，且不再对历史版本号返回相等）
    assert isinstance(SCHEMA_VERSION, str)
    assert SCHEMA_VERSION == "1.4"
    assert SCHEMA_VERSION != "1.2"


# ==========================================================================
# 2. inferred + 命中边界 → boundary_ambiguous（不要求重复全等 / SEM=0）
# ==========================================================================
def test_inferred_boundary_hit_is_ambiguous_even_without_identical_replicates():
    F, C = 6.0, 10.5
    # 重复**不全等**且 SEM ≠ 0 —— 旧三态会判 measured_exact
    st = classify_measurement_state(
        [F, 6.4, 5.7], sem=0.21, value=F, floor=F, ceiling=C, boundary_status="inferred"
    )
    assert st is MeasurementState.BOUNDARY_AMBIGUOUS, st
    # 未命中边界 → exact
    st2 = classify_measurement_state(
        [8.0, 8.1], sem=0.05, value=8.0, floor=F, ceiling=C, boundary_status="inferred"
    )
    assert st2 is MeasurementState.EXACT, st2
    # unresolved → 一律 exact（绝不把推断冒充事实）
    st3 = classify_measurement_state(
        [F, F, F], sem=0.0, value=F, floor=F, ceiling=C, boundary_status="unresolved"
    )
    assert st3 is MeasurementState.EXACT, st3


# ==========================================================================
# 3. explicit + CL-7 → censored
# ==========================================================================
def test_explicit_boundary_with_cl7_is_censored():
    F, C = 6.0, 10.5
    st = classify_measurement_state(
        [F, F, F], sem=0.0, value=F, floor=F, ceiling=C, boundary_status="explicit", n_expected=3
    )
    assert st is MeasurementState.CENSORED, st
    # 缺一个重复 ⇒ 缺失重复 ≠ 删失
    st2 = classify_measurement_state(
        [F, F], sem=0.0, value=F, floor=F, ceiling=C, boundary_status="explicit", n_expected=3
    )
    assert st2 is MeasurementState.EXACT, st2


# ==========================================================================
# 4. 无 floor ⇒ 永不产生 censored / boundary_ambiguous
# ==========================================================================
def test_no_floor_never_produces_censoring_states():
    for bs in ("unresolved", "inferred"):
        st = classify_measurement_state(
            [6.0, 6.0, 6.0], sem=0.0, value=6.0, floor=None, ceiling=None, boundary_status=bs
        )
        assert st in (MeasurementState.EXACT, MeasurementState.MISSING), (bs, st)
        assert st is not MeasurementState.CENSORED
        assert st is not MeasurementState.BOUNDARY_AMBIGUOUS


# ==========================================================================
# 5/6. v1.4 硬规则
# ==========================================================================
def test_exact_forbids_at_inferred_floor():
    rows = [_row(measurement_state="exact", at_inferred_floor=True, censoring_evidence="none")]
    errs = validate_measurement_row_v14(rows[0])
    assert any("at_inferred_floor" in e for e in errs), errs


def test_censored_requires_explicit_evidence():
    bad = _row(measurement_state="censored", censoring_evidence="none", at_inferred_floor=False)
    errs = validate_measurement_row_v14(bad)
    assert any("censored" in e and "explicit" in e for e in errs), errs

    bad2 = _row(
        measurement_state="boundary_ambiguous",
        censoring_evidence="explicit",
        at_inferred_floor=True,
    )
    errs2 = validate_measurement_row_v14(bad2)
    assert any("boundary_ambiguous" in e for e in errs2), errs2

    ok = _row(measurement_state="exact", censoring_evidence="none", at_inferred_floor=False)
    assert validate_measurement_row_v14(ok) == [], validate_measurement_row_v14(ok)


def test_evidence_mapping_is_canonical():
    assert evidence_for_state("censored") is CensoringEvidence.EXPLICIT
    assert evidence_for_state("boundary_ambiguous") is CensoringEvidence.INFERRED
    assert evidence_for_state("exact") is CensoringEvidence.NONE
    assert evidence_for_state("missing") is CensoringEvidence.NONE


# ==========================================================================
# 7. degree_present vs degree_informative 必然不同
# ==========================================================================
def _tiny_graph():
    """4 个二元位点 → 16 节点的小型乘积空间（CR9114 h3 风格的合例）。"""
    profiles = ["".join(bits) for bits in __import__("itertools").product("01", repeat=4)]
    space = MixedAlphabetSpace.from_masked_profiles(profiles)
    return space, GenotypeGraph(space)


def test_degree_informative_differs_from_degree_present():
    space, graph = _tiny_graph()
    center = tuple("0000")

    # 全部 4 个邻居 present，但只有 1 个 informative（其余是 censored —— 看得见但没判别力）
    rows: List[Dict[str, Any]] = []
    for i, nb in enumerate(space.neighbors_list(center)):
        gid = space.node_id(nb)
        censored = i > 0
        rows.append(
            {
                "genotype_id": gid,
                "task_id": "T",
                "condition_id": "c",
                "measurement_state": "censored" if censored else "exact",
                "informative": not censored,
            }
        )
    assert graph.degree_present(center, rows, "T", "c") == 4
    assert graph.degree_informative(center, rows, "T", "c") == 1
    # 同义入口等价性
    assert graph.effective_degree(center, rows, "T", "c") == graph.degree_present(center, rows, "T", "c")

    # boundary_ambiguous 也算 present（它不是 missing），但不 informative
    rows2 = [
        {
            "genotype_id": space.node_id(nb),
            "task_id": "T",
            "condition_id": "c",
            "measurement_state": "boundary_ambiguous",
            "informative": False,
        }
        for nb in space.neighbors_list(center)
    ]
    assert graph.degree_present(center, rows2, "T", "c") == 4
    assert graph.degree_informative(center, rows2, "T", "c") == 0

    # missing 不算 present
    rows3 = [dict(r, measurement_state="missing") for r in rows2]
    assert graph.degree_present(center, rows3, "T", "c") == 0


# ==========================================================================
# 8. 边界容差：圆整的 floor 字面量不得静默漏判（TEM-1 实况）
# ==========================================================================
def test_rounded_floor_literal_is_not_silently_missed():
    gap = abs(LOG10_1P5 - TEM1_FLOOR_LITERAL)
    assert gap > 1e-12, "本测试的前提是 gap 超过 NUMERIC_TOLERANCE"
    assert gap < BOUNDARY_ABS_TOL, "BOUNDARY_ABS_TOL 必须覆盖十进制圆整误差"

    st = classify_measurement_state(
        [LOG10_1P5, LOG10_1P5, LOG10_1P5],
        sem=0.0,
        value=LOG10_1P5,
        floor=TEM1_FLOOR_LITERAL,
        ceiling=None,
        boundary_status="inferred",
    )
    assert st is MeasurementState.BOUNDARY_AMBIGUOUS, st


# ==========================================================================
# 9. 真实 parquet 的重分类自洽性
# ==========================================================================
def test_parquet_reclassification_is_self_consistent():
    pd = pytest.importorskip("pandas")
    assert PARQUET.exists(), f"缺少 {PARQUET}"
    df = pd.read_parquet(
        PARQUET,
        columns=[
            "dataset_id",
            "task_id",
            "measurement_state",
            "censoring_evidence",
            "at_inferred_floor",
            "boundary_status",
        ],
    )
    states = set(df["measurement_state"].unique())
    assert "measured_exact" not in states, "旧值 measured_exact 必须已被改写为 exact"
    assert states <= {"exact", "censored", "boundary_ambiguous", "missing"}, states

    # 硬规则在真实表上成立
    bad_exact = ((df["measurement_state"] == "exact") & (df["at_inferred_floor"] == True)).sum()  # noqa: E712
    assert int(bad_exact) == 0, f"exact ∧ at_inferred_floor=True 的行数 = {bad_exact}"
    bad_cens = (
        (df["measurement_state"] == "censored") & (df["censoring_evidence"] != "explicit")
    ).sum()
    assert int(bad_cens) == 0, f"censored ∧ evidence≠explicit 的行数 = {bad_cens}"
    bad_amb = (
        (df["measurement_state"] == "boundary_ambiguous")
        & (df["censoring_evidence"] != "inferred")
    ).sum()
    assert int(bad_amb) == 0, f"boundary_ambiguous ∧ evidence≠inferred 的行数 = {bad_amb}"
    bad_none = (
        (df["censoring_evidence"] == "none")
        & (~df["measurement_state"].isin(["exact", "missing"]))
    ).sum()
    assert int(bad_none) == 0, f"evidence=none 配了非法状态的行数 = {bad_none}"

    # unresolved 的 task 不得出现 censored / boundary_ambiguous
    unres = df[df["boundary_status"] == "unresolved"]
    assert not unres.empty
    assert set(unres["measurement_state"].unique()) <= {"exact", "missing"}
    # inferred 的 task 不得出现真 censored
    inf = df[df["boundary_status"] == "inferred"]
    assert "censored" not in set(inf["measurement_state"].unique())
    # CR9114（explicit）必须仍有 censored，且零 boundary_ambiguous
    ex = df[df["dataset_id"] == "Phillips2021_CR9114"]
    assert (ex["measurement_state"] == "censored").any()
    assert (ex["measurement_state"] == "boundary_ambiguous").sum() == 0


# ==========================================================================
# 10. 回归：两个冻结测试文件仍全绿
# ==========================================================================
@pytest.mark.parametrize("frozen", [V11_TEST, V12_TEST])
def test_frozen_suites_still_green(frozen: Path):
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(frozen), "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"{frozen.name} 失败：\n{proc.stdout}\n{proc.stderr}"


# ==========================================================================
# 独立运行入口
# ==========================================================================
def _run() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in tests:
        try:
            if fn.__name__ == "test_frozen_suites_still_green":
                fn(V11_TEST)
                fn(V12_TEST)
            else:
                fn()
            passed += 1
            print(f"  PASS  {fn.__name__}")
        except Exception as exc:  # pragma: no cover
            failed += 1
            print(f"  FAIL  {fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\nschema v1.4 tests — passed={passed} failed={failed} total={passed + failed}")
    print(f"SCHEMA_VERSION = {SCHEMA_VERSION}  (value={SCHEMA_VERSION.value})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(_run())
