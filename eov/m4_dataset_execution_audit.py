"""收尾审计：把「批次 #37 的教训」系统化。

批次 #37 的教训（第 21 条纪律）：**若某个数据集在冻结 ledger 里已登记、许可已判定、
角色已指定，却没有任何脚本读它 —— 那通常不是"不需要"，而是被某处的要求引用了却没被执行。**

TrpB4 就是这样被找出来的。本脚本把这条检查**系统化**：
对 `PROVENANCE_LEDGER.csv` 里的每个 dataset，判定它处于哪一档：

    A 已被脚本读取（有产物）         → 已执行
    B 已物化进 M2 长表               → 已执行
    C 已在 data/external 下但无产物   → 下载了但没分析 → **可能是漏交**
    D 仅登记、既无物化也无本地数据     → **重点怀疑对象**（TrpB4 在修正前属于这一档）

并对 D/C 档逐个给出"它在冻结文档里被什么要求引用了"。
"""
from __future__ import annotations

import csv
import glob
import os
import re

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "data_registry", "PROVENANCE_LEDGER.csv")
OUT = os.path.join(ROOT, "data_registry", "M4_DATASET_EXECUTION_AUDIT.csv")


def main() -> int:
    led = pd.read_csv(LEDGER)
    did = [c for c in led.columns if "dataset" in c.lower()][0]
    m2 = pd.read_parquet(os.path.join(ROOT, "data", "processed", "M2_measurements.parquet"))
    m2_ids = set(m2.dataset_id.unique())
    ext = os.path.join(ROOT, "data", "external")
    ext_dirs = set(os.listdir(ext)) if os.path.isdir(ext) else set()
    # 产物里出现过哪些 dataset 名
    prod = ""
    for p in glob.glob(os.path.join(ROOT, "data_registry", "*.csv")) + \
             glob.glob(os.path.join(ROOT, "data_registry", "*.md")) + \
             glob.glob(os.path.join(ROOT, "eov", "*.py")):
        try:
            prod += open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            pass
    # 冻结文档（用于回答"被什么引用了"）
    frozen = ""
    for p in glob.glob(os.path.join(ROOT, "*.md")) + glob.glob(os.path.join(ROOT, "prereg", "*.md")):
        try:
            frozen += open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            pass

    rows = []
    for _, r in led.iterrows():
        d = str(r[did])
        keys = [k for k in re.split(r"[_\s]+", d) if len(k) >= 4]
        in_m2 = d in m2_ids
        in_ext = any(any(k.lower() in e.lower() for k in keys) for e in ext_dirs)
        in_prod = any(("%s" % d) in prod for _ in [0]) or any(
            k.lower() in prod.lower() for k in keys[:2])
        if in_m2:
            tier = "B_materialized"
        elif in_ext:
            tier = "C_downloaded_no_product" if not in_prod else "A_has_product"
        else:
            tier = "A_has_product" if in_prod else "D_registered_only"
        cited = []
        for pat, label in [(r"强制\s*baseline", "AMENDMENT-007 强制 baseline"),
                           (r"L119", "PHASE1_DECISION L119 基线集"),
                           (r"必(须|需)", "含'必须/必需'的要求"),
                           (r"oracle[- ]only", "oracle-only 角色"),
                           (r"single_task_control", "单任务对照角色")]:
            if re.search(pat, frozen) and any(k.lower() in frozen.lower() for k in keys[:1]):
                cited.append(label)
        rows.append(dict(dataset_id=d, role=r.get("role", ""),
                         source_type=r.get("source_type", ""),
                         analysis_allowed=r.get("analysis_allowed", ""),
                         tier=tier,
                         cited_by="; ".join(sorted(set(cited))),
                         note=str(r.get("notes", ""))[:90]))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for x in rows:
            w.writerow(x)
    R = pd.DataFrame(rows)
    print("WROTE", OUT, len(rows), "rows\n")
    print(R.tier.value_counts().to_string())
    for t in ("D_registered_only", "C_downloaded_no_product"):
        z = R[R.tier == t]
        if len(z) == 0:
            continue
        print("\n=== %s (%d) ===" % (t, len(z)))
        for _, x in z.iterrows():
            print("  %-28s role=%-22s cited=%s" % (x.dataset_id, x.role, x.cited_by or "-"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
