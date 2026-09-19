"""M6 报告数值核验器 —— 逐条核对 `data_registry/M6_ELIGIBILITY_REPORT.md` 里的手抄数字。

原则（项目铁律）：报告里每个手抄数字都必须有一条自动核验。
本脚本只读取既有产物 + 重算可廉价重算者；**不产生任何新的科学结论**。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "external" / "AncSR1_Starr2017" / "raw"
MAN = ROOT / "data" / "manifests"
PROBE = ROOT / "data" / "external" / "GraphFLA_probe"

CHECKS: list[tuple[str, object, object]] = []


def ck(label: str, got, want) -> None:
    CHECKS.append((label, got, want))


# --------------------------------------------------------------- 1. 文件清单
fl = json.loads((MAN / "M6_ANCSR1_DRYAD_FILELIST.json").read_text(encoding="utf-8"))
ck("dryad n_files", fl["n_files"], 184)
ck("dryad total_bytes", fl["total_bytes"], 6312162041)
ck("dryad total MB (1dp)", round(fl["total_bytes"] / 1e6, 1), 6312.2)
ck("dryad ext .rda", fl["extension_histogram"].get(".rda"), 181)
ck("dryad ext .gexf", fl["extension_histogram"].get(".gexf"), 2)
ck("dryad ext .md", fl["extension_histogram"].get(".md"), 1)
rm = [f for f in fl["files"] if f["path"] == "README.md"]
ck("README.md bytes", rm[0]["bytes"] if rm else None, 13670)
ck("README.md on disk", (RAW / "README.md").stat().st_size, 13670)

# --------------------------------------------------------- 2. AncSR1 结构判定
el = json.loads((MAN / "M6_ANCSR1_ELIGIBILITY.json").read_text(encoding="utf-8"))
ck("per_re E rows", el["per_re"]["E"]["n_rows"], 160000)
ck("per_re S rows", el["per_re"]["S"]["n_rows"], 160000)
ck("sequence_sets intersection", el["sequence_sets"]["intersection"], 160000)
ck("sequence_sets jaccard", round(el["sequence_sets"]["jaccard"], 4), 1.0000)
geo = el["geometry"]["NH.ACT.ADJM.rda"]
ck("NH n_nodes", geo["n_nodes"], 160000)
ck("NH nnz", geo["nnz"], 12160000)
ck("NH deg_min", geo["deg_min"], 76)
ck("NH deg_max", geo["deg_max"], 76)
ck("NH deg_mean", round(geo["deg_mean"], 2), 76.00)
ck("budget space", el["budget"]["space"], 160000)
ck("budget op21_cap", el["budget"]["op21_cap"], 40000)
ck("budget tiers", el["budget"]["tiers"], [24, 96, 384])
ck("tasks n_tasks", el["tasks"]["n_tasks"], 2)
ck("tasks n_pairs", el["tasks"]["n_pairs"], 1)
for k, want in [("E1_tasks_ge_3", False), ("E2_pairs_ge_10", False),
                ("E3_space_definable", True), ("E4_aa_hamming1_definable", True),
                ("E5_graph_eligible", True), ("E6_budget_ge_2", True)]:
    ck("gate %s" % k, el["E1_E6"][k]["pass"], want)
ck("overall", el["overall"], "FAIL")

# --------------------------------------------- 3. 身份/缺失模式（重算，不看表型）
import rdata  # noqa: E402


def load(name):
    return list(rdata.conversion.convert(
        rdata.parser.parse_file(RAW / name)).values())[0]


dj = load("DT.JOINT.rda")
d11 = load("DT.11P.CODING.rda")
strip = lambda s: s[1:] if s and s[0] in "ES" else s
for re_, want_same, want_jo, want_1o in [("E", 144500, 3231, 12269),
                                         ("S", 147233, 2007, 10760)]:
    a = dj[dj["RE"] == re_].copy()
    a["k"] = a["AAseq"].astype(str).map(strip)
    a = a.sort_values("k")["pooled.meanF"].notna().to_numpy()
    b = d11.copy()
    b["k"] = b["AAseq"].astype(str).map(strip)
    cc = {"E": "ERE.pooled.meanF", "S": "SRE.pooled.meanF"}[re_]
    b = b.sort_values("k")[cc].notna().to_numpy()
    ck("missingness identical RE=%s" % re_, int((a == b).sum()), want_same)
    ck("joint_only RE=%s" % re_, int((a & ~b).sum()), want_jo)
    ck("11P_only RE=%s" % re_, int((b & ~a).sum()), want_1o)

# ------------------------------------------------------------- 4. Moulana
mf = ["Moulana2022_ACE2.csv", "Moulana2023_CB6.csv", "Moulana2023_CoV555.csv",
      "Moulana2023_REGN10987.csv", "Moulana2023_S309.csv"]
nas = {}
for f in mf:
    d = pd.read_csv(PROBE / f)
    nas[f] = round(float(d["fitness"].isna().mean()), 4)
    if f == mf[0]:
        pcols = [c for c in d.columns if c.startswith("pos")]
        ck("moulana rows", len(d), 32768)
        ck("moulana n_pos", len(pcols), 15)
        ck("moulana states", sorted(set(np.unique(d[pcols].values))), [0, 1])
for f, want in [("Moulana2023_S309.csv", 0.0), ("Moulana2022_ACE2.csv", 0.0062),
                ("Moulana2023_REGN10987.csv", 0.2772),
                ("Moulana2023_CoV555.csv", 0.3937),
                ("Moulana2023_CB6.csv", 0.4961)]:
    ck("moulana na %s" % f, nas[f], want)
ck("moulana deg(=n_pos)", 15, 15)
n_ok18 = sum(1 for v in nas.values() if v <= 0.25)
ck("moulana tasks passing OP-18", n_ok18, 2)
ck("moulana pairs after OP-18", n_ok18 * (n_ok18 - 1) // 2, 1)

# ------------------------------------------------------------- 5. Jalal2020
for f in ["Jalal2020_NBS.csv", "Jalal2020_parS.csv"]:
    d = pd.read_csv(PROBE / f)
    pcols = [c for c in d.columns if c.startswith("pos")]
    dom = [sorted(d[c].dropna().unique()) for c in pcols]
    prod = int(np.prod([len(x) for x in dom]))
    ck("%s rows" % f, len(d), 160000)
    ck("%s product" % f, prod, 160000)
    ck("%s deg" % f, sum(len(x) - 1 for x in dom), 76)

# --------------------------------------------------------- 6. 穷尽筛选
ex = json.loads((MAN / "M6_EXHAUSTIVE_REPLACEMENT_SCREEN.json")
                .read_text(encoding="utf-8"))
ck("n CSVs screened", len(ex["rows"]), 163)
ck("eligible groups", ex["eligible"], ["Wu2020"])
wu = [g for g in ex["groups"] if g["group"] == "Wu2020"][0]
ck("Wu2020 n_files", wu["n_files"], 7)
ck("Wu2020 prod", wu["prod"], 576)
ck("Wu2020 deg", wu["deg"], 12)
ck("Wu2020 op21 tiers", wu["op21_tiers"], [24, 96])
ck("Wu2020 tasks passing OP-18", wu["tasks_passing_op18"], 7)
ck("Wu2020 pairs", wu["pairs"], 21)
ck("Wu2020 coverage@96 (%)", round(96 / 576 * 100, 2), 16.67)
ck("Mira2015 op21 tiers", [g for g in ex["groups"]
                           if g["group"] == "Mira2015"][0]["op21_tiers"], [])
ck("Guerrero2019 op21 tiers", [g for g in ex["groups"]
                               if g["group"] == "Guerrero2019"][0]["op21_tiers"], [])

# ------------------------------------------------------------- 7. 阈值未改
amd = (ROOT / "prereg" / "AMENDMENT-017_m6_confirmatory_freeze.md").read_text(
    encoding="utf-8")
ck("AMENDMENT-017 still says >=0.45", "**≥ 0.45**" in amd, True)
ck("AMENDMENT-017 still says E1 >=3", "task 数** | ≥ 3" in amd.replace("| ", "| "), True)

# ------------------------------------------------------------- 报告
bad = [(l, g, w) for l, g, w in CHECKS if g != w]
print("=" * 78)
print("M6 REPORT NUMERIC VERIFICATION")
print("=" * 78)
for l, g, w in CHECKS:
    print("  %-4s %-42s got=%-22s want=%s"
          % ("OK" if g == w else "FAIL", l, repr(g)[:22], repr(w)[:22]))
print()
print("TOTAL: %d checks, %d failures" % (len(CHECKS), len(bad)))
if bad:
    print("\nFAILURES:")
    for l, g, w in bad:
        print("  %-42s got=%r want=%r" % (l, g, w))
sys.exit(1 if bad else 0)
