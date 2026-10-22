#!/usr/bin/env python3
"""v1.10 数据包测试:公告 + 倒计时 + 新老访客 + 停留时长 + CSV"""
import http.cookiejar
import io
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
            return e.code, {"_raw": raw[:80]}


print("=== 登录后台(admin API 需先登录) ===")
svg = get("/admin/captcha.svg")[1]
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
data = urllib.parse.urlencode({"password": PWD, "captcha": cap}).encode()
req = urllib.request.Request(BASE + "/admin/login", data=data,
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
body = op.open(req, timeout=15).read().decode("utf-8", "replace")
ck("登录成功", "panel-dashboard" in body)

print()
print("=== 公告 API ===")
st, d = post("/api/notices/admin", {"body": "测试公告:明天考高数"})
ck("发布公告", st == 200 and d.get("ok"), f"{st} {d}")
st, raw = get("/api/notices/active")
d = json.loads(raw)
ck("前台拿到 active 公告", d.get("notice") and "高数" in d["notice"]["body"], str(d))
nid = d["notice"]["id"] if d.get("notice") else 0

st, d = post("/api/notices/admin", {"body": ""})
ck("空公告 400", st == 400, f"{st} {d}")

# 下架后前台拿不到
st, d = post(f"/api/notices/{nid}/mod", {"action": "off"})
ck("下架成功", st == 200 and d.get("ok"), f"{st}")
d = json.loads(get("/api/notices/active")[1])
ck("下架后前台为空", d.get("notice") is None, str(d))

# 再上架
st, d = post(f"/api/notices/{nid}/mod", {"action": "on"})
ck("上架成功", st == 200, f"{st}")

print()
print("=== 倒计时 API ===")
st, d = post("/api/countdowns/admin",
             {"title": "蓝桥杯", "target": "2099-04-01", "emoji": "🏆", "active": 1})
ck("新增倒计时", st == 200 and d.get("ok"), f"{st} {d}")
st, raw = get("/api/countdowns/active")
d = json.loads(raw)
ck("前台拿到倒计时", d.get("countdown") and d["countdown"]["title"] == "蓝桥杯", str(d))
cid = d["countdown"]["id"] if d.get("countdown") else 0

st, d = post("/api/countdowns/admin", {"title": "坏日期", "target": "99-1-1"})
ck("坏日期 400", st == 400, f"{st} {d}")

# 编辑
st, d = post("/api/countdowns/admin",
             {"id": cid, "title": "蓝桥杯决赛", "target": "2099-04-02",
              "emoji": "🥇", "active": 1})
ck("编辑倒计时", st == 200 and d.get("ok"), f"{st} {d}")
d = json.loads(get("/api/countdowns/active")[1])
ck("编辑生效", d.get("countdown") and d["countdown"]["title"] == "蓝桥杯决赛", str(d))
cid = d["countdown"]["id"] if d.get("countdown") else cid

print()
print("=== track: 新老 + 停留时长 ===")
st, d = post("/api/track", {"path": "/", "is_new": True})
ck("track 新访客 200", st == 200 and d.get("ok"), f"{st} {d}")
vid1 = d.get("vid")
ck("返回 vid", isinstance(vid1, int) and vid1 > 0, str(d))

st, d = post("/api/track", {"path": "/", "is_new": False})
ck("track 回访 200", st == 200 and d.get("ok"), f"{st}")
vid2 = d.get("vid")

st, d = post("/api/track/dur", {"vid": vid1, "dur_s": 95})
ck("补报停留 95s", st == 200 and d.get("ok"), f"{st} {d}")
st, d = post("/api/track/dur", {"vid": vid1, "dur_s": 30})
ck("重复补报取 MAX", st == 200, f"{st}")
st, d = post("/api/track/dur", {"vid": 0, "dur_s": 10})
ck("vid=0 拒绝", st == 400, f"{st}")
st, d = post("/api/track/dur", {"vid": vid1, "dur_s": 999999})
ck("超 2h 封顶不报错", st == 200, f"{st}")

print()
print("=== 访客深度 + CSV ===")
st, raw = get("/api/stats/visitors?days=30")
d = json.loads(raw)
ck("visitors 200", st == 200, str(st))
ck("含 new/back/avg_dur", all(k in d for k in ("new", "back", "avg_dur")), str(d))
ck("新访客>0", d.get("new", 0) >= 1, str(d))
ck("平均停留>0", d.get("avg_dur", 0) >= 1, str(d))

st, raw = get("/api/stats/visits/csv?days=7")
ck("CSV 200", st == 200, str(st))
ck("CSV 含表头", "日期" in raw and "停留秒" in raw, raw[:80])
ck("CSV 含数据行", raw.count("\n") >= 2, str(raw.count(chr(10))))
# 先报 95 再报 999999(封顶 7200),MAX 逻辑下应显示 7200
ck("CSV 有封顶 7200 行(999999→7200,M 生效)", any(",7200" in ln for ln in raw.splitlines()[1:]), "(未找到)")

print()
print("=== 清理测试数据 ===")
st, d = post(f"/api/notices/{nid}/mod", {"action": "delete"})
ck("删公告", st == 200, f"{st}")
st, d = post(f"/api/countdowns/{cid}/delete", {})
ck("删倒计时", st == 200, f"{st}")

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
