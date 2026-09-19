"""M6 step S2a — AncSR1 (Dryad 10.5061/dryad.jsxksn0hk) 下载 + 校验。

只做三件事：
  1. 走完 Dryad API v2 的全部分页，得到真实文件清单（M0 记的是 20，需核实）
  2. 逐文件下载到 data/external/AncSR1_Starr2017/raw/
  3. 用 API 给的 sha-256 校验

**不读取任何 phenotype 数值。** 本脚本只输出文件级 metadata。
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

VERSION = 272141
DOI = "10.5061/dryad.jsxksn0hk"
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "external" / "AncSR1_Starr2017" / "raw"
API = "https://datadryad.org/api/v2"


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": "eov-phase1/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def list_all_files() -> list[dict]:
    """Walk every page. Total file count is NOT assumed."""
    entries: list[dict] = []
    url = f"{API}/versions/{VERSION}/files?page=1"
    page = 0
    while url:
        page += 1
        payload = get_json(url)
        batch = payload.get("_embedded", {}).get("stash:files", [])
        entries.extend(batch)
        print(f"  page {page}: +{len(batch)}  (running total {len(entries)}, "
              f"API reports total={payload.get('total')})", flush=True)
        nxt = payload.get("_links", {}).get("next", {}).get("href")
        url = f"https://datadryad.org{nxt}" if nxt else None
        if page > 50:
            raise RuntimeError("pagination runaway")
    return entries


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)

    print("[1/3] walking Dryad API pagination ...", flush=True)
    files = list_all_files()
    # de-duplicate by file id (defensive: pages could overlap)
    by_id = {f["_links"]["self"]["href"].rsplit("/", 1)[-1]: f for f in files}
    print(f"      -> {len(files)} entries, {len(by_id)} unique file ids")

    print("[2/3] downloading + verifying ...", flush=True)
    manifest = []
    for fid, f in sorted(by_id.items(), key=lambda kv: kv[1]["path"]):
        name = f["path"]
        size = f["size"]
        want = f["digest"]
        dest = RAW / name
        if dest.exists() and dest.stat().st_size == size and sha256_of(dest) == want:
            got, status = want, "cached"
        else:
            url = f"{API}/files/{fid}/download"
            tmp = dest.with_suffix(dest.suffix + ".part")
            with urllib.request.urlopen(url, timeout=600) as r, tmp.open("wb") as out:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    out.write(chunk)
            tmp.replace(dest)
            got = sha256_of(dest)
            status = "ok" if got == want else "MISMATCH"
        manifest.append({"file_id": fid, "path": name, "bytes": size,
                         "sha256_expected": want, "sha256_actual": got,
                         "status": status})
        flag = "OK " if status in ("ok", "cached") else "!!!"
        print(f"      {flag} {name:32s} {size:>12,} B  [{status}]", flush=True)

    bad = [m for m in manifest if m["status"] not in ("ok", "cached")]
    out = ROOT / "data" / "manifests" / "M6_ANCSR1_DRYAD_FILES.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        {"doi": DOI, "version_id": VERSION, "n_files": len(manifest),
         "api_total_field": None, "files": manifest}, indent=2), encoding="utf-8")
    print(f"[3/3] manifest -> {out}")
    print(f"      {len(manifest)} files, {len(bad)} hash failures")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
