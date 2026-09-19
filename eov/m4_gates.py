"""M4.0 — 一次性执行 CL-5（任务相似度门）与 C9/G-FTI（identifiability 门），冻结 eligible task surface。

⛔ 本脚本不做 EOV/regret/parent ranking —— 它只决定"哪些任务允许进入 M4 的正式分析"。

## CL-5（OP-25）
  作为 held-out future task 的任务，必须与 today task 的 Spearman rho <= 0.9。
  **非盲决定披露义务**：阈值 0.9 是在已知 rho 之后由项目负责人确定的；0.8 阈值下的结果
  一并报告（AMENDMENT-004 D-3 / FREEZE_LEDGER 批次 #7）。

## C9 / G-FTI（future-task identifiability gate）
  对每个候选条件计算
      signal     = IQR(该条件下 informative 组的 value_group)
      uncertainty= median(该条件下 informative 组的 value_sem)
      ratio      = signal / uncertainty
  预注册规则：
      - 只考虑 informative_frac >= 50% 的条件；
      - 通过 G-FTI 需 ratio >= 2.0（与 H1 的 "IQR >= 2x uncertainty" 同源）；
      - future condition = 通过者中 ratio 最高者（并列时取 informative_frac 更高者）。
  若某任务所有条件都不通过 -> 该任务的 strict Tomorrow Test 不成立（如实记录，不救）。
"""
from __future__ import annotations

import csv
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
TP = os.path.join(ROOT, "data", "processed", "M3_taskpanel_measurements.parquet")
OUT = os.path.join(ROOT, "data_registry", "M4_GATES.csv")
SURFACE = os.path.join(ROOT, "data_registry", "M4_ELIGIBLE_TASK_SURFACE.csv")

RHO_GATE = 0.9          # OP-25（非盲：已知 rho 之后确定）
RHO_STRICT = 0.8        # 用于强制共同报告
RATIO_MIN = 2.0         # G-FTI 判据
INF_FRAC_MIN = 50.0     # 任务准入（CL-9）
TEV_TIERS = ((100, "exclude_from_task_level_inference"),
             (500, "descriptive_sensitivity_only"),
             (10 ** 9, "eligible_for_formal_task_level_evaluation"))


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    """带并列平均秩的 Spearman rho（Spearman 相关 = 秩的 Pearson 相关）。"""
    def ranks(v):
        order = np.argsort(v, kind="mergesort")
        r = np.empty(len(v), dtype=float)
        i = 0
        sv = v[order]
        while i < len(order):
            j = i
            while j + 1 < len(order) and sv[j + 1] == sv[i]:
                j += 1
            r[order[i:j + 1]] = (i + j) / 2.0 + 1
            i = j + 1
        return r
    ra, rb = ranks(a), ranks(b)
    ra = ra - ra.mean(); rb = rb - rb.mean()
    d = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
    return float((ra * rb).sum() / d) if d > 0 else float("nan")


def label_of(row) -> str:
    return str(row.get("task_id") if pd.isna(row.get("condition_id")) else
               "%s@%s" % (row.get("task_id"), row.get("condition_id")))


def main() -> int:
    df = pd.read_parquet(MEAS)
    tp = pd.read_parquet(TP) if os.path.exists(TP) else pd.DataFrame()
    keys = ["dataset_id", "task_id", "condition_id", "genotype_id"]
    g = (df.groupby(keys, as_index=False)
           .agg(state=("measurement_state", "first"),
                informative=("informative", "first"),
                vg=("value_group", "first"),
                sem=("value_sem", "first")))
    g["label"] = g["task_id"].astype(str) + "@" + g["condition_id"].astype(str)
    rows = []

    # ---------------- C9 / G-FTI：逐条件 signal / uncertainty ----------------
    for ds, sub in g.groupby("dataset_id"):
        for lab, s in sub.groupby("label"):
            n = len(s)
            inf = s[s["informative"].astype(bool) & s["vg"].notna() & s["sem"].notna()]
            n_inf = len(inf)
            frac = 100.0 * n_inf / n if n else 0.0
            if n_inf >= 2:
                iqr = float(np.percentile(inf["vg"], 75) - np.percentile(inf["vg"], 25))
                med_sem = float(np.median(inf["sem"]))
                ratio = iqr / med_sem if med_sem > 0 else float("inf")
            else:
                iqr = med_sem = ratio = float("nan")
            eligible = (frac >= INF_FRAC_MIN) and (ratio >= RATIO_MIN)
            rows.append(dict(dataset_id=ds, task_condition=lab, n_groups=n, n_informative=n_inf,
                             informative_frac=round(frac, 2), iqr_signal=round(iqr, 6) if iqr == iqr else "",
                             median_sem=round(med_sem, 6) if med_sem == med_sem else "",
                             signal_over_uncertainty=round(ratio, 4) if ratio == ratio else "",
                             gfti_pass=bool(eligible)))

    # ---------------- CL-5：任务对相似度 ----------------
    for ds, sub in g.groupby("dataset_id"):
        labs = sorted(set(sub["label"]))
        func = [l for l in labs if "expression" not in l]
        if len(func) < 2:
            continue
        piv = sub[sub["label"].isin(func)].pivot_table(
            index="genotype_id", columns="label", values="vg", aggfunc="first")
        piv = piv.dropna(how="any")
        rows.append(dict(dataset_id=ds, task_condition="CL5_note", n_groups=len(piv), n_informative=len(piv),
                         informative_frac="", iqr_signal="", median_sem="", signal_over_uncertainty="",
                         gfti_pass="", note="共同可测基因型交集 = %d" % len(piv)))
        for i, a in enumerate(func):
            for b in func[i + 1:]:
                rho = spearman(piv[a].values, piv[b].values)
                rows.append(dict(dataset_id=ds, task_condition="CL5|%s~%s" % (a, b),
                                 n_groups=len(piv), n_informative=len(piv), informative_frac="",
                                 iqr_signal="", median_sem="", signal_over_uncertainty=round(rho, 4),
                                 gfti_pass=bool(rho <= RHO_GATE),
                                 note=("rho=%.4f ; <=0.9 gate %s ; <=0.8 strict %s"
                                       % (rho, "PASS" if rho <= RHO_GATE else "FAIL",
                                          "PASS" if rho <= RHO_STRICT else "FAIL"))))

    cols = ["dataset_id", "task_condition", "n_groups", "n_informative", "informative_frac",
            "iqr_signal", "median_sem", "signal_over_uncertainty", "gfti_pass", "note"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})
    print("WROTE", OUT, "rows=%d" % len(rows))

    # ---------------- TEM-1 的 future condition 选择 ----------------
    print()
    print("=== C9/G-FTI：TEM-1 全部条件（signal/uncertainty）===")
    tem = [r for r in rows if r["dataset_id"] == "TEM-1CML" and r["task_condition"].startswith(("AMP@", "AZT@"))]
    for r in sorted(tem, key=lambda r: -1e18 if r["signal_over_uncertainty"] == "" else -float(r["signal_over_uncertainty"])):
        print("  %-14s n=%-7d inf=%-7d frac=%6.2f%%  IQR=%-10s SEM=%-9s ratio=%-10s %s" % (
            r["task_condition"], r["n_groups"], r["n_informative"], r["informative_frac"],
            r["iqr_signal"], r["median_sem"], r["signal_over_uncertainty"],
            "PASS" if r["gfti_pass"] else ""))
    azt = [r for r in tem if r["task_condition"].startswith("AZT@") and r["signal_over_uncertainty"] != ""]
    passed = [r for r in azt if r["gfti_pass"]]
    print()
    if passed:
        best = max(passed, key=lambda r: (float(r["signal_over_uncertainty"]), float(r["informative_frac"])))
        print("★ TEM-1 future condition = **%s**（ratio=%.3f, informative_frac=%.2f%%）"
              % (best["task_condition"], float(best["signal_over_uncertainty"]), float(best["informative_frac"])))
    else:
        print("★ TEM-1 **没有任何 AZT 条件通过 G-FTI** -> strict Tomorrow Test 不成立；"
              "按裁决：如实写 'TEM-1 measurement resolution insufficient for a strong "
              "prospective Tomorrow Test'，TEM-1 退为 sensitivity evidence，主论据转回 Phillips。")
        if azt:
            b = max(azt, key=lambda r: float(r["signal_over_uncertainty"]))
            print("  （最接近的是 %s：ratio=%.3f）" % (b["task_condition"], float(b["signal_over_uncertainty"])))

    # ---------------- 冻结 eligible task surface ----------------
    surf = []
    for ds, sub in g.groupby("dataset_id"):
        for lab, s in sub.groupby("label"):
            surf.append(dict(dataset_id=ds, task_condition=lab, n_groups=len(s)))
    if not tp.empty:
        for (ds, t), s in tp.groupby(["dataset_id", "task_id"]):
            n = s["genotype_id"].nunique()
            tier = next(t for lim, t in TEV_TIERS if n < lim)
            surf.append(dict(dataset_id=ds, task_condition="%s" % t, n_groups=n,
                             task_panel_tier=tier, graph_eligible=False))
    with open(SURFACE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for r in surf for k in r}))
        w.writeheader()
        for r in surf:
            w.writerow(r)
    print()
    print("WROTE", SURFACE, "rows=%d" % len(surf))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
