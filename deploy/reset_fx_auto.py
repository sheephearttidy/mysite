#!/usr/bin/env python3
"""把生产 fx 恢复为 auto(正常状态:按日期自动,今天 10-22 无节日)"""
import http.cookiejar
import json
import os
import re
import urllib.parse
import urllib.request

BASE = "https://imyxj.xyz"
PWD = os.environ.get("PROD_PWD", "")
op = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def get(p):
    return op.open(BASE + p, timeout=20).read().decode("utf-8", "replace")


svg = get("/admin/captcha.svg")
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
data = urllib.parse.urlencode({"password": PWD, "captcha": cap}).encode()
req = urllib.request.Request(BASE + "/admin/login", data=data,
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
op.open(req, timeout=20).read()

body = json.dumps({"fx_holiday_mode": "auto", "fx_holiday_key": "",
                   "fx_effects": "1"}).encode()
req = urllib.request.Request(BASE + "/api/security/fx", data=body,
                             headers={"Content-Type": "application/json"})
print("POST:", op.open(req, timeout=20).read().decode()[:120])

print("当前 /api/fx:", json.loads(get("/api/fx")))
