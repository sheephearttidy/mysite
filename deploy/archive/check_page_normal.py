#!/usr/bin/env python3
"""确认 auto 模式无节日时页面本身完全正常(只是没有粒子)"""
import re
import subprocess
import tempfile
import os

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
prof = tempfile.mkdtemp(prefix="chk_")
out = os.path.join(prof, "d.html")

subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                "--user-data-dir=" + prof, "--virtual-time-budget=8000",
                "--dump-dom", "https://imyxj.xyz/"],
               stdout=open(out, "w", encoding="utf-8"),
               stderr=subprocess.DEVNULL, timeout=180)
with open(out, encoding="utf-8", errors="replace") as f:
    dom = f.read()

print(f"DOM 长度: {len(dom)}")
print()
nav_links = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>',
                       dom.split('class="nav-links"')[1].split("</ul>")[0]) \
    if 'class="nav-links"' in dom else []

checks = [
    ("导航 7 个链接", len(nav_links) >= 7),
    ("导航含来访地图", any("map" in h for h, _ in nav_links)),
    ("首屏大字存在", "至尊杰" in dom),
    ("主内容区存在", "container" in dom),
    ("holiday.js 带版本", bool(re.search(r'js/holiday\.js\?v=[a-f0-9]+', dom))),
    ("无 data-holiday(auto+10-22 正确)", 'data-holiday=' not in dom),
    ("无粒子容器(正确)", 'class="holiday-fx"' not in dom),
]
for name, ok in checks:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")

print()
print("导航链接:")
for h, t in nav_links:
    print(f"  {h:16s} {t.strip()}")

print()
allok = all(c for _, c in checks)
print("=>", "页面正常,只是今天没有节日(符合预期)" if allok else "页面有问题")
import shutil
shutil.rmtree(prof, ignore_errors=True)
