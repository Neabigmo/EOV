"""M6 step S2a-quater — 拆解 Dryad 的公开下载路径。

事实：
  /api/v2/files/{id}/download            -> 401 {"error":"Unauthorized, must have current bearer token"}
  /downloads/file_stream/{id}            -> 200 text/html  = Anubis PoW 挑战页
  /api/v2/files/{id}                     -> 200 application/json (纯 metadata，可用)

目标：找出**公开、合法、可编程**的下载路径（数据是 CC0）。
本脚本只探测与解析，不判读任何 phenotype 数值。
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
SMALL = 2821543  # ME.COEFS.EFFECT.ADJ.B0.rda, 89 B


def get(url: str, accept: str = "*/*"):
    req = urllib.request.Request(url, headers={
        "Accept": accept, "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=90) as x:
            return x.status, x.read(), dict(x.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers or {})


print("### 1. full /api/v2/files/{id} metadata")
c, b, h = get("https://datadryad.org/api/v2/files/%d" % SMALL, "application/json")
print("   status", c)
if c == 200:
    print(json.dumps(json.loads(b), indent=2)[:2000])

print()
print("### 2. Anubis challenge page — full body")
c, b, h = get("https://datadryad.org/downloads/file_stream/%d" % SMALL, "text/html")
print("   status", c, "ctype", h.get("Content-Type"), "len", len(b))
print("   set-cookie:", h.get("Set-Cookie"))
txt = b.decode("utf-8", "replace")
print("   ---- body ----")
print(txt)

print()
print("### 3. other candidate public routes")
for label, u in [
    ("stash file_stream", "https://datadryad.org/stash/downloads/file_stream/%d" % SMALL),
    ("api v2 file download alt",
     "https://datadryad.org/api/v2/files/%d/download?token=" % SMALL),
    ("datadryad media", "https://datadryad.org/api/v2/files/%d/media" % SMALL),
    ("api root", "https://datadryad.org/api/v2/"),
]:
    c, b, h = get(u)
    ct = h.get("Content-Type", "")
    print("   [%s] %-24s ctype=%-30s len=%s" % (c, label, ct, len(b)))
    if c == 200 and "html" not in ct:
        print("        first:", repr(b[:200]))
