"""M4.1 — WT/dead 锚点可分辨性审计（在看任何 V / regret / NR 之前执行）。

问题
----
PHASE1_PROTOCOL.md §3.1 把 TEM-1 的主尺度定义为 WT/dead 双锚定：
    u_anchor(z) = clip((z - F_dead) / (F_WT - F_dead), 0, 1)
该式**隐含**一个前提：`F_WT` 与 `F_dead` 必须彼此可分。若两者之差小到与测量噪声同阶，
分母就是噪声，`u` 会被噪声放大到任意尺度，而 clip 又把大多数点压到 0/1 两端 ——
于是"任务间差异"会被**纯噪声**制造出来。

审计量
------
    anchor_resolvability(τ) = |F_WT - F_dead| / median_genotype(value_sd_τ)
分位数与中位数都只用**该条件的 informative 基因型**。

结论（见 AMENDMENT-013）：该量必须在任何 u/V/regret 之前计算并冻结。
"""
from __future__ import annotations

import csv
import os
import re

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
OUT = os.path.join(ROOT, "data_registry", "M4_ANCHOR_RESOLVABILITY.csv")

# 预注册阈值（AMENDMENT-013 §2）：分离度必须 >= 2 个噪声单位，否则该条件不得使用锚点尺度
THRESHOLD = 2.0
SENTINELS = {
    "all_dot": re.compile(r"^\.+$"),      # WT（未突变）
    "all_zero": re.compile(r"^0+$"),      # 二元库的 WT
}
DEAD_SENTINEL = re.compile(r"^X+$")       # TEM-1dead spike-in（**不是** WT 候选）


def main() -> int:
    df = pd.read_parquet(MEAS)
    rows = []
    for ds in sorted(df.dataset_id.unique()):
        t = df[df.dataset_id == ds]
        for (tid, cid), s in t.groupby(["task_id", "condition_id"], sort=True):
            gi = s.genotype_id.astype(str)
            by_g = s.groupby(gi.underlying if hasattr(gi, "underlying") else np.asarray(gi))
            g = by_g.value_group.median()
            sd = by_g.value_sd.median()
            inf = by_g.informative.max().astype(bool)
            keep = inf[inf].index
            g = g.loc[keep]
            noise = float(np.nanmedian(sd.loc[keep].values))
            for name, rx in SENTINELS.items():
                hit = sorted({x for x in keep if rx.match(str(x))})
                if not hit:
                    continue
                wt_id = hit[0]
                dead_id = "X" * len(wt_id)
                f_wt = float(g.get(wt_id, np.nan))
                f_dead = float(g.get(dead_id, np.nan))
                sep = abs(f_wt - f_dead) if (f_wt == f_wt and f_dead == f_dead) else np.nan
                resolv = sep / noise if (sep == sep and noise > 0) else np.nan
                rows.append(dict(
                    dataset_id=ds, task_id=tid, condition_id=cid, wt_row=name,
                    wt_genotype_id=wt_id, dead_genotype_id=dead_id if dead_id in set(keep) else "",
                    F_WT="" if f_wt != f_wt else round(f_wt, 6),
                    F_dead="" if f_dead != f_dead else round(f_dead, 6),
                    anchor_sep="" if sep != sep else round(sep, 6),
                    noise_unit=round(noise, 6),
                    anchor_resolvability="" if resolv != resolv else round(resolv, 4),
                    anchor_admissible=(("" if resolv != resolv else (resolv >= THRESHOLD))),
                    n_informative=int(len(g)),
                    q05=round(float(np.percentile(g, 5)), 4),
                    q50=round(float(np.percentile(g, 50)), 4),
                    q95=round(float(np.percentile(g, 95)), 4),
                    gmax=round(float(g.max()), 4),
                ))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("WROTE", OUT, "rows=%d" % len(rows))
    adm = [r for r in rows if r["anchor_admissible"] is True]
    print("anchor_admissible=True  n=%d" % len(adm))
    for r in rows:
        if r["dataset_id"] == "TEM-1CML":
            print("  %-4s@%-7s resolv=%-9s admissible=%s" % (
                r["task_id"], r["condition_id"], r["anchor_resolvability"],
                r["anchor_admissible"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
