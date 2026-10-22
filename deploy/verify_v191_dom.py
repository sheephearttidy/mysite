#!/usr/bin/env python3
"""真实浏览器验证 v1.9.1:主题色按钮 + 问候语渲染"""
import os
import re
import shutil
import subprocess
import tempfile

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
prof = tempfile.mkdtemp(prefix="v191_")
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


ck("ambience.js 已加载", "ambience.js" in dom)
ck("主题色按钮已渲染", 'class="accent-btn"' in dom)
ck("六色面板已渲染", 'class="accent-panel"' in dom)
ck("面板含 6 个色点", dom.count("accent-opt") >= 6)
ck("问候语已插入", 'class="greet-line"' in dom)
ck("问候 emoji 已插入", 'class="greet-emoji"' in dom)

m = re.search(r'class="greet-line">([^<]*)<', dom)
print(f"\n问候内容: {m.group(1) if m else '(无)'} (现在是 16 点段,应为 下午好!)")
ck("问候文案正确", m and "好!" in m.group(1), m.group(1) if m else "无")

# v1.9.0 互动元素仍在(回归)
ck("留言墙仍在", 'id="msgwallGrid"' in dom)
ck("点赞按钮仍在", 'id="likeBtn"' in dom)

print()
print(f"通过 {P} 项,失败 {F} 项")
exit(1 if F else 0)
