#!/usr/bin/env python3
"""诊断:后台手动指定特效为何不生效"""
import json
import urllib.request

B = "http://127.0.0.1:5100"

print("=== /api/fx 当前返回 ===")
r = urllib.request.urlopen(B + "/api/fx", timeout=10)
raw = r.read().decode()
print("  raw:", raw)
d = json.loads(raw)
print("  mode :", repr(d.get("mode")))
print("  key  :", repr(d.get("key")))
print("  effects:", repr(d.get("effects")))

print()
print("=== 生产 holiday.js 关键片段 ===")
js = urllib.request.urlopen(B + "/js/holiday.js", timeout=10).read().decode()
for kw in ("/api/fx", "xhr.open", "mode === 'manual'", "readConfig", "detectByDate", "effects"):
    print(f"  {'✓' if kw in js else '✗'} 含 {kw!r}")
print()
print("  文件长度:", len(js))
print("  前 3 行:")
for line in js.split("\n")[:3]:
    print("   ", line)

print()
print("=== 数据库里的 fx 设置 ===")
import sqlite3
c = sqlite3.connect("/var/www/mysite/admin/data/mysite.db")
for row in c.execute("SELECT key, value FROM settings WHERE key LIKE 'fx%'"):
    print(f"  {row[0]:22s} = {row[1]!r}")
c.close()
