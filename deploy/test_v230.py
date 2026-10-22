#!/usr/bin/env python3
"""v2.3.0 安全加固验收:Origin 校验/CSP/密码策略/限制值拒绝/IP 绑定审计"""
import json
import re
import sys
import urllib.parse
import urllib.request
import urllib.error
import http.cookiejar

sys.stdout.reconfigure(encoding="utf-8")
BASE = "http://127.0.0.1:5102"
PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    print(("PASS  " if cond else "FAIL  ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if cond:
        PASS += 1
    else:
        FAIL += 1


_cj = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj))


def api(path, method="GET", form=None, body=None, headers=None, opener=None):
    op = opener or OPENER
    data = None
    r = urllib.request.Request(BASE + path, method=method)
    for k, v in (headers or {}).items():
        r.add_header(k, v)
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
    elif body is not None:
        r.add_header("Content-Type", "application/json")
        data = json.dumps(body).encode()
    try:
        resp = op.open(r, data, timeout=15)
        return resp.status, resp.read().decode(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), dict(e.headers)


# ---------- 登录 ----------
svg = api("/admin/captcha.svg")[1]
code = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", svg))
api("/admin/login", "POST", form={"password": "admin", "captcha": code})
ck("登录成功", any(c.name == "session" for c in _cj))

# ---------- CSP ----------
st, html, hh = api("/admin/login")
csp = hh.get("Content-Security-Policy", "")
ck("登录页带 CSP", "Content-Security-Policy" in hh)
ck("CSP 含 nonce-", "nonce-" in csp)
ck("CSP 禁 object", "object-src 'none'" in csp)
m = re.search(r"nonce-([A-Za-z0-9+/=]+)", csp)
nonce = m.group(1) if m else ""
ck("内联脚本带同一 nonce", f'nonce="{nonce}"' in html if nonce else False)
ck("登录页 no-store", "no-store" in hh.get("Cache-Control", ""))
st, html, hh = api("/admin")
ck("后台页带 CSP", "Content-Security-Policy" in hh)
m2 = re.search(r'nonce="([A-Za-z0-9+/=]+)"', html)
ck("后台页 nonce 注入", bool(m2))

# ---------- Origin 校验 ----------
anon = urllib.request.build_opener()
st, b, _ = api("/api/messages", "POST",
               body={"name": "a", "body": "b"},
               headers={"Origin": "https://evil.example"}, opener=anon)
ck("跨站 Origin POST → 403", st == 403, f"st={st} {b[:60]}")
st, b, _ = api("/api/messages", "POST",
               body={"name": "a", "body": "b"},
               headers={"Origin": "https://imyxj.xyz"}, opener=anon)
# 429=留言 60s 限速:说明请求已通过 Origin 校验到达业务逻辑
ck("本站 Origin POST 正常放行(200/201/429)", st in (200, 201, 429), f"st={st}")
st, b, _ = api("/api/messages", "POST",
               body={"name": "a", "body": "b"},
               headers={"Referer": "https://evil.example/attack"},
               opener=anon)
ck("恶意 Referer POST → 403", st == 403, f"st={st}")

# ---------- 密码策略 ----------
# 注意:old=admin 是正确旧密码,策略通过就真改密(并清 session),流程要按真改密设计
def set_policy(minlen, classes):
    return api("/api/security/settings", "POST",
               body={"sec_pass_minlen": minlen, "sec_pass_classes": classes})


def try_pwd(old, new):
    return api("/api/password", "POST", body={"old": old, "new": new})


def relogin(pwd="admin"):
    s2 = api("/admin/captcha.svg")[1]
    code2 = "".join(re.findall(r"<text[^>]*>([A-Z0-9])</text>", s2))
    api("/admin/login", "POST", form={"password": pwd, "captcha": code2})
    return any(c.name == "session" for c in _cj)


st, b, _ = set_policy(8, 3)
ck("保存密码策略(8位/3类)", st == 200)
ck("弱密码 abc123 → 拒(长度+种类)", try_pwd("admin", "abc123")[0] == 400)
ck("8位2类 password1 → 拒(种类)", try_pwd("admin", "password1")[0] == 400)
st, b, _ = try_pwd("admin", "Qwe12345")
ck("8位3类 Qwe12345 → 策略通过,真改密 200", st == 200, f"st={st} {b[:50]}")
ck("改密后 session 已清,需重登", relogin("Qwe12345"))
st, b, _ = try_pwd("Qwe12345", "Admin2026x")
ck("新密码再改一步也按策略走", st == 200, f"st={st}")
ck("二次改密后再重登", relogin("Admin2026x"))
set_policy(8, 2)
ck("策略越界 65 位 → 400", api("/api/security/settings", "POST",
   body={"sec_pass_minlen": 65})[0] == 400)
ck("策略越界 5 类 → 400", api("/api/security/settings", "POST",
   body={"sec_pass_classes": 5})[0] == 400)
ck("时延越界 11 秒 → 400", api("/api/security/settings", "POST",
   body={"sec_login_delay": 11})[0] == 400)

# ---------- 审计含新动作 ----------
st, b, _ = api("/api/security/audit?limit=500")
acts = {r["action"] for r in json.loads(b)["rows"]}
ck("审计记录 csrf_block", "csrf_block" in acts)
ck("审计记录 sec_settings", "sec_settings" in acts)

print(f"\n通过 {PASS} 项,失败 {FAIL} 项")
sys.exit(1 if FAIL else 0)
