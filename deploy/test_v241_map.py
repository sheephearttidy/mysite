#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2.4.1 地图修复验证:真实轮廓 + 星星对齐 + 列表不重复"""
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:15102"
PASS = FAIL = 0
FAILS = []


def ck(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        FAILS.append(name)
        print(f"  FAIL {name}  {detail}")


r = subprocess.run(
    [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
     "--headless=new", "--disable-gpu", "--no-sandbox",
     "--virtual-time-budget=20000", "--dump-dom", BASE + "/map.html"],
    capture_output=True, encoding="utf-8", errors="replace", timeout=180)
dom = r.stdout
err = r.stderr

print("=" * 60)
print("v2.4.1 地图验证")
print("=" * 60)

land = re.findall(r'class="map-land"[^>]*>(.*?)</g>', dom, re.S)
paths = re.findall(r'<path d="(M[^"]+)"', land[0] if land else "")
ck("有真实大陆轮廓", len(paths) >= 6, f"paths={len(paths)}")

# 每块都在画布内
bad = []
for i, p in enumerate(paths):
    n = [float(x) for x in re.findall(r"-?\d+\.?\d*", p)]
    ys = n[1::2]
    if ys and (max(ys) > 520 or min(ys) < 0):
        bad.append(i)
ck("轮廓都在画布内", not bad, f"超界块={bad}")

# 无跨全宽横线(180° 回绕残留)
wraps = 0
for p in paths:
    pts = [(float(a), float(b)) for a, b in
           re.findall(r"(-?\d+\.?\d*) (-?\d+\.?\d*)", p)]
    for j in range(len(pts)):
        x1, y1 = pts[j]
        x2, y2 = pts[(j + 1) % len(pts)]
        if abs(x2 - x1) > 400 and abs(y2 - y1) < 6:
            wraps += 1
ck("无 180° 回绕横线", wraps == 0, f"发现 {wraps} 条")

# 星星
stars = re.findall(r'translate\(([\d.]+),([\d.]+)\)', dom)
ck("星星已渲染", len(stars) >= 1, f"stars={len(stars)}")

# 星星落在陆地包围盒内
boxes = []
for p in paths:
    n = [float(x) for x in re.findall(r"-?\d+\.?\d*", p)]
    xs, ys = n[0::2], n[1::2]
    if xs and ys:
        boxes.append((min(xs), min(ys), max(xs), max(ys)))
inside = sum(1 for sx, sy in stars
             if any(b[0] <= float(sx) <= b[2] and b[1] <= float(sy) <= b[3] for b in boxes))
ck("星星落在陆地上", stars and inside == len(stars), f"{inside}/{len(stars)}")

# 列表无重复
items = re.findall(r'<li class="city-item[^"]*">(.*?)</li>', dom, re.S)
names = [re.search(r'class="city-name">([^<]*)<', it).group(1)
         for it in items if re.search(r'class="city-name">([^<]*)<', it)]
ck("城市不重复", len(names) == len(set(names)), f"{names}")
ck("无「没在地图上」汇总条", "等你来找它" not in dom and "没在地图上" not in dom)

# 无 JS 报错
jserr = [l for l in err.splitlines() if "Uncaught" in l or "TypeError" in l]
ck("无 JS 异常", not jserr, str(jserr[:2]))

print("\n" + "=" * 60)
print(f"结果:PASS={PASS}  FAIL={FAIL}")
for f in FAILS:
    print("  -", f)
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)
