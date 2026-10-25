#!/usr/bin/env python3
"""生产环境验证:前台主题功能 + 后台登录页主题"""
import re
import ssl
import sys
import urllib.request

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


def get(path):
    req = urllib.request.Request(B + path)
    r = urllib.request.urlopen(req, timeout=15, context=ctx)
    return r.status, r.read().decode("utf-8", "replace")


st, body = get("/")
ck("前台 200", st == 200, str(st))
ck("前台含 themeToggle", 'id="themeToggle"' in body)
ck("前台含 theme.js", 'src="js/theme.js"' in body)
ck("前台含防闪脚本", "尽早应用主题" in body or "data-theme-source" in body)
ck("前台含双 meta", body.count('name="theme-color"') >= 2)

st, css = get("/css/dark.css")
ck("dark.css 200", st == 200)
ck("dark.css 含 Morandi 深色块", '[data-theme="dark"]' in css and "#d488a6" in css)

st, js = get("/js/theme.js")
ck("theme.js 200", st == 200)
ck("theme.js 前后台通用", "themeToggle" in js and "themeBtn" in js)

st, lh = get("/admin/login")
ck("登录页 200", st == 200)
ck("登录页含主题按钮", 'id="themeBtn"' in lh)
ck("登录页含 theme.js", "js/theme.js" in lh)
ck("登录页含防闪", "尽早应用主题" in lh)
ck("登录页含双 meta", lh.count('name="theme-color"') >= 2)

st, ac = get("/admin/static/css/admin.css")
ck("admin.css 200", st == 200)
ck("admin.css 含深色块", '[data-theme="dark"]' in ac)
ck("admin.css 含主题按钮样式", ".theme-btn" in ac)
ck("admin.css 含 bf- 类", ".bf-pink" in ac)

st, aj = get("/admin/static/js/admin.js")
ck("admin.js 200", st == 200)
ck("admin.js 无 COLORS 硬编码", "COLORS" not in aj)
ck("admin.js 用 bf- 类", "bf-" in aj)

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
