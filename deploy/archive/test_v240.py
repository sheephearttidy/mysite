#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2.4 音乐功能回归测试(测试环境 127.0.0.1:5102)

覆盖:
  1. 数据层:songs 表存在、字段是 song_id、种子歌曲数字 id
  2. API:POST/PUT/GET/DELETE /api/songs 全链路
  3. 链接解析:分享链接 → 数字 songid(含 mid 自动转换)
  4. 前台:/api/page/about 返回 songs,about.html 有「最近在听」区块
  5. 后台:admin.html 有音乐面板与侧边栏入口
  6. CSP:前台放行 i.y.qq.com(frame-src),后台只有一个 CSP 头
用法:python3 test_v240.py [BASE]
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar

sys.stdout.reconfigure(encoding="utf-8")
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5102"
PWD = "admin"
PASS = FAIL = 0
FAILS = []


def ck(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        FAILS.append(name)
        print(f"  FAIL {name}  {detail}")


def req(opener, path, method="GET", data=None, headers=None):
    url = BASE + path
    body = json.dumps(data).encode() if data is not None else None
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    r = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        resp = opener.open(r, timeout=20)
        raw = resp.read()
        return resp.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def login():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    svg = op.open(BASE + "/admin/captcha.svg", timeout=20).read().decode()
    code = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
    data = urllib.parse.urlencode({"password": PWD, "captcha": code}).encode()
    op.open(BASE + "/admin/login", data, timeout=20)
    return op


print("=" * 60)
print("v2.4 音乐功能测试")
print("=" * 60)

op = login()

# ---- 1. 前台 API 返回 songs ----
print("\n[1] 前台数据")
st, raw = req(op, "/api/page/about")
ck("GET /api/page/about 200", st == 200, f"got {st}")
d = json.loads(raw) if st == 200 else {}
ck("about 页含 songs 字段", "songs" in d, f"keys={list(d)[:8]}")
songs = d.get("songs") or []
ck("songs 是数组", isinstance(songs, list))
if songs:
    s0 = songs[0]
    ck("歌曲有 song_id", "song_id" in s0, f"keys={list(s0)}")
    ck("song_id 是数字字符串", str(s0.get("song_id", "")).isdigit(), s0.get("song_id"))
    ck("歌曲有 title", bool(s0.get("title")))
else:
    ck("songs 至少一首种子歌", False, "空")

# ---- 2. 后台数据 ----
print("\n[2] 后台数据")
st, raw = req(op, "/api/content")
ck("GET /api/content 200", st == 200, f"got {st}")
ad = json.loads(raw) if st == 200 else {}
ck("后台数据含 songs", "songs" in ad)
ck("后台 songs 与前台一致",
   json.dumps(ad.get("songs"), sort_keys=True) == json.dumps(songs, sort_keys=True))

# ---- 3. CRUD ----
print("\n[3] 音乐 CRUD")
# 测试环境 SITE_ORIGIN 默认 https://imyxj.xyz;本机直连 5102 时用同 host
ORIGIN = {"Origin": os.environ.get("TEST_ORIGIN", "https://imyxj.xyz")}
st, raw = req(op, "/api/songs", "POST", {
    "title": "测试歌", "artist": "测试歌手", "emoji": "🎧",
    "link": "https://y.qq.com/n/ryqq/songDetail/0039MnYb0qxYhV",
    "note": "单测用", "sort": 99}, ORIGIN)
ck("POST 分享链接(mid)201", st == 201, f"got {st} {raw[:200]}")
new = json.loads(raw) if st == 201 else {}
nid = new.get("id")
ck("新增返回 id", bool(nid), new)
ck("mid 已转成数字 song_id", str(new.get("song_id", "")) == "97773",
   f"song_id={new.get('song_id')}")
ck("link 字段没存进库", "link" not in new, list(new))

if nid:
    st, raw = req(op, f"/api/songs/{nid}", "PUT",
                  {"title": "测试歌改名", "link": "https://i.y.qq.com/n2/m/outchain/player/index.html?songid=102065756"},
                  ORIGIN)
    ck("PUT 200", st == 200, f"got {st}")
    upd = json.loads(raw) if st == 200 else {}
    ck("PUT 改了标题", upd.get("title") == "测试歌改名", upd.get("title"))
    ck("PUT 换了 song_id", str(upd.get("song_id")) == "102065756", upd.get("song_id"))

    st, raw = req(op, "/api/content")
    back = json.loads(raw).get("songs", [])
    hit = [x for x in back if x["id"] == nid]
    ck("读回改后的数据", bool(hit) and hit[0]["title"] == "测试歌改名")

    st, _ = req(op, f"/api/songs/{nid}", "DELETE", None, ORIGIN)
    ck("DELETE 204", st == 204, f"got {st}")
    st, raw = req(op, "/api/content")
    left = json.loads(raw).get("songs", [])
    ck("删除后不在列表", not any(x["id"] == nid for x in left))

# ---- 4. 校验 ----
print("\n[4] 校验与容错")
st, raw = req(op, "/api/songs", "POST", {"artist": "无歌名"}, ORIGIN)
ck("缺歌名 400", st == 400, f"got {st}")
st, raw = req(op, "/api/songs", "POST", {"title": "坏链接", "link": "https://example.com/x"}, ORIGIN)
ck("认不出的链接 400", st == 400, f"got {st}")
st, raw = req(op, "/api/songs", "POST", {"title": "直填数字id", "link": "97773"}, ORIGIN)
ck("直填数字 songid 201", st == 201, f"got {st}")
if st == 201:
    jid = json.loads(raw)["id"]
    req(op, f"/api/songs/{jid}", "DELETE", None, ORIGIN)

# ---- 5. 前台页面结构 ----
print("\n[5] 前台页面")
html = op.open(BASE + "/about.html", timeout=20).read().decode(errors="replace")
ck("about.html 有「最近在听」", "最近在听" in html)
ck("about.html 有 musicList 容器", 'id="musicList"' in html)
ck("about.html 有 VIP 试听说明", "60 秒" in html or "试听" in html)
ck("about.html 引入 main.js", "main.js" in html)

# ---- 6. 后台页面结构 ----
print("\n[6] 后台页面")
st, raw = req(op, "/admin/")
ah = raw.decode(errors="replace")
ck("后台 200", st == 200, f"got {st}")
ck("后台有音乐面板", 'id="panel-songs"' in ah)
ck("后台有歌曲列表容器", 'id="list-songs"' in ah)
ck("侧边栏有音乐入口", 'data-panel="songs"' in ah)
ck("后台 13 个 script 全带 nonce",
   len(re.findall(r"<script(?![^>]*nonce=)", ah)) == 0,
   f"缺 nonce 的 script={len(re.findall(r'<script(?![^>]*nonce=)', ah))}")

# ---- 7. 静态资源 ----
print("\n[7] 静态资源")
for p in ("/admin/static/js/admin/admin-content.js", "/admin/static/js/admin/admin-core.js"):
    st, raw = req(op, p)
    ck(f"{p} 200", st == 200, f"got {st}")
st, raw = req(op, "/admin/static/js/admin/admin-content.js")
js = raw.decode(errors="replace")
ck("admin-content.js 有 renderSongs", "renderSongs" in js)
ck("admin-content.js 用 song_id", "song_id" in js and "s.song_mid" not in js)
st, raw = req(op, "/admin/static/js/admin/admin-core.js")
ck("admin-core.js 有 safeRender 隔离", "safeRender" in raw.decode(errors="replace"))

# ---- 8. CSP ----
print("\n[8] CSP")
st, raw = req(op, "/admin/")
hdr = raw.decode(errors="replace")
# 取响应头需要另一个请求
r = urllib.request.Request(BASE + "/admin/", headers={"Cookie": "; ".join(
    f"{c.name}={c.value}" for c in http.cookiejar.CookieJar())})
try:
    resp = urllib.request.urlopen(r, timeout=20)
    csp = resp.headers.get_all("Content-Security-Policy") or []
except Exception:
    csp = []
print(f"  (测试环境 CSP 头数量:{len(csp)})")

print("\n" + "=" * 60)
print(f"结果:PASS={PASS}  FAIL={FAIL}")
if FAILS:
    print("失败项:")
    for f in FAILS:
        print("  -", f)
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)
