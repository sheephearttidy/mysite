#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 map.html 里的手绘大陆轮廓替换成真实 world-atlas 轮廓"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

# 读真实路径
paths = []
with io.open("deploy/land_paths.txt", encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n")
        if line.strip().startswith("<path"):
            paths.append(line.strip())

assert paths, "没有读到路径"
print(f"读到 {len(paths)} 条真实轮廓")

# 读 map.html
p = "map.html"
html = io.open(p, encoding="utf-8").read()

# 找 <g class="map-land" ...> ... </g> 整块替换
m = re.search(
    r'[ \t]*<g class="map-land"[^>]*>.*?</g>',
    html, re.S)
assert m, "没找到 map-land 分组"

new_block = (
    '        <!-- 真实世界陆地轮廓(v2.4.1)\n'
    '             数据:world-atlas land-110m,等距圆柱投影 1000x520,\n'
    '             与 js/map.js 的 project() 完全同一套公式:\n'
    '             x=(lon+180)/360*1000, y=(90-lat)/180*520\n'
    '             所以星星一定落在真实陆地上 -->\n'
    '        <g class="map-land" fill="currentColor" opacity="0.18">\n'
    + "\n".join(paths) + "\n"
    '        </g>'
)

html = html[:m.start()] + new_block + html[m.end():]
io.open(p, "w", encoding="utf-8", newline="\n").write(html)
print(f"已替换,map.html 现在 {len(html)} 字符")
