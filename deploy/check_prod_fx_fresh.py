#!/usr/bin/env python3
"""用全新的 Chrome 用户目录渲染,彻底排除本地缓存干扰"""
import re
import subprocess
import sys
import tempfile
import shutil
import os

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = "https://imyxj.xyz/"
P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n}  {e}")
        F += 1


# 每次全新 profile,等价于无痕/首次访问
prof = tempfile.mkdtemp(prefix="chrome_fresh_")
out = os.path.join(prof, "dom.html")

print(f"用全新 profile 渲染 {URL} ...")
subprocess.run([
    CHROME, "--headless", "--disable-gpu", "--no-sandbox",
    "--user-data-dir=" + prof,
    "--disable-application-cache", "--disk-cache-size=1",
    "--virtual-time-budget=8000", "--dump-dom", URL,
], stdout=open(out, "w", encoding="utf-8"), stderr=subprocess.DEVNULL, timeout=180)

with open(out, encoding="utf-8", errors="replace") as f:
    dom = f.read()

print(f"DOM 长度: {len(dom)}")
print()

m = re.search(r'<html[^>]*data-holiday="([^"]*)"', dom)
got = m.group(1) if m else ""
print(f"data-holiday = {got!r}")

ck("data-holiday 已设置", bool(got), "空 = 没有节日特效")
ck("holiday-fx 容器已插入", 'class="holiday-fx"' in dom)

m2 = re.search(r'data-holiday-label="([^"]*)"', dom)
print(f"label = {m2.group(1) if m2 else '(无)'}")

# 统计各粒子
for cls in ("plane", "candle", "heart", "flag", "snowflake", "streamer", "teacher-star"):
    n = dom.count(f'class="{cls}"')
    if n:
        print(f"  {cls}: {n} 个")

ck("有粒子渲染", any(dom.count(f'class="{c}"') for c in
                    ("plane", "candle", "heart", "flag", "snowflake", "streamer", "teacher-star")))

# 检查 holiday.js 版本
mm = re.search(r'js/holiday\.js\?v=([a-f0-9]+)', dom)
print(f"\nholiday.js 版本: {mm.group(1) if mm else '(无版本参数!)'}")
ck("带版本参数", bool(mm))

shutil.rmtree(prof, ignore_errors=True)

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
