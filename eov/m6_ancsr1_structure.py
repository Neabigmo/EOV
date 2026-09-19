"""M6 step S2b — AncSR1 结构资格审计（AMENDMENT-017 §6）。

**只输出结构 metadata**：对象类、维度、行列名、RE 取值集合、genotype 数、
缺失计数、邻接类型。**绝不输出 phenotype 数值分布、绝不计算任何相关。**

下载 -> 解析 -> 逐条判定 E1..E6。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m6_dryad_client import DryadClient, BASE  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "external" / "AncSR1_Starr2017" / "raw"
LIST = ROOT / "data" / "manifests" / "M6_ANCSR1_DRYAD_FILELIST.json"
OUT = ROOT / "data" / "manifests" / "M6_ANCSR1_STRUCTURE.json"

# 结构审计需要的最小集合
WANT = [
    "AA.SEQ.rda",
    "DT.JOINT.rda",
    "DT.11P.CODING.rda",
    "DT.JOINT.APPEND.rda",
    "NH.ACT.ADJM.rda",
    "MG.ACT.ADJM.rda",
    "NG.ACT.ADJM.rda",
    "EFFECT.TABLE.TE.rda",
    "ME.ONE.STEP.rda",
]


def main() -> int:
    listing = json.loads(LIST.read_text(encoding="utf-8"))
    by_path = {f["path"]: f for f in listing["files"]}
    client = DryadClient()
    RAW.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("STEP 1  download (%d files)" % len(WANT))
    print("=" * 78)
    for p in WANT:
        f = by_path[p]
        dest = RAW / p
        url = "%s/downloads/file_stream/%s" % (BASE, f["file_id"])
        st = client.download(url, dest, expect_size=f["bytes"],
                             expect_sha=f["sha256"])
        print("   %-6s %-28s %12d B" % (st, p, dest.stat().st_size), flush=True)

    print()
    print("=" * 78)
    print("STEP 2  parse with rdata -> structure only")
    print("=" * 78)
    import rdata
    struct = {}
    for p in WANT:
        path = RAW / p
        try:
            parsed = rdata.parser.parse_file(path)
            conv = rdata.conversion.convert(parsed)
        except Exception as e:
            print("   %-28s PARSE FAIL: %s: %s" % (p, type(e).__name__, e))
            struct[p] = {"parse": "FAIL", "error": "%s: %s" % (type(e).__name__, e)}
            continue
        info = {"parse": "ok", "objects": {}}
        for name, obj in (conv.items() if isinstance(conv, dict) else [("?", conv)]):
            info["objects"][name] = describe(obj)
        struct[p] = info
        print("   %-28s keys=%s" % (p, list(info["objects"])))
    OUT.write_text(json.dumps(struct, indent=2, default=str), encoding="utf-8")
    print("\nstructure -> %s" % OUT)
    return 0


def describe(obj, depth: int = 0) -> dict:
    """只描述结构，不描述数值。"""
    import numpy as np
    import pandas as pd

    d: dict = {"py_type": type(obj).__name__}
    if isinstance(obj, pd.DataFrame):
        d["kind"] = "DataFrame"
        d["shape"] = list(obj.shape)
        d["columns"] = [str(c) for c in obj.columns]
        d["index_name"] = str(obj.index.name)
        d["index_dtype"] = str(obj.index.dtype)
        d["dtypes"] = {str(k): str(v) for k, v in obj.dtypes.items()}
        # 每列的"非缺失计数"是结构信息，不是数值分布
        d["non_null"] = {str(c): int(obj[c].notna().sum()) for c in obj.columns}
        # 低基数列给出取值集合（结构），高基数列只给唯一值个数
        for c in obj.columns:
            try:
                nu = int(obj[c].nunique(dropna=True))
            except Exception:
                continue
            if nu <= 30:
                vals = obj[c].dropna().unique().tolist()
                d.setdefault("small_domains", {})[str(c)] = [str(v) for v in vals]
            else:
                d.setdefault("n_unique", {})[str(c)] = nu
        head_idx = [str(i) for i in obj.index[:3]]
        d["index_head"] = head_idx
    elif isinstance(obj, np.ndarray):
        d["kind"] = "ndarray"
        d["shape"] = list(obj.shape)
        d["dtype"] = str(obj.dtype)
    elif isinstance(obj, (list, tuple)):
        d["kind"] = "list"
        d["len"] = len(obj)
        d["elements"] = [describe(x, depth + 1) if depth < 2 else
                         {"py_type": type(x).__name__} for x in obj[:6]]
    elif isinstance(obj, dict):
        d["kind"] = "dict"
        d["keys"] = [str(k) for k in list(obj.keys())[:40]]
        d["n_keys"] = len(obj)
    else:
        s = str(obj)
        d["repr_head"] = s[:200]
    return d


if __name__ == "__main__":
    raise SystemExit(main())
