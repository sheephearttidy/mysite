#!/usr/bin/env python3
"""本地生成节日特效测试页 + headless Chrome 截图验证:
- 国庆(国旗飘) / 情人节(爱心) / 公祭日(全站黑白)
- 用 map.html 作为基底(带完整 CSS 链)
"""
import os
import re
import subprocess

ROOT = r"D:\Agent_Work_Base\my-portfolio"
OUT = r"D:\Agent_Work_Base\_shots"
os.makedirs(OUT, exist_ok=True)

# 基底页:用 about.html(结构简单)
base = os.path.join(ROOT, "about.html")
with open(base, encoding="utf-8") as f:
    html = f.read()

HOLIDAYS = {
    "national-day": "国庆",
    "valentine": "情人节",
    "memorial": "公祭日",
}

for key, label in HOLIDAYS.items():
    # 1. html 加 data-holiday
    h = html.replace('<html lang="zh-CN">', f'<html lang="zh-CN" data-holiday="{key}">', 1)
    # 2. 去掉 holiday.js 自动检测(直接注入 key,日期无关)
    h = h.replace('<script src="js/holiday.js"></script>', '')
    # 3. 截掉 real fetch(本地无后台,主脚本会静默回退,不影响粒子)
    out = os.path.join(ROOT, f"_shot_holiday_{key}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(h)

    url = f"http://127.0.0.1:8777/_shot_holiday_{key}.html"
    png = os.path.join(OUT, f"holiday_{key}.png")
    cmd = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
           "--headless", "--disable-gpu", "--hide-scrollbars",
           "--virtual-time-budget=6000",
           "--window-size=1280,900", f"--screenshot={png}", url]
    subprocess.run(cmd, capture_output=True, timeout=60)
    print(f"{label}: {'OK' if os.path.exists(png) else 'FAIL'} {png}")

print("done")
