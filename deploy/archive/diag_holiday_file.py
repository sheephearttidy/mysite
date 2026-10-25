#!/usr/bin/env python3
"""检查生产磁盘上的 holiday.js 是否为新版(读 /api/fx 的那版)"""
import io

P = "/var/www/mysite/js/holiday.js"
with io.open(P, encoding="utf-8") as f:
    js = f.read()

print(f"文件: {P}")
print(f"长度: {len(js)} 字符")
print(f"修改时间: ", end="")
import os
import time
st = os.stat(P)
print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)))
print(f"大小: {st.st_size} 字节")
print()
print("=== 关键特征检查 ===")
for kw in ("/api/fx", "readConfig", "xhr.open", "mode === 'manual'",
           "detectByDate", "effects", "XMLHttpRequest"):
    print(f"  {'✓' if kw in js else '✗'} 含 {kw!r}")
print()
print("=== 前 12 行 ===")
for i, line in enumerate(js.split("\n")[:12], 1):
    print(f"  {i:2d}| {line}")

print()
print("=== 与本地文件对比 ===")
local = r"D:\Agent_Work_Base\my-portfolio\js\holiday.js"
with io.open(local, encoding="utf-8") as f:
    ljs = f.read()
print(f"  本地长度: {len(ljs)}, 生产长度: {len(js)}, 一致: {ljs.strip() == js.strip()}")
