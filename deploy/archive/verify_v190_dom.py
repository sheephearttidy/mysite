#!/usr/bin/env python3
"""真实浏览器渲染生产首页:确认留言墙/点赞/标题彩蛋元素都在"""
import re
import subprocess
import tempfile
import os

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
prof = tempfile.mkdtemp(prefix="v190_")
out = os.path.join(prof, "d.html")

subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                "--user-data-dir=" + prof, "--virtual-time-budget=8000",
                "--dump-dom", "https://imyxj.xyz/"],
               stdout=open(out, "w", encoding="utf-8"),
               stderr=subprocess.DEVNULL, timeout=180)
with open(out, encoding="utf-8", errors="replace") as f:
    dom = f.read()

import shutil
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


ck("留言墙容器", 'id="msgwallGrid"' in dom)
ck("留言输入框", 'id="msgBody"' in dom)
ck("发送按钮", 'id="msgSend"' in dom)
ck("点赞按钮", 'id="likeBtn"' in dom)
ck("计数 span", 'class="like-n"' in dom)
ck("interact.js 已加载", "interact.js" in dom)
ck("标题彩蛋代码", "别走嘛" in dom)

# 点赞数字被 JS 填充(不再是 –)
m = re.search(r'class="like-n">([^<]*)<', dom)
print(f"\n点赞数字: {m.group(1) if m else '(无)'}")
ck("点赞数字已填充", m and m.group(1) not in ("–", ""), m.group(1) if m else "无")

print()
print(f"通过 {P} 项,失败 {F} 项")
exit(1 if F else 0)
