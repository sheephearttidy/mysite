#!/usr/bin/env python3
"""v2.0.1 生产验证:四项修复逐一确认(Chrome 渲染)"""
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
prof = tempfile.mkdtemp(prefix="v201_")
out = os.path.join(prof, "d.html")
subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                "--user-data-dir=" + prof, "--virtual-time-budget=8000",
                "--dump-dom", "https://imyxj.xyz/"],
               stdout=open(out, "w", encoding="utf-8"),
               stderr=subprocess.DEVNULL, timeout=180)
dom = open(out, encoding="utf-8", errors="replace").read()
shutil.rmtree(prof, ignore_errors=True)
P = F = 0


def ck(n, c, e=""):
    global P, F
    print(("PASS  " if c else "FAIL  ") + n + ("  " + e if e and not c else ""))
    if c:
        P += 1
    else:
        F += 1


# 修复1:留言表单输入框样式(widgets.css 新增段)
ck("widgets.css 含 .sf-input 前台定义",
   ".sf-input" in urllib.request.urlopen(
       "https://imyxj.xyz/css/widgets.css?v=0b736f55", timeout=20).read().decode())
# 修复2:works 封面配色类改回 wc-N
st = urllib.request.urlopen("https://imyxj.xyz/works.html", timeout=20)
works = st.read().decode()
ck("works.html 用 wc-N(有配色)", 'work-cover wc-1' in works and 'cover-1' not in works)
# 修复3:公告条结构(nb-inner 栅格对齐)——无 active 公告时看 JS 源
se = urllib.request.urlopen("https://imyxj.xyz/js/site-extra.js?v=696152a5", timeout=20).read().decode()
ck("site-extra.js 插到 nav 前", "querySelector('nav.nav')" in se)
ck("site-extra.js 用 nb-inner 容器", 'nb-inner' in se)
wcss = urllib.request.urlopen(
    "https://imyxj.xyz/css/widgets.css?v=0b736f55", timeout=20).read().decode()
ck("widgets.css 有 nb-inner 栅格样式", ".nb-inner" in wcss and "max-width: 1080px" in wcss)
# 渲染确认
ck("首页正常渲染", "<title>" in dom and "至尊杰" in dom)
ck("留言墙区域在", 'id="msgwallGrid"' in dom)
ck("v2.0 SW 挂载仍在", "serviceWorker.register" in dom)
ck("works 卡片在渲染 DOM 有 wc-1", "wc-1" in dom if "work-cover" in dom else True)

print()
print(f"通过 {P} 项,失败 {F} 项")
exit(1 if F else 0)
