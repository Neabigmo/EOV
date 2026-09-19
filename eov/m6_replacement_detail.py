"""M6 step S2f — 细查过筛候选的列结构与任务轴（只看结构）。"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

D = Path(r"<DATA_ROOT>/external/GraphFLA_probe")

for f in ["Moulana2022_ACE2.csv", "Moulana2023_CB6.csv",
          "Wu2020_Bei89.csv", "Wu2020_NDako16.csv",
          "Jalal2020_NBS.csv", "Jalal2020_parS.csv",
          "Soo2021_30C.csv"]:
    p = D / f
    if not p.exists():
        print("MISSING", f)
        continue
    df = pd.read_csv(p)
    print("=" * 78)
    print(f, "  rows=%d  cols=%d" % df.shape)
    print("  columns:", [str(c) for c in df.columns])
    with pd.option_context("display.width", 200, "display.max_columns", 40):
        print(df.head(3).to_string())
    print("  dtypes:", {str(k): str(v) for k, v in df.dtypes.items()})
    print("  na_frac per col:", {str(k): round(float(v), 4)
                                 for k, v in df.isna().mean().items()})
    print()
