#!/usr/bin/env python3
"""生产验证 v1.4.0"""
import os
import sys
import requests

B = "https://imyxj.xyz"
PWD = os.environ.get("TEST_PWD", "")
P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n} {e}")
        F += 1


def login(sess, pwd=None):
    """完整登录:先拿验证码,再从生产页面的 SVG 里人工无法读,
    所以这里只验证「有验证码时纯密码登录会失败」"""
    return sess.post(f"{B}/admin/login", data={"password": pwd or PWD},
                     allow_redirects=False, timeout=15)


print("=== 1. 简历功能已彻底移除 ===")
h = requests.get(B + "/", timeout=15).text
ck("无 resumeBtn", "resumeBtn" not in h)
ck("无 printHint", "printHint" not in h)
ck("无 doPrintBtn", "doPrintBtn" not in h)
ck("无「下载简历」文案", "下载简历" not in h)
ck("无 print-hint 类", "print-hint" not in h)
css = requests.get(B + "/css/style.css", timeout=15).text
ck("CSS 无 @media print", "@media print" not in css)
ck("CSS 无 print-hint", "print-hint" not in css)
ck("CSS 无 @page", "@page" not in css)
js = requests.get(B + "/js/main.js", timeout=15).text
ck("JS 无 window.print", "window.print" not in js)
ck("JS 无 initResume", "initResume" not in js)
ck("JS 仍保留访问上报", "/api/track" in js)

print()
print("=== 2. 验证码 ===")
r = requests.get(B + "/admin/captcha.svg", timeout=15)
ck("200", r.status_code == 200, f"实得 {r.status_code}")
ck("是 SVG", "svg" in r.headers.get("Content-Type", ""),
   r.headers.get("Content-Type"))
ck("含 <svg", b"<svg" in r.content)
ck("禁止缓存", "no-store" in r.headers.get("Cache-Control", ""),
   r.headers.get("Cache-Control"))
svg = r.content.decode("utf-8", "ignore")
ck("4 个字符", svg.count("<text") == 4, f"实得 {svg.count('<text')}")
ck("有干扰线", svg.count("<path") >= 4)
ck("有噪点", svg.count("<circle") >= 20)
ck("有旋转", "rotate(" in svg)
# 两次不同
r2 = requests.get(B + "/admin/captcha.svg", timeout=15)
ck("每次不同", r.content != r2.content)

print()
print("=== 3. 登录页含验证码 ===")
h = requests.get(B + "/admin/login", timeout=15).text
ck("验证码输入框", 'name="captcha"' in h)
ck("验证码图片", 'id="capImg"' in h)
ck("指向 captcha.svg", '/admin/captcha.svg' in h)
ck("点击刷新", 'capBox' in h)
ck("提示 3 分钟", "3 分钟" in h)

print()
print("=== 4. 有验证码时纯密码登录必须失败 ===")
s = requests.Session()
r = login(s)
ck("返回 302", r.status_code == 302, f"实得 {r.status_code}")
ck("未进入后台", s.get(B + "/admin/", allow_redirects=False,
                        timeout=15).status_code == 302)
ck("仍停在登录页", s.get(B + "/admin/login", timeout=15).status_code == 200)

print()
print("=== 5. 验证码错误 + 密码正确 也必须失败 ===")
s = requests.Session()
s.get(B + "/admin/captcha.svg", timeout=15)
r = s.post(B + "/admin/login",
           data={"password": PWD, "captcha": "ZZZZ"},
           allow_redirects=False, timeout=15)
ck("302 回登录页", r.status_code == 302, f"实得 {r.status_code}")
ck("未进入后台", s.get(B + "/admin/", allow_redirects=False,
                       timeout=15).status_code == 302)

print()
print("=== 6. 安全接口未登录全部 401 ===")
for path, method in [("/api/security/overview", "get"), ("/api/security/settings", "get"),
                     ("/api/security/audit", "get"), ("/api/security/settings", "post"),
                     ("/api/security/unblock", "post"), ("/api/security/revoke", "post"),
                     ("/api/security/revoke-all", "post"), ("/api/security/audit", "delete")]:
    r = getattr(requests, method)(B + path, json={}, timeout=15)
    ck(f"{method.upper()} {path}", r.status_code == 401, f"实得 {r.status_code}")

print()
print("=== 7. 原有功能完好 ===")
d = requests.get(B + "/api/content", timeout=15).json()
ck("skills=8", len(d["skills"]) == 8, f"实得 {len(d['skills'])}")
ck("timeline=4", len(d["timeline"]) == 4)
ck("stats=4", len(d["stats"]) == 4)
ck("works=6", len(d["works"]) == 6)
ck("profile=7", len(d["profile"]) == 7)
ck("SEO 资源仍在", requests.get(B + "/robots.txt", timeout=15).status_code == 200)
ck("og 图仍在", requests.get(B + "/assets/og-image.png", timeout=15).status_code == 200)
ck("访问上报仍在", requests.post(B + "/api/track", json={"path": "/"},
                                timeout=15).status_code == 200)

print()
print("=== 8. 安全加固仍生效 ===")
hd = requests.get(B + "/", timeout=15).headers
ck("HSTS", "strict-transport-security" in {k.lower() for k in hd})
ck("nosniff", "x-content-type-options" in {k.lower() for k in hd})
ck("X-Frame-Options", "x-frame-options" in {k.lower() for k in hd})
ck("未登录写被拒",
   requests.post(B + "/api/works", json={}, timeout=15).status_code == 401)
ck("db 仍 404",
   requests.get(B + "/admin/data/mysite.db", timeout=15).status_code == 404)
ck("py 源码 403",
   requests.get(B + "/admin/captcha.py", timeout=15).status_code in (403, 404))
ck("3MB 请求 413",
   requests.post(B + "/api/works", data=b"A" * (3 * 1024 * 1024),
                 headers={"Content-Type": "application/json"},
                 timeout=20).status_code == 413)

print()
print("=== 9. 验证码限速生效 ===")
codes = []
for i in range(40):
    codes.append(requests.get(B + "/admin/captcha.svg", timeout=15).status_code)
n429 = codes.count(429)
ck("高频请求被限速(出现 429)", n429 > 0, f"429 次数 {n429}")
ck("限速后仍有正常响应", 200 in codes, f"200 次数 {codes.count(200)}")

print()
print("=" * 40)
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(0 if F == 0 else 1)
