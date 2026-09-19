"""M6 step S2a-ter — 决定性对照 + 备用数据入口探测。

问题：AncSR1 的 Dryad deposit（jsxksn0hk, versionStatus=submitted）返回
      401 "must have current bearer token"。
必须排除"这是 Dryad API 的通用行为"，即用**已发布**数据集做对照。

同时探测代码仓库是否含数据副本。

**不读取任何 phenotype 数值。**
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def get(url: str, accept: str = "application/json"):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=90) as x:
            return x.status, x.read(), dict(x.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300], dict(e.headers or {})


print("=" * 78)
print("CONTROL: Bank2016 Hsp90  doi:10.5061/dryad.th0rj  (a PUBLISHED Dryad dataset)")
print("=" * 78)
c, b, _ = get("https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.th0rj")
print("dataset metadata status:", c)
if c == 200:
    j = json.loads(b)
    print("  versionStatus :", j.get("versionStatus"))
    print("  versionNumber :", j.get("versionNumber"))
    vl = j["_links"]["stash:version"]["href"]
    c2, b2, _ = get("https://datadryad.org" + vl + "/files?page=1")
    j2 = json.loads(b2)
    fl = j2["_embedded"]["stash:files"]
    print("  n files (page1):", len(fl), " api total:", j2.get("total"))
    f0 = fl[0]
    fid = f0["_links"]["self"]["href"].rsplit("/", 1)[-1]
    print("  probe file     :", fid, f0["path"], f0["size"], "B")
    c3, b3, h3 = get("https://datadryad.org/api/v2/files/%s/download" % fid,
                     accept="*/*")
    print("  download       : [%s] ctype=%s clen=%s" % (
        c3, h3.get("Content-Type"), h3.get("Content-Length")))
    print("  first bytes    :", repr(b3[:60]))

print()
print("=" * 78)
print("SECOND DEPOSIT  doi:10.5061/dryad.18931zd7m")
print("=" * 78)
c, b, _ = get("https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.18931zd7m")
if c == 200:
    j = json.loads(b)
    print("  title         :", j.get("title"))
    print("  versionStatus :", j.get("versionStatus"), " number:", j.get("versionNumber"))
    print("  license       :", j.get("license"))
    print("  authors       :", ", ".join(
        "%s %s" % (a.get("firstName"), a.get("lastName")) for a in j.get("authors", [])))
    vl = j["_links"]["stash:version"]["href"]
    c2, b2, _ = get("https://datadryad.org" + vl + "/files?page=1")
    j2 = json.loads(b2)
    print("  n files       :", j2.get("count"), " of total", j2.get("total"))
    for f in j2["_embedded"]["stash:files"]:
        print("     %12s  %s" % (f["size"], f["path"]))
else:
    print("  ERR", c, b[:200])

print()
print("=" * 78)
print("GITHUB: JoeThorntonLab/DBD.GeneticArchitecture")
print("=" * 78)
c, b, _ = get("https://api.github.com/repos/JoeThorntonLab/DBD.GeneticArchitecture")
print("repo status:", c)
if c == 200:
    j = json.loads(b)
    print("  default_branch:", j.get("default_branch"), " size(KB):", j.get("size"),
          " pushed:", j.get("pushed_at"))
c, b, _ = get("https://api.github.com/repos/JoeThorntonLab/DBD.GeneticArchitecture/"
              "git/trees/HEAD?recursive=1")
print("tree status:", c)
if c == 200:
    j = json.loads(b)
    print("  truncated:", j.get("truncated"), " entries:", len(j.get("tree", [])))
    for e in j.get("tree", []):
        if e["type"] == "blob":
            print("   %12s  %s" % (e.get("size", 0), e["path"]))
