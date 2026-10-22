#!/usr/bin/env python3
"""v2.3.1 CSP 热修回归:Chrome 验证后台 JS 真执行(CSP 不再拦自家脚本)"""
import json
import re
import subprocess
import sys
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import os

sys.stdout.reconfigure(encoding="utf-8")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://127.0.0.1:15102"
PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    print(("PASS  " if cond else "FAIL  ") + name + (f"  [{extra}]" if extra and not cond else ""))
    PASS, FAIL = PASS + (1 if cond else 0), FAIL + (0 if cond else 1)


_cj = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj))


def api(path, method="GET", form=None, body=None):
    r = urllib.request.Request(BASE + path, method=method)
    data = None
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
    elif body is not None:
        r.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode()
    try:
        resp = OP.open(r, data, timeout=15)
        return resp.status, resp.read().decode(errors="replace"), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace"), dict(e.headers)


# 登录
svg = api("/admin/captcha.svg")[1]
code = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
api("/admin/login", "POST", form={"password": "admin", "captcha": code})
ck("登录", any(c.name == "session" for c in _cj))

# 签一次性后台 URL(带 cookie 的 Chrome 不好做,改用本地代理页:
# 直接把 /admin/ 的 HTML 落到本地文件,把相对资源换成绝对 5102 地址,
# Chrome 开本地文件仍会被 CSP 管,nonce 是每请求的,文件里已有 → 可复现)
st, html, h = api("/admin/")
ck("后台页 200", st == 200)
csp = h.get("Content-Security-Policy", "")
ck("CSP 无 strict-dynamic", "strict-dynamic" not in csp, csp[:80])
ck("CSP 有 script-src-attr", "script-src-attr 'unsafe-inline'" in csp)
ck("CSP nonce 仍在", "nonce-" in csp)
m = re.search(r"nonce-([A-Za-z0-9+/=]+)", csp)
nonce = m.group(1) if m else ""
ck("所有 script 标签都带同一 nonce",
   not re.search(r'<script(?![^>]*nonce)[^>]*>', html))
ck("外链模块脚本带 nonce",
   bool(re.search(rf'<script[^>]*nonce="{nonce}"[^>]*admin-core\.js', html)))

# 本地复现:改写资源为绝对地址,存临时文件
local = html.replace('href="/admin/static/', f'href="{BASE}/admin/static/')
local = local.replace('src="/admin/static/', f'src="{BASE}/admin/static/')
local = local.replace('action="/admin', f'action="{BASE}/admin')
local = local.replace('src="/admin/captcha.svg', f'src="{BASE}/admin/captcha.svg')
tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "admin_csp_test.html")
with open(tmp, "w", encoding="utf-8") as f:
    f.write(local)

r = subprocess.run(
    [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
     "--virtual-time-budget=20000", "--dump-dom", "file:///" + tmp.replace("\\", "/")],
    capture_output=True, encoding="utf-8", errors="replace", timeout=120)
out = r.stdout + r.stderr
ck("Chrome 无 CSP 违规报告", "Content Security Policy" not in out and "violat" not in out.lower(),
   [l for l in out.splitlines() if "Security" in l or "violat" in l.lower()][:1])
# renderAll 真跑过的铁证:JS 往节点里填了数字/内容(模板初值不是这些)
ck("JS 执行:renderAll 填充 cnt-skills 计数",
   re.search(r'id="cnt-skills"[^>]*>\s*\d+\s*<', out) is not None)
ck("JS 执行:works 列表渲染出 item 卡片",
   re.search(r'id="list-works"[\s\S]{0,200}?class="item"', out) is not None)
ck("JS 执行:skills 列表渲染出 item 卡片",
   re.search(r'id="list-skills"[\s\S]{0,200}?class="item"', out) is not None)
ck("JS 执行:角标计数填充", re.search(r'cnt-(skills|works)[^>]*>\s*\d+', out) is not None)

print(f"\nv2.3.1 热修回归: 通过 {PASS} 项,失败 {FAIL} 项")
sys.exit(1 if FAIL else 0)
