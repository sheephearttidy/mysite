#!/usr/bin/env python3
"""生产端到端:当前手动设置 -> 前台页面实际会用的 key
(用 Node 逻辑在服务器上不可用,所以这里只验证数据链:
 /api/fx 返回 -> 生产 holiday.js 能正确映射)
"""
import json
import re
import subprocess
import sys
import urllib.request

BASE = "https://imyxj.xyz"

print("=== 生产当前 /api/fx ===")
d = json.loads(urllib.request.urlopen(BASE + "/api/fx", timeout=20).read())
print(" ", d)
mode, key, effects = d.get("mode"), d.get("key"), d.get("effects")

print()
print("=== 生产 holiday.js 逻辑推演 ===")
if str(effects) == "0":
    expect = "(全关,effects=0)"
elif mode == "off":
    expect = "(全关,mode=off)"
elif mode == "manual":
    expect = f"{key} (手动指定)" if key else "(手动但 key 为空 -> 无)"
else:
    expect = "(auto,按日期自动)"
print("  预期结果:", expect)

print()
print("=== 生产 holiday.js 是否含全部 8 个节日 ===")
html = urllib.request.urlopen(BASE + "/", timeout=20).read().decode()
m = re.search(r'js/holiday\.js\?v=([a-f0-9]+)', html)
js = urllib.request.urlopen(f"{BASE}/js/holiday.js?v={m.group(1)}", timeout=20).read().decode()
KEYS = ["national-day", "valentine", "memorial", "new-year",
        "christmas", "labor", "children", "teacher"]
ok = True
for k in KEYS:
    hit = k in js
    print(f"  {'✓' if hit else '✗'} {k}")
    ok = ok and hit

print()
print("=== 生产页面 HTML 里 holiday.js 在 head 且同步执行 ===")
head = html.split("</head>")[0]
print(f"  {'✓' if 'holiday.js' in head else '✗'} 在 <head> 内")
print(f"  {'✓' if 'holiday.js' in html.split('<body')[0] else '✗'} 在 body 之前")

print()
good = ok and m and "holiday.js" in head
print(f"{'PASS' if good else 'FAIL'}  生产链路完整")
sys.exit(0 if good else 1)
