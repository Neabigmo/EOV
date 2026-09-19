import glob
import io
import os
import re

import pandas as pd

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)

led = pd.read_csv(os.path.join(ROOT, "data_registry", "PROVENANCE_LEDGER.csv"))
code = ""
for p in glob.glob(os.path.join(ROOT, "eov", "*.py")):
    code += io.open(p, encoding="utf-8", errors="ignore").read()
frozen = ""
for p in glob.glob(os.path.join(ROOT, "*.md")) + glob.glob(os.path.join(ROOT, "prereg", "*.md")):
    frozen += io.open(p, encoding="utf-8", errors="ignore").read()

did = [c for c in led.columns if "dataset" in c.lower()][0]
print("%-30s %-22s %-8s %-10s %s" % ("dataset_id", "role", "allowed", "in_code", "in_frozen_doc"))
print("-" * 100)
suspects = []
for _, r in led.iterrows():
    d = str(r[did])
    toks = [k for k in re.split(r"[_\s]+", d) if len(k) >= 4]
    in_code = any(t.lower() in code.lower() for t in toks)
    in_frozen = any(t.lower() in frozen.lower() for t in toks)
    allowed = str(r.get("analysis_allowed", ""))
    print("%-30s %-22s %-8s %-10s %s" % (d[:29], str(r.get("role", ""))[:21],
                                         allowed, in_code, in_frozen))
    if allowed.lower() == "true" and in_frozen and not in_code:
        suspects.append(d)

print()
print("=" * 100)
if suspects:
    print("🔴 疑似漏交（已登记 + analysis_allowed + 被冻结文档引用 + 代码里没有）：")
    for s in suspects:
        print("   -", s)
else:
    print("✅ 没有第二个 TrpB 式漏交：凡被冻结文档引用且 analysis_allowed 的数据集，代码里都出现过。")
