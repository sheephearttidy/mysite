#!/usr/bin/env python3
"""v2.0.0 生产验证:PWA + 2FA(绑定→登录→关闭,全程不留启用状态)"""
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

BASE = "https://imyxj.xyz"
PWD = os.environ.get("PROD_PWD", "")
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
        r = op.open(BASE + p, timeout=20)
        return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def post(p, obj):
    data = json.dumps(obj).encode()
    req = urllib.request.Request(BASE + p, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        r = op.open(req, timeout=20)
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


print("=== PWA(匿名可测) ===")
st, raw = get("/manifest.json")
ck("manifest 200", st == 200 and "至尊杰" in raw, str(st))
st, raw = get("/sw.js")
ck("sw.js 200 且不缓存 API", st == 200 and "'/api/'" in raw, str(st))
st, raw = get("/assets/icon-192.png")
ck("icon-192 200", st == 200, str(st))
html = get("/")[1]
ck("首页挂 manifest+SW", 'rel="manifest"' in html and "serviceWorker.register" in html)

print()
print("=== 登录后台 ===")
if not PWD:
    print("(未设 PROD_PWD)")
    sys.exit(1 if F else 0)
svg = get("/admin/captcha.svg")[1]
cap = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
data = urllib.parse.urlencode({"password": PWD, "captcha": cap, "totp": ""}).encode()
req = urllib.request.Request(BASE + "/admin/login", data=data,
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
body = op.open(req, timeout=20).read().decode("utf-8", "replace")
ck("登录成功", "panel-dashboard" in body)

print()
print("=== 2FA 生产绑定(立即回滚,不留启用状态) ===")
st, raw = get("/api/security/2fa/setup")
d = json.loads(raw)
ck("setup uri", st == 200 and d.get("uri", "").startswith("otpauth://"), f"{st}")
secret = re.search(r"secret=([A-Z2-7]+)", d["uri"]).group(1)
st, d = post("/api/security/2fa/enable", {"code": totp_code(secret)})
ck("enable 成功", st == 200 and d.get("ok"), f"{st} {d}")
st, raw = get("/api/security/2fa/status")
ck("enabled=True", json.loads(raw).get("enabled") is True, raw[:60])
st, d = post("/api/security/2fa/disable", {"code": totp_code(secret)})
ck("disable 成功(现场还原)", st == 200 and d.get("ok"), f"{st} {d}")
st, raw = get("/api/security/2fa/status")
ck("enabled=False(最终状态)", json.loads(raw).get("enabled") is False, raw[:60])

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
