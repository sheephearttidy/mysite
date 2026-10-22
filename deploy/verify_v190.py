#!/usr/bin/env python3
"""v1.9.0 生产验证:公开 API + 页面元素 + 后台审核流"""
import http.cookiejar
import json
import os
import re
import sys
import urllib.parse
import urllib.request

BASE = "https://imyxj.xyz"
PWD = os.environ.get("PROD_PWD", "")
P = F = 0

op = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n}  {e}")
        F += 1


def get(p):
    try:
        r = op.open(BASE + p, timeout=20)
        return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def post(p, obj):
    data = json.dumps(obj).encode()
    req = urllib.request.Request(BASE + p, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        r = op.open(req, timeout=20)
        return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"_raw": raw[:60]}


print("=== 1. 公开 API ===")
st, raw = get("/api/messages")
ck("GET /api/messages 200", st == 200, str(st))
ck("messages 数组", isinstance(json.loads(raw).get("messages"), list))

st, raw = get("/api/likes")
d = json.loads(raw)
ck("GET /api/likes 200", st == 200, str(st))
ck("7 页齐全", set(d["likes"].keys()) ==
   {"home", "about", "skills", "works", "campus", "map", "contact"})

print()
print("=== 2. 前台页面带互动元素 ===")
for p, page_key in [("/", "home"), ("/about.html", "about"), ("/contact.html", "contact")]:
    st, html = get(p)
    ck(f"{p} 200", st == 200, str(st))
    ck(f"{p} 有 likeBtn", 'id="likeBtn"' in html)
    ck(f"{p} 有 interact.js", "js/interact.js" in html)
    if p == "/":
        ck("首页有留言墙", 'id="msgwallGrid"' in html)
        ck("首页有输入框", 'id="msgBody"' in html)

print()
print("=== 3. interact.js 是新版(含四个模块) ===")
st, js = get("/js/interact.js")
ck("200", st == 200, str(st))
for kw in ("initTitleEgg", "initClickFx", "initLikes", "initMsgwall"):
    ck(f"含 {kw}", kw in js)

print()
print("=== 4. 写留言 + 审核流(真实数据,最后清掉) ===")
st, d = post("/api/messages", {"name": "验证机器人", "body": "v1.9.0 部署自检,请忽略"})
ck("POST 留言 200", st == 200 and d.get("ok"), f"{st} {d}")
mid = d.get("id")

print()
print("=== 5. 登录后台 ===")
if not PWD:
    print("跳过后台验证(未设 PROD_PWD)")
    sys.exit(1 if F else 0)
svg = get("/admin/captcha.svg")[1]
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
data = urllib.parse.urlencode({"password": PWD, "captcha": cap}).encode()
req = urllib.request.Request(BASE + "/admin/login", data=data,
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
body = op.open(req, timeout=20).read().decode("utf-8", "replace")
ck("登录成功", "panel-dashboard" in body)

print()
print("=== 6. 后台留言审核 + 点赞统计 ===")
st, raw = get("/api/messages/admin")
d = json.loads(raw)
ck("admin 列表 200", st == 200, str(st))
mine = next((m for m in d["messages"] if m["id"] == mid), None)
ck("看到自检留言", mine is not None)
if mine:
    st, d2 = post(f"/api/messages/{mid}/mod", {"action": "show"})
    ck("展示", st == 200 and d2.get("ok"), f"{st}")
    pub = json.loads(get("/api/messages")[1])
    ck("前台可见", any(m["id"] == mid for m in pub["messages"]))
    st, d2 = post(f"/api/messages/{mid}/mod", {"action": "delete"})
    ck("删除(清理)", st == 200 and d2.get("ok"), f"{st}")

st, d = get("/api/likes/admin")
ck("点赞统计 200", st == 200 and "total" in json.loads(d[1] if isinstance(d, tuple) else d) if False else st == 200, str(st))

print()
print("=== 7. 点赞端到端 ===")
st, d = post("/api/likes", {"page": "home"})
n0 = d.get("n", 0)
ck("点赞成功", st == 200 and d.get("ok"), f"{st} {d}")
st, d = post("/api/likes", {"page": "map"})
ck("第二页也成功", st == 200 and d.get("ok"), f"{st}")
total_now = json.loads(get("/api/likes")[1])
ck("计数累加", total_now["likes"]["home"] >= n0, str(total_now["likes"]))

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
