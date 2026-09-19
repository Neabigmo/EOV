"""M6 step S2a-bis — 取全 184 个文件的清单（仅文件名/大小/摘要），并探明下载端点。

M0 的审计基于 Dryad API 第 1 页 -> 只看到 20 个文件。实际 184 个。
本脚本把完整清单落盘，并探测可用的下载 URL 形式。

**不下载、不读取任何 phenotype 数值；只处理文件级 metadata。**
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

VERSION = 272141
ROOT = Path(__file__).resolve().parents[1]
API = "https://datadryad.org/api/v2"
OUT = ROOT / "data" / "manifests" / "M6_ANCSR1_DRYAD_FILELIST.json"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def get(url: str, accept: str = "application/json") -> tuple[int, bytes, dict]:
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:400], dict(e.headers or {})


def main() -> int:
    entries: list[dict] = []
    url = f"{API}/versions/{VERSION}/files?page=1"
    while url:
        code, body, _ = get(url)
        if code != 200:
            raise RuntimeError(f"listing page failed: {code}")
        payload = json.loads(body.decode("utf-8"))
        entries.extend(payload.get("_embedded", {}).get("stash:files", []))
        nxt = payload.get("_links", {}).get("next", {}).get("href")
        url = f"https://datadryad.org{nxt}" if nxt else None

    rows = []
    for f in entries:
        fid = f["_links"]["self"]["href"].rsplit("/", 1)[-1]
        rows.append({"file_id": fid, "path": f["path"], "bytes": f["size"],
                     "sha256": f["digest"], "status": f.get("status")})
    rows.sort(key=lambda r: r["path"])

    # ---- 结构画像：扩展名分布 / 目录层级（只有文件名） ----
    from collections import Counter
    ext = Counter(Path(r["path"]).suffix.lower() for r in rows)
    top = Counter(r["path"].split("/")[0] if "/" in r["path"] else "<root>"
                  for r in rows)
    total_bytes = sum(r["bytes"] for r in rows)

    report = {
        "doi": "10.5061/dryad.jsxksn0hk",
        "version_id": VERSION,
        "n_files": len(rows),
        "total_bytes": total_bytes,
        "extension_histogram": dict(ext.most_common()),
        "toplevel_histogram": dict(top.most_common()),
        "files": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"files={len(rows)}  total={total_bytes/1e6:.1f} MB")
    print("extensions:", dict(ext.most_common()))
    print("top-level :", dict(top.most_common()))
    print(f"manifest -> {OUT}\n")

    print("--- all 184 paths (sorted) ---")
    for r in rows:
        print(f"  {r['bytes']:>12,}  {r['path']}")

    # ---- 探测下载端点 ----
    probe = rows[0]["file_id"]
    print("\n--- download endpoint probe ---")
    for label, u in [
        ("api /files/{id}/download", f"{API}/files/{probe}/download"),
        ("web /downloads/file_stream/{id}",
         f"https://datadryad.org/downloads/file_stream/{probe}"),
        ("api /files/{id}", f"{API}/files/{probe}"),
    ]:
        req = urllib.request.Request(u, headers={"User-Agent": UA}, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                head = r.read(64)
                print(f"  [200] {label}  ctype={r.headers.get('Content-Type')} "
                      f"len={r.headers.get('Content-Length')} first={head[:16]!r}")
        except urllib.error.HTTPError as e:
            print(f"  [{e.code}] {label}  {e.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
