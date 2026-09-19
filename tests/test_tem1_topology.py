"""M1 单元测试 —— TEM-1 genotype topology（**无权图**）。

运行方式（两种都支持）：

    & 'F:\\anaconda3\\python.exe' -m pytest tests/ -q
    & 'F:\\anaconda3\\python.exe' tests\\test_tem1_topology.py

覆盖（AMENDMENT-008 §5-5 要求）：

* 55,296 个节点；13 位点；等位数 = 2,2,3,2,4,2,2,2,2,3,2,3,2；
  乘积 = 4 × 3³ × 2⁹ = 55,296
* 替换总数 = 3 + 3×2 + 9 = 18；所有完整节点的 topology degree = 18
* 边数 = 55,296 × 18 / 2 = 497,664
* 邻居良构（无自环、无重复、对称）
* **图平面不含任何 fitness / task / weight 载荷**（契约审计）
* 大空间必须走生成式接口（``materialize`` 受上限保护）

⛔ 本测试**不**计算 EOV / regret / ranking / 搜索 / 可达性最大值。
"""

from __future__ import annotations

import itertools
import math
import os
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eov.landscape import (  # noqa: E402
    DEFAULT_MATERIALIZE_LIMIT,
    GenotypeGraph,
    MeasurementIndex,
    MixedAlphabetSpace,
    audit_graph_contract,
)
from eov.schema import (  # noqa: E402
    MeasurementState,
    classify_measurement_state,
    classify_informative,
)

# --------------------------------------------------------------------------
# 期望常量（全部来自 M0 实测，见 data_registry/M0_verification_log.md §M0-2a）
# --------------------------------------------------------------------------
EXPECTED_N_POSITIONS = 13
EXPECTED_ALLELE_COUNTS: Tuple[int, ...] = (2, 2, 3, 2, 4, 2, 2, 2, 2, 3, 2, 3, 2)
EXPECTED_SPACE_SIZE = 55_296                     # = 4 × 3³ × 2⁹
EXPECTED_DEGREE = 18                             # = 3 + 3×2 + 9
EXPECTED_EDGE_COUNT = 497_664                    # = 55_296 × 18 / 2
EXPECTED_N_FOUR_ALLELE_POSITIONS = 1
EXPECTED_N_THREE_ALLELE_POSITIONS = 3
EXPECTED_N_TWO_ALLELE_POSITIONS = 9

TEM1_INTENDED_CSV = (
    ROOT
    / "data"
    / "external"
    / "TEM1_Gaszek2025"
    / "data"
    / "processed"
    / "TEM1-combinatorial-mutagenesis-intended.csv"
)

_SPACE_CACHE = {}


def _load_space() -> Tuple[MixedAlphabetSpace, int]:
    if "space" not in _SPACE_CACHE:
        # 用 pandas 读取（**不得**对 git 输出做 .split() —— M0 曾因此出错）
        space, observed = MixedAlphabetSpace.from_intended_csv(str(TEM1_INTENDED_CSV))
        _SPACE_CACHE["space"] = space
        _SPACE_CACHE["observed"] = observed
    return _SPACE_CACHE["space"], _SPACE_CACHE["observed"]


# ==========================================================================
# A. 空间结构
# ==========================================================================
def test_intended_csv_exists():
    assert TEM1_INTENDED_CSV.exists(), f"missing data file: {TEM1_INTENDED_CSV}"


def test_space_geometry():
    space, observed = _load_space()
    assert space.n_positions == EXPECTED_N_POSITIONS
    assert space.allele_count_vector() == EXPECTED_ALLELE_COUNTS
    assert space.space_size() == EXPECTED_SPACE_SIZE
    assert observed == EXPECTED_SPACE_SIZE, "observed unique genotypes != theoretical space size"


def test_product_identity_4x3pow3x2pow9():
    """显式验证 4 × 3³ × 2⁹ = 55,296 与等位数分组的自洽。"""
    counts = EXPECTED_ALLELE_COUNTS
    n4 = sum(1 for c in counts if c == 4)
    n3 = sum(1 for c in counts if c == 3)
    n2 = sum(1 for c in counts if c == 2)
    assert (n4, n3, n2) == (
        EXPECTED_N_FOUR_ALLELE_POSITIONS,
        EXPECTED_N_THREE_ALLELE_POSITIONS,
        EXPECTED_N_TWO_ALLELE_POSITIONS,
    )
    assert (4**n4) * (3**n3) * (2**n2) == EXPECTED_SPACE_SIZE
    assert 4 * 3**3 * 2**9 == EXPECTED_SPACE_SIZE


def test_degree_and_substitutions():
    space, _ = _load_space()
    # 3 + 3×2 + 9 = 18
    assert 3 + 3 * 2 + 9 == EXPECTED_DEGREE
    assert space.degree_topology() == EXPECTED_DEGREE
    assert space.total_substitutions() == EXPECTED_DEGREE


def test_all_nodes_have_topology_degree_18():
    """枚举全部 55,296 个节点，逐个校验合法性并确认度为 18。"""
    space, _ = _load_space()
    n = 0
    for node in space.iter_nodes():
        space.validate_node(node)          # 长度 + 每位点等位合法
        assert space.degree_of(node) == EXPECTED_DEGREE
        n += 1
    assert n == EXPECTED_SPACE_SIZE


def test_node_id_roundtrip_on_real_profiles():
    space, _ = _load_space()
    import pandas as pd

    df = pd.read_csv(TEM1_INTENDED_CSV, dtype=str)
    for pid in df["mut_profile_masked"].astype(str).head(50):
        node = space.node_from_id(pid)
        assert space.node_id(node) == pid


def test_index_roundtrip():
    space, _ = _load_space()
    for i in (0, 1, 17, 18, 12345, EXPECTED_SPACE_SIZE - 1):
        node = space.node_from_index(i)
        assert space.index_of(node) == i
    # 单调性：index 与 tuple 生成顺序一致（itertools.product 的行主序）
    assert space.node_from_index(0) == tuple(a[0] for a in space.alleles)
    assert space.node_from_index(EXPECTED_SPACE_SIZE - 1) == tuple(a[-1] for a in space.alleles)


# ==========================================================================
# B. 邻居与边
# ==========================================================================
def test_neighbors_are_wellformed():
    space, _ = _load_space()
    sample = list(itertools.islice(space.iter_nodes(), 0, 40))
    sample += [space.node_from_index(i) for i in (1000, 27000, EXPECTED_SPACE_SIZE - 1)]
    for node in sample:
        nbs = space.neighbors_list(node)
        assert len(nbs) == EXPECTED_DEGREE, f"degree != 18 for {node}"
        assert len(set(nbs)) == len(nbs), "duplicate neighbors"
        assert node not in nbs, "self loop detected"
        for nb in nbs:
            space.validate_node(nb)
            # 恰好一个位点不同，且是该位点的另一个等位
            diff = [i for i in range(space.n_positions) if nb[i] != node[i]]
            assert len(diff) == 1
            assert nb[diff[0]] != node[diff[0]]
            # 对称性
            assert node in space.neighbors_list(nb)


def test_edge_count_matches_closed_form():
    space, _ = _load_space()
    g = GenotypeGraph(space)
    assert g.edge_count() == EXPECTED_EDGE_COUNT
    assert g.edge_count() == EXPECTED_SPACE_SIZE * EXPECTED_DEGREE // 2
    assert EXPECTED_SPACE_SIZE * EXPECTED_DEGREE % 2 == 0, "handshake lemma requires even product"


def test_edge_enumeration_on_small_space_matches_formula():
    """在小空间上**完整枚举**边，验证 |E| = |V|·d/2 与去重规则。"""
    small = MixedAlphabetSpace([["a", "b"], ["x", "y", "z"], ["p", "q"]])
    g = GenotypeGraph(small)
    edges = list(g.iter_edges())
    assert len(edges) == small.space_size() * small.degree_topology() // 2
    assert g.edge_count() == len(edges)
    # 无向、无重复：每条边只出现一次，且索引 u < v
    seen = set()
    for u, v in edges:
        iu, iv = small.index_of(u), small.index_of(v)
        assert iu < iv
        assert (iu, iv) not in seen
        seen.add((iu, iv))


def test_iter_edges_limit_and_laziness():
    space, _ = _load_space()
    g = GenotypeGraph(space)
    got = list(g.iter_edges(limit=25))
    assert len(got) == 25
    for u, v in got:
        assert space.index_of(u) < space.index_of(v)


# ==========================================================================
# C. 图平面**不含** fitness / task / weight（M1 硬约束）
# ==========================================================================
def test_graph_contract_has_no_fitness_payload():
    space, _ = _load_space()
    g = GenotypeGraph(space)
    rep = audit_graph_contract(g)
    assert rep["ok"] is True
    assert rep["nodes_are_plain_tuples"] is True
    assert rep["edges_are_plain_tuples"] is True
    assert rep["no_weight_method"] is True
    # 公开属性里不得出现任何 payload 键
    for key in ("value", "fitness", "score", "weight", "task_id", "condition_id"):
        assert key not in rep["graph_public_attrs"], f"graph exposes forbidden payload: {key}"


def test_measurement_index_discards_values():
    """MeasurementIndex 只保留状态：value 绝不可从索引里读回来。"""
    rows = [
        {
            "genotype_id": "....",
            "task_id": "AMP",
            "condition_id": "781.0",
            "measurement_state": "measured_exact",
            "informative": True,
            "value": 999.0,          # 故意塞入：必须被丢弃
        },
        {
            "genotype_id": "..L.",
            "task_id": "AMP",
            "condition_id": "781.0",
            "measurement_state": "censored",
            "informative": False,
            "value": -1.90534896288408,
        },
    ]
    idx = MeasurementIndex(rows)
    assert idx.has_measurement("....", "AMP", "781.0") is True
    assert idx.has_measurement("..L.", "AMP", "781.0") is True          # censored 仍算 present
    assert idx.has_measurement("..L.", "AMP", "781.0", require_informative=True) is False
    assert idx.has_measurement("....", "AZT", "781.0") is False
    assert idx.n_present() == 2 and idx.n_informative() == 1
    for attr in ("value", "fitness", "values", "scores"):
        assert not hasattr(idx, attr), f"MeasurementIndex must not expose {attr}"
    # slots 结构：不得存在任何存放数值的槽
    assert set(MeasurementIndex.__slots__) == {"_present", "_informative", "_n_rows"}


def test_effective_degree_uses_only_measurement_state():
    """effective_degree 由外部 measurement 表导出，且**不写进图**。"""
    space, _ = _load_space()
    g = GenotypeGraph(space)
    node = space.node_from_id(".............")
    nbs = space.neighbors_list(node)
    assert len(nbs) == EXPECTED_DEGREE

    # (a) 全部邻居 present → 18
    rows_all = [
        {
            "genotype_id": space.node_id(nb),
            "task_id": "AMP",
            "condition_id": "781.0",
            "measurement_state": MeasurementState.MEASURED_EXACT.value,
            "informative": True,
        }
        for nb in nbs
    ]
    assert g.effective_degree(node, rows_all, "AMP", "781.0") == EXPECTED_DEGREE

    # (b) 去掉一个 → 17
    assert g.effective_degree(node, rows_all[:-1], "AMP", "781.0") == EXPECTED_DEGREE - 1

    # (c) missing 不计入
    rows_missing = list(rows_all)
    rows_missing[0] = dict(rows_missing[0], measurement_state="missing", informative=False)
    assert g.effective_degree(node, rows_missing, "AMP", "781.0") == EXPECTED_DEGREE - 1

    # (d) require_informative=True 时 censored 不计入
    rows_cens = list(rows_all)
    rows_cens[1] = dict(rows_cens[1], measurement_state="censored", informative=False)
    assert g.effective_degree(node, rows_cens, "AMP", "781.0") == EXPECTED_DEGREE
    assert (
        g.effective_degree(node, rows_cens, "AMP", "781.0", require_informative=True)
        == EXPECTED_DEGREE - 1
    )

    # (e) 图本身没有被写入任何有效度/任务字段
    assert not hasattr(g, "effective_degrees")
    assert not hasattr(g, "task_id")


# ==========================================================================
# D. 三态判定（schema 层，供 measurement 表使用）
# ==========================================================================
def test_classify_measurement_state_boundary_rules():
    F, C = 6.000, 10.5
    # censored：重复完全相同 ∧ sem=0 ∧ 落在边界
    assert (
        classify_measurement_state([F, F, F], sem=0.0, value=F, floor=F, ceiling=C)
        is MeasurementState.CENSORED
    )
    # 落在边界但 sem != 0 → 不是 censored
    assert (
        classify_measurement_state([F, F, F], sem=0.01, value=F, floor=F, ceiling=C)
        is MeasurementState.MEASURED_EXACT
    )
    # sem 缺省 → 保守地不判 censored
    assert (
        classify_measurement_state([F, F, F], sem=None, value=F, floor=F, ceiling=C)
        is MeasurementState.MEASURED_EXACT
    )
    # 重复相同、sem=0，但值不在边界 → 不是 censored
    assert (
        classify_measurement_state([8.0, 8.0], sem=0.0, value=8.0, floor=F, ceiling=C)
        is MeasurementState.MEASURED_EXACT
    )
    # 无重复 → missing
    assert (
        classify_measurement_state([], sem=None, value=None, floor=F, ceiling=C)
        is MeasurementState.MISSING
    )
    # 有重复但无代表值 → missing
    assert (
        classify_measurement_state([7.0, 7.1], sem=0.05, value=None, floor=F, ceiling=C)
        is MeasurementState.MISSING
    )


def test_classify_informative_rules():
    F = 6.0
    assert classify_informative("measured_exact", 7.0, sem=0.05, floor=F, ceiling=None) is True
    assert classify_informative("measured_exact", 6.05, sem=0.05, floor=F, ceiling=None) is False
    assert classify_informative("censored", 6.0, sem=0.0, floor=F, ceiling=None) is False
    assert classify_informative("missing", None, sem=None, floor=F, ceiling=None) is False
    # SEM 缺省 → 保守 False
    assert classify_informative("measured_exact", 9.0, sem=None, floor=F, ceiling=None) is False


# ==========================================================================
# E. 大空间必须走生成式接口
# ==========================================================================
def test_large_space_is_lazy_and_guarded():
    # 20^4 = 160,000（TrpB4 / Jalal2020 的量级）
    big = MixedAlphabetSpace([list("ACDEFGHIKLMNPQRSTVWY")] * 4)
    assert big.space_size() == 160_000
    assert big.degree_topology() == 4 * 19 == 76
    g = GenotypeGraph(big)                      # 使用默认上限
    assert g.edge_count() == 160_000 * 76 // 2 == 6_080_000
    assert g.is_materialized is False
    first = list(itertools.islice(g.iter_nodes(), 3))
    assert first[0] == tuple("AAAA")
    assert len(first) == 3
    nb = list(itertools.islice(g.neighbors(first[0]), 5))
    assert len(nb) == 5
    # 超过上限时必须拒绝物化（默认上限即可拒绝 160,000）
    try:
        g.materialize()
    except MemoryError:
        pass
    else:  # pragma: no cover
        raise AssertionError("materialize() must refuse spaces above the limit")


def test_materialize_limit_policy_matches_m1_instruction():
    """M1 指令：55,296 可全建；65,536 / 160,000 必须走生成式接口。"""
    assert DEFAULT_MATERIALIZE_LIMIT == 60_000
    assert EXPECTED_SPACE_SIZE <= DEFAULT_MATERIALIZE_LIMIT          # TEM-1 可物化
    # 65,536（4^8, Soo2021）与 160,000（20^4）必须被拒
    for size, space in (
        (65_536, MixedAlphabetSpace([list("ACGU")] * 8)),
        (160_000, MixedAlphabetSpace([list("ACDEFGHIKLMNPQRSTVWY")] * 4)),
    ):
        assert space.space_size() == size
        assert size > DEFAULT_MATERIALIZE_LIMIT
        try:
            GenotypeGraph(space).materialize()
        except MemoryError:
            pass
        else:  # pragma: no cover
            raise AssertionError(f"materialize() must refuse {size}-node space by default")


def test_materialized_adjacency_agrees_with_lazy_neighbors():
    """物化路径必须与生成式路径给出同一组邻居（在小空间上完整验证）。"""
    small = MixedAlphabetSpace([["a", "b"], ["x", "y", "z"], ["p", "q"]])
    lazy = GenotypeGraph(small)
    mat = GenotypeGraph(small)
    mat.materialize()
    assert mat.is_materialized is True
    assert len(list(mat.iter_nodes())) == small.space_size()
    for node in small.iter_nodes():
        assert sorted(lazy.neighbors_list(node)) == sorted(mat.neighbors_list(node))
        assert len(mat.neighbors_list(node)) == small.degree_topology()
    assert len(list(mat.iter_edges())) == lazy.edge_count()


def test_soo2021_style_rna_space_degree():
    """4^8（RNA, Soo2021）→ 拓扑度 = 8×3 = 24（M0 sweep 实测的同型空间）。"""
    rna = MixedAlphabetSpace([list("ACGU")] * 8)
    assert rna.space_size() == 65_536
    assert rna.degree_topology() == 24
    assert GenotypeGraph(rna).edge_count() == 65_536 * 24 // 2


def test_mixed_alphabet_is_not_hypercube():
    """混合字母表：度恒定但对节点无关于各位点分支因子。"""
    space, _ = _load_space()
    counts = space.allele_count_vector()
    assert len(set(counts)) > 1, "TEM-1 space must be mixed-alphabet"
    assert max(counts) - min(counts) >= 2
    # 度 = Σ(k_i − 1)，与"位点数×1"（二元超立方体）不同
    assert space.degree_topology() != space.n_positions


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
    print(f"M1 TEM-1 topology tests — {len(tests)} tests")
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
