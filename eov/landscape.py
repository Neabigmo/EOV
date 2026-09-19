"""EOV Phase I — **无权** genotype graph（M1 冻结实现）。

规范文档：``prereg/M1_SCHEMA_SPEC.md`` v1.0 §5；执行指令见
``prereg/AMENDMENT-008_m1_preconditions.md`` §5。

⛔ 本模块的边界（M1 禁令）
------------------------------------------------------------------
**图 = 纯 genotype topology。**

* 节点 = genotype（位点等位的笛卡尔积）；
* 边   = **一步合法突变**（某位点换成该位点的**另一个**等位）；
* **节点与边都不携带任何 fitness / weight / task / condition。**

具体地，本文件**不含**且**禁止**加入：
EOV、regret、parent ranking、搜索策略、预算模拟、可达性最大值（``R_k``）、
模型拟合、任何 Tomorrow-Test 结果。

* ``degree_topology`` 由空间结构决定（完整乘积空间下对每个节点恒定）；
* ``degree_effective`` **必须**由外部传入的 measurement 表导出，**绝不写进图**；
* 空间形态是**混合字母表乘积空间**（TEM-1 = 4×3³×2⁹ = 55,296），
  **不是**二元超立方体——不得假设位点等位数相同。

大空间（160,000 / 65,536 / 更大）通过生成式接口使用（``iter_nodes`` / ``neighbors``），
``iter_edges`` 与 ``materialize`` 受显式上限保护。
"""

from __future__ import annotations

import itertools
import math
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

try:  # 允许作为包导入与直接执行两种方式
    from eov.schema import MeasurementState, group_key
except ModuleNotFoundError:  # pragma: no cover - 直接执行时的兜底
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from eov.schema import MeasurementState, group_key  # type: ignore

__all__ = [
    "WT_ALLELE",
    "MixedAlphabetSpace",
    "GenotypeGraph",
    "MeasurementIndex",
    "DEFAULT_MATERIALIZE_LIMIT",
    "GRAPH_FORBIDDEN_PAYLOAD_KEYS",
    "audit_graph_contract",
]

#: TEM-1 等数据集用 '.' 表示 wild-type 等位。
WT_ALLELE = "."

#: 超过此节点数则禁止显式建全图（改用生成式接口）。
#: 取值依据 M1 指令："55,296 节点可全建；更大空间（65,536 / 160,000）必须支持不显式建全图"。
#: 因此上限取在 55,296 与 65,536 之间。
DEFAULT_MATERIALIZE_LIMIT = 60_000

#: 图平面**禁止**出现的载荷键（用于契约审计，防止 fitness 泄漏进拓扑平面）。
GRAPH_FORBIDDEN_PAYLOAD_KEYS: Tuple[str, ...] = (
    "value",
    "fitness",
    "score",
    "weight",
    "task_id",
    "condition_id",
    "sem",
    "sd",
)


# ==========================================================================
# 1. 混合字母表乘积空间
# ==========================================================================
class MixedAlphabetSpace:
    """``Π_i |alleles_i|`` 形式的离散基因型空间。

    参数
    ----
    alleles_per_position : 每个位点的等位集合（顺序即编码顺序；建议把 WT 等位放在首位）。
    """

    def __init__(self, alleles_per_position: Sequence[Sequence[str]]) -> None:
        if not alleles_per_position:
            raise ValueError("alleles_per_position must be non-empty")
        normalized: List[Tuple[str, ...]] = []
        for i, al in enumerate(alleles_per_position):
            seq = tuple(str(a) for a in al)
            if len(seq) < 2:
                raise ValueError(f"position {i}: need >= 2 alleles, got {seq!r}")
            if len(set(seq)) != len(seq):
                raise ValueError(f"position {i}: duplicate alleles in {seq!r}")
            if any(len(a) != 1 for a in seq):
                raise ValueError(f"position {i}: alleles must be single characters, got {seq!r}")
            normalized.append(seq)
        self._alleles: Tuple[Tuple[str, ...], ...] = tuple(normalized)

    # ---- 基本属性 -------------------------------------------------------
    @property
    def n_positions(self) -> int:
        return len(self._alleles)

    @property
    def alleles(self) -> Tuple[Tuple[str, ...], ...]:
        return self._alleles

    def alleles_at(self, position: int) -> Tuple[str, ...]:
        return self._alleles[position]

    def space_size(self) -> int:
        return math.prod(len(a) for a in self._alleles)

    def degree_topology(self) -> int:
        """``Σ(位点等位数 − 1)``——完整乘积空间下每个节点的度。"""
        return sum(len(a) - 1 for a in self._alleles)

    def total_substitutions(self) -> int:
        """替换总数 = ``Σ(等位数 − 1)``（与 ``degree_topology`` 同值；保留语义别名）。"""
        return self.degree_topology()

    def allele_count_vector(self) -> Tuple[int, ...]:
        return tuple(len(a) for a in self._alleles)

    def is_complete_product(self) -> bool:
        """按构造恒为 True（所有等位组合都被枚举）。"""
        return True

    def describe(self) -> Dict[str, Any]:
        return {
            "n_positions": self.n_positions,
            "allele_counts": self.allele_count_vector(),
            "space_size": self.space_size(),
            "degree_topology": self.degree_topology(),
            "total_substitutions": self.total_substitutions(),
            "complete_product": self.is_complete_product(),
        }

    # ---- 生成式接口（懒加载） -------------------------------------------
    def iter_nodes(self) -> Iterator[Tuple[str, ...]]:
        return itertools.product(*self._alleles)

    def neighbors(self, node: Sequence[str]) -> Iterator[Tuple[str, ...]]:
        """一步合法突变的所有邻居（生成式；不物化）。"""
        self.validate_node(node)
        for pos in range(self.n_positions):
            current = node[pos]
            for alt in self._alleles[pos]:
                if alt == current:
                    continue
                yield tuple(node[:pos]) + (alt,) + tuple(node[pos + 1 :])

    def neighbors_list(self, node: Sequence[str]) -> List[Tuple[str, ...]]:
        return list(self.neighbors(node))

    def degree_of(self, node: Sequence[str]) -> int:
        self.validate_node(node)
        return self.degree_topology()

    # ---- 索引编解码 -----------------------------------------------------
    def node_from_index(self, index: int) -> Tuple[str, ...]:
        n = self.space_size()
        if not (0 <= index < n):
            raise IndexError(f"index {index} out of range [0, {n})")
        out: List[str] = [""] * self.n_positions
        for pos in range(self.n_positions - 1, -1, -1):
            al = self._alleles[pos]
            out[pos] = al[index % len(al)]
            index //= len(al)
        return tuple(out)

    def index_of(self, node: Sequence[str]) -> int:
        self.validate_node(node)
        idx = 0
        for pos in range(self.n_positions):
            al = self._alleles[pos]
            idx = idx * len(al) + al.index(node[pos])
        return idx

    # ---- 校验与渲染 -----------------------------------------------------
    def validate_node(self, node: Sequence[str]) -> None:
        if len(node) != self.n_positions:
            raise ValueError(
                f"node length {len(node)} != n_positions {self.n_positions}: {node!r}"
            )
        for pos, a in enumerate(node):
            if a not in self._alleles[pos]:
                raise ValueError(f"position {pos}: allele {a!r} not in {self._alleles[pos]!r}")

    def node_id(self, node: Sequence[str]) -> str:
        """节点 → 字符串 ID（TEM-1 即 13 位 ``mut_profile_masked``，'.' = WT）。"""
        self.validate_node(node)
        return "".join(node)

    def node_from_id(self, node_id: str) -> Tuple[str, ...]:
        if len(node_id) != self.n_positions:
            raise ValueError(f"node_id length {len(node_id)} != {self.n_positions}")
        node = tuple(node_id)
        self.validate_node(node)
        return node

    # ---- 构造器 ---------------------------------------------------------
    @classmethod
    def from_masked_profiles(cls, profiles: Iterable[str]) -> "MixedAlphabetSpace":
        """从 ``mut_profile_masked`` 式字符串推导空间（WT 等位 '.' 置于首位）。"""
        profiles = [str(p) for p in profiles]
        if not profiles:
            raise ValueError("no profiles given")
        lengths = {len(p) for p in profiles}
        if len(lengths) != 1:
            raise ValueError(f"profiles have inconsistent lengths: {sorted(lengths)}")
        n = lengths.pop()
        per_pos: List[List[str]] = []
        for pos in range(n):
            seen = sorted({p[pos] for p in profiles})
            if WT_ALLELE in seen:
                seen.remove(WT_ALLELE)
                seen = [WT_ALLELE] + seen
            per_pos.append(seen)
        return cls(per_pos)

    @classmethod
    def from_intended_csv(
        cls, path: str, column: str = "mut_profile_masked"
    ) -> Tuple["MixedAlphabetSpace", int]:
        """从 TEM-1 的 intended CSV 推导空间；返回 (space, 观测到的唯一基因型数)。

        用 pandas 读取（**不得**用对 git 输出做 ``.split()`` 的方式取文件名——M0 曾因此出错）。
        """
        import pandas as pd  # 局部导入，保持模块导入轻量

        df = pd.read_csv(path, dtype=str)
        if column not in df.columns:
            raise KeyError(f"column {column!r} not in {list(df.columns)}")
        profiles = df[column].astype(str)
        space = cls.from_masked_profiles(profiles)
        return space, int(profiles.nunique())


# ==========================================================================
# 2. 测量索引（**只保留状态，主动丢弃 value**）
# ==========================================================================
class MeasurementIndex:
    """``(genotype_id, task_id, condition_id) → measurement_state / informative``。

    ⛔ **主动丢弃 ``value``**：本索引只保留"该格是否有可用测量"，用于计算
    ``degree_effective``。这是"fitness 不得进入图平面"这一约束的实现层保障。

    可接收：
    * measurement 长表的行序列（``Mapping`` 列表）；或
    * pandas ``DataFrame``（自动转为行字典）。
    """

    __slots__ = ("_present", "_informative", "_n_rows")

    def __init__(self, rows: Any) -> None:
        if hasattr(rows, "to_dict"):  # pandas DataFrame 的轻量鸭子类型判定
            records: Iterable[Mapping[str, Any]] = rows.to_dict("records")
        else:
            records = rows
        present = set()
        informative = set()
        n = 0
        for r in records:
            n += 1
            gid = str(r.get("genotype_id", ""))
            tid = str(r.get("task_id", ""))
            cid = r.get("condition_id", None)
            cid = None if cid in (None, "") else str(cid)
            st = r.get("measurement_state")
            st = st.value if isinstance(st, MeasurementState) else str(st)
            if st == MeasurementState.MISSING.value:
                continue
            present.add((gid, tid, cid))
            inf = r.get("informative")
            if inf is True or str(inf).strip().lower() in ("true", "1"):
                informative.add((gid, tid, cid))
        self._present = present
        self._informative = informative
        self._n_rows = n

    @property
    def n_rows_read(self) -> int:
        return self._n_rows

    def has_measurement(
        self,
        genotype_id: str,
        task_id: str,
        condition_id: Optional[str] = None,
        require_informative: bool = False,
    ) -> bool:
        key = (str(genotype_id), str(task_id), None if condition_id in (None, "") else str(condition_id))
        if require_informative:
            return key in self._informative
        return key in self._present

    def n_present(self) -> int:
        return len(self._present)

    def n_informative(self) -> int:
        return len(self._informative)


# ==========================================================================
# 3. 无权基因型图
# ==========================================================================
class GenotypeGraph:
    """``G = (V, E)``，无权、无属性。

    * ``V`` = 空间内全部基因型；
    * ``E`` = 一步合法突变对（无向，每对只计一次）；
    * 节点与边**不携带任何载荷**；``task_id`` / ``condition_id`` / 数值永远不进入本对象。
    """

    def __init__(
        self,
        space: MixedAlphabetSpace,
        materialize_limit: int = DEFAULT_MATERIALIZE_LIMIT,
    ) -> None:
        self._space = space
        self._limit = int(materialize_limit)
        self._nodes: Optional[Tuple[Tuple[str, ...], ...]] = None
        self._adj: Optional[Dict[int, Tuple[int, ...]]] = None

    # ---- 基本属性 -------------------------------------------------------
    @property
    def space(self) -> MixedAlphabetSpace:
        return self._space

    def space_size(self) -> int:
        return self._space.space_size()

    def topology_degree(self, node: Optional[Sequence[str]] = None) -> int:
        """拓扑度（完整乘积空间下与节点无关）。"""
        if node is not None:
            self._space.validate_node(node)
        return self._space.degree_topology()

    def edge_count(self) -> int:
        """``|E| = |V| · degree / 2``（算术求得，不枚举）。"""
        return self.space_size() * self.topology_degree() // 2

    def max_materialize(self) -> int:
        return self._limit

    @property
    def is_materialized(self) -> bool:
        return self._nodes is not None

    # ---- 生成式接口 -----------------------------------------------------
    def iter_nodes(self) -> Iterator[Tuple[str, ...]]:
        if self._nodes is not None:
            return iter(self._nodes)
        return self._space.iter_nodes()

    def neighbors(self, node: Sequence[str]) -> Iterator[Tuple[str, ...]]:
        if self._adj is not None:
            idx = self._space.index_of(node)
            for j in self._adj[idx]:
                yield self._nodes[j]  # type: ignore[index]
            return
        yield from self._space.neighbors(node)

    def neighbors_list(self, node: Sequence[str]) -> List[Tuple[str, ...]]:
        return list(self.neighbors(node))

    def iter_edges(self, limit: Optional[int] = None) -> Iterator[Tuple[Tuple[str, ...], Tuple[str, ...]]]:
        """懒生成每条边一次（按索引 ``u < v`` 去重）。

        ``limit`` 仅用于抽样；``None`` 表示全量（TEM-1 为 497,664 条）。
        """
        emitted = 0
        for node in self.iter_nodes():
            iu = self._space.index_of(node)
            for nb in self._space.neighbors(node):
                if self._space.index_of(nb) > iu:
                    yield node, nb
                    emitted += 1
                    if limit is not None and emitted >= limit:
                        return

    # ---- 物化（受上限保护） ---------------------------------------------
    def materialize(self) -> None:
        n = self.space_size()
        if n > self._limit:
            raise MemoryError(
                f"space_size {n} exceeds materialize limit {self._limit}; "
                "use iter_nodes()/neighbors() instead"
            )
        nodes = tuple(self._space.iter_nodes())
        adj: Dict[int, Tuple[int, ...]] = {}
        for i, node in enumerate(nodes):
            adj[i] = tuple(self._space.index_of(nb) for nb in self._space.neighbors(node))
        self._nodes = nodes
        self._adj = adj

    # ---- 有效度（**必须**由外部 measurement 表导出，绝不写进图） --------
    def effective_degree(
        self,
        node: Sequence[str],
        measurement_table: Any,
        task_id: str,
        condition_id: Optional[str] = None,
        require_informative: bool = False,
    ) -> int:
        """该节点在给定任务下**有可用测量**的 Hamming-1 邻居数。

        ⚠️ **口径声明（AMENDMENT-011 §3.2，v1.4 起强制）**

            effective_degree(...)  ≡  degree_present(...)

        即本方法是 **present 口径**：``measurement_state != missing`` 的邻居才计数 ——
        ``censored`` 与 ``boundary_ambiguous`` **都算 present**（它们不是 missing）。

        **今后禁止在其他语境笼统使用 "effective degree" 一词。** 任何"local
        neighborhood"表述都必须写明是 **present neighborhood** 还是
        **informative neighborhood**；后者请用 :meth:`degree_informative`。

        Parameters
        ----------
        measurement_table :
            measurement 长表（行字典序列或 pandas DataFrame）。
        task_id, condition_id :
            指定任务（``condition_id=None`` 表示该任务下任意条件）。
        require_informative :
            ``False`` → **present 口径**（``measurement_state != missing``）；
            ``True``  → **informative 口径**（``informative == True``），等价于
            :meth:`degree_informative`。保留此参数仅为向后兼容，新代码请用显式方法名。

        Notes
        -----
        本方法**只读状态字段**（``MeasurementIndex`` 已丢弃 ``value``），
        返回值**不缓存在图上**，因此不会把 task 信息写入拓扑平面。
        """
        index = measurement_table
        if not isinstance(index, MeasurementIndex):
            index = MeasurementIndex(measurement_table)
        node_id = self._space.node_id(node)
        count = 0
        for nb in self._space.neighbors(node):
            nb_id = self._space.node_id(nb)
            if index.has_measurement(
                nb_id, task_id, condition_id, require_informative=require_informative
            ):
                count += 1
        return count

    # ---- v1.4：两个**分离**的邻域口径 ------------------------------------
    def degree_present(
        self,
        node: Sequence[str],
        measurement_table: Any,
        task_id: str,
        condition_id: Optional[str] = None,
    ) -> int:
        """**present 口径**（AMENDMENT-011 §3.2）：

            d_present(x, τ) = #{ y ∈ N₁(x) : state(y, τ) ≠ missing }

        ``censored`` 与 ``boundary_ambiguous`` **都算 present**（它们不是 missing）。
        本方法是 :meth:`effective_degree` 的**同义入口**（后者保留历史名称）。
        """
        return self.effective_degree(
            node, measurement_table, task_id, condition_id, require_informative=False
        )

    def degree_informative(
        self,
        node: Sequence[str],
        measurement_table: Any,
        task_id: str,
        condition_id: Optional[str] = None,
    ) -> int:
        """**informative 口径**（AMENDMENT-011 §3.2）：

            d_informative(x, τ) = #{ y ∈ N₁(x) : informative(y, τ) = TRUE }

        ⚠️ 这条口径与 :meth:`degree_present` 可以**极度分离**：CR9114 的 h3 / fluB
        绝大多数邻居"看得见"（present 近似满值），但真正有判别力的邻居已经塌掉
        （informative 从 h1 的 ~6.3 万降到 fluB 的 164）。
        """
        return self.effective_degree(
            node, measurement_table, task_id, condition_id, require_informative=True
        )

    # ---- 契约审计 -------------------------------------------------------
    def payload_audit(self) -> Dict[str, Any]:
        """证明图平面不含载荷：返回结构检查结果（供测试断言）。"""
        sample = next(iter(self.iter_nodes()))
        nb = next(iter(self.neighbors(sample)))
        return {
            "nodes_are_plain_tuples": isinstance(sample, tuple),
            "edges_are_plain_tuples": isinstance(nb, tuple),
            "graph_has_no_attributes": self._nodes is None or isinstance(self._nodes, tuple),
            "graph_public_attrs": sorted(
                a for a in dir(self) if not a.startswith("_") and not callable(getattr(self, a))
            ),
            "forbidden_payload_keys": list(GRAPH_FORBIDDEN_PAYLOAD_KEYS),
            "no_weight_method": not hasattr(self, "weight"),
        }


def audit_graph_contract(graph: GenotypeGraph) -> Dict[str, Any]:
    """对外的契约审计入口（tests 使用）。"""
    report = graph.payload_audit()
    report["ok"] = bool(
        report["nodes_are_plain_tuples"]
        and report["edges_are_plain_tuples"]
        and report["no_weight_method"]
    )
    return report
