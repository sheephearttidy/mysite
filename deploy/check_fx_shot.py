#!/usr/bin/env python3
"""PIL 检查后台面板截图布局"""
import sys
from PIL import Image

p = r"D:\Agent_Work_Base\_shots\fx_panel.png"
im = Image.open(p).convert("RGB")
w, h = im.size
print(f"尺寸 {w}x{h}")
px = im.load()
P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n}  {e}")
        F += 1


# 1. 页面不是空白(有足够多的非背景色像素)
bg = px[5, 5]
non_bg = sum(1 for y in range(0, h, 4) for x in range(0, w, 4)
             if abs(px[x, y][0] - bg[0]) + abs(px[x, y][1] - bg[1]) + abs(px[x, y][2] - bg[2]) > 30)
ck("页面有内容(非空白)", non_bg > 2000, f"{non_bg}")

# 2. 顶部区域(侧边栏分组)有卡片边框色
top = im.crop((0, 0, w, 600))
colors = top.getcolors(maxcolors=200000)
ck("侧边栏区有配色", colors is not None and len(colors) > 20, str(len(colors) if colors else 0))

# 3. 中部面板区有黄色阴影装饰(主色系)
mid = im.crop((0, 700, w, 1400))
mc = mid.getcolors(maxcolors=200000)
warm = 0
if mc:
    for cnt, (r, g, b) in mc:
        if r > 180 and g > 140 and b < 130:  # 偏黄/橙
            warm += cnt
ck("面板区有暖色装饰", warm > 500, str(warm))

# 4. 底部有内容(说明面板足够高)
bot = im.crop((0, h - 300, w, h))
bc = bot.getcolors(maxcolors=200000)
ck("底部有内容", bc is not None and len(bc) > 5, str(len(bc) if bc else 0))

print()
print(f"通过 {P} 项,失败 {F} 项")
sys.exit(1 if F else 0)
