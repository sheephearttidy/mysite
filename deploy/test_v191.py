#!/usr/bin/env python3
"""v1.9.1 氛围包验证(测试环境):页面挂载 + ambience.js 内容"""
import re
import sys
import urllib.request

BASE = "http://127.0.0.1:5102"
P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n}  {e}")
        F += 1


def get(p):
    r = urllib.request.urlopen(BASE + p, timeout=15)
    return r.read().decode("utf-8", "replace")


js = get("/js/ambience.js")
ck("ambience.js 200", len(js) > 500)
for kw in ("THEMES", "applyAccent", "initAccent", "initGreeting", "mysite_accent"):
    ck(f"含 {kw}", kw in js)
ck("用 --pink 变量", "--pink" in js)
ck("六套主题", js.count("key: '") >= 6)

pages = ["index.html", "about.html", "skills.html", "works.html",
         "campus.html", "map.html", "contact.html"]
for p in pages:
    html = get("/" + p)
    ck(f"{p} 挂 ambience.js", "js/ambience.js" in html)
    m = re.search(r'src="js/ambience\.js\?v=([a-f0-9]{8})"', html)
    ck(f"{p} 带版本参数", bool(m))

css = get("/css/widgets.css")
ck("CSS 含 accent-btn", ".accent-btn" in css)
ck("CSS 含 greet-line", ".greet-line" in css)

# 问候插在 .role 前面:确认 index 有 .hero .role 结构
html = get("/index.html")
ck("index 有 .role 挂载点", 'class="role"' in html)

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
