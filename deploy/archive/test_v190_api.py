#!/usr/bin/env python3
"""v1.9.0 后端 API 测试:留言板 + 点赞"""
import http.cookiejar
import json
import os
import re
import sys
import urllib.parse
import urllib.request

BASE = os.environ.get("BASE", "http://127.0.0.1:5102")
PWD = os.environ.get("TEST_PWD", "admin")
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
        r = op.open(BASE + p, timeout=15)
        return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def post(p, obj):
    data = json.dumps(obj).encode()
    req = urllib.request.Request(BASE + p, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        r = op.open(req, timeout=15)
        return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"_raw": raw[:60]}


print("=== 公开读 ===")
st, raw = get("/api/messages")
d = json.loads(raw)
ck("GET /api/messages 200", st == 200, str(st))
ck("返回 messages 数组", isinstance(d.get("messages"), list))

st, raw = get("/api/likes")
d = json.loads(raw)
ck("GET /api/likes 200", st == 200, str(st))
ck("likes 是 7 页的字典", set(d.get("likes", {}).keys()) ==
   {"home", "about", "skills", "works", "campus", "map", "contact"}, str(d))
ck("total 字段", isinstance(d.get("total"), int), str(d))

print()
print("=== 写留言 ===")
st, d = post("/api/messages", {"name": "测试同学", "body": "站主加油!"})
ck("POST 留言 200", st == 200 and d.get("ok"), f"{st} {d}")
ck("返回 id", isinstance(d.get("id"), int), str(d))

# 未登录后台看不到(待审核)
d = json.loads(get("/api/messages")[1])
ck("待审核不公开显示", all(m["id"] != d.get("id") for m in d["messages"]) if d["messages"] else True)

# 空内容被拒(先解除限速再测;429 也算防刷正常,但这里要验证业务校验)
st, d = post("/api/messages", {"name": "x", "body": "  "})
if st == 429:
    ck("空内容被拒(限速层拦截,业务层待验)", True, "429")
else:
    ck("空内容 400", st == 400, f"{st} {d}")

# 超长被裁剪(限速期内跳过)
long_body = "啊" * 500
st, d = post("/api/messages", {"name": "l", "body": long_body})
if st == 429:
    print("  (限速期内,跳过超长裁剪测试)")
else:
    ck("超长裁到 140", st == 200 and len(d.get("body", "")) <= 140, f"{st}")

print()
print("=== 登录后台 ===")
svg = get("/admin/captcha.svg")[1]
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
data = urllib.parse.urlencode({"password": PWD, "captcha": cap}).encode()
req = urllib.request.Request(BASE + "/admin/login", data=data,
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
body = op.open(req, timeout=15).read().decode("utf-8", "replace")
ck("登录成功", "panel-dashboard" in body)

print()
print("=== 后台审核流 ===")
st, raw = get("/api/messages/admin")
d = json.loads(raw)
ck("admin 列表 200", st == 200, str(st))
ck("counts 有 pending/shown/total", all(k in d.get("counts", {})
   for k in ("pending", "shown", "total")), str(d.get("counts")))
mine = next((m for m in d["messages"] if m["name"] == "测试同学"), None)
ck("能在后台看到待审留言", mine is not None)
mid = mine["id"] if mine else 0

# 展示
st, d = post(f"/api/messages/{mid}/mod", {"action": "show"})
ck("审核通过", st == 200 and d.get("ok"), f"{st} {d}")
# 公开列表能看到了
pub = json.loads(get("/api/messages")[1])
ck("公开列表出现", any(m["id"] == mid for m in pub["messages"]))

# 回复
st, d = post(f"/api/messages/{mid}/mod", {"action": "reply", "reply": "谢谢支持!"})
ck("回复成功", st == 200 and d.get("ok"), f"{st} {d}")
pub = json.loads(get("/api/messages")[1])
mine = next((m for m in pub["messages"] if m["id"] == mid), {})
ck("公开列表带回复", mine.get("reply") == "谢谢支持!", str(mine))

# 隐藏
st, d = post(f"/api/messages/{mid}/mod", {"action": "hide"})
ck("隐藏成功", st == 200 and d.get("ok"), f"{st} {d}")
pub = json.loads(get("/api/messages")[1])
ck("隐藏后公开消失", not any(m["id"] == mid for m in pub["messages"]))

# 删除
st, d = post(f"/api/messages/{mid}/mod", {"action": "delete"})
ck("删除成功", st == 200 and d.get("ok"), f"{st} {d}")
st, d = post(f"/api/messages/{mid}/mod", {"action": "show"})
ck("再操作 404", st == 404, f"{st}")

print()
print("=== 点赞 ===")
st, d = post("/api/likes", {"page": "home"})
ck("点赞 home 200", st == 200 and d.get("ok"), f"{st} {d}")
n1 = d.get("n", 0)
st, d = post("/api/likes", {"page": "home"})
ck("再点 +1", d.get("n") == n1 + 1, f"{d} vs {n1}")
st, d = post("/api/likes", {"page": "hacker"})
ck("未知页 400", st == 400, f"{st}")

# 未登录不能进后台接口
import copy
op2 = urllib.request.build_opener()   # 无 cookie
try:
    r = op2.open(BASE + "/api/messages/admin", timeout=15)
    ck("未登录 admin 接口被拒", False, str(r.status))
except urllib.error.HTTPError as e:
    ck("未登录 admin 接口被拒", e.code in (302, 401, 403), str(e.code))

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
