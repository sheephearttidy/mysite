#!/usr/bin/env python3
"""v2.3.0 生产验证:https://imyxj.xyz 安全头/CSP/Origin/登录链路"""
import json
import re
import sys
import urllib.parse
import urllib.request
import urllib.error
import http.cookiejar

sys.stdout.reconfigure(encoding="utf-8")
BASE = "https://imyxj.xyz"
PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    print(("PASS  " if cond else "FAIL  ") + name + (f"  [{extra}]" if extra and not cond else ""))
    PASS, FAIL = PASS + (1 if cond else 0), FAIL + (0 if cond else 1)


def call(path, method="GET", form=None, body=None, headers=None, opener=None):
    op = opener or urllib.request.build_opener()
    r = urllib.request.Request(BASE + path, method=method)
    for k, v in (headers or {}).items():
        r.add_header(k, v)
    data = None
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
    elif body is not None:
        r.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode()
    try:
        resp = op.open(r, data, timeout=15)
        return resp.status, resp.read().decode(errors="replace"), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace"), dict(e.headers)


# ---------- 匿名可见面 ----------
st, html, h = call("/admin/login")
ck("登录页 200", st == 200)
csp = h.get("Content-Security-Policy", "")
ck("登录页 CSP(nginx always 透传)", "default-src 'self'" in csp, csp[:60])
ck("CSP 含 nonce", "nonce-" in csp)
ck("CSP frame-ancestors", "frame-ancestors 'self'" in csp)
ck("CSP object-src none", "object-src 'none'" in csp)
ck("登录页 no-store", "no-store" in h.get("Cache-Control", ""))
ck("HSTS 仍在", h.get("Strict-Transport-Security", "").startswith("max-age"))
ck("内联脚本 nonce 注入", bool(re.search(r'<script nonce="[A-Za-z0-9+/=]{16,}">', html)))

st, b, h = call("/")
ck("首页 200", st == 200)
csp2 = h.get("Content-Security-Policy", "")
ck("首页 CSP(前台版,无 nonce)", "script-src 'self'" in csp2 and "nonce-" not in csp2, csp2[:80])
ck("首页 style-src 放行 Google Fonts", "fonts.googleapis.com" in csp2)

# ---------- Origin 校验 ----------
st, b, _ = call("/api/messages", "POST", body={"name": "a", "body": "b"},
                headers={"Origin": "https://evil.example"})
ck("生产跨站 POST → 403", st == 403, f"st={st}")
st, b, _ = call("/api/messages", "POST", body={"name": "a", "body": "b"},
                headers={"Referer": "https://evil.example/x"})
ck("生产恶意 Referer → 403", st == 403, f"st={st}")
st, b, _ = call("/api/health")
ck("正常 GET 不受影响(health 200)", st == 200, f"st={st}")

# ---------- 管理员登录链路(密码从 env 读) ----------
import os
PWD = os.environ.get("PROD_PWD", "")
ck("PROD_PWD 已注入", bool(PWD))
cj = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
svg = call("/admin/captcha.svg", opener=OP)[1]
code = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
st, b, _ = call("/admin/login", "POST", opener=OP,
                form={"password": PWD, "captcha": code})
ck("管理员登录成功", st in (200, 302))
st, b, h = call("/admin/", opener=OP)
ck("后台页 200+CSP", st == 200 and "Content-Security-Policy" in h)
ck("后台页 nonce 注入", bool(re.search(r'<script nonce="', b)))
st, b, _ = call("/api/security/overview", opener=OP)
s = json.loads(b)["settings"]
ck("overview 正常,含 v2.3 新键",
   all(k in s for k in ("sec_pass_minlen", "sec_pass_classes",
                        "sec_login_delay", "sec_bind_ip")))
st, b, _ = call("/api/security/settings", "POST", opener=OP,
                body={"sec_pass_minlen": 99})
ck("越界值拒绝(99 位)", st == 400)
st, b, _ = call("/api/security/settings", "POST", opener=OP,
                body={"sec_pass_minlen": 8})
ck("合法值写回 8", st == 200)
ck("退出", call("/admin/logout", opener=OP)[0] in (200, 302))

print(f"\n生产验证: 通过 {PASS} 项,失败 {FAIL} 项")
sys.exit(1 if FAIL else 0)
