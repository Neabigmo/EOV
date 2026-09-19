#!/usr/bin/env python
"""Build the four paper figures from the shipped result tables.

    python figures/make_figures.py [--outdir figures/out]

Requires matplotlib (not a core dependency).  If it is missing the script still
writes the per-panel source CSVs into the output directory, so the numbers behind
every panel stay inspectable.

Fig. 1  Future value is not present value   -> conceptual, no data (see README)
Fig. 2  Starting-point value is budget-stable
Fig. 3  Starting-point value collapses across tasks
Fig. 4  The boundary is predictable
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "results" / "tables"
M = ROOT / "data" / "manifests"


def _sp(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = ~np.isnan(a) & ~np.isnan(b)
    if ok.sum() < 3:
        return float("nan")
    ra = pd.Series(a[ok]).rank().to_numpy()
    rb = pd.Series(b[ok]).rank().to_numpy()
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def load():
    d = {}
    for k, p in [("m4_rho", T / "M4_INVARIANT5_EXP1_RHO.csv"),
                 ("m5_map", T / "M5_TRANSFER_MAP.csv"),
                 ("m5_clean", T / "M5_FEATURE_VS_TRANSFER_CLEAN.csv"),
                 ("m6_map", T / "M6_WU2020_TRANSFER_MAP.csv"),
                 ("m7_curve", T / "M7_SPARSE_CURVE.csv"),
                 ("m7b_pairs", T / "M7B_GATE_PAIRS.csv")]:
        d[k] = pd.read_csv(p) if p.exists() else None
    d["m6"] = (json.loads((M / "M6_WU2020_RESULT.json").read_text(encoding="utf-8"))
               if (M / "M6_WU2020_RESULT.json").exists() else None)
    d["m7b"] = (json.loads((M / "M7B_GATE_RESULT.json").read_text(encoding="utf-8"))
                if (M / "M7B_GATE_RESULT.json").exists() else None)
    return d


def fig2(d, out):
    """Cross-budget stability of the starting-point ranking."""
    r = d["m4_rho"]
    if r is None:
        return None
    csv = out / "fig2_budget_stability.csv"
    r.to_csv(csv, index=False)
    return csv


def fig3(d, out):
    """Pair-level transfer across tasks, discovery and confirmation."""
    rows = []
    m5 = d["m5_map"]
    if m5 is not None:
        g = m5.groupby(["dataset", "task_A", "task_B"], as_index=False)["rho_rank"].mean()
        for x in g.itertuples():
            rows.append(dict(source="M5 discovery", dataset=x.dataset,
                             pair="%s~%s" % (x.task_A, x.task_B), rho=x.rho_rank))
    if d["m6"] is not None:
        for k, v in d["m6"]["rho_pair_level"].items():
            rows.append(dict(source="M6 confirmation", dataset="Wu2020",
                             pair=k, rho=v))
    df = pd.DataFrame(rows)
    csv = out / "fig3_transfer_collapse.csv"
    df.to_csv(csv, index=False)
    return csv


def fig4(d, out):
    """The boundary is predictable: discovery vs confirmation, plus M7/M7-B."""
    rows = []
    c = d["m5_clean"]
    if c is not None:
        f = c[c.feature == "f1_landscape_rho"]
        for x in f.itertuples():
            rows.append(dict(panel="discovery", subset=x.subset, n=x.n_used,
                             spearman=x.spearman))
    if d["m6"] is not None:
        rows.append(dict(panel="confirmation", subset="Wu2020 15 pairs",
                         n=d["m6"]["n_pairs"],
                         spearman=d["m6"]["spearman_f1_vs_rho"]))
    df = pd.DataFrame(rows)
    df.to_csv(out / "fig4_boundary.csv", index=False)
    extra = {}
    if d["m7_curve"] is not None:
        d["m7_curve"].to_csv(out / "fig4_m7_curve.csv", index=False)
        extra["m7_m16"] = float(
            d["m7_curve"][d["m7_curve"]["m"].astype(str) == "16"]["rho_hat"].iloc[0])
    if d["m7b"] is not None:
        extra["m7b_rho_zero"] = d["m7b"]["rho_zero"]
        extra["m7b_cluster_ci"] = d["m7b"]["cluster_ci"]
        extra["m7b_verdict"] = d["m7b"]["verdict"]
    (out / "fig4_extras.json").write_text(json.dumps(extra, indent=2),
                                          encoding="utf-8")
    return out / "fig4_boundary.csv"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="figures/out")
    a = ap.parse_args()
    out = (ROOT / a.outdir) if not Path(a.outdir).is_absolute() else Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    d = load()

    print("=" * 70)
    print("Panels sourced from the shipped result tables")
    print("=" * 70)
    for name, fn in (("Fig.2 budget-stable", fig2),
                     ("Fig.3 transfer collapses", fig3),
                     ("Fig.4 boundary predictable", fig4)):
        p = fn(d, out)
        print("  %-28s -> %s" % (name, p.name if p else "SOURCE MISSING"))
    print("\n  Fig.1 is conceptual (no data); see README.md.")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        print("\n  matplotlib unavailable (%s) — wrote source CSVs only." % e)
        return 0

    # Fig.3 — the headline panel
    df = pd.read_csv(out / "fig3_transfer_collapse.csv")
    if len(df):
        fig, ax = plt.subplots(figsize=(7.2, 3.6))
        for i, (src, g) in enumerate(df.groupby("source")):
            ax.scatter(np.full(len(g), i) + np.linspace(-.08, .08, len(g)),
                       g.rho, s=26, alpha=.8, label="%s (n=%d)" % (src, len(g)))
            med = float(g.rho.median())
            ax.hlines(med, i - .22, i + .22, color="k", lw=2)
            ax.annotate("median %.4f" % med, (i + .24, med), va="center", fontsize=8)
        ax.axhline(0, color="grey", lw=.8, ls="--")
        ax.set_xticks(range(df.source.nunique()))
        ax.set_xticklabels(sorted(df.source.unique()))
        ax.set_ylabel(r"pair-level $\rho_{\rm rank}$  (transfer)")
        ax.set_title("Starting-point value collapses across tasks")
        fig.tight_layout()
        fig.savefig(out / "fig3_transfer_collapse.png", dpi=200)
        plt.close(fig)
        print("  wrote fig3_transfer_collapse.png")

    # Fig.4 — the boundary
    b = pd.read_csv(out / "fig4_boundary.csv")
    if len(b):
        fig, ax = plt.subplots(figsize=(6.4, 3.6))
        sub = b.dropna(subset=["spearman"])
        ax.barh(range(len(sub)), sub.spearman)
        ax.set_yticks(range(len(sub)))
        ax.set_yticklabels(["%s  (n=%d)" % (r.subset, r.n)
                            for r in sub.itertuples()], fontsize=8)
        ax.axvline(0.45, color="r", ls="--", lw=1)
        ax.annotate("frozen threshold 0.45", (0.45, -0.6), color="r", fontsize=8)
        ax.set_xlabel(r"Spearman($f_1$, pair-level $\rho_{\rm rank}$)")
        ax.set_title("The boundary is predictable")
        fig.tight_layout()
        fig.savefig(out / "fig4_boundary.png", dpi=200)
        plt.close(fig)
        print("  wrote fig4_boundary.png")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
