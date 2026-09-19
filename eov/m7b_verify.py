"""M7-B 独立核验器 —— 独立代码路径重算 + 报告正文数值核对 + **判据逐条对照**。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "data" / "manifests" / "M7B_GATE_RESULT.json"
CSV = ROOT / "results" / "tables" / "M7B_GATE_PAIRS.csv"
AMD = ROOT / "prereg" / "AMENDMENT-021_m7b_zero_measurement_gate.md"
REP = ROOT / "data_registry" / "M7B_REPORT.md"

F: list = []
ck = lambda l, g, w: F.append((l, g, w))


def rank(x):
    x = np.asarray(x, float)
    o = np.argsort(x, kind="mergesort")
    r = np.empty(len(x), float)
    sx = x[o]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sx[j + 1] == sx[i]:
            j += 1
        r[o[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return r


def sp(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ok = ~np.isnan(a) & ~np.isnan(b)
    if ok.sum() < 3:
        return float("nan")
    ra, rb = rank(a[ok]), rank(b[ok])
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


res = json.loads(RES.read_text(encoding="utf-8"))
d = pd.read_csv(CSV)
T = d.rho_rank.to_numpy(); S = d.S0.to_numpy()

# ---- 结构 ----
ck("n_pairs", len(d), res["n_pairs"])
ck("n_pairs == 33", len(d), 33)
ck("n_tasks", res["n_tasks"], 14)
ck("systems", sorted(d.system.unique()), res["systems"])
ck("excluded system", "Phillips2023" in res["excluded_system"], True)
ck("label exploratory", res["label"].startswith("exploratory"), True)

# ---- S0 公式独立复算（从 task 标签重算，不复用脚本函数）----
CHEM = {"AMP|AMP": 1.0, "AZT|AZT": 1.0, "AMP|AZT": 0.109756}
YRS = {"HK68": 1968, "Bk79": 1979, "Bei89": 1989, "Mos99": 1999,
       "Bris07": 2007, "NDako16": 2016}
bad = []
for r in d.itertuples():
    if r.system == "TEM-1CML":
        d1, c1 = r.A.split("@"); d2, c2 = r.B.split("@")
        c1, c2 = float(c1), float(c2)
        sc = CHEM["|".join(sorted([d1, d2]))]
        if c1 == 0 and c2 == 0:
            sk = 1.0
        elif c1 == 0 or c2 == 0:
            sk = 0.0
        else:
            sk = float(np.exp(-abs(np.log10(c1) - np.log10(c2))))
        want = sc * sk
    else:
        want = float(np.exp(-abs(YRS[r.A] - YRS[r.B]) / 10.0))
    if abs(want - r.S0) > 1e-12:
        bad.append((r.key, r.S0, want))
ck("S0 recomputed for all 33 pairs", bad, [])
ck("chem constant frozen", res["S0_constants"]["chem_tanimoto_AMP_AZT"], 0.109756)
ck("year scale frozen", res["S0_constants"]["year_scale"], 10.0)
ck("form is product", "product" in res["S0_constants"]["form"], True)
ck("n pairs with S0==0", int((S == 0).sum()), 5)

# ---- 主统计量 ----
rz = sp(S, T)
ck("rho_zero", round(rz, 6), res["rho_zero"])
ck("rho_zero value", round(rz, 4), round(0.3527, 4))

# ---- 判定逐条（核心：不能只信脚本的 if/elif）----
clo, chi = res["cluster_ci"]
p_perm = res["perm"]["p"]
low_screen = res["low_tertile_screening"]["holds"]
c_go = bool(rz >= 0.45 and clo > 0)
c_cond = bool(0.25 <= rz < 0.45 and p_perm < 0.05 and low_screen)
c_nogo = bool(rz < 0.25 or (clo < 0 < chi))
ck("condition Primary GO", c_go, False)
ck("condition Conditional GO", c_cond, False)
ck("condition NO-GO", c_nogo, True)
ck("verdict", res["verdict"], "NO-GO")
ck("verdict is NO-GO (not Conditional)", res["verdict"] == "Conditional GO", False)

# ---- CI / 置换 ----
ck("cluster CI lower", round(clo, 4), round(-0.1520, 4))
ck("cluster CI upper", round(chi, 4), round(0.6747, 4))
ck("cluster CI spans 0", bool(clo < 0 < chi), True)
ck("naive pair CI lower", round(res["naive_pair_ci"][0], 4), round(0.0457, 4))
ck("naive pair CI excludes 0", bool(res["naive_pair_ci"][0] > 0), True)
ck("perm p", round(p_perm, 5), 0.016)
ck("perm p < 0.05", bool(p_perm < 0.05), True)

# ---- 三分位（独立重算）----
q = np.quantile(S, [1 / 3, 2 / 3])
lab = np.where(S <= q[0], "low", np.where(S <= q[1], "mid", "high"))
for g in ("low", "mid", "high"):
    s = T[lab == g]
    t = res["secondaries"]["tertiles"][g]
    ck("tercile[%s].n" % g, int(len(s)), t["n"])
    ck("tercile[%s].T_median" % g, round(float(np.median(s)), 4), t["T_median"])
    ck("tercile[%s].T_mean" % g, round(float(np.mean(s)), 4), t["T_mean"])
ck("median(T|low) == overall median", round(float(np.median(T[lab == "low"])), 4),
   round(float(np.median(T)), 4))
ck("overall T median", round(float(np.median(T)), 4), 0.0407)
ck("median(T|low) > 0", bool(np.median(T[lab == "low"]) > 0), True)

# ---- 辅助 ----
ck("drop_zero_conc rho", round(res["secondaries"]["drop_zero_conc"]["rho"], 4), 0.2327)
ck("drop_zero_conc n", res["secondaries"]["drop_zero_conc"]["n"], 28)
ck("drop_zero_conc < 0.25", bool(res["secondaries"]["drop_zero_conc"]["rho"] < 0.25), True)
ck("rank-norm rho", round(res["secondaries"]["within_system_ranknorm"], 4), 0.3603)
ck("TEM-1 rho", res["secondaries"]["per_system"]["TEM-1CML"]["rho"], 0.4057)
ck("Wu2020 rho", res["secondaries"]["per_system"]["Wu2020_H3N2_siteB"]["rho"], 0.2985)

# ---- 协议未被改 ----
amd = AMD.read_text(encoding="utf-8")
for must in ["Primary GO", "Conditional GO", "NO-GO", "0.109756", "10 年 = 1 单位",
             "task-cluster bootstrap", "系统内部置换"]:
    ck("amendment contains %r" % must[:24], must in amd, True)

# ---- 报告正文手抄数字 ----
rep = REP.read_text(encoding="utf-8")
for must in ["+0.3527", "[−0.1520, +0.6747]", "p = 0.01600", "**NO-GO**",
             "+0.0407", "+0.0073", "+0.0532", "0.109756", "**+0.2327**",
             "+0.3603", "+0.4057", "+0.2985", "0.0457", "+0.6747", "9.04"]:
    ck("report contains %r" % must[:24], must in rep, True)

bad_l = [(l, g, w) for l, g, w in F if g != w]
print("=" * 78); print("M7-B VERIFICATION")
print("=" * 78)
for l, g, w in F:
    print("  %-4s %-42s got=%-20s want=%s"
          % ("OK" if g == w else "FAIL", l, repr(g)[:20], repr(w)[:20]))
print("\nTOTAL: %d checks, %d failures" % (len(F), len(bad_l)))
for l, g, w in bad_l:
    print("  FAIL %-42s got=%r want=%r" % (l, g, w))
sys.exit(1 if bad_l else 0)
