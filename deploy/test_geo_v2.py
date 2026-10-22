#!/usr/bin/env python3
"""验证修复后的 geo(独立目录,加载新版 geo.py)"""
import sys

sys.path.insert(0, "/tmp/geotest")
import geo

print("=== 多源解析(nginx 日志真实 IP) ===")
ips = ["223.104.101.73", "45.138.12.51", "39.144.87.218",
       "113.215.189.82", "82.102.18.188", "59.82.83.223",
       "121.40.40.105", "111.55.24.203", "66.132.186.183",
       "34.175.42.73", "114.114.114.114", "8.8.8.8"]
for ip in ips:
    print(f"  {ip:18s} -> {geo.locate(ip)!r}")

print()
print("=== 缓存统计 ===")
print(geo.stats())

print()
print("=== 二次调用耗时(应命中缓存) ===")
import time
t0 = time.time()
for ip in ips:
    geo.locate(ip)
print(f"  {(time.time()-t0)*1000:.1f} ms")

print()
print("=== 缓存明细(空=失败短缓存) ===")
for k, (v, ts) in list(geo._cache.items()):
    print(f"  {k:18s} {v or '(空)':14s} age={time.time()-ts:.0f}s")
