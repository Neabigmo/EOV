"""M3.4 — PHASE1_ANALYSIS_READY_MANIFEST 生成器（M4 的真正入口）。

用法：
    $env:PYTHONPATH='<PROJECT_ROOT>'; & '<PYTHON>' eov/analysis_ready_manifest.py

输入：
  - data_registry/M2_AUDIT_TABLE.csv          （graph-eligible landscape 的统计）
  - data_registry/M3_TASKPANEL_QC.csv         （task panel 的统计，若已存在）
  - data_registry/PROVENANCE_LEDGER.csv       （role / 许可 / source_type）
  - data/processed/M2_measurements.parquet    （用于逐 dataset 的 processed_hash）

输出：
  - data_registry/PHASE1_ANALYSIS_READY_MANIFEST.csv

⚠️ 本文件**不是分析结果**。它只宣布：从这一刻起，**哪些数据能进入哪一种科学问题，不能再根据结果更改**。

⛔ 本脚本不计算 EOV / regret / parent ranking / 搜索策略 / 预算模拟 / Tomorrow-Test 相关任何量。
"""
from __future__ import annotations

import csv
import hashlib
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(ROOT, "data_registry", "M2_AUDIT_TABLE.csv")
TASKPANEL = os.path.join(ROOT, "data_registry", "M3_TASKPANEL_QC.csv")
LEDGER = os.path.join(ROOT, "data_registry", "PROVENANCE_LEDGER.csv")
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
OUT = os.path.join(ROOT, "data_registry", "PHASE1_ANALYSIS_READY_MANIFEST.csv")

# 冻结的测量状态政策（AMENDMENT-011 §2.1）
POLICY_WITH_AMBIGUOUS = ("primary: only censored(censoring_evidence=explicit) treated as censored; "
                         "sensitivity: boundary_ambiguous treated as left-censored")
POLICY_EXPLICIT_ONLY = ("primary: only censored(censoring_evidence=explicit) treated as censored; "
                        "no boundary_ambiguous rows in this task")

# 冻结的 M4 前置门（**不在 M3 执行**）
M4_GATES = "M4-pre gates pending: CL-5 task-similarity (Spearman rho <= 0.9) and C9 identifiability (G-FTI)"

# 冻结的 source artifact（= 我们实际 ingest 的那份文件）
SOURCE_ARTIFACT = {
    "TEM-1CML": ["data/external/TEM1_Gaszek2025/data/processed/amp_auc_wide_df.parquet",
                 "data/external/TEM1_Gaszek2025/data/processed/azt_auc_wide_df.parquet"],
}
# eLife 两个数据集的源文件下载在 %TEMP%（不长期保留）→ 若仍在则计入，否则标 not_available
TEMP_ARTIFACT = {
    "Phillips2023_HA_CH65": os.path.join(os.environ.get("TEMP", ""), "eov_m2", "phillips2023.xlsx"),
    "Phillips2021_CR9114": os.path.join(os.environ.get("TEMP", ""), "eov_m2", "cr9114.csv"),
}

COLS = [
    "dataset_id", "task_id", "role",
    "graph_eligible", "task_panel_eligible", "future_task_eligible",
    "boundary_status", "boundary_evidence", "ceiling_status",
    "measurement_state_policy",
    "n_groups", "present_frac", "exact_frac", "censored_frac", "boundary_ambiguous_frac", "missing_frac",
    "informative_fraction", "usable_uncertainty",
    "degree_topology", "d_present_mean", "d_informative_mean",
    "source_hash", "processed_hash",
    "inclusion_exclusion_reason",
]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def source_hash_for(dataset_id: str) -> str:
    parts = []
    for rel in SOURCE_ARTIFACT.get(dataset_id, []):
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            parts.append("%s=%s" % (os.path.basename(rel), sha256_file(p)))
    tmp = TEMP_ARTIFACT.get(dataset_id)
    if tmp and os.path.exists(tmp):
        parts.append("%s=%s" % (os.path.basename(tmp), sha256_file(tmp)))
    return " | ".join(parts) if parts else "not_available"


def processed_hash_for(df: pd.DataFrame, dataset_id: str) -> str:
    """逐 dataset 的规范化摘要（组级字段排序后哈希）—— 便于将来判断"这一份数据有没有被改过"。"""
    sub = df[df["dataset_id"] == dataset_id]
    if sub.empty:
        return "not_available"
    keys = ["dataset_id", "task_id", "condition_id", "genotype_id"]
    agg = {c: "first" for c in sub.columns
           if c not in keys + ["replicate", "value", "value_sd"]}
    g = sub.groupby(keys, as_index=False).agg(agg)
    g = g.reindex(sorted(g.columns), axis=1).sort_values(keys)
    h = hashlib.sha256()
    for row in g.itertuples(index=False):
        h.update(("|".join("" if pd.isna(v) else str(v) for v in row) + "\n").encode("utf-8"))
    return h.hexdigest()


def main() -> int:
    audit = list(csv.DictReader(open(AUDIT, encoding="utf-8")))
    ledger = {r["dataset_id"]: r for r in csv.DictReader(open(LEDGER, encoding="utf-8"))}
    meas = pd.read_parquet(MEAS) if os.path.exists(MEAS) else pd.DataFrame(columns=["dataset_id"])
    proc_cache = {d: processed_hash_for(meas, d) for d in sorted(set(meas.get("dataset_id", [])))}

    rows = []
    for a in audit:
        ds, task = a["dataset_id"], a["task_id"]
        led = ledger.get(ds, {})
        role = a.get("dataset_role") or led.get("role", "")
        aux = a.get("measurement_modality") == "auxiliary"
        ge = str(a.get("graph_eligible", "")).strip().lower() == "true"
        tp = role == "task_panel"
        inf_frac = float(a["informative_pct"]) if a.get("informative_pct") not in ("", None) else None
        # future-task eligibility：**只做结构性判定**
        #   功能模态 ∧ informative_frac >= 50%（CL-9 主门槛）∧ 边界状态已确定
        bstat = a.get("floor_status", "")
        reasons = []
        if aux:
            reasons.append("auxiliary modality: 不是 functional task（AMENDMENT-009 §4）→ 不作 future task")
        if inf_frac is not None and inf_frac < 50.0:
            reasons.append("informative_frac=%.2f%% < 50%%（CL-9 主任务门槛）" % inf_frac)
        if bstat in ("unresolved", ""):
            reasons.append("boundary_status=%s：边界未定，不得产出边界删失" % (bstat or "empty"))
        if not reasons:
            reasons.append("结构上可作 future task（%s）" % M4_GATES)
        fte = (not aux) and (inf_frac is not None and inf_frac >= 50.0) and bstat not in ("unresolved", "")

        has_amb = "boundary_ambiguous" in a  # 审计表 v1.4 才有的列
        rows.append({
            "dataset_id": ds,
            "task_id": task,
            "role": role,
            "graph_eligible": ge,
            "task_panel_eligible": tp,
            "future_task_eligible": bool(fte),
            "boundary_status": bstat,
            "boundary_evidence": a.get("floor_source", ""),
            "ceiling_status": a.get("ceiling_status", ""),
            "measurement_state_policy": POLICY_WITH_AMBIGUOUS if has_amb else POLICY_EXPLICIT_ONLY,
            "n_groups": a.get("n_groups", ""),
            "present_frac": a.get("present_pct", ""),
            "exact_frac": a.get("exact_pct", ""),
            "censored_frac": a.get("censored_pct", ""),
            "boundary_ambiguous_frac": a.get("boundary_ambiguous_pct", ""),
            "missing_frac": a.get("missing_pct", ""),
            "informative_fraction": a.get("informative_pct", ""),
            "usable_uncertainty": a.get("uncertainty_available_pct", ""),
            "degree_topology": a.get("degree_topology", ""),
            "d_present_mean": a.get("eff_degree_mean", ""),
            "d_informative_mean": a.get("d_informative_mean", ""),
            "source_hash": source_hash_for(ds),
            "processed_hash": proc_cache.get(ds, "not_available"),
            "inclusion_exclusion_reason": "; ".join(reasons),
        })

    # task panel（M3.1/M3.2）——**不含任何 degree 字段**
    if os.path.exists(TASKPANEL):
        for t in csv.DictReader(open(TASKPANEL, encoding="utf-8")):
            ds = t["dataset_id"]
            rows.append({
                "dataset_id": ds, "task_id": t.get("task_id", ""), "role": "task_panel",
                "graph_eligible": False, "task_panel_eligible": True, "future_task_eligible": False,
                "boundary_status": t.get("floor_status", "unresolved"),
                "boundary_evidence": t.get("boundary_evidence", "none"),
                "ceiling_status": t.get("ceiling_status", ""),
                "measurement_state_policy": POLICY_EXPLICIT_ONLY,
                "n_groups": t.get("n_variants_measured", ""),
                "present_frac": t.get("measured_frac", ""),
                "exact_frac": "", "censored_frac": t.get("censored_n", ""),
                "boundary_ambiguous_frac": t.get("boundary_ambiguous_n", ""),
                "missing_frac": t.get("missing_n", ""),
                "informative_fraction": t.get("informative_frac", ""),
                "usable_uncertainty": t.get("uncertainty_coverage", ""),
                "degree_topology": "", "d_present_mean": "", "d_informative_mean": "",
                "source_hash": "not_available",
                "processed_hash": "not_available",
                "inclusion_exclusion_reason":
                    "task_panel：无合法 combinatorial neighborhood → 只允许 coverage 类输出，"
                    "禁止任何 degree 字段（AMENDMENT-009 §5 / 011 §6.1）",
            })

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("WROTE %s  rows=%d" % (OUT, len(rows)))
    for r in rows:
        print("  %-22s %-24s role=%-18s ge=%-5s tp=%-5s fte=%-5s inf=%-7s" % (
            r["dataset_id"], r["task_id"], r["role"], r["graph_eligible"],
            r["task_panel_eligible"], r["future_task_eligible"], r["informative_fraction"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
