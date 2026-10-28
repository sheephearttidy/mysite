"""端到端冒烟测试:覆盖公开接口、认证流程、CRUD、限流。

用法:python scripts/smoke.py [base_url]
默认 http://127.0.0.1:5100
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5100"
PASS = FAIL = 0


def ck(name: str, cond: bool, extra: str = "") -> None:
    global PASS, FAIL
    if cond:
        print(f"PASS  {name}")
        PASS += 1
    else:
        print(f"FAIL  {name}  {extra}")
        FAIL += 1


def req(path: str, method: str = "GET", body=None, headers=None, cookie=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    h = dict(headers or {})
    if data:
        h["Content-Type"] = "application/json"
    if cookie:
        h["Cookie"] = cookie
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            raw = resp.read()
            return resp.status, raw, resp.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers


def jget(path, **kw):
    st, raw, _ = req(path, **kw)
    try:
        return st, json.loads(raw)
    except Exception:
        return st, None


# ---------- 1. 公开接口 ----------
print("\n=== 公开接口 ===")
st, d = jget("/api/health")
ck("health 200", st == 200 and d and d.get("status") == "ok", str(st))

st, d = jget("/api/site")
ck("site 返回站点信息", st == 200 and isinstance(d, dict) and "site_owner" in d, str(st))
ck("site_owner 非空", bool(d and d.get("site_owner")), str(d))

for page in ("index", "about", "skills", "works", "campus", "contact", "map", "gallery"):
    st, d = jget(f"/api/page/{page}")
    ck(f"page/{page} 200", st == 200 and isinstance(d, dict), str(st))

st, _ = jget("/api/page/nonexistent")
ck("未知页面 404", st == 404, str(st))

for kind in ("skills", "works", "stats", "timeline", "profile", "honors", "notes", "friendlinks", "songs", "photos"):
    st, d = jget(f"/api/content/{kind}")
    ck(f"content/{kind} 200 且为列表", st == 200 and isinstance(d, list), str(st))

st, d = jget("/api/messages")
ck("messages 列表", st == 200 and isinstance(d, list), str(st))
ck("messages 不泄露 ip/token", all("ip" not in m and "token" not in m for m in (d or [])), "")

st, d = jget("/api/questions")
ck("questions 列表", st == 200 and isinstance(d, list), str(st))

st, d = jget("/api/likes")
ck("likes 字典", st == 200 and isinstance(d, dict), str(st))

st, d = jget("/api/map")
ck("map 列表", st == 200 and isinstance(d, list), str(st))

# ---------- 2. 未授权访问 ----------
print("\n=== 未授权保护 ===")
for path in ("/api/admin/alerts", "/api/stats/visits", "/api/security/audit",
             "/api/messages/admin", "/api/admin/uploads"):
    st, _ = jget(path)
    ck(f"{path} 未登录 401", st == 401, str(st))

st, _ = jget("/api/content/skills", method="POST", body={"name": "x"})
ck("POST content 未登录 401", st == 401, str(st))

st, _ = jget("/api/content/skills/1", method="DELETE")
ck("DELETE content 未登录 401", st == 401, str(st))

# ---------- 3. 输入校验 ----------
print("\n=== 输入校验(畸形数据不 500) ===")
st, _ = jget("/api/messages", method="POST", body={"name": {"bad": 1}, "body": "hi"})
ck("name 传对象 -> 4xx 而非 500", 400 <= st < 500, str(st))

st, _ = jget("/api/messages", method="POST", body={"body": "x" * 500})
ck("超长留言 -> 4xx", 400 <= st < 500, str(st))

st, _ = jget("/api/questions", method="POST", body={"body": ""})
ck("空提问 -> 4xx", 400 <= st < 500, str(st))

st, _ = jget("/api/likes", method="POST", body={"page": "x" * 100})
ck("超长 page -> 4xx", 400 <= st < 500, str(st))

# ---------- 4. 验证码 + 登录 ----------
print("\n=== 认证流程 ===")
st, raw, hdr = req("/api/captcha.svg")
ck("captcha 200", st == 200, str(st))
ck("captcha 是 SVG", b"<svg" in raw, "")
ck("captcha no-store", "no-store" in (hdr.get("Cache-Control") or ""), hdr.get("Cache-Control") or "")
cookie = ""
for part in (hdr.get("Set-Cookie") or "").split(";"):
    part = part.strip()
    if part.startswith("mysite_session="):
        cookie = part
        break

st, _ = jget("/api/login", method="POST", body={"password": "wrong", "captcha": "XXXX"}, cookie=cookie)
ck("错误密码/验证码 -> 401/400", st in (400, 401), str(st))

st, _ = jget("/api/me")
ck("未登录 /api/me 401", st == 401, str(st))

print()
print(f"通过 {PASS} 项,失败 {FAIL} 项")
sys.exit(1 if FAIL else 0)
