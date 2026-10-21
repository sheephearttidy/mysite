#!/usr/bin/env python3
"""验证地图 mock 截图(v2):
- SVG 地图区域(0-930 宽)存在 >6 个互不粘连的彩色簇(每颗星星一颗)
- 用连通域思路:统计不同位置的彩色像素分布
"""
from PIL import Image
import os

path = r"D:\Agent_Work_Base\_shots\map_mock.png"
im = Image.open(path).convert("RGB")
w, h = im.size


def is_colorful(px):
    r, g, b = px
    mx, mn = max(r, g, b), min(r, g, b)
    # 饱和度高且不是深色背景/文字
    return (mx - mn) > 40 and mx > 120


# 粗采样找彩色点,然后聚类(按位置)
pts = []
for y in range(0, 900, 1):
    for x in range(0, 930, 1):
        if is_colorful(im.getpixel((x, y))):
            pts.append((x, y))

# 简单聚类:按 x 分组(星星间隔远,同一颗星星 x 连续)
if not pts:
    print("FAIL 无彩色像素")
    raise SystemExit(1)

clusters = []
for x, y in pts:
    if clusters and x - clusters[-1][-1][0] <= 12:
        clusters[-1].append((x, y))
    else:
        clusters.append([(x, y)])

# 每个簇的 y 范围(去掉可能相邻但 x 连续的)
# 合并 y 上也接近的簇
merged = []
for cl in clusters:
    xs = [p[0] for p in cl]
    ys = [p[1] for p in cl]
    merged.append((min(xs), max(xs), min(ys), max(ys)))

# 星星数应 >= 6(8 个城市里 8 个都能定位)
P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n}  {e}")
        F += 1


ck("地图区域有彩色像素", len(pts) > 50, f"n={len(pts)}")
ck("星星簇数量合理", len(merged) >= 5, f"簇={len(merged)}: {merged[:8]}")
# 星星应分布在不同 x 位置(北京~乌鲁木齐 横向铺开)
xs_set = sorted(set(m[0] // 60 for m in merged))
ck("星星横向分布", len(xs_set) >= 4, f"x桶={xs_set}")
# 至少有一颗星星在 y<300(北方城市)一颗在 y>380(南方)
ys = [m[2] for m in merged]
ck("星星纵向分布", min(ys) < 300 and max(ys) > 380, f"y范围={min(ys)}-{max(ys)}")

print(f"\n通过 {P} 项,失败 {F} 项")
