#!/usr/bin/env python3
"""诊断:直接调 db 函数看真实统计 + nginx 日志真实 IP + geo 解析"""
import subprocess
import sys

sys.path.insert(0, "/var/www/mysite/admin")
import db

db.DB_PATH = "/var/www/mysite/admin/data/mysite.db"

print("=== get_visit_stats(30) 直接调用 ===")
d = db.get_visit_stats(30)
print("total       :", d["total"])
print("total_real  :", d["total_real"])
print("today       :", d["today"])
print("by_day      :", d["by_day"])
print("by_day 天数 :", len(d["by_day"]), " <-- 前端按此画柱状图")
print("by_ref      :", d["by_ref"])
print("by_ua       :", d["by_ua"])
print("by_hour 非零:", {h: n for h, n in enumerate(d["by_hour"]) if n})
print("cities      :", d["cities"])
print("recent      :", len(d["recent"]), "条")

print()
print("=== get_visit_cities() 直接调用 ===")
print(db.get_visit_cities())

print()
print("=== nginx 日志真实 IP 统计 ===")
ips = {}
try:
    out = subprocess.run(
        ["grep", "-ohE", r"^[0-9]{1,3}(\.[0-9]{1,3}){3}",
         "/var/log/nginx/access.log"],
        capture_output=True, text=True, timeout=15).stdout
    for ip in out.split("\n"):
        ip = ip.strip()
        if ip:
            ips[ip] = ips.get(ip, 0) + 1
except Exception as e:
    print("读取失败:", e)
for ip, n in sorted(ips.items(), key=lambda x: -x[1])[:15]:
    print(f"  {ip:20s} {n} 次")

print()
print("=== geo 解析 ===")
import geo
for ip in list(ips.keys())[:12]:
    try:
        print(f"  {ip:20s} -> {geo.locate(ip)!r}")
    except Exception as e:
        print(f"  {ip:20s} -> ERROR {e}")
