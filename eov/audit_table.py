"""M2.4 审计表生成器（M2 出口交付物）。

用法：
    & '<PYTHON>' eov/audit_table.py

输入：
  - data/processed/M2_measurements.parquet      （schema v1.2 统一 measurement 长表）
  - data_registry/PROVENANCE_LEDGER.csv         （角色 / 空间规模 / 许可）
  - 本文件内冻结的 BOUNDARY 表                  （来自 M2_TEM1/ELIFE_BOUNDARY_EVIDENCE.md）

输出：
  - data_registry/M2_AUDIT_TABLE.csv            （每个 dataset × task 一行）

⛔ 本脚本**只做覆盖度与图的可用性统计**：
   不计算 EOV、不计算 R_{B,pi}、不做 regret、不做 parent ranking、不做任何 Tomorrow-Test 相关量；
   不比较、不排序、不选择任何 fitness 数值（唯一用到的 fitness 相关量是"是否存在/是否 informative"）。
"""
from __future__ import annotations

import collections
import csv
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eov.landscape import GenotypeGraph, MeasurementIndex, MixedAlphabetSpace  # noqa: E402
from eov.schema import graph_eligible  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
LEDGER = os.path.join(ROOT, "data_registry", "PROVENANCE_LEDGER.csv")
OUT = os.path.join(ROOT, "data_registry", "M2_AUDIT_TABLE.csv")

# ---------------------------------------------------------------------------
# 冻结边界（依据 data_registry/M2_TEM1_BOUNDARY_EVIDENCE.md 与 M2_ELIFE_BOUNDARY_EVIDENCE.md）
# 键 = (dataset_id, task_id)
# ---------------------------------------------------------------------------
NONE_CEIL = ("not_reached", "none")
BOUNDARY = {
    ("TEM-1CML", "AMP"): dict(floor="0.1760912591", status="inferred", source="transformation"),
    ("TEM-1CML", "AZT"): dict(floor="0.1760912591", status="inferred", source="transformation"),
    ("Phillips2021_CR9114", "h1"): dict(floor="7.0", status="explicit", source="assay_detection"),
    ("Phillips2021_CR9114", "h3"): dict(floor="6.0", status="explicit", source="assay_detection"),
    ("Phillips2021_CR9114", "fluB"): dict(floor="6.0", status="explicit", source="assay_detection"),
    ("Phillips2023_HA_CH65", "MA90"): dict(floor="", status="none", source="none"),
    ("Phillips2023_HA_CH65", "SI06"): dict(floor="6.0", status="inferred", source="assay_detection"),
    ("Phillips2023_HA_CH65", "G189E"): dict(floor="6.0", status="inferred", source="assay_detection"),
    ("Phillips2023_HA_CH65", "expression"): dict(floor="", status="none", source="none"),
}

# `X` = non-functional / dead 哨兵（见 DATA_AUDIT §2.1），不是替换；不得计入等位集合。
DEAD_SENTINEL = "X"

# 图的构造：如何把 genotype_id 变成节点（必须与 measurement key 同一构造路径）
GRAPH_SPEC = {
    "TEM-1CML": dict(kind="profile", degree=18),
    "Phillips2021_CR9114": dict(kind="binary16", degree=16),
    "Phillips2023_HA_CH65": dict(kind="binary16", degree=16),
}

COLS = [
    "dataset_id", "task_id", "measurement_modality", "dataset_role", "graph_eligible",
    "total_genotype_space", "n_groups",
    "present_n", "present_pct", "exact_n", "exact_pct", "censored_n", "censored_pct",
    "boundary_ambiguous_n", "boundary_ambiguous_pct", "missing_n", "missing_pct",
    "informative_n", "informative_pct",
    "uncertainty_available_n", "uncertainty_available_pct",
    "floor_value", "floor_status", "floor_source", "ceiling_value", "ceiling_status", "ceiling_source",
    "degree_topology", "eff_degree_mean", "eff_degree_min", "eff_degree_n_at_full", "eff_degree_n_ge_half",
    "d_informative_mean", "d_informative_min", "d_informative_n_at_full", "d_informative_n_ge_half",
    "materialized_in_m2", "note",
]


def load_ledger() -> dict:
    with open(LEDGER, encoding="utf-8") as f:
        return {r["dataset_id"]: r for r in csv.DictReader(f)}


def group_level(df: pd.DataFrame) -> pd.DataFrame:
    """折叠到组级：一行 = 一个 (dataset, task, condition, genotype) 组。"""
    keys = ["dataset_id", "task_id", "condition_id", "genotype_id"]
    return df.groupby(keys, as_index=False).agg(
        state=("measurement_state", "first"),
        informative=("informative", "first"),
        sem=("value_sem", "first"),
        sd=("value_sd", "first"),
        modality=("measurement_modality", "first"),
    )


def build_space(dataset_id: str, profiles):
    return MixedAlphabetSpace.from_masked_profiles(profiles)


def eff_degree_summary(sub_cond, task_id, space, g=None):
    """`sub_cond` 必须是**单一条件**下的组级行（否则 effective degree 无定义）。

    **快速路径**：不调用 `GenotypeGraph.effective_degree`（逐节点 API 在 55k 节点上需数分钟），
    改为直接由"等位集合 + present 集合"做集合式邻域查询（同规模实测 ~2 s）。
    结果与 `eov/landscape.py` 的逐节点结果已交叉验证一致（见 M1_INDEPENDENT_VERIFICATION.md）。
    """
    raw = [str(x) for x in sub_cond["genotype_id"]]
    states = [str(x) for x in sub_cond["state"]]
    infs = [bool(x) for x in sub_cond["informative"]]
    # `X` = non-functional / dead 哨兵（DATA_AUDIT §2.1），**不是替换** ——
    # 若把它当作等位，会给每个位点各加 1 个等位（TEM-1: 18 -> 31），必须剔除。
    keep = [i for i, p in enumerate(raw) if DEAD_SENTINEL not in p]
    n_dead = len(raw) - len(keep)
    profiles = [raw[i] for i in keep]
    L = len(profiles[0])
    alleles = [sorted({p[i] for p in profiles}) for i in range(L)]
    D = sum(len(a) - 1 for a in alleles)
    # v1.4：present 与 informative 是两个**不同**的口径，不得混用（AMENDMENT-011 §3）
    #   present       = state != missing   （censored 与 boundary_ambiguous 都算 present）
    #   informative   = informative == True（primary 分支下 boundary_ambiguous 通常不计入）
    present = {profiles[j] for j, i in enumerate(keep) if states[i] != "missing"}
    inform = {profiles[j] for j, i in enumerate(keep) if infs[i]}
    hist_p = collections.Counter()
    hist_i = collections.Counter()
    for p in profiles:
        dp = di = 0
        for i in range(L):
            cur = p[i]
            for alt in alleles[i]:
                if alt == cur:
                    continue
                nb = p[:i] + alt + p[i + 1:]
                if nb in present:
                    dp += 1
                if nb in inform:
                    di += 1
        hist_p[dp] += 1
        hist_i[di] += 1

    def summ(hist):
        tot = sum(hist.values())
        vals = [k for k, v in hist.items() for _ in range(v)]
        return dict(
            mean=round(sum(vals) / len(vals), 4),
            min=min(vals),
            n_at_full=hist.get(D, 0),
            n_ge_half=sum(v for k, v in hist.items() if k >= D // 2),
            total=tot,
        )

    sp, si = summ(hist_p), summ(hist_i)
    return dict(
        degree_topology=D,
        # d_present（= 旧的 "effective_degree"，见 AMENDMENT-011 §3.2）
        eff_degree_mean=sp["mean"], eff_degree_min=sp["min"],
        eff_degree_n_at_full=sp["n_at_full"], eff_degree_n_ge_half=sp["n_ge_half"],
        # d_informative（v1.4 新增）
        d_informative_mean=si["mean"], d_informative_min=si["min"],
        d_informative_n_at_full=si["n_at_full"], d_informative_n_ge_half=si["n_ge_half"],
        total=sp["total"],
        n_observed_profiles=len(profiles),
        n_dead_sentinel=n_dead,
    )


# 预注册主条件（OP-15）。TEM-1 是多条件任务，effective degree 必须在**单一条件**下定义。
PRIMARY_CONDITION = {
    ("TEM-1CML", "AMP"): "781.0",
    ("TEM-1CML", "AZT"): "36.0",
}


def main() -> int:
    df = pd.read_parquet(MEAS)
    ledger = load_ledger()
    gl = group_level(df)

    out = []
    for (ds, task), sub in gl.groupby(["dataset_id", "task_id"], sort=True):
        rec = dict.fromkeys(COLS, "")
        rec["dataset_id"] = ds
        rec["task_id"] = task
        rec["measurement_modality"] = sub["modality"].iloc[0]
        led = ledger.get(ds, {})
        rec["dataset_role"] = led.get("role", "")
        space_size = led.get("theoretical_space_size", "")
        rec["total_genotype_space"] = space_size
        n = len(sub)
        rec["n_groups"] = n
        cnt = collections.Counter(sub["state"])
        # 四态（AMENDMENT-011 §1.2）。同时兼容 v1.3 的旧命名 `measured_exact`，
        # 使本生成器在重分类前后都能正确工作。
        n_exact = cnt.get("exact", 0) + cnt.get("measured_exact", 0)
        n_cens = cnt.get("censored", 0)
        n_amb = cnt.get("boundary_ambiguous", 0)
        n_miss = cnt.get("missing", 0)
        n_present = n_exact + n_cens + n_amb  # present = 非 missing
        for label, v in (("present", n_present), ("exact", n_exact), ("censored", n_cens),
                         ("boundary_ambiguous", n_amb), ("missing", n_miss)):
            rec[f"{label}_n"] = v
            rec[f"{label}_pct"] = round(100.0 * v / n, 2)
        inf_n = int(sub["informative"].sum())
        rec["informative_n"] = inf_n
        rec["informative_pct"] = round(100.0 * inf_n / n, 2)
        unc = int((sub["sem"].notna() | sub["sd"].notna()).sum())
        rec["uncertainty_available_n"] = unc
        rec["uncertainty_available_pct"] = round(100.0 * unc / n, 2)

        b = BOUNDARY.get((ds, task), {})
        rec["floor_value"] = b.get("floor", "")
        rec["floor_status"] = b.get("status", "")
        rec["floor_source"] = b.get("source", "")
        rec["ceiling_value"] = ""
        rec["ceiling_status"], rec["ceiling_source"] = NONE_CEIL

        role = led.get("role", "")
        ge = graph_eligible(
            role,
            complete_product=led.get("complete_product"),
            observed_genotype_count=led.get("observed_genotype_count"),
            theoretical_space_size=space_size,
        )
        rec["graph_eligible"] = bool(ge)
        rec["materialized_in_m2"] = True
        if ge:
            spec = GRAPH_SPEC.get(ds)
            conds = sorted(set(sub["condition_id"].astype(str)))
            primary = PRIMARY_CONDITION.get((ds, task))
            if primary is None and len(conds) == 1:
                primary = conds[0]
            if spec is None or primary is None:
                rec["note"] = ("graph_eligible 但无法确定图构造方式或主条件"
                               "（GRAPH_SPEC/PRIMARY_CONDITION 未登记，且该任务有 %d 个条件）" % len(conds))
            else:
                sub_cond = sub[sub["condition_id"].astype(str) == primary]
                if spec is None:
                    rec["note"] = "graph_eligible 但未登记 GRAPH_SPEC（无法确定图构造方式）"
                else:
                    s = eff_degree_summary(sub_cond, task, None, None)
                    rec["degree_topology"] = s["degree_topology"]
                    rec["eff_degree_mean"] = s["eff_degree_mean"]
                    rec["eff_degree_min"] = s["eff_degree_min"]
                    rec["eff_degree_n_at_full"] = s["eff_degree_n_at_full"]
                    rec["eff_degree_n_ge_half"] = s["eff_degree_n_ge_half"]
                    rec["d_informative_mean"] = s["d_informative_mean"]
                    rec["d_informative_min"] = s["d_informative_min"]
                    rec["d_informative_n_at_full"] = s["d_informative_n_at_full"]
                    rec["d_informative_n_ge_half"] = s["d_informative_n_ge_half"]
                    rec["note"] = ("d_present(=eff_degree) 与 d_informative 均为主条件 %s 上的**不同口径**"
                                   "（AMENDMENT-011 §3）；该任务共 %d 个条件；扫描 %d 个已观测基因型，"
                                   "剔除 %d 个含 X 的 dead 哨兵"
                                   % (primary, len(conds), s["n_observed_profiles"], s["n_dead_sentinel"]))
        else:
            rec["note"] = "非 graph-eligible：不输出任何 degree 字段（AMENDMENT-009 §5）"
        out.append(rec)

    # 未在 M2 materialize 的 task_panel / 其它数据集，单独列出（诚实标注）
    for ds, led in sorted(ledger.items()):
        if led.get("role") == "task_panel" and ds not in set(gl["dataset_id"]):
            rec = dict.fromkeys(COLS, "")
            rec["dataset_id"] = ds
            rec["task_id"] = "(not materialized in M2)"
            rec["dataset_role"] = "task_panel"
            rec["graph_eligible"] = False
            rec["materialized_in_m2"] = False
            rec["note"] = ("task_panel：按 AMENDMENT-009 §5 只应输出 task coverage / measured / "
                           "censored / informative / uncertainty 覆盖度；本阶段未 materialize -> deferred to M3")
            out.append(rec)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in out:
            w.writerow(r)
    print("WROTE %s  rows=%d" % (OUT, len(out)))
    for r in out:
        print("  %-22s %-22s groups=%-6s present=%-6s censored=%-6s informative=%-6s ge=%s" % (
            r["dataset_id"], r["task_id"], r["n_groups"], r["present_n"], r["censored_n"],
            r["informative_n"], r["graph_eligible"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
