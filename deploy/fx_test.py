#!/usr/bin/env python3
"""v1.8.0 测试:后台控制前台特效 + 安全多级菜单"""
import http.cookiejar
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:5102"
P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n}  {e}")
        F += 1


cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def get(path):
    r = op.open(BASE + path, timeout=15)
    return r.status, r.read().decode("utf-8", "replace")


def post(path, payload):
    req = urllib.request.Request(BASE + path,
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        r = op.open(req, timeout=15)
        return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
        except Exception:
            body = {}
        return e.code, body


# ---- 1. 公开 /api/fx(先看结构,状态稍后重置后再断言) ----
st, body = get("/api/fx")
d = json.loads(body)
ck("/api/fx 200", st == 200, str(st))
ck("/api/fx 有 mode/key/effects", all(k in d for k in ("mode", "key", "effects")), str(d))

# ---- 2. 未登录不能读后台 fx 设置 ----
try:
    st2, _ = get("/api/security/fx")
    ck("未登录 /api/security/fx 被拒", st2 in (302, 401, 403), str(st2))
except urllib.error.HTTPError as e:
    ck("未登录 /api/security/fx 被拒", e.code in (302, 401, 403), str(e.code))

# ---- 3. 登录 ----
svg = get("/admin/captcha.svg")[1]
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
data = urllib.parse.urlencode({"password": "admin", "captcha": cap}).encode()
req = urllib.request.Request(BASE + "/admin/login", data=data,
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
r = op.open(req, timeout=15)
ck("登录成功", "panel-dashboard" in r.read().decode("utf-8", "replace"))

# 重置为默认,保证测试可重复运行
post("/api/security/fx", {"fx_holiday_mode": "auto", "fx_holiday_key": "", "fx_effects": "1"})
st, body = get("/api/fx")
ck("/api/fx 默认 auto", json.loads(body)["mode"] == "auto", body[:80])

# ---- 4. 后台 fx 设置读写 ----
st, body = get("/api/security/fx")
d = json.loads(body)
ck("后台 fx 设置可读", st == 200 and "fx_holiday_mode" in d, str(d)[:80])
ck("返回节日 key 列表", len(d.get("keys", [])) == 8, str(d.get("keys")))

# 改成 manual/valentine
st, r1 = post("/api/security/fx", {"fx_holiday_mode": "manual",
                                   "fx_holiday_key": "valentine",
                                   "fx_effects": "1"})
ck("保存 manual/valentine", st == 200 and r1.get("ok"), str(r1)[:80])

st, body = get("/api/fx")
d = json.loads(body)
ck("公开接口同步为 manual", d["mode"] == "manual", str(d))
ck("公开接口同步 key=valentine", d["key"] == "valentine", str(d))

# 非法值拒绝
st, r2 = post("/api/security/fx", {"fx_holiday_mode": "bogus"})
ck("非法 mode 被拒", st == 400, str(r2)[:60])
st, r3 = post("/api/security/fx", {"fx_holiday_key": "hacker"})
ck("非法 key 被拒", st == 400, str(r3)[:60])

# 关闭
st, r4 = post("/api/security/fx", {"fx_holiday_mode": "off", "fx_holiday_key": ""})
ck("保存 off", st == 200 and r4.get("ok"))
st, body = get("/api/fx")
ck("公开接口同步 off", json.loads(body)["mode"] == "off")

# 动效总开关
st, r5 = post("/api/security/fx", {"fx_effects": "0"})
ck("动效总开关关闭", st == 200 and r5.get("ok"))
st, body = get("/api/fx")
ck("公开接口 effects=0", json.loads(body)["effects"] == "0")

# 恢复默认 auto
post("/api/security/fx", {"fx_holiday_mode": "auto", "fx_holiday_key": "", "fx_effects": "1"})

# ---- 5. 安全多级菜单:admin.html 结构 ----
st, body = get("/admin/")
ck("管理页 200", st == 200)
for pid in ["panel-sec-pass", "panel-sec-login", "panel-sec-blocked",
            "panel-sec-sessions", "panel-sec-audit", "panel-sec-status",
            "panel-fx"]:
    ck(f"含 {pid}", pid in body)
ck("侧边栏有安全中心组", 'data-group="security"' in body)
ck("侧边栏 6 个安全子项", body.count('data-panel="sec-') == 6, str(body.count('data-panel="sec-')))
ck("侧边栏有前台特效入口", 'data-panel="fx"' in body)
ck("旧 security 面板已移除", 'id="panel-security"' not in body)

# ---- 6. 前台 holiday.js 读配置 ----
st, js = get("/js/holiday.js")
ck("holiday.js 读 /api/fx", "/api/fx" in js)
ck("holiday.js 支持 off", "'off'" in js or '"off"' in js)
ck("holiday.js 支持 manual", "manual" in js)
ck("holiday.js 尊重 effects 开关", "effects" in js)
ck("holiday.js 有日期回退", "detectByDate" in js)

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
