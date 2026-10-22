#!/usr/bin/env python3
"""生产真实浏览器验证:全部 8 个节日 + 全关状态
通过后台 API 切换,用 Chrome 渲染前台,检查 data-holiday 和粒子数。
"""
import http.cookiejar
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "https://imyxj.xyz"
PWD = os.environ.get("PROD_PWD", "")
P = F = 0
tmp = tempfile.mkdtemp()

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
    return op.open(BASE + p, timeout=20).read().decode("utf-8", "replace")


def post(p, obj):
    data = json.dumps(obj).encode()
    req = urllib.request.Request(BASE + p, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        r = op.open(req, timeout=20)
        return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {}


def render_dom(url, tag):
    out = os.path.join(tmp, f"{tag}.html")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--virtual-time-budget=6000", "--dump-dom", url],
                   stdout=open(out, "w", encoding="utf-8"),
                   stderr=subprocess.DEVNULL, timeout=120)
    with open(out, encoding="utf-8", errors="replace") as f:
        return f.read()


if not PWD:
    print("跳过:未设置 PROD_PWD")
    sys.exit(0)

# 登录
svg = get("/admin/captcha.svg")
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
data = urllib.parse.urlencode({"password": PWD, "captcha": cap}).encode()
req = urllib.request.Request(BASE + "/admin/login", data=data,
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
try:
    op.open(req, timeout=20).read()
    print("已登录生产后台")
except urllib.error.HTTPError as e:
    print(f"登录失败 {e.code}")
    sys.exit(1)

# 记录原始设置,最后恢复
orig = json.loads(get("/api/fx"))
print(f"原始设置: {orig}")
print()

# 每个节日的粒子 class 和数量
SPEC = {
    "national-day": ("flag", 16),
    "valentine": ("heart", 18),
    "memorial": ("candle", 6),
    "new-year": ("streamer", 24),
    "christmas": ("snowflake", 26),
    "labor": ("streamer", 18),
    "children": ("plane", 8),
    "teacher": ("teacher-star", 20),
}

print("=== 逐个节日:真实浏览器渲染 ===")
for key, (cls, want_n) in SPEC.items():
    st, d = post("/api/security/fx", {"fx_holiday_mode": "manual",
                                      "fx_holiday_key": key, "fx_effects": "1"})
    if st != 200:
        ck(f"{key} 设置", False, str(st))
        continue
    time.sleep(0.4)
    dom = render_dom(BASE + "/", key)

    m = re.search(r'<html[^>]*data-holiday="([^"]*)"', dom)
    got = m.group(1) if m else ""
    ck(f"{key}: data-holiday", got == key, f"实际 {got!r}")

    n = dom.count(f'class="{cls}"')
    ck(f"{key}: {cls} 粒子 {want_n} 个", n == want_n, f"实际 {n}")

print()
print("=== 全关状态 ===")
post("/api/security/fx", {"fx_holiday_mode": "off",
                          "fx_holiday_key": "", "fx_effects": "1"})
time.sleep(0.4)
dom = render_dom(BASE + "/", "off")
m = re.search(r'<html[^>]*data-holiday="([^"]*)"', dom)
got = m.group(1) if m else ""
ck("mode=off 无 data-holiday", got == "", f"实际 {got!r}")
ck("mode=off 无特效容器", 'class="holiday-fx"' not in dom)

print()
print("=== effects=0 ===")
post("/api/security/fx", {"fx_holiday_mode": "manual",
                          "fx_holiday_key": "christmas", "fx_effects": "0"})
time.sleep(0.4)
dom = render_dom(BASE + "/", "eff0")
m = re.search(r'<html[^>]*data-holiday="([^"]*)"', dom)
got = m.group(1) if m else ""
ck("effects=0 无 data-holiday", got == "", f"实际 {got!r}")

print()
print("=== 恢复原始设置 ===")
post("/api/security/fx", {"fx_holiday_mode": orig["mode"],
                          "fx_holiday_key": orig["key"],
                          "fx_effects": orig["effects"]})
now = json.loads(get("/api/fx"))
ck("已恢复", now == orig, f"{now} vs {orig}")

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
