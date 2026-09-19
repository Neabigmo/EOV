"""M7 独立核验器 —— 独立代码路径重算，并核对报告正文的每个手抄数字。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NPZ = ROOT / "data" / "processed" / "M7_SPARSE.npz"
RES = ROOT / "data" / "manifests" / "M7_SPARSE_RESULT.json"
CSV = ROOT / "results" / "tables" / "M7_SPARSE_CURVE.csv"

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


d = np.load(NPZ, allow_pickle=True)
res = json.loads(RES.read_text(encoding="utf-8"))
rr = d["rho_rank"]
n = len(rr)
ck("n_pairs_used", n, res["n_pairs_used"])
ck("n_pairs_used == 36", n, 36)
ck("dropped == 0", res["dropped"], [])
ck("label is exploratory", res["label"].startswith("exploratory"), True)
ck("verdict", res["verdict"], "PASS")

# --- 主曲线独立重算 ---
for m in [4, 8, 16, 32, 64, 128]:
    st = sp(d["fbar_%d" % m], rr)
    ck("curve[%d].rho_hat" % m, round(st, 6), res["curve"][str(m)]["rho_hat"])
stf = sp(d["fbar_full"], rr)
ck("full rho_hat", round(stf, 6), round(res["full_rho_hat"], 6))
ck("m*=16 rho_hat", round(sp(d["fbar_16"], rr), 6),
   res["curve"]["16"]["rho_hat"])

# --- retention 与 full 的自洽 ---
for m in [4, 8, 16, 32, 64, 128, "full"]:
    r = res["curve"][str(m)]
    ck("retention[%s]" % m, round(r["rho_hat"] / stf, 4), r["retention"])

# --- 单次抽样分布独立重算 ---
for m in [4, 8, 16, 32, 64, 128]:
    D = d["draws_%d" % m]
    vals = np.array([sp(D[:, t], rr) for t in range(D.shape[1])])
    ck("draw_q05[%d]" % m, round(float(np.percentile(vals, 5)), 4),
       res["curve"][str(m)]["draw_q05"])
    ck("draw_median[%d]" % m, round(float(np.median(vals)), 4),
       res["curve"][str(m)]["draw_median"])
    ck("draw_q95[%d]" % m, round(float(np.percentile(vals, 95)), 4),
       res["curve"][str(m)]["draw_q95"])

# --- 三分位决策效用独立重算 ---
fb = d["fbar_16"]
q = np.quantile(fb, [1 / 3, 2 / 3])
lab = np.where(fb <= q[0], "low", np.where(fb <= q[1], "mid", "high"))
for g in ("low", "mid", "high"):
    s = rr[lab == g]
    t = res["terciles_m16"][g]
    ck("tercile[%s].n" % g, int(len(s)), t["n"])
    ck("tercile[%s].rho_median" % g, round(float(np.median(s)), 4), t["rho_median"])
    ck("tercile[%s].rho_mean" % g, round(float(np.mean(s)), 4), t["rho_mean"])
    ck("tercile[%s].rho_max" % g, round(float(np.max(s)), 4), t["rho_max"])

# --- CSV 一致 ---
cv = pd.read_csv(CSV)
ck("curve csv rows", int(len(cv)), 7)
_row16 = cv[cv["m"].astype(str) == "16"]
ck("curve csv has m=16", int(len(_row16)), 1)
ck("curve csv m*=16", float(_row16["rho_hat"].iloc[0]),
   res["curve"]["16"]["rho_hat"])

# --- AMENDMENT-020 阈值与 m* 未被改 ---
amd = (ROOT / "prereg" / "AMENDMENT-020_m7_sparse_probing.md").read_text(encoding="utf-8")
ck("amendment m*=16", "`m* = 16`" in amd, True)
ck("amendment threshold 0.45", "ρ̂(16) ≥ 0.45" in amd, True)
ck("amendment M_GRID", "`m ∈ {4, 8, 16, 32, 64, 128}`" in amd, True)

# --- 报告正文手抄数字 ---
rep = (ROOT / "data_registry" / "M7_REPORT.md").read_text(encoding="utf-8")
for must in ["+0.6659", "[+0.3406, +0.8734]", "**0.079**", "**0.401**",
             "36/36", "**PASS**", "+0.7429", "+0.4365",
             "−0.0030", "+0.0906", "0.2119"]:
    ck("report contains %r" % must[:26], must in rep, True)

bad = [(l, g, w) for l, g, w in F if g != w]
print("=" * 78); print("M7 VERIFICATION")
print("=" * 78)
for l, g, w in F:
    print("  %-4s %-38s got=%-20s want=%s"
          % ("OK" if g == w else "FAIL", l, repr(g)[:20], repr(w)[:20]))
print("\nTOTAL: %d checks, %d failures" % (len(F), len(bad)))
for l, g, w in bad:
    print("  FAIL %-38s got=%r want=%r" % (l, g, w))
sys.exit(1 if bad else 0)
