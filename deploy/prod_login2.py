#!/usr/bin/env python3
"""生产环境:真实登录测试(验证码 + 密码),确认后台可正常进入"""
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

def open_url(url, data=None):
    req = urllib.request.Request(url, data=data)
    return op.open(req, timeout=15)

# 验证码
svg = open_url(B + "/admin/captcha.svg").read().decode()
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
ck("验证码图可取", len(cap) >= 4, repr(cap))

# 登录(密码从环境变量读,永不落盘)
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

ck("登录成功进入后台", st == 200 and "panel-dashboard" in body, f"{st}")
ck("后台含主题按钮", 'id="themeBtn"' in body)
ck("后台含 admin.css", "css/admin.css" in body)
ck("后台含防闪", "尽早应用主题" in body)

# 错误消息(若登录失败)
m = re.search(r'<div class="err[^"]*">(.*?)</div>', body, re.S)
if m and "panel-dashboard" not in body:
    print("  错误消息:", m.group(1).strip()[:80])

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
