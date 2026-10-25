#!/usr/bin/env python3
"""v2.0 测试:PWA 文件 + 2FA 全链路 + CI 检查"""
import base64
import hashlib
import hmac
import http.cookiejar
import json
import os
import re
import struct
import sys
import time
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


def totp_code(secret_b32, t=None):
    pad = "=" * ((8 - len(secret_b32) % 8) % 8)
    key = base64.b32decode(secret_b32 + pad)
    counter = (t or int(time.time())) // 30
    d = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    off = d[-1] & 0x0F
    return f"{(struct.unpack('>I', d[off:off+4])[0] & 0x7FFFFFFF) % 1000000:06d}"


print("=== PWA 文件 ===")
st, raw = get("/manifest.json")
ck("manifest 200", st == 200 and "至尊杰" in raw, str(st))
st, raw = get("/sw.js")
ck("sw.js 200", st == 200 and "CACHE_NAME" in raw, str(st))
ck("sw.js 不缓存 API", "'/api/'" in raw)
st, raw = get("/assets/icon-192.png")
ck("icon-192 200", st == 200, str(st))
st, raw = get("/assets/icon-512.png")
ck("icon-512 200", st == 200, str(st))
html = get("/index.html")[1]
ck("首页挂 manifest", 'rel="manifest"' in html)
ck("首页有 SW 注册", "serviceWorker.register" in html)

print()
print("=== 登录(未启用 2FA,动态码留空) ===")
svg = get("/admin/captcha.svg")[1]
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
data = urllib.parse.urlencode({"password": PWD, "captcha": cap, "totp": ""}).encode()
req = urllib.request.Request(BASE + "/admin/login", data=data,
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
body = op.open(req, timeout=15).read().decode("utf-8", "replace")
ck("无 2FA 登录成功", "panel-dashboard" in body)

print()
print("=== 2FA 绑定流程 ===")
st, raw = get("/api/security/2fa/setup")
d = json.loads(raw)
ck("setup 返回 uri", st == 200 and d.get("uri", "").startswith("otpauth://totp/"), f"{st} {raw[:80]}")
secret = re.search(r"secret=([A-Z2-7]+)", d["uri"]).group(1)
code = totp_code(secret)
st, d = post("/api/security/2fa/enable", {"code": code})
ck("enable 用真码成功", st == 200 and d.get("ok"), f"{st} {d}")

st, raw = get("/api/security/2fa/status")
d = json.loads(raw)
ck("status enabled=True", d.get("enabled") is True, str(d))

# 错码不能启用/关闭
st, d = post("/api/security/2fa/disable", {"code": "000000"})
ck("错码不能关闭", st == 400, f"{st} {d}")

print()
print("=== 带 2FA 登录 ===")
op2 = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def get2(p):
    r = op2.open(BASE + p, timeout=15)
    return r.read().decode("utf-8", "replace")


def post_form(opx, fields):
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(BASE + "/admin/login", data=data,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        r = opx.open(req, timeout=15)
        return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.read().decode("utf-8", "replace")


svg = get2("/admin/captcha.svg")
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
body = post_form(op2, {"password": PWD, "captcha": cap, "totp": ""})
ck("2FA 启用后:缺动态码被拒", "panel-dashboard" not in body and "动态码" in body, "(未拒或无提示)")

svg = get2("/admin/captcha.svg")
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
body = post_form(op2, {"password": PWD, "captcha": cap,
                       "totp": totp_code(secret)})
ck("2FA 启用后:真码登录成功", "panel-dashboard" in body)

print()
print("=== 关闭 2FA ===")
st, d = post("/api/security/2fa/disable", {"code": totp_code(secret)})
ck("真码关闭成功", st == 200 and d.get("ok"), f"{st} {d}")
st, raw = get("/api/security/2fa/status")
d = json.loads(raw)
ck("status enabled=False", d.get("enabled") is False, str(d))

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
