#!/usr/bin/env python3
"""用 headless Chrome 实测:手动指定后页面 data-holiday 是否真的被设置
这是最接近真实用户的验证(执行 JS,读 DOM)。
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import http.cookiejar

BASE = "http://127.0.0.1:5102"
PWD = os.environ.get("TEST_PWD", "admin")
CHROME = "/usr/bin/google-chrome"
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


def post(p, obj):
    data = json.dumps(obj).encode()
    req = urllib.request.Request(BASE + p, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        r = op.open(req, timeout=15)
        return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {}


def get(p):
    r = op.open(BASE + p, timeout=15)
    return r.read().decode("utf-8", "replace")


# 登录
svg = get("/admin/captcha.svg")
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
data = urllib.parse.urlencode({"password": PWD, "captcha": cap}).encode()
req = urllib.request.Request(BASE + "/admin/login", data=data,
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
op.open(req, timeout=15).read()
print("已登录后台")


def dump_dom(url, out):
    """用 chrome headless 渲染并导出 DOM"""
    with open(out, "w", encoding="utf-8") as f:
        subprocess.run([
            CHROME, "--headless", "--disable-gpu", "--no-sandbox",
            "--virtual-time-budget=5000", "--dump-dom", url,
        ], stdout=f, stderr=subprocess.DEVNULL, timeout=60)
    with open(out, encoding="utf-8") as f:
        return f.read()


print()
print("=== 逐个节日:headless Chrome 实测 data-holiday ===")
tmp = tempfile.mkdtemp()

KEYS = ["valentine", "christmas", "national-day", "memorial"]

for key in KEYS:
    st, d = post("/api/security/fx", {"fx_holiday_mode": "manual",
                                      "fx_holiday_key": key, "fx_effects": "1"})
    if st != 200:
        ck(f"{key} 设置", False, str(st))
        continue
    time.sleep(0.3)

    out = os.path.join(tmp, f"{key}.html")
    dom = dump_dom(BASE + "/", out)

    m = re.search(r'<html[^>]*data-holiday="([^"]*)"', dom)
    got = m.group(1) if m else "(无)"
    ck(f"manual={key} -> data-holiday={key}", got == key, f"实际 {got!r}")

    # 检查粒子是否渲染
    fx_count = dom.count('class="holiday-fx"')
    ck(f"  {key} 特效容器已插入", fx_count >= 1, str(fx_count))

print()
print("=== mode=off 应无 data-holiday ===")
post("/api/security/fx", {"fx_holiday_mode": "off",
                          "fx_holiday_key": "", "fx_effects": "1"})
time.sleep(0.3)
dom = dump_dom(BASE + "/", os.path.join(tmp, "off.html"))
m = re.search(r'<html[^>]*data-holiday="([^"]*)"', dom)
got = m.group(1) if m else "(无)"
ck("mode=off 无特效", got in ("", None) or "(无)" == got, f"实际 {got!r}")

print()
print("=== effects=0 应无特效 ===")
post("/api/security/fx", {"fx_holiday_mode": "manual",
                          "fx_holiday_key": "christmas", "fx_effects": "0"})
time.sleep(0.3)
dom = dump_dom(BASE + "/", os.path.join(tmp, "eff0.html"))
m = re.search(r'<html[^>]*data-holiday="([^"]*)"', dom)
got = m.group(1) if m else "(无)"
ck("effects=0 无特效", got in ("", None) or "(无)" == got, f"实际 {got!r}")

print()
print("=== 恢复 auto ===")
post("/api/security/fx", {"fx_holiday_mode": "auto",
                          "fx_holiday_key": "", "fx_effects": "1"})
pub = json.loads(get("/api/fx"))
ck("恢复 auto", pub.get("mode") == "auto", str(pub))

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
