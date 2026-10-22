#!/usr/bin/env python3
"""本地用 headless Chrome 渲染生产页面,验证特效真的渲染
(PIL 只能看像素,这里用 --dump-dom 拿 DOM 更准)
"""
import re
import subprocess
import sys
import tempfile

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


tmp = tempfile.mkdtemp()
out = tmp + r"\dom.html"

print(f"渲染 {URL} ...")
subprocess.run([
    CHROME, "--headless", "--disable-gpu", "--no-sandbox",
    "--virtual-time-budget=6000", "--dump-dom", URL,
], stdout=open(out, "w", encoding="utf-8"), stderr=subprocess.DEVNULL, timeout=120)

with open(out, encoding="utf-8", errors="replace") as f:
    dom = f.read()

print(f"DOM 长度: {len(dom)}")
print()

# 1. data-holiday 是否设置
m = re.search(r'<html[^>]*data-holiday="([^"]*)"', dom)
got = m.group(1) if m else ""
print(f"data-holiday = {got!r}")
ck("data-holiday 已设置(非空)", bool(got), "空 = 没有节日特效")
ck("与后台 manual/memorial 一致", got == "memorial", f"实际 {got!r}")

# 2. 特效容器
ck("holiday-fx 容器已插入", 'class="holiday-fx"' in dom)

# 3. 蜡烛粒子(memorial 用 .candle)
candles = dom.count('class="candle"')
print(f"蜡烛粒子数: {candles}")
ck("蜡烛粒子已生成(应为 6 个)", candles == 6, f"实际 {candles}")

# 4. label
m2 = re.search(r'data-holiday-label="([^"]*)"', dom)
ck("label = 国家公祭日", m2 and m2.group(1) == "国家公祭日", m2.group(1) if m2 else "无")

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
