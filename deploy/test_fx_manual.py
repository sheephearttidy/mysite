#!/usr/bin/env python3
"""验证:后台手动指定节日 -> 前台生效(「手动指定未生效」回归测试)
含:资源版本参数(缓存穿透) + 手动指定全流程 + 真实页面渲染检查
"""
import http.cookiejar
import json
import os
import re
import sys
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:5102"
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
    r = op.open(BASE + p, timeout=15)
    return r.status, r.read().decode("utf-8", "replace")


def post(p, obj):
    data = json.dumps(obj).encode()
    req = urllib.request.Request(BASE + p, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        r = op.open(req, timeout=15)
        raw = r.read().decode("utf-8", "replace")
        try:
            return r.status, json.loads(raw)
        except Exception:
            return r.status, {"_raw": raw}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"_raw": raw}


print("=== 1. 前台资源都带版本参数(解决 7 天强缓存) ===")
st, html = get("/")
refs = re.findall(r'(?:src|href)="((?:js|css)/[^"]+)"', html)
ck("资源数 >= 10", len(refs) >= 10, str(len(refs)))
missing = [r for r in refs if "?v=" not in r]
ck("全部带 ?v=", not missing, str(missing))
ck("holiday.js 带版本", any("holiday.js?v=" in r for r in refs))
ck("theme.js 带版本", any("theme.js?v=" in r for r in refs))

print()
print("=== 2. 登录(需验证码) ===")
svg = get("/admin/captcha.svg")[1]
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
data = urllib.parse.urlencode({"password": PWD, "captcha": cap}).encode()
req = urllib.request.Request(BASE + "/admin/login", data=data,
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
try:
    body = op.open(req, timeout=15).read().decode("utf-8", "replace")
    ok = "panel-dashboard" in body or "数据看板" in body
except urllib.error.HTTPError as e:
    ok = False
    body = str(e.code)
ck("登录成功", ok, body[:60])

# 重置默认
post("/api/security/fx", {"fx_holiday_mode": "auto",
                          "fx_holiday_key": "", "fx_effects": "1"})

print()
print("=== 3. 逐个节日手动指定 ===")
KEYS = ["national-day", "valentine", "memorial", "new-year",
        "christmas", "labor", "children", "teacher"]

for key in KEYS:
    st, d = post("/api/security/fx", {"fx_holiday_mode": "manual",
                                      "fx_holiday_key": key,
                                      "fx_effects": "1"})
    if st != 200 or not d.get("ok"):
        ck(f"设置 {key}", False, f"{st} {str(d)[:60]}")
        continue
    st, raw = get("/api/fx")
    pub = json.loads(raw)
    ok_set = pub.get("mode") == "manual" and pub.get("key") == key
    ck(f"手动指定 {key}", ok_set, str(pub))

print()
print("=== 4. holiday.js 能把 manual 转成 data-holiday ===")
st, js = get("/js/holiday.js")
ck("holiday.js 读 /api/fx", "/api/fx" in js)
ck("holiday.js 有 manual 分支", "manual" in js)
ck("holiday.js 有 LABELS 映射", "LABELS" in js)
# 8 个节日 key 都应出现在 JS 里
for key in KEYS:
    ck(f"  JS 认识 {key}", key in js, "缺失")

print()
print("=== 5. effects=0 全关 ===")
post("/api/security/fx", {"fx_holiday_mode": "manual",
                          "fx_holiday_key": "christmas", "fx_effects": "0"})
pub = json.loads(get("/api/fx")[1])
ck("effects=0 生效", pub.get("effects") == "0", str(pub))

print()
print("=== 6. mode=off 全关 ===")
post("/api/security/fx", {"fx_holiday_mode": "off",
                          "fx_holiday_key": "", "fx_effects": "1"})
pub = json.loads(get("/api/fx")[1])
ck("mode=off 生效", pub.get("mode") == "off", str(pub))

print()
print("=== 7. 非法值被拒 ===")
st, d = post("/api/security/fx", {"fx_holiday_mode": "bogus"})
ck("非法 mode 被拒", st == 400, f"{st} {str(d)[:50]}")
st, d = post("/api/security/fx", {"fx_holiday_key": "not-a-holiday"})
ck("非法 key 被拒", st == 400, f"{st} {str(d)[:50]}")

print()
print("=== 8. 恢复默认 auto ===")
post("/api/security/fx", {"fx_holiday_mode": "auto",
                          "fx_holiday_key": "", "fx_effects": "1"})
pub = json.loads(get("/api/fx")[1])
ck("恢复 auto", pub.get("mode") == "auto", str(pub))

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
