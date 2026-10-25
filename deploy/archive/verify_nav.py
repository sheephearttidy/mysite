#!/usr/bin/env python3
"""生产:验证 7 个页面导航完全一致(含来访地图)"""
import re
import ssl
import sys
import urllib.request

B = "https://imyxj.xyz"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

EXPECT = ["首页", "关于我", "技能树", "小破项目", "校园日常", "来访地图", "来找我玩"]
PAGES = {"index": "", "about": "about.html", "skills": "skills.html",
         "works": "works.html", "campus": "campus.html",
         "map": "map.html", "contact": "contact.html"}
P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n}  {e}")
        F += 1


for name, fn in PAGES.items():
    url = B + ("/" + fn if fn else "/")
    body = urllib.request.urlopen(url, timeout=15, context=ctx).read().decode("utf-8", "replace")
    nav = re.findall(r'<li><a href="/[^"]*"[^>]*>([^<]+)</a></li>', body)
    ck(f"{name} 导航 7 项一致", nav == EXPECT, str(nav))
    ck(f"{name} 有来访地图链接", "/map.html" in body)

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
