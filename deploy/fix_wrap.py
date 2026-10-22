#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修 180° 经线回绕:跨全宽的线段把环切断,拆成独立子路径。

world-atlas 里亚欧大陆跨 ±180° 经线,投影后一条边会从 x=1000 直接
连回 x=0,在图上表现为一条横跨全图的直线。正确做法是把它当作
"路径断开",即用新的 M 起一段,而不是画一条长线。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

p = "map.html"
html = io.open(p, encoding="utf-8").read()
m = re.search(r'(<g class="map-land"[^>]*>)(.*?)(</g>)', html, re.S)
assert m, "没找到 map-land"
head, body, tail = m.group(1), m.group(2), m.group(3)

paths = re.findall(r'<path d="(M[^"]+)"\s*/>', body)
print(f"原始 {len(paths)} 块")

W = 1000
out = []
for i, d in enumerate(paths):
    pts = [(float(a), float(b)) for a, b in re.findall(r"(-?\d+\.?\d*) (-?\d+\.?\d*)", d)]
    if len(pts) < 3:
        continue
    # 拆成若干子路径:相邻点 x 跨度 > 40% 画布宽 => 断开
    subs = [[pts[0]]]
    for j in range(1, len(pts)):
        if abs(pts[j][0] - pts[j - 1][0]) > W * 0.4:
            subs.append([pts[j]])
        else:
            subs[-1].append(pts[j])
    # 处理闭合:若最后一点和第一点相连也跨全宽,则不要闭合
    cuts = 0
    for sub in subs:
        if len(sub) < 3:
            continue
        dd = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in sub) + " Z"
        out.append(dd)
        cuts += 1
    if cuts > 1:
        print(f"  #{i} 拆成 {cuts} 段(有跨 180° 回绕)")

print(f"输出 {len(out)} 段")
new_body = "\n" + "\n".join(f'          <path d="{d}" />' for d in out) + "\n        "
html = html[:m.start()] + head + new_body + tail + html[m.end():]
io.open(p, "w", encoding="utf-8", newline="\n").write(html)
print(f"已写入,map.html {len(html)} 字符")
