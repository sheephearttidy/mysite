#!/usr/bin/env python3
"""v1.10.0 生产验证:公告/倒计时/track/CSV(只读为主,登录后清理)"""
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


print("=== 公开接口 ===")
st, raw = get("/api/notices/active")
ck("notices/active 200", st == 200 and json.loads(raw).get("notice") is None, str(st))
st, raw = get("/api/countdowns/active")
ck("countdowns/active 200", st == 200 and json.loads(raw).get("countdown") is None, str(st))
st, d = post("/api/track", {"path": "/", "is_new": True})
ck("track 返回 vid", st == 200 and d.get("vid", 0) > 0, f"{st} {d}")
vid = d.get("vid", 0)
st, d = post("/api/track/dur", {"vid": vid, "dur_s": 5})
ck("track/dur 200", st == 200 and d.get("ok"), f"{st}")

print()
print("=== 页面挂载 ===")
st, html = get("/")
ck("首页 200", st == 200, str(st))
ck("挂 site-extra.js", "js/site-extra.js" in html)
ck("main.js 新版含 is_new", "mysite_seen" in get("/js/main.js")[1])
ck("site-extra.js 新版含公告+倒计时", "initNotice" in get("/js/site-extra.js")[1])

print()
print("=== 后台(登录) ===")
if not PWD:
    print("(未设 PROD_PWD,跳过后台)")
    sys.exit(1 if F else 0)
svg = get("/admin/captcha.svg")[1]
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
data = urllib.parse.urlencode({"password": PWD, "captcha": cap}).encode()
req = urllib.request.Request(BASE + "/admin/login", data=data,
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
body = op.open(req, timeout=20).read().decode("utf-8", "replace")
ck("登录成功", "panel-dashboard" in body)

st, raw = get("/api/notices/admin")
d = json.loads(raw)
ck("notices/admin 200", st == 200 and isinstance(d.get("notices"), list), str(st))

# 发布→验证前台→下架→删除(全程清理)
st, d = post("/api/notices/admin", {"body": "自检公告:系统运行正常 🎉"})
ck("发布自检公告", st == 200 and d.get("ok"), f"{st}")
d2 = json.loads(get("/api/notices/active")[1])
ck("前台可见", d2.get("notice") and "运行正常" in d2["notice"]["body"], str(d2))
nid = d2["notice"]["id"]
post(f"/api/notices/{nid}/mod", {"action": "delete"})
d2 = json.loads(get("/api/notices/active")[1])
ck("删除后前台为空", d2.get("notice") is None, str(d2))

# 倒计时同样流程
st, d = post("/api/countdowns/admin",
             {"title": "自检事件", "target": "2099-01-01", "active": 1})
ck("新增自检倒计时", st == 200 and d.get("ok"), f"{st}")
d2 = json.loads(get("/api/countdowns/active")[1])
ck("前台可见倒计时", d2.get("countdown") and d2["countdown"]["title"] == "自检事件", str(d2))
cid = d2["countdown"]["id"]
post(f"/api/countdowns/{cid}/delete", {})
d2 = json.loads(get("/api/countdowns/active")[1])
ck("删除后前台为空", d2.get("countdown") is None, str(d2))

st, raw = get("/api/stats/visitors?days=30")
ck("visitors 200", st == 200, str(st))
st, raw = get("/api/stats/visits/csv?days=7")
ck("CSV 200 且含表头", st == 200 and "日期" in raw, str(st))

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
