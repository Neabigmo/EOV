"""M2.0 单元测试 —— schema v1.2（metadata-only）。

运行方式（与 v1.1 测试相同，两种都支持）：

    & 'F:\\anaconda3\\python.exe' -m pytest tests/ -q
    & 'F:\\anaconda3\\python.exe' tests\\test_schema_v1_2.py

覆盖（AMENDMENT-009 §6 要求）：

1. ``task_panel`` **不得** graph-eligible（代码级硬防守，含负向对照）
2. 许可五字段：``redistribution_basis`` 必填；``redistribution_allowed=True`` 时
   不得是占位串；且 ``source_data_license`` 与 ``redistribution_allowed``
   **不得机械绑定**（二者可矛盾，只要 basis 说明清楚）
3. ``n_expected / n_observed / n_missing`` 三元组自洽（含 ``n_observed > n_expected`` 负例）
4. ``boundary_status="unresolved"`` ⇒ **不得出现 censored**（行级 + 组级 + task 级）
5. ``auxiliary`` modality **不被计入** functional task 数
6. 迁移后的 ``data_registry/PROVENANCE_LEDGER.csv`` 25/25 通过 v1.2 校验（读真实文件）
7. 回归：v1.1 的 ``tests/test_tem1_topology.py`` 未被改动且仍全绿

⛔ 本测试**不**计算 EOV / regret / ranking / 搜索 / 预算 / Tomorrow-Test。
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eov.schema import (  # noqa: E402
    DATASET_RECORD_COLUMNS_V12,
    GRAPH_ELIGIBLE_QC_FIELDS,
    MEASUREMENT_COLUMNS_V12,
    NON_GRAPH_QC_FIELDS,
    SCHEMA_VERSION,
    BoundarySource,
    BoundaryStatus,
    DatasetRole,
    MeasurementModality,
    MeasurementState,
    allowed_qc_fields,
    auxiliary_task_ids,
    classify_measurement_state,
    functional_task_ids,
    graph_eligible,
    validate_dataset_record_v12,
    validate_measurement_group_v12,
    validate_measurement_row_v12,
    validate_measurement_table_v12,
)

# --------------------------------------------------------------------------
# 常量（来自本轮实测 / 冻结记录）
# --------------------------------------------------------------------------
LEDGER = ROOT / "data_registry" / "PROVENANCE_LEDGER.csv"
V11_TEST_FILE = ROOT / "tests" / "test_tem1_topology.py"
#: v1.1 冻结测试文件的 sha256 —— 任何改动都会触发本 tripwire。
V11_TEST_SHA256 = "537afe9bc681ff242a99c34d67de1d23c5e32c36e82d79f172cfdf4f6abbbcec"
V11_TEST_SHA256_PREREG = "ca142f6b0b4836b47880bc0e202ab70037d23abcfeebbc34d71763c586eb50d4"
V11_SPEC = ROOT / "prereg" / "M1_SCHEMA_SPEC.md"


# --------------------------------------------------------------------------
# 构造器：一条**合法**的 v1.2 measurement 行
# --------------------------------------------------------------------------
def _valid_v12_row(**overrides: Any) -> Dict[str, Any]:
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
        "measurement_state": "measured_exact",
        "measurement_modality": "functional",
        "floor": 6.0,
        "ceiling": 10.5,
        "boundary_status": "explicit",
        "boundary_source": "assay_detection",
        "informative": True,
        "source_row_ref": "row1",
    }
    row.update(overrides)
    return row


def _valid_v12_dataset(**overrides: Any) -> Dict[str, Any]:
    rec: Dict[str, Any] = {
        "dataset_id": "DS1",
        "protein_or_system": "TEM-1",
        "source_type": "author_deposit",
        "original_deposit_url": "https://example.invalid/orig",
        "fetched_url": "https://example.invalid/fetched",
        "paper_license": "CC BY 4.0",
        "source_data_license": "CC0-1.0",
        "code_license": "",
        "analysis_allowed": "TRUE",
        "redistribution_allowed": "TRUE",
        "redistribution_basis": "Dryad dataset API v2 license field = CC0-1.0 (verified 2026-09-19)",
        "role": "strict_multi_task",
        "theoretical_space_size": 64,
        "complete_product": "TRUE",
        "observed_genotype_count": 64,
        "notes": "",
    }
    rec.update(overrides)
    return rec


# ==========================================================================
# 1. task_panel 硬防守
# ==========================================================================
def test_task_panel_is_never_graph_eligible():
    """`task_panel` 即使空间完整、计数相等，也**永远**不得 graph-eligible。"""
    # 硬防守：其他条件全部满足，role=task_panel 仍必须 False
    assert (
        graph_eligible(
            "task_panel",
            complete_product=True,
            observed_genotype_count=64,
            theoretical_space_size=64,
        )
        is False
    )
    # 负向对照①：同样条件下 strict_multi_task / single_task_control 必须 True
    for good_role in ("strict_multi_task", "single_task_control"):
        assert (
            graph_eligible(
                good_role,
                complete_product=True,
                observed_genotype_count=55296,
                theoretical_space_size=55296,
            )
            is True
        ), good_role
    # 负向对照②：其余非 graph 角色一律 False
    for bad_role in ("oracle_only", "modality_control", "conditional"):
        assert (
            graph_eligible(
                bad_role,
                complete_product=True,
                observed_genotype_count=64,
                theoretical_space_size=64,
            )
            is False
        ), bad_role
    # 负向对照③：空间不完整 / 计数不等 / 未声明完整 → False（保守）
    assert (
        graph_eligible(
            "strict_multi_task",
            complete_product=True,
            observed_genotype_count=1917,
            theoretical_space_size=2048,
        )
        is False
    )
    assert graph_eligible("strict_multi_task") is False
    assert graph_eligible("strict_multi_task", complete_product=False) is False
    # QC 范围：task_panel 不得输出任何 degree 字段
    tp_qc = allowed_qc_fields("task_panel")
    for f in GRAPH_ELIGIBLE_QC_FIELDS:
        assert f not in tp_qc, f
    for f in NON_GRAPH_QC_FIELDS:
        assert f in tp_qc, f
    # graph-eligible 才解锁 degree 字段
    ok_qc = allowed_qc_fields(
        "strict_multi_task",
        complete_product=True,
        observed_genotype_count=55296,
        theoretical_space_size=55296,
    )
    for f in GRAPH_ELIGIBLE_QC_FIELDS:
        assert f in ok_qc, f
    # 枚举值本身
    assert DatasetRole.TASK_PANEL.value == "task_panel"


# ==========================================================================
# 2. 许可五字段与 redistribution_basis
# ==========================================================================
def test_license_fields_require_redistribution_basis():
    # 完整合法记录 → 无错
    assert validate_dataset_record_v12(_valid_v12_dataset()) == []

    # 缺列 → 报错
    missing = _valid_v12_dataset()
    del missing["redistribution_basis"]
    assert any("redistribution_basis" in e for e in validate_dataset_record_v12(missing))

    # 空白 basis → 报错
    blank = _valid_v12_dataset(redistribution_basis="   ")
    assert any("redistribution_basis" in e for e in validate_dataset_record_v12(blank))

    # redistribution_allowed=True 但 basis 是占位串 → 必须报错
    for ph in ("TBD", "n/a", "unknown", "placeholder", "-"):
        bad = _valid_v12_dataset(redistribution_allowed="TRUE", redistribution_basis=ph)
        errs = validate_dataset_record_v12(bad)
        assert any("placeholder" in e for e in errs), ph

    # ⛔ 不得机械绑定：source_data_license 与 redistribution_allowed 可矛盾，只要 basis 说清楚
    # 情形 A：原始 deposit 宽松，但 ingest 的是第三方 repack → 允许 FALSE
    a = _valid_v12_dataset(
        source_data_license="CC0-1.0",
        redistribution_allowed="FALSE",
        redistribution_basis=(
            "third-party repack (GraphFLA); underlying data license not stated "
            "-> must not be re-packaged (C8-2)"
        ),
    )
    assert validate_dataset_record_v12(a) == [], validate_dataset_record_v12(a)
    # 情形 B：ingest 的 artifact 无 LICENSE，但 basis 依据论文许可 → 允许 TRUE
    b = _valid_v12_dataset(
        source_data_license="NONE (repo has NO LICENSE file)",
        redistribution_allowed="TRUE",
        redistribution_basis=(
            "paper CC BY 4.0 (Crossref verified) and the ingested Zenodo deposit "
            "record license = cc-by-4.0 (verified)"
        ),
    )
    assert validate_dataset_record_v12(b) == [], validate_dataset_record_v12(b)
    # 反向：宽松许可 + TRUE 也是允许的（不存在"必须 TRUE"的机械规则）
    c = _valid_v12_dataset(source_data_license="CC BY 4.0", redistribution_allowed="TRUE")
    assert validate_dataset_record_v12(c) == []


# ==========================================================================
# 3. replicate 三计数自洽
# ==========================================================================
def test_replicate_count_triplet_consistency():
    # 合法三元组
    assert validate_measurement_row_v12(_valid_v12_row(n_expected=3, n_observed=3, n_missing=0)) == []
    assert validate_measurement_row_v12(_valid_v12_row(n_expected=3, n_observed=1, n_missing=2)) == []
    # n_observed > n_expected → 必须报错
    errs = validate_measurement_row_v12(_valid_v12_row(n_expected=2, n_observed=5, n_missing=0))
    assert any("n_observed" in e and "n_expected" in e for e in errs), errs
    # n_missing != n_expected - n_observed → 必须报错
    errs = validate_measurement_row_v12(_valid_v12_row(n_expected=3, n_observed=2, n_missing=0))
    assert any("n_missing" in e for e in errs), errs
    # n_expected < 1 → 报错
    assert any("n_expected" in e for e in validate_measurement_row_v12(_valid_v12_row(n_expected=0, n_observed=0, n_missing=0)))
    # 列缺失 → 报错
    r = _valid_v12_row()
    del r["n_missing"]
    assert any("missing column: n_missing" in e for e in validate_measurement_row_v12(r))

    # 组级：n_observed 必须等于"带值的行数"（未观测重复不得发射成行）
    g_ok = [
        _valid_v12_row(replicate="1", value=8.0, n_observed=2, n_missing=1),
        _valid_v12_row(replicate="2", value=8.2, n_observed=2, n_missing=1),
    ]
    assert validate_measurement_group_v12(g_ok) == [], validate_measurement_group_v12(g_ok)
    g_bad = [
        _valid_v12_row(replicate="1", value=8.0, n_observed=3, n_missing=0),
    ]
    assert any("n_observed" in e for e in validate_measurement_group_v12(g_bad))


# ==========================================================================
# 4. unresolved boundary ⇒ 不得出现 censored
# ==========================================================================
def _censored_row(**overrides: Any) -> Dict[str, Any]:
    base = dict(
        value=6.0,
        value_sem=0.0,
        value_sd=0.0,
        measurement_state="censored",
        informative=False,
        floor=6.0,
        n_expected=3,
        n_observed=3,
        n_missing=0,
    )
    base.update(overrides)
    return _valid_v12_row(**base)


def test_unresolved_boundary_forbids_censored():
    # 正向对照：boundary 已解决时，censored 合法
    ok = _censored_row(boundary_status="explicit", boundary_source="assay_detection")
    assert validate_measurement_row_v12(ok) == [], validate_measurement_row_v12(ok)
    ok2 = _censored_row(boundary_status="inferred", boundary_source="replicate_pattern")
    assert validate_measurement_row_v12(ok2) == []

    # 行级：unresolved 时出现 censored → 必须报错
    bad = _censored_row(boundary_status="unresolved", boundary_source="none")
    errs = validate_measurement_row_v12(bad)
    assert any("unresolved" in e and "censored" in e for e in errs), errs

    # unresolved 与 boundary_source 的一致性
    assert any(
        "boundary_source" in e
        for e in validate_measurement_row_v12(
            _valid_v12_row(boundary_status="unresolved", boundary_source="assay_detection")
        )
    )
    assert any(
        "boundary_source" in e
        for e in validate_measurement_row_v12(
            _valid_v12_row(boundary_status="explicit", boundary_source="none")
        )
    )

    # 组级
    assert any(
        "unresolved" in e
        for e in validate_measurement_group_v12([bad])
    )

    # task 级：整表里另一条行是 censored，也必须被抓住
    rows = [
        _valid_v12_row(replicate="1", task_id="T1", boundary_status="unresolved", boundary_source="none"),
        _censored_row(replicate="1", task_id="T1", boundary_status="unresolved", boundary_source="none"),
    ]
    rep = validate_measurement_table_v12(rows)
    assert rep["ok"] is False
    assert rep["n_invalid_tasks"] >= 1
    assert any("unresolved" in msg for _, msgs in rep["task_errors"] for msg in msgs)

    # 反向对照：同结构但 boundary 已解决 → 不因该规则报错
    rows_ok = [
        _valid_v12_row(replicate="1", task_id="T1"),
        _censored_row(replicate="1", task_id="T1"),
    ]
    rep_ok = validate_measurement_table_v12(rows_ok)
    assert not any("unresolved" in msg for _, msgs in rep_ok["task_errors"] for msg in msgs)


# ==========================================================================
# 5. auxiliary modality 不计入 functional task 数
# ==========================================================================
def test_auxiliary_modality_not_counted_as_functional_task():
    rows: List[Dict[str, Any]] = []
    for t in ("MA90", "SI06", "G189E"):
        rows.append(_valid_v12_row(task_id=t, measurement_modality="functional"))
    rows.append(_valid_v12_row(task_id="expression", measurement_modality="auxiliary"))

    assert functional_task_ids(rows) == ("G189E", "MA90", "SI06")
    assert len(functional_task_ids(rows)) == 3
    assert auxiliary_task_ids(rows) == ("expression",)
    assert "expression" not in functional_task_ids(rows)

    rep = validate_measurement_table_v12(rows)
    assert len(rep["functional_task_ids"]) == 3
    assert rep["auxiliary_task_ids"] == ("expression",)

    # modality 缺失/非法 → 报错
    r = _valid_v12_row()
    del r["measurement_modality"]
    assert any("measurement_modality" in e for e in validate_measurement_row_v12(r))
    assert any(
        "measurement_modality" in e
        for e in validate_measurement_row_v12(_valid_v12_row(measurement_modality="other"))
    )


# ==========================================================================
# 6. 迁移后的 PROVENANCE_LEDGER.csv 25/25 通过 v1.2 校验
# ==========================================================================
def test_migrated_provenance_ledger_passes_v12():
    assert LEDGER.exists(), LEDGER
    with LEDGER.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = tuple(reader.fieldnames or ())
        rows = list(reader)

    assert header == DATASET_RECORD_COLUMNS_V12, header
    assert len(rows) == 25, len(rows)
    assert "license" not in header, "v1.1 单列 license 必须已被五字段取代"

    bad: List[Tuple[str, List[str]]] = []
    for r in rows:
        e = validate_dataset_record_v12(r)
        if e:
            bad.append((r.get("dataset_id", "?"), e))
    assert not bad, bad

    by_id = {r["dataset_id"]: r for r in rows}

    # 裁决：TEV / DAOx 必须是 task_panel，且都不得 graph-eligible
    for did in ("TEV_ProtRec", "DAOx_multi_substrate"):
        rec = by_id[did]
        assert rec["role"] == "task_panel", (did, rec["role"])
        assert (
            graph_eligible(
                rec["role"],
                complete_product=rec["complete_product"],
                observed_genotype_count=rec["observed_genotype_count"],
                theoretical_space_size=rec["theoretical_space_size"],
            )
            is False
        ), did

    # AncSR1：用户已裁定 CC0-1.0 / analysis TRUE / redistribution TRUE
    a = by_id["AncSR1_Starr2017"]
    assert "CC0-1.0" in a["source_data_license"]
    assert a["analysis_allowed"].strip().upper() == "TRUE"
    assert a["redistribution_allowed"].strip().upper() == "TRUE"
    assert a["redistribution_basis"].strip() != ""

    # 每条 basis 都必须非空（"必填文本"）
    for r in rows:
        assert str(r["redistribution_basis"]).strip(), r["dataset_id"]


# ==========================================================================
# 7. 回归：v1.1 冻结资产未被改动且仍全绿
# ==========================================================================
def test_v11_assets_unchanged_and_v11_suite_green():
    # tripwire ①：v1.1 测试文件字节未变
    actual = hashlib.sha256(V11_TEST_FILE.read_bytes()).hexdigest()
    assert actual == V11_TEST_SHA256, (
        "tests/test_tem1_topology.py 已改变 —— 它是 v1.1 冻结资产，"
        f"预期 {V11_TEST_SHA256}，实际 {actual}"
    )
    # tripwire ②：v1.1 规范文档字节未变
    spec = hashlib.sha256(V11_SPEC.read_bytes()).hexdigest()
    assert spec == V11_TEST_SHA256_PREREG, (
        "prereg/M1_SCHEMA_SPEC.md 已改变 —— v1.1 原文与哈希必须保留，"
        f"预期 {V11_TEST_SHA256_PREREG}，实际 {spec}"
    )
    # tripwire ③：v1.1 的枚举取值未被删改（只允许新增）
    for v in (
        "strict_multi_task",
        "single_task_control",
        "oracle_only",
        "modality_control",
        "conditional",
    ):
        assert v in {r.value for r in DatasetRole}, v
    # AMENDMENT-012：原先此处断言 `SCHEMA_VERSION == "1.2"` —— 那是**过度指定**：
    # 它把"v1.2 契约仍然成立"错误地表达成了"版本号永远停在 1.2"。schema 演进到
    # v1.3 / v1.4 后该断言必然失败，而当时的应对（让版本字符串对历史版本号返回相等）
    # 会制造"说谎的相等"，使 `if SCHEMA_VERSION == "1.2"` 之类的分支在 v1.4 模块上静默走错路。
    # 改为**契约断言**：v1.2 的冻结常量不变，且当前版本仍是 1.x 家族成员。
    from eov.schema import V12_SCHEMA_VERSION

    assert V12_SCHEMA_VERSION == "1.2"
    assert isinstance(SCHEMA_VERSION, str) and not isinstance(SCHEMA_VERSION, type("", (), {}))
    assert SCHEMA_VERSION.split(".")[0] == "1"
    assert SCHEMA_VERSION >= "1.2"

    # tripwire ④：v1.1 三态判定语义在**不传** v1.2 参数时保持不变
    F, C = 6.000, 10.5
    assert (
        classify_measurement_state([F, F, F], sem=0.0, value=F, floor=F, ceiling=C)
        is MeasurementState.CENSORED
    )
    assert (
        classify_measurement_state([F, F, F], sem=0.01, value=F, floor=F, ceiling=C)
        is MeasurementState.MEASURED_EXACT
    )
    assert (
        classify_measurement_state([F, F, F], sem=None, value=F, floor=F, ceiling=C)
        is MeasurementState.MEASURED_EXACT
    )
    assert (
        classify_measurement_state([8.0, 8.0], sem=0.0, value=8.0, floor=F, ceiling=C)
        is MeasurementState.MEASURED_EXACT
    )
    assert (
        classify_measurement_state([], sem=None, value=None, floor=F, ceiling=C)
        is MeasurementState.MISSING
    )
    assert (
        classify_measurement_state([7.0, 7.1], sem=0.05, value=None, floor=F, ceiling=C)
        is MeasurementState.MISSING
    )

    # tripwire ⑤：v1.1 测试套件本身仍然全绿（子进程实跑）
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(V11_TEST_FILE), "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"v1.1 suite failed:\n{proc.stdout}\n{proc.stderr}"


# ==========================================================================
# 直接运行入口（无 pytest 时使用）
# ==========================================================================
def _run_all() -> int:
    tests: List[Tuple[str, object]] = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    passed, failed = 0, []
    print("=" * 72)
    print(f"schema v1.2 tests — {len(tests)} tests  (SCHEMA_VERSION={SCHEMA_VERSION})")
    print("=" * 72)
    for name, fn in tests:
        try:
            fn()  # type: ignore[operator]
        except Exception as exc:  # noqa: BLE001
            failed.append((name, exc))
            print(f"FAIL  {name}\n        {type(exc).__name__}: {exc}")
        else:
            passed += 1
            print(f"PASS  {name}")
    print("-" * 72)
    print(f"passed={passed}  failed={len(failed)}  total={len(tests)}")
    if failed:
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
