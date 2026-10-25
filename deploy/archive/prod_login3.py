#!/usr/bin/env python3
"""生产环境:真实登录测试(多页拆分后确认后台正常)"""
import http.cookiejar
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
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))


def json_dumps(d):
    import json
    return json.dumps(d).encode()


def open_url(url, data=None):
    req = urllib.request.Request(url, data=data)
    return op.open(req, timeout=15)


svg = open_url(B + "/admin/captcha.svg").read().decode()
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
ck("验证码可取", len(cap) >= 4, repr(cap))

pwd = os.environ.get("PROD_PWD", "")
ck("生产密码已提供", len(pwd) > 0)
data = urllib.parse.urlencode({"password": pwd, "captcha": cap}).encode()
try:
    r = open_url(B + "/admin/login", data=data)
    body = r.read().decode("utf-8", "replace")
    st = r.status
except HTTPError as e:
    st = e.code
    body = e.read().decode("utf-8", "replace")

ck("登录成功进后台", st == 200 and "panel-dashboard" in body, f"{st}")
ck("后台主题按钮", 'id="themeBtn"' in body)

# 访问统计:提交 about 页路径应被接受
try:
    r = open_url(B + "/api/track", data=json_dumps({"path": "/about.html"}))
    ck("about 页可统计", r.status == 200)
except HTTPError as e:
    ck("about 页可统计", False, f"{e.code}")

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
