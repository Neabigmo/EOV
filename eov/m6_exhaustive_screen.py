"""M6 step S2h — 穷尽结构筛选：**是否存在**任何合格的 M6 确认候选？

对 GraphFLA `data/BioSequence` 的**全部**文件做结构筛选，按组（前缀）汇总：
  组内任务数 / 是否完整乘积空间 / 空间大小 / OP-21 可用预算档 /
  各任务缺失率 / 过 OP-18(<=25%) 的任务数 -> 可用 pair 数

判定"合格"= 过 OP-18 的任务数 >= 4（=> C(4,2)=6 >= ? 见下）且 OP-21 档 >= 2。

注意：AMENDMENT-017 §6 的 E2 要求 **>=10 对**，即需 **>=5 个任务全部过 OP-18**。
本脚本如实报告每组能达到多少对，不放松阈值。

来源=GraphFLA 整理版，仅用于**结构筛选**；合格者须回原始 deposit 取数。
"""
from __future__ import annotations

import io
import json
import re
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "external" / "GraphFLA_probe" / "_all"
BASE = ("https://raw.githubusercontent.com/COLA-Laboratory/GraphFLA/"
        "main/data/BioSequence/")
TM = ROOT / "data" / "external" / "GraphFLA"


def names() -> list[str]:
    import subprocess
    out = subprocess.run(["git", "ls-tree", "-r", "--name-only",
                          "HEAD"], cwd=str(TM), capture_output=True, text=True)
    return [l.replace("data/BioSequence/", "") for l in out.stdout.splitlines()
            if l.startswith("data/BioSequence/") and l.endswith(".csv")]


def fetch(name: str) -> bytes | None:
    DEST.mkdir(parents=True, exist_ok=True)
    p = DEST / name
    if p.exists():
        return p.read_bytes()
    try:
        req = urllib.request.Request(BASE + urllib.parse.quote(name),
                                     headers={"User-Agent": "eov-phase1/1.0"})
        with urllib.request.urlopen(req, timeout=180) as r:
            b = r.read()
        p.write_bytes(b)
        return b
    except Exception:
        return None


def screen(name: str, raw: bytes) -> dict:
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as e:
        return {"file": name, "err": str(e)[:60]}
    pcols = [c for c in df.columns if re.fullmatch(r"pos\d+", str(c))]
    valcol = None
    for c in df.columns:
        if c not in pcols and str(df[c].dtype).startswith("float"):
            valcol = c
            break
    r = {"file": name, "rows": int(len(df)), "n_pos": len(pcols),
         "value_col": valcol}
    if not pcols or valcol is None:
        r["complete"] = None
        return r
    dom = [sorted(df[c].dropna().unique().tolist()) for c in pcols]
    prod = 1
    for d in dom:
        prod *= len(d)
    r["prod"] = int(prod)
    r["states"] = [len(d) for d in dom]
    r["n_unique_seq"] = int(df["sequences"].nunique()) if "sequences" in df else None
    r["complete"] = bool(df["sequences"].nunique() == prod) if "sequences" in df else None
    r["deg"] = int(sum(len(d) - 1 for d in dom))
    r["na"] = float(df[valcol].isna().mean())
    r["n_obs"] = int(df[valcol].notna().sum())
    r["op21_tiers"] = [b for b in (24, 96, 384) if b <= prod // 4]
    return r


def main() -> int:
    ns = names()
    print("total CSVs:", len(ns))
    groups: dict[str, list[str]] = defaultdict(list)
    for n in ns:
        key = re.split(r"[_]", n)[0]
        groups[key].append(n)

    rows = []
    for n in ns:
        raw = fetch(n)
        if raw is None:
            rows.append({"file": n, "err": "fetch"})
            continue
        rows.append(screen(n, raw))
    by = {r["file"]: r for r in rows}

    print()
    print("=" * 100)
    print("GROUPS with >= 3 files")
    print("=" * 100)
    print("%-24s %5s %6s %8s %10s %6s %-18s %8s %6s %6s"
          % ("group", "files", "n_pos", "prod", "complete", "deg", "OP21tiers",
             "n_ok25", "pairs", "verdict"))

    summary = []
    for g, fs in sorted(groups.items()):
        if len(fs) < 3:
            continue
        good = [by[f] for f in fs if by.get(f) and by[f].get("complete")]
        prod = good[0]["prod"] if good else None
        npos = good[0]["n_pos"] if good else None
        deg = good[0]["deg"] if good else None
        tiers = good[0]["op21_tiers"] if good else []
        same_space = bool(good) and all(x["prod"] == prod and x["n_pos"] == npos
                                        for x in good)
        ok = [x for x in good if x["na"] <= 0.25]
        n_ok = len(ok) if same_space else 0
        pairs = n_ok * (n_ok - 1) // 2
        verdict = ("ELIGIBLE" if pairs >= 10 and len(tiers) >= 2 else
                   ("%d pairs < 10" % pairs if pairs else "no"))
        print("%-24s %5d %6s %8s %10s %6s %-18s %8d %6d %6s"
              % (g, len(fs), npos, prod, same_space, deg, str(tiers),
                 n_ok, pairs, verdict))
        summary.append({"group": g, "n_files": len(fs), "n_pos": npos,
                        "prod": prod, "same_space": same_space, "deg": deg,
                        "op21_tiers": tiers, "tasks_passing_op18": n_ok,
                        "pairs": pairs, "verdict": verdict,
                        "tasks": [{"f": x["file"], "na": round(x["na"], 4)}
                                  for x in good]})

    print()
    print("=" * 100)
    print("ANY GROUP WITH >=10 PAIRS AND >=2 OP-21 TIERS ?")
    print("=" * 100)
    elig = [s for s in summary if s["verdict"] == "ELIGIBLE"]
    print("  eligible groups:", [s["group"] for s in elig] or "NONE")

    out = ROOT / "data" / "manifests" / "M6_EXHAUSTIVE_REPLACEMENT_SCREEN.json"
    out.write_text(json.dumps({"rows": rows, "groups": summary,
                               "eligible": [s["group"] for s in elig]},
                              indent=2, default=str), encoding="utf-8")
    print("-> %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
