#!/usr/bin/env python3
"""深挖:为什么浏览器里 data-holiday 是空的
对比:直接访问 /api/fx vs 页面里同步 XHR
"""
import json
import re
import subprocess
import tempfile

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
tmp = tempfile.mkdtemp()

print("=== 1. 直接用 Chrome 打开 /api/fx(确认浏览器能拿到数据) ===")
out1 = tmp + r"\api.html"
subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                "--virtual-time-budget=5000", "--dump-dom", "https://imyxj.xyz/api/fx"],
               stdout=open(out1, "w", encoding="utf-8"), stderr=subprocess.DEVNULL, timeout=120)
with open(out1, encoding="utf-8", errors="replace") as f:
    d1 = f.read()
print("  DOM:", d1[:300])

print()
print("=== 2. 页面里 holiday.js 的实际内容(从生产 URL 拿) ===")
import urllib.request
html = urllib.request.urlopen("https://imyxj.xyz/", timeout=20).read().decode()
m = re.search(r'js/holiday\.js\?v=([a-f0-9]+)', html)
print(f"  页面引用: js/holiday.js?v={m.group(1) if m else '无'}")
js = urllib.request.urlopen(f"https://imyxj.xyz/js/holiday.js?v={m.group(1)}", timeout=20).read().decode()
print(f"  JS 长度: {len(js)}")
print("  JS 中 readConfig 片段:")
i = js.find("function readConfig")
print("  " + js[i:i+400].replace("\n", "\n  "))

print()
print("=== 3. 用 Chrome 渲染并抓 console 错误 ===")
out2 = tmp + r"\console.txt"
subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                "--virtual-time-budget=6000", "--enable-logging=stderr",
                "--v=1", "--dump-dom", "https://imyxj.xyz/"],
               stdout=subprocess.DEVNULL,
               stderr=open(out2, "w", encoding="utf-8"), timeout=120)
with open(out2, encoding="utf-8", errors="replace") as f:
    log = f.read()
# 找相关错误
for line in log.split("\n"):
    low = line.lower()
    if any(k in low for k in ("error", "xhr", "api/fx", "holiday", "blocked", "cors")):
        print("  ", line[:200])
