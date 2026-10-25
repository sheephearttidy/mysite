#!/usr/bin/env python3
"""v1.8.0 生产验证:后台控制前台特效 + 安全多级菜单"""
import http.cookiejar
import json
import re
import ssl
import sys
import urllib.parse
import urllib.request

B = "https://imyxj.xyz"
PWD = __import__("os").environ.get("PROD_PWD", "")
P = F = 0

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),
                                 urllib.request.HTTPSHandler(context=ctx))


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n}  {e}")
        F += 1


def get(path):
    r = op.open(B + path, timeout=20)
    return r.status, r.read().decode("utf-8", "replace")


def post(path, payload):
    req = urllib.request.Request(B + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        r = op.open(req, timeout=20)
        return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            b = json.loads(e.read().decode())
        except Exception:
            b = {}
        return e.code, b


# 1. 公开接口
st, body = get("/api/fx")
d = json.loads(body)
ck("生产 /api/fx 200", st == 200, str(st))
ck("生产 /api/fx 结构完整", all(k in d for k in ("mode", "key", "effects")), str(d))

# 2. 前台 7 页引用新 holiday.js
for fn in ["", "about.html", "skills.html", "works.html",
           "campus.html", "map.html", "contact.html"]:
    st, h = get("/" + fn)
    ck(f"前台 {fn or 'index'} 200", st == 200, str(st))
    ck(f"前台 {fn or 'index'} 有 holiday.js", "js/holiday.js" in h)

# 3. 前台 holiday.js 是新版
st, js = get("/js/holiday.js")
ck("holiday.js 读 /api/fx", "/api/fx" in js)
ck("holiday.js 支持 manual/off", "manual" in js and "'off'" in js)
ck("holiday.js 有日期回退", "detectByDate" in js)
ck("holiday.js 尊重 effects", "effects" in js)

# 4. 登录后台
svg = get("/admin/captcha.svg")[1]
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
data = urllib.parse.urlencode({"password": PWD, "captcha": cap}).encode()
req = urllib.request.Request(B + "/admin/login", data=data,
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
r = op.open(req, timeout=20)
ck("生产登录成功", "panel-dashboard" in r.read().decode("utf-8", "replace"))

# 5. 后台 fx 设置接口
st, body = get("/api/security/fx")
d = json.loads(body)
ck("后台 fx 设置可读", st == 200 and "fx_holiday_mode" in d, str(d)[:80])
ck("节日 key 列表 8 个", len(d.get("keys", [])) == 8, str(d.get("keys")))

# 6. 后台页面结构:多级菜单
st, h = get("/admin/")
ck("管理页 200", st == 200)
ck("安全中心组存在", 'data-group="security"' in h)
ck("6 个安全子项", h.count('data-panel="sec-') == 6, str(h.count('data-panel="sec-')))
for pid in ["panel-fx", "panel-sec-pass", "panel-sec-login", "panel-sec-blocked",
            "panel-sec-sessions", "panel-sec-audit", "panel-sec-status"]:
    ck(f"含 {pid}", pid in h)
ck("旧 security 面板已移除", 'id="panel-security"' not in h)
ck("含 fxHolidayOn 开关", "fxHolidayOn" in h)
ck("含 fxMode 下拉", "fxMode" in h)
ck("含 fxKey 下拉", "fxKey" in h)

# 7. 端到端:手动指定 → 公开接口同步 → 恢复
st, r1 = post("/api/security/fx", {"fx_holiday_mode": "manual",
                                   "fx_holiday_key": "valentine",
                                   "fx_effects": "1"})
ck("生产保存 manual/valentine", st == 200 and r1.get("ok"), str(r1)[:80])
st, body = get("/api/fx")
d = json.loads(body)
ck("生产公开接口同步 manual", d["mode"] == "manual" and d["key"] == "valentine", str(d))

# 非法值
st, r2 = post("/api/security/fx", {"fx_holiday_mode": "bogus"})
ck("生产非法 mode 被拒", st == 400, str(r2)[:60])

# 恢复默认 auto
st, r3 = post("/api/security/fx", {"fx_holiday_mode": "auto",
                                   "fx_holiday_key": "", "fx_effects": "1"})
ck("生产恢复 auto", st == 200 and r3.get("ok"))
st, body = get("/api/fx")
ck("生产公开接口恢复 auto", json.loads(body)["mode"] == "auto")

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
