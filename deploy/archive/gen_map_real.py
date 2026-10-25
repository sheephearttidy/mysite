#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""world-atlas land-110m -> 等距圆柱投影(1000x520) SVG path(修正版)

关键修正:
1. 闭合环去掉重复的末点(首尾相同会让 Douglas-Peucker 退化)
2. 面积阈值按占比 0.25%,保留大陆 + 主要岛屿
3. 简化容差 0.8 像素,保住海岸线形状
"""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
W, H = 1000, 520
SRC = "/tmp/land110m.json"

topo = json.load(open(SRC, encoding="utf-8"))
tr = topo["transform"]
sx, sy = tr["scale"]
tx, ty = tr["translate"]

arcs = []
for arc in topo["arcs"]:
    x = y = 0
    pts = []
    for dx, dy in arc:
        x += dx
        y += dy
        pts.append((x * sx + tx, y * sy + ty))
    arcs.append(pts)


def arc_points(idx):
    return list(reversed(arcs[~idx])) if idx < 0 else list(arcs[idx])


def ring_points(ring):
    out = []
    for i, idx in enumerate(ring):
        pts = arc_points(idx)
        out.extend(pts if i == 0 else pts[1:])
    return out


def proj(lon, lat):
    return ((lon + 180) / 360 * W, (90 - lat) / 180 * H)


def ring_area(pts):
    a = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def simplify_closed(pts, tol=0.8):
    """闭合环简化:先去重末点,再用 DP,最后补回闭合"""
    if len(pts) > 1 and abs(pts[0][0] - pts[-1][0]) < 1e-9 and abs(pts[0][1] - pts[-1][1]) < 1e-9:
        pts = pts[:-1]
    n = len(pts)
    if n < 8:
        return pts

    # 找离首点最远的点作为对分点,把环拆成两段分别 DP,避免退化
    x0, y0 = pts[0]
    far, fi = -1.0, n // 2
    for i in range(1, n):
        d = (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2
        if d > far:
            far, fi = d, i

    def dp(lo, hi):
        stack = [(lo, hi)]
        keep = {lo, hi}
        while stack:
            a, b = stack.pop()
            if b <= a + 1:
                continue
            x1, y1 = pts[a]
            x2, y2 = pts[b]
            dx, dy = x2 - x1, y2 - y1
            norm = (dx * dx + dy * dy) ** 0.5 or 1e-9
            best, bi = 0.0, -1
            for i in range(a + 1, b):
                px, py = pts[i]
                d = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / norm
                if d > best:
                    best, bi = d, i
            if best > tol and bi > 0:
                keep.add(bi)
                stack.append((a, bi))
                stack.append((bi, b))
        return keep

    k1 = dp(0, fi)
    # 后半段:fi..n-1 以及回到 0 的闭合段
    k2 = dp(fi, n - 1)
    keep = sorted(k1 | k2)
    return [pts[i] for i in keep]


rings = []
for geom in topo["objects"]["land"]["geometries"]:
    polys = [geom["arcs"]] if geom["type"] == "Polygon" else geom["arcs"]
    for poly in polys:
        pts = ring_points(poly[0])
        if len(pts) >= 4:
            pr = [proj(lon, lat) for lon, lat in pts]
            rings.append((ring_area(pr), pr))

total = sum(a for a, _ in rings)
MIN_AREA = total * 0.0025
kept = sorted([(a, r) for a, r in rings if a >= MIN_AREA], key=lambda t: -t[0])

paths = []
for area, r in kept:
    s = simplify_closed(r, 0.8)
    if len(s) < 3:
        continue
    d = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in s) + " Z"
    paths.append(d)

print(f"<!-- 真实陆地轮廓:world-atlas land-110m,等距圆柱投影 {W}x{H} -->")
print(f"<!-- x=(lon+180)/360*{W}, y=(90-lat)/180*{H};保留 {len(paths)} 块(占比>0.25%) -->")
for d in paths:
    print(f'          <path d="{d}" />')
print(f"\n# 保留 {len(paths)}/{len(rings)} 块,总字符 {sum(len(p) for p in paths)}",
      file=sys.stderr)
