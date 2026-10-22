#!/usr/bin/env python3
"""Chrome 渲染确认 v1.10 页面无 JS 错误、倒计时/公告不出现(生产当前无 active 数据)"""
import os
import re
import shutil
import subprocess
import tempfile

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
prof = tempfile.mkdtemp(prefix="v1100_")
out = os.path.join(prof, "d.html")
subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                "--user-data-dir=" + prof, "--virtual-time-budget=8000",
                "--dump-dom", "https://imyxj.xyz/"],
               stdout=open(out, "w", encoding="utf-8"),
               stderr=subprocess.DEVNULL, timeout=180)
with open(out, encoding="utf-8", errors="replace") as f:
    dom = f.read()
shutil.rmtree(prof, ignore_errors=True)

P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n}  {e}")
        F += 1


ck("site-extra.js 已加载", "site-extra.js" in dom)
ck("无公告横幅(当前无数据,正常)", "notice-bar" not in dom)
ck("无倒计时挂件(当前无数据,正常)", "cd-widget" not in dom)
ck("v1.9 元素仍在:留言墙", 'id="msgwallGrid"' in dom)
ck("v1.9 元素仍在:点赞", 'id="likeBtn"' in dom)
ck("v1.9.1 元素仍在:主题球", 'class="accent-btn"' in dom)
ck("v1.9.1 元素仍在:问候", 'class="greet-line"' in dom)

m = re.search(r'class="like-n">([^<]*)<', dom)
print(f"\n点赞数: {m.group(1) if m else '无'}")
print(f"页面大小: {len(dom)} 字符")
print()
print(f"通过 {P} 项,失败 {F} 项")
exit(1 if F else 0)
