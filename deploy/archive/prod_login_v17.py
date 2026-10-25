#!/usr/bin/env python3
"""生产环境:登录 + 看板城市区块验证"""
import http.cookiejar
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request
from urllib.error import HTTPError

B = "https://imyxj.xyz"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

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
op = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cj),
    urllib.request.HTTPSHandler(context=ctx))


def open_url(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    return op.open(req, timeout=15)


svg = open_url(B + "/admin/captcha.svg").read().decode()
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
ck("验证码可取", len(cap) >= 4, repr(cap))

pwd = os.environ.get("PROD_PWD", "")
ck("生产密码已提供", len(pwd) > 0)
data = urllib.parse.urlencode({"password": pwd, "captcha": cap}).encode()
try:
    r = open_url(B + "/admin/login", data=data,
                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    body = r.read().decode("utf-8", "replace")
    st = r.status
except HTTPError as e:
    st = e.code
    body = e.read().decode("utf-8", "replace")

ck("登录成功进后台", st == 200 and "panel-dashboard" in body, f"{st}")

# 看板接口返回城市
try:
    r = open_url(B + "/api/stats/visits?days=7")
    j = json.loads(r.read().decode())
    ck("看板含 cities", "cities" in j, str(list(j.keys())))
    ck("cities 是数组", isinstance(j["cities"], list))
    # 登录后能拿到新写入的南京/北京记录
    if j["cities"]:
        ck("cities 有数据", len(j["cities"]) > 0, str(j["cities"][:3]))
except Exception as e:
    ck("看板含 cities", False, str(e)[:120])

# 管理页 HTML 含城市区块
try:
    r = open_url(B + "/admin/")
    b2 = r.read().decode("utf-8", "replace")
    ck("管理页含城市区块", "dashCities" in b2)
    ck("管理页含 holiday 接入", "holiday.js" in b2 and "holidays.css" in b2)
except Exception as e:
    ck("管理页含城市区块", False, str(e)[:120])

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
