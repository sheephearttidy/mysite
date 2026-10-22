#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交叉校验:侧边栏 data-panel 值 vs PANELS 键 vs 实际存在的 panel-<name> 容器

三者必须完全对齐,否则点击会静默兜底到 skills 面板。
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

html = io.open("admin/templates/admin.html", encoding="utf-8").read()
js = io.open("admin/static/js/admin/admin-panel.js", encoding="utf-8").read()

sb = re.findall(r'data-panel="([^"]+)"', html)
panels_block = re.search(r"const PANELS = \{(.*?)\n\};", js, re.S)
keys = re.findall(r"'([^']+)':\s*\{", panels_block.group(1)) if panels_block else []
divs = re.findall(r'id="panel-([^"]+)"', html)

print(f"侧边栏 data-panel: {len(sb)} 个")
print(f"PANELS 键:        {len(keys)} 个")
print(f"panel-* 容器:     {len(divs)} 个\n")

ok = True
missing_key = [x for x in sb if x not in keys]
missing_div = [x for x in sb if x not in divs]
orphan_key = [x for x in keys if x not in sb]
orphan_div = [x for x in divs if x not in sb]

if missing_key:
    ok = False
    print(f"❌ 侧边栏有、PANELS 没键(会兜底到 skills): {missing_key}")
else:
    print("✅ 侧边栏每项都有 PANELS 标题")

if missing_div:
    ok = False
    print(f"❌ 侧边栏有、但没有 panel- 容器: {missing_div}")
else:
    print("✅ 侧边栏每项都有对应面板容器")

if orphan_key:
    print(f"ℹ️  PANELS 有多余键(无侧边栏入口): {orphan_key}")
if orphan_div:
    print(f"ℹ️  有多余面板容器(无侧边栏入口): {orphan_div}")

sys.exit(0 if ok else 1)
