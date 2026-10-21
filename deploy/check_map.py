#!/usr/bin/env python3
"""验证地图 mock 截图:
- 有星星(莫兰迪彩色小像素簇,分布在地图区域)
- 右侧城市列表有文字
"""
from PIL import Image
import os

path = r"D:\Agent_Work_Base\_shots\map_mock.png"
im = Image.open(path).convert("RGB")
w, h = im.size
print(f"尺寸 {w}x{h}")

# 星星颜色集合(莫兰迪):#ff6b9d #ffb84d #7ec8b8 #9aa7ff #f2a0c8 #8fd460 #ffd93d
STARS = [(255, 107, 157), (255, 184, 77), (126, 200, 184), (154, 167, 255),
         (242, 160, 200), (143, 212, 96), (255, 217, 61)]
tol = 20
found = {c: 0 for c in STARS}
P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n}  {e}")
        F += 1


for y in range(0, h, 1):
    for x in range(0, w, 1):
        px = im.getpixel((x, y))
        for c in STARS:
            if all(abs(a - b) <= tol for a, b in zip(px, c)):
                found[c] += 1

total = sum(found.values())
ck("地图有星星像素", total > 100, f"total={total}")
ck("多种星星颜色", sum(1 for v in found.values() if v > 10) >= 4,
   str({k: v for k, v in found.items() if v > 10}))

# 右侧列表区域(x > 950)有深色文字
dark = 0
for y in range(150, h - 50, 2):
    for x in range(950, w - 10, 2):
        r, g, b = im.getpixel((x, y))
        if r < 90 and g < 90 and b < 90:
            dark += 1
ck("右侧城市列表有文字", dark > 80, f"dark={dark}")

print(f"\n通过 {P} 项,失败 {F} 项")
