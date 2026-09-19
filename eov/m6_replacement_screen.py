"""M6 step S2e — AMENDMENT-017 §7 替代候选的**结构筛选**（不看 phenotype 值）。

唯一要回答的问题：
    候选是否 = 「组合乘积空间」+「相同蛋白背景下的 >=3 个 task」？

对每个候选只报告：行数、列名、genotype 表示、位点数、每个位点的状态数、
实际观测基因型数 vs 乘积空间大小、缺失率、task 列数。

来源：GraphFLA 整理版（仅用于**快速结构筛选**；若通过，再回原始 deposit 取数）。
"""
from __future__ import annotations

import io
import json
import urllib.request
from collections import Counter
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "external" / "GraphFLA_probe"
BASE = ("https://raw.githubusercontent.com/COLA-Laboratory/GraphFLA/"
        "main/data/BioSequence/")

CANDIDATES = {
    "Moulana": ["Moulana2022_ACE2.csv", "Moulana2023_CB6.csv",
                "Moulana2023_CoV555.csv", "Moulana2023_REGN10987.csv",
                "Moulana2023_S309.csv"],
    "Jalal2020": ["Jalal2020_NBS.csv", "Jalal2020_parS.csv"],
    "Phillips2021": ["Phillips2021_CR6261_h1.csv", "Phillips2021_CR6261_h9.csv",
                     "Phillips2021_CR9114_h1.csv", "Phillips2021_CR9114_h3.csv",
                     "Phillips2021_CR9114_fluB.csv"],
    "Wu2020": ["Wu2020_Bei89.csv", "Wu2020_Bk79.csv", "Wu2020_HK68.csv",
               "Wu2020_Mos99.csv", "Wu2020_NDako16.csv"],
    "Hall2019": ["Hall2019_Acetate.csv", "Hall2019_Beef.csv",
                 "Hall2019_Casinino.csv"],
    "Bakerlee2022": ["Bakerlee2022_hap_37C.csv", "Bakerlee2022_hap_salt.csv"],
    "Guerrero2019": ["Guerrero2019_E_coli_WT.csv",
                     "Guerrero2019_E_coli_GroEL.csv"],
    "Skwara2023": ["Skwara2023_Butyrate.csv", "Skwara2023_pyoverdine.csv"],
    "Soo2021": ["Soo2021_30C.csv", "Soo2021_37C.csv"],
    "Khan2011": ["Khan2011Flynn2013_DM25.csv",
                 "Khan2011Flynn2013_DM25_EGTA.csv"],
    "Lozovsky": ["Lozovsky_DHFR_ic50_c57.csv", "Lozovsky_DHFR_ic50_c61.csv"],
}


def fetch(name: str) -> bytes:
    DEST.mkdir(parents=True, exist_ok=True)
    p = DEST / name
    if p.exists():
        return p.read_bytes()
    url = BASE + urllib.parse.quote(name)
    req = urllib.request.Request(url, headers={"User-Agent": "eov-phase1/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        b = r.read()
    p.write_bytes(b)
    return b


def screen(name: str, raw: bytes) -> dict:
    import pandas as pd
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as e:
        return {"file": name, "error": "%s: %s" % (type(e).__name__, e)}
    out = {"file": name, "n_rows": int(len(df)), "columns": [str(c) for c in df.columns]}
    seqcol = None
    for c in df.columns:
        cs = df[c].astype(str)
        head = cs.head(20).tolist()
        if all(len(x) >= 3 and x.isalpha() for x in head) and cs.nunique() > 2:
            w = Counter(len(x) for x in cs.head(2000))
            if len(w) <= 2:
                seqcol = c
                break
    if seqcol is None:
        out["genotype_column"] = None
        out["verdict"] = "no sequence column detected"
        return out
    s = df[seqcol].astype(str)
    widths = Counter(len(x) for x in s)
    width = widths.most_common(1)[0][0]
    out["genotype_column"] = seqcol
    out["genotype_width"] = width
    out["n_unique_genotypes"] = int(s.nunique())
    sub = s[s.str.len() == width]
    states = [sorted(set(sub.str[i])) for i in range(width)]
    out["n_sites"] = width
    out["states_per_site"] = [len(x) for x in states]
    prod_size = 1
    for k in out["states_per_site"]:
        prod_size *= k
    out["product_space_size"] = int(prod_size)
    out["coverage_of_product"] = (out["n_unique_genotypes"] / prod_size
                                  if prod_size else None)
    out["is_complete_product"] = bool(out["n_unique_genotypes"] == prod_size)
    out["mean_degree_if_complete"] = int(sum(k - 1 for k in out["states_per_site"]))
    out["numeric_cols"] = [str(c) for c in df.columns
                           if c != seqcol and str(df[c].dtype).startswith("float")
                           or str(df[c].dtype).startswith("int")]
    out["n_numeric_cols"] = len(out["numeric_cols"])
    out["na_frac_mean"] = float(df.isna().mean().mean())
    return out


def main() -> int:
    import urllib.parse  # noqa: F401  (used inside fetch)
    globals()["urllib"].parse = urllib.parse
    rows = []
    for grp, files in CANDIDATES.items():
        print("=" * 78)
        print("GROUP:", grp)
        print("=" * 78)
        for f in files:
            try:
                raw = fetch(f)
            except Exception as e:
                print("  %-42s FETCH ERR %s" % (f, e))
                rows.append({"file": f, "error": str(e)})
                continue
            r = screen(f, raw)
            rows.append(r)
            if "error" in r and "verdict" not in r:
                print("  %-42s %s" % (f, r["error"]))
                continue
            print("  %-42s rows=%-8s sites=%-3s states=%-16s prod=%-10s "
                  "obs=%-8s complete=%-5s deg=%-4s numcols=%s"
                  % (f, r.get("n_rows"), r.get("n_sites"),
                     r.get("states_per_site"), r.get("product_space_size"),
                     r.get("n_unique_genotypes"), r.get("is_complete_product"),
                     r.get("mean_degree_if_complete"), r.get("n_numeric_cols")))
            if r.get("error"):
                print("        note:", r["error"])
    out = ROOT / "data" / "manifests" / "M6_REPLACEMENT_SCREEN.json"
    out.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    print("\n-> %s" % out)
    return 0


if __name__ == "__main__":
    import urllib.parse
    raise SystemExit(main())
