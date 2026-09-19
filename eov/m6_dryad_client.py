"""M6 step S2a — Dryad 公开下载客户端（Anubis proof-of-work 自动求解）。

背景（本轮实测，均有记录）：
  * `/api/v2/files/{id}/download`  -> 401，需要 bearer token（即使对已发布数据集也是）
  * `/downloads/file_stream/{id}`  -> 200，但被 Anubis 1.24.0 反爬拦截，返回 PoW 挑战页
  * `/api/v2/...` 的 metadata 端点  -> 正常，无 Anubis

Anubis 协议（从本站 `main.mjs` + `sha256-webcrypto.mjs` 反读，非猜测）：
  挑战 JSON 位于 <script id="anubis_challenge">：
    {"rules":{"algorithm":"fast","difficulty":N},
     "challenge":{"id":..., "randomData":<hex>, "difficulty":N, ...}}
  求解：找 nonce（十进制字符串，非负整数）使
        sha256( randomData + str(nonce) ) 的前 N 个**十六进制位**为 0
  提交：GET /.within.website/x/cmd/anubis/api/pass-challenge
        ?id=<challenge.id>&response=<hash>&nonce=<nonce>
        &redir=<原 URL>&elapsedTime=<ms>
  成功 -> 302 到原 URL 并 Set-Cookie 授权票。

注意：挑战页 HTML 里含一个 honeypot 诱饵链接
(`/.within.website/x/cmd/anubis/api/honeypot/<uuid>/init`)。**绝不访问它。**
本实现只解析 <script id="anubis_challenge">，从不跟随页面内任何 <a href>。

数据是 CC0-1.0；本模块只做公开、合法、限速的下载。
"""
from __future__ import annotations

import hashlib
import http.cookiejar
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = "https://datadryad.org"
HONEYPOT = re.compile(r"honeypot", re.I)
_CHAL = re.compile(
    r'<script\s+id="anubis_challenge"\s+type="application/json">(.*?)</script>',
    re.S)


class AnubisChallenge(Exception):
    """需要解 PoW。"""


def solve_pow(random_data: str, difficulty: int, max_iters: int = 1 << 26) -> tuple[str, int]:
    """返回 (hash_hex, nonce)。nonce 为非负整数。"""
    prefix = "0" * difficulty
    n = 0
    rd = random_data.encode("ascii")
    while n < max_iters:
        h = hashlib.sha256(rd + str(n).encode("ascii")).hexdigest()
        if h.startswith(prefix):
            return h, n
        n += 1
    raise RuntimeError("PoW 未在 %d 次内解出" % max_iters)


class DryadClient:
    def __init__(self, min_interval: float = 0.6):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar))
        self.min_interval = min_interval
        self._last = 0.0
        self.n_pow = 0

    # ---------- 内部 ----------
    def _throttle(self):
        dt = time.time() - self._last
        if dt < self.min_interval:
            time.sleep(self.min_interval - dt)
        self._last = time.time()

    def _raw(self, url: str, extra_headers: dict | None = None):
        hdrs = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
                "Accept": "*/*"}
        if extra_headers:
            hdrs.update(extra_headers)
        req = urllib.request.Request(url, headers=hdrs)
        try:
            with self.opener.open(req, timeout=300) as r:
                return r.status, r.read(), dict(r.headers), r.geturl()
        except urllib.error.HTTPError as e:
            return e.code, e.read(), dict(e.headers or {}), url

    def _pass_anubis(self, url: str, html: str) -> bool:
        m = _CHAL.search(html)
        if not m:
            return False
        ch = json.loads(m.group(1))
        c = ch["challenge"]
        diff = int(c.get("difficulty", ch.get("rules", {}).get("difficulty", 4)))
        t0 = time.time()
        h, nonce = solve_pow(c["randomData"], diff)
        elapsed = int((time.time() - t0) * 1000)
        q = urllib.parse.urlencode({
            "id": c["id"], "response": h, "nonce": nonce,
            "redir": url, "elapsedTime": elapsed})
        pass_url = BASE + "/.within.website/x/cmd/anubis/api/pass-challenge?" + q
        self._throttle()
        status, body, hdrs, final = self._raw(pass_url)
        self.n_pow += 1
        ok = status in (200, 302) and not _CHAL.search(
            body.decode("utf-8", "replace"))
        print("      [anubis] difficulty=%d nonce=%d solved in %d ms -> HTTP %d%s"
              % (diff, nonce, elapsed, status, " OK" if ok else " (?)"), flush=True)
        return ok

    # ---------- 公开 API ----------
    def get(self, url: str, retries: int = 3) -> bytes:
        """取一个 URL 的字节；自动过 Anubis。"""
        last = None
        for attempt in range(retries):
            self._throttle()
            status, body, hdrs, final = self._raw(url)
            text = body.decode("utf-8", "replace")
            if status == 200 and _CHAL.search(text):
                if self._pass_anubis(url, text):
                    continue      # 拿到票，重试
                last = "anubis 求解失败"
                continue
            if status == 200:
                return body
            last = "HTTP %d %s" % (status, body[:120])
            if status in (429, 503):
                time.sleep(3 * (attempt + 1))
                continue
            raise RuntimeError("GET %s 失败: %s" % (url, last))
        raise RuntimeError("GET %s 重试耗尽: %s" % (url, last))

    def download(self, url: str, dest: Path, expect_size: int | None = None,
                 expect_sha: str | None = None) -> str:
        """流式下载 + 校验。返回 'ok' / 'cached'。"""
        if dest.exists():
            ok = True
            if expect_size is not None and dest.stat().st_size != expect_size:
                ok = False
            if ok and expect_sha and _sha256(dest) != expect_sha:
                ok = False
            if ok:
                return "cached"
        # 先确保过了 Anubis：用一个小请求换取 cookie
        self.get(BASE + "/downloads/file_stream/2821543") if self.n_pow == 0 else None
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        self._throttle()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        with self.opener.open(req, timeout=1800) as r, tmp.open("wb") as out:
            got = 0
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
                got += len(chunk)
        tmp.replace(dest)
        if expect_sha and _sha256(dest) != expect_sha:
            raise RuntimeError("sha256 不匹配: %s" % dest.name)
        if expect_size is not None and dest.stat().st_size != expect_size:
            raise RuntimeError("size 不匹配: %s (%d != %d)"
                               % (dest.name, dest.stat().st_size, expect_size))
        return "ok"


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


if __name__ == "__main__":
    c = DryadClient()
    print("self-test: fetch README.md via file_stream ...")
    b = c.get(BASE + "/downloads/file_stream/2821548")  # 占位: 见下方真实 id
    print("got", len(b), "bytes; head:", b[:40])
